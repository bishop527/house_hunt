"""
Unit tests for Score/calculate_scores.py

Tests scoring algorithms and ranking logic with mock data.
Run with: python -m pytest Tests/Score/test_calculate_scores.py -v
"""
import os
import sys
import pytest
import pandas as pd
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from Score.calculate_scores import LocationScorer, calculate_scores


# --- Fixtures ---

@pytest.fixture
def sample_config():
    """Sample scoring configuration"""
    return {
        "weights": {
            "commute": 0.50,
            "housing": 0.35,
            "crime": 0.15
        },
        "commute_preferences": {
            "ideal_time_minutes": 20,
            "max_acceptable_time": 45
        },
        "housing_preferences": {
            "budget_min": 400000,
            "budget_max": 600000,
            "budget_ideal": 500000,
            "over_budget_penalty_scale": "exponential",
            "ideal_tax_rate": 10.0,
            "max_acceptable_tax_rate": 15.0
        },
        "filters": {
            "max_commute_time": 60,
            "max_price": 800000,
            "require_both_datasets": True
        }
    }


@pytest.fixture
def sample_commute_data():
    """Sample commute statistics"""
    return pd.DataFrame({
        'Town': ['Lexington', 'Bedford', 'Concord', 'Arlington'],
        'State': ['MA', 'MA', 'MA', 'MA'],
        'Zip': ['02421', '01730', '01742', '02474'],
        'Distance': [5.0, 10.0, 12.5, 8.5],
        'Total_Runs': [10, 8, 6, 12],
        'Last_Run_Date': ['2026-01-15'] * 4,
        'Min_Time': [12.5, 18.0, 25.0, 16.0],
        'Max_Time': [18.3, 25.0, 35.0, 22.0],
        'Average_Time': [15.2, 21.0, 28.5, 18.0]
    })


@pytest.fixture
def sample_housing_data():
    """Sample housing statistics"""
    return pd.DataFrame({
        'Town': ['Lexington', 'Bedford', 'Concord', 'Arlington'],
        'State': ['MA', 'MA', 'MA', 'MA'],
        'Zip': ['02421', '01730', '01742', '02474'],
        'Total_Runs': [5, 4, 3, 6],
        'Last_Run_Date': ['2026-01-14'] * 4,
        'Min_Price': [600000, 480000, 720000, 780000],
        'Max_Price': [700000, 560000, 840000, 880000],
        'Average_Price': [650000, 520000, 780000, 825000],
        'Latest_Median_Sale': [650000, 520000, 780000, 825000],
        'Latest_Median_List': [670000, 540000, 800000, 850000],
        'Latest_PPSF': [425, 380, 510, 575],
        'Latest_Homes_Sold': [8, 10, 5, 6],
        'Latest_Inventory': [12, 15, 8, 7],
        'Months_Of_Supply': [4.2, 5.5, 3.8, 2.9],
        'Tax_Rate_Per_1000': [10.76, 17.98, 11.23, 13.52]  # Tax rates per 1000
    })

@pytest.fixture
def sample_crime_data():
    """Sample crime statistics"""
    return pd.DataFrame({
        'Town': ['Lexington', 'Bedford', 'Concord'],
        'Crime_Score': [95.0, 85.0, 90.0],
        'Crime_Rate_Per_1000': [2.5, 4.0, 3.2],
        'Total_Crime_Weight': [50, 60, 55],
        '2024': [20000, 15000, 17000]
    })


# --- Test LocationScorer initialization ---

def test_scorer_init_with_config(tmp_path, sample_config):
    """Test scorer initialization with config file"""
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f)

    scorer = LocationScorer(str(config_file))

    assert scorer.config['weights']['commute'] == 0.50
    assert scorer.config['weights']['housing'] == 0.35
    assert scorer.config['weights']['crime'] == 0.15


def test_scorer_init_without_config(sample_config):
    """Test scorer initialization with fallback to default config"""
    # Mock default config file existence and content
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', MagicMock()):
            with patch('json.load', return_value=sample_config):
                scorer = LocationScorer(None)

    assert 'weights' in scorer.config
    assert 'housing_preferences' in scorer.config


def test_scorer_init_invalid_json(tmp_path):
    """Test scorer handles invalid JSON by exiting"""
    config_file = tmp_path / "bad_config.json"
    config_file.write_text("{ invalid json }")

    # Should call sys.exit(1) when JSON is invalid
    with pytest.raises(SystemExit) as exc_info:
        LocationScorer(str(config_file))

    assert exc_info.value.code == 1


# --- Test commute scoring functions ---

def test_score_commute_time_ideal(sample_config):
    """Test commute time scoring for ideal time"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # 15 min < 20 min ideal = full points
    score = scorer._score_commute_time(15.0)

    assert score == 100.0


def test_score_commute_time_acceptable(sample_config):
    """Test commute time scoring for acceptable time"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # 30 min between ideal (20) and max (45)
    score = scorer._score_commute_time(30.0)

    assert 50.0 <= score <= 100.0


def test_score_commute_time_poor(sample_config):
    """Test commute time scoring for poor time"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # 55 min > max acceptable (45)
    score = scorer._score_commute_time(55.0)

    assert 0.0 <= score <= 50.0


def test_calculate_commute_score(sample_config, sample_commute_data):
    """Test full commute score calculation"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    row = sample_commute_data.iloc[0]  # Lexington
    result = scorer.calculate_commute_score(row)

    assert 'commute_score' in result
    assert 0 <= result['commute_score'] <= 100


# --- Test housing scoring functions ---

def test_score_housing_price_ideal(sample_config):
    """Test housing price scoring for ideal budget"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # $500k = ideal budget
    score = scorer._score_housing_price(500000)

    assert 45.0 <= score <= 50.0


def test_score_housing_price_within_budget(sample_config):
    """Test housing price scoring within budget"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # $550k between ideal (500k) and max (600k)
    score = scorer._score_housing_price(550000)

    assert 35.0 <= score <= 45.0


def test_score_housing_price_over_budget_exponential(sample_config):
    """Test exponential penalty for over-budget pricing"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    # $650k = 8.3% over budget
    score_650k = scorer._score_housing_price(650000)

    # $700k = 16.7% over budget
    score_700k = scorer._score_housing_price(700000)

    # Exponential penalty should make 700k worse than 650k
    assert score_700k < score_650k

    # The gap should be significant (at least 3 points)
    assert (score_650k - score_700k) >= 3.0


def test_calculate_housing_score(sample_config, sample_housing_data):
    """Test full housing score calculation"""
    scorer = LocationScorer(None)
    scorer.config = sample_config
    scorer.housing_data = sample_housing_data

    row = sample_housing_data.iloc[1]  # Bedford
    result = scorer.calculate_housing_score(row)

    assert 'housing_score' in result
    assert 'price_score' in result
    assert 'tax_score' in result
    assert 0 <= result['housing_score'] <= 100


# --- Test tier assignment ---

def test_assign_tier_a_plus(sample_config):
    """Test A+ tier assignment"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    tier = scorer._assign_tier(96.0)

    assert tier == 'A+'


def test_assign_tier_b(sample_config):
    """Test B tier assignment"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    tier = scorer._assign_tier(77.0)

    assert tier == 'B'


def test_assign_tier_f(sample_config):
    """Test F tier assignment"""
    scorer = LocationScorer(None)
    scorer.config = sample_config

    tier = scorer._assign_tier(35.0)

    assert tier == 'F'


# --- Test full scoring pipeline ---

def test_score_all_locations(sample_config, sample_commute_data,
                             sample_housing_data, sample_crime_data):
    """Test scoring all locations end-to-end"""
    scorer = LocationScorer(None)
    scorer.config = sample_config
    scorer.commute_data = sample_commute_data
    scorer.housing_data = sample_housing_data
    scorer.crime_data = sample_crime_data

    results = scorer.score_all_locations()

    assert results is not None
    assert len(results) > 0
    assert 'Total_Score' in results.columns
    assert 'Tier' in results.columns
    assert 'Rank' in results.columns

    # Results should be sorted by score descending
    assert results['Total_Score'].is_monotonic_decreasing


def test_score_all_locations_with_filters(sample_config,
                                          sample_commute_data,
                                          sample_housing_data,
                                          sample_crime_data):
    """Test filtering during scoring"""
    scorer = LocationScorer(None)
    scorer.config = sample_config
    scorer.config['filters']['max_commute_time'] = 20  # Very strict
    scorer.commute_data = sample_commute_data
    scorer.housing_data = sample_housing_data
    scorer.crime_data = sample_crime_data

    results = scorer.score_all_locations()

    # Should filter out locations with commute > 20 min
    assert all(results['Avg_Commute_Min'] <= 20)


def test_score_all_locations_missing_data():
    """Test handling of missing data"""
    scorer = LocationScorer(None)
    scorer.commute_data = None
    scorer.housing_data = None
    scorer.crime_data = None

    results = scorer.score_all_locations()

    assert results is None


@pytest.mark.unit
def test_save_results(tmp_path, sample_config, sample_commute_data,
                      sample_housing_data, sample_crime_data, monkeypatch):
    """Test saving results to CSV"""
    # Force property type and results dir for predictable filename
    monkeypatch.setattr('Score.calculate_scores.PROPERTY_TYPES', ['TestType'])
    monkeypatch.setattr('Score.calculate_scores.RESULTS_DIR', str(tmp_path))

    scorer = LocationScorer(None)
    scorer.config = sample_config
    scorer.commute_data = sample_commute_data
    scorer.housing_data = sample_housing_data
    scorer.crime_data = sample_crime_data

    # Expected dynamic filename: scored_locations-TestType.csv
    expected_file = tmp_path / "scored_locations-TestType.csv"

    scorer.score_all_locations()
    success = scorer.save_results()

    assert success
    assert expected_file.exists()

    # Verify CSV can be read back
    df = pd.read_csv(expected_file)
    assert len(df) > 0
    assert 'Total_Score' in df.columns


def test_get_summary_stats(sample_config, sample_commute_data,
                           sample_housing_data, sample_crime_data):
    """Test summary statistics generation"""
    scorer = LocationScorer(None)
    scorer.config = sample_config
    scorer.commute_data = sample_commute_data
    scorer.housing_data = sample_housing_data
    scorer.crime_data = sample_crime_data

    scorer.score_all_locations()
    stats = scorer.get_summary_stats()

    assert 'total_locations' in stats
    assert 'avg_total_score' in stats
    assert 'tier_counts' in stats
    assert 'top_location' in stats
    assert stats['total_locations'] > 0


# --- Integration test ---

@pytest.mark.integration
@patch('Score.calculate_scores.load_csv_with_zip')
def test_calculate_scores_main_function(mock_load, tmp_path,
                                        sample_config,
                                        sample_commute_data,
                                        sample_housing_data,
                                        sample_crime_data,
                                        monkeypatch):
    """Test main calculate_scores() function"""
    # Setup config file
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f)

    # Force property type and results dir for predictable filename
    monkeypatch.setattr('Score.calculate_scores.PROPERTY_TYPES', ['MainTest'])
    monkeypatch.setattr('Score.calculate_scores.RESULTS_DIR', str(tmp_path))
    
    # Expected output file
    expected_file = tmp_path / "scored_locations-MainTest.csv"

    # Mock housing data re-derivation to return sample data
    # (The function normally returns a DataFrame formatted for scorer)
    def mock_derive(self):
        df = sample_housing_data.copy()
        # Ensure column names match what scorer expects from housing stats
        df = df.rename(columns={
            'Latest_Median_Sale': 'Latest_Median_Sale', # already matches
            'Average_Price': 'Avg_Monthly_Price'
        })
        return df
    
    monkeypatch.setattr(LocationScorer, '_derive_housing_from_redfin', mock_derive)

    # Mock CSV loading
    def mock_load_side_effect(filepath):
        if 'commute' in filepath:
            return sample_commute_data
        elif 'housing' in filepath:
            return sample_housing_data
        elif 'crime' in filepath:
            return sample_crime_data
        return pd.DataFrame()

    mock_load.side_effect = mock_load_side_effect

    # Run main function
    success, _, _, _ = calculate_scores(str(config_file))

    assert success
    assert expected_file.exists()



if __name__ == "__main__":
    pytest.main([__file__, "-v"])