"""
Unit tests for utils.py

Tests core utility functions with mocked API calls to avoid costs.
Run with: python -m pytest Tests/test_utils.py -v
"""
import os
import sys
import pytest
import pandas as pd
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime, timedelta
import googlemaps.exceptions
import logging

from utils import (
    get_google_api_key,
    get_hours_until_first_time_check,
    get_zip_data,
    get_zips_within_range,
    check_api_budget,
    load_csv_with_zip,
    update_api_usage_by_tier,
    get_current_usage_by_tier,
    calculate_tier_costs,
    validate_local_tracking
)


# --- Fixtures ---

@pytest.fixture
def mock_zip_csv():
    """Sample ZIP code CSV data"""
    return """zip,type,decommissioned,primary_city,state,latitude,longitude
02421,STANDARD,0,Lexington,MA,42.44,-71.23
02420,STANDARD,0,Lexington,MA,42.46,-71.22
99999,STANDARD,0,Test City,MA,,,
88888,STANDARD,0,,MA,42.0,-71.0
01195,STANDARD,1,Springfield,MA,42.1,-72.58
06001,STANDARD,0,Avon,CT,41.8,-72.83"""


@pytest.fixture
def mock_api_key_file():
    """Mock API key file content"""
    return "test_api_key_12345"


@pytest.fixture
def mock_distance_matrix_response():
    """Mock Google Distance Matrix API response"""
    return {
        'status': 'OK',
        'rows': [
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 8046, 'text': '5.0 mi'},
                        'duration': {'value': 600, 'text': '10 mins'}
                    }
                ]
            },
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 80467, 'text': '50.0 mi'},
                        'duration': {'value': 3000, 'text': '50 mins'}
                    }
                ]
            },
            {
                'elements': [
                    {
                        'status': 'ZERO_RESULTS'
                    }
                ]
            }
        ]
    }


# --- Test get_google_api_key ---

def test_get_google_api_key_success(mock_api_key_file, tmp_path):
    """Test successful API key retrieval"""
    key_file = tmp_path / "google_api_key"
    key_file.write_text(mock_api_key_file)

    key = get_google_api_key(key_loc=str(tmp_path), key_file="google_api_key")

    assert key == "test_api_key_12345"


def test_get_google_api_key_missing_file(tmp_path):
    """Test handling of missing API key file"""
    key = get_google_api_key(key_loc=str(tmp_path), key_file="nonexistent")

    assert key is None


def test_get_google_api_key_whitespace(tmp_path):
    """Test API key with trailing whitespace is stripped"""
    key_file = tmp_path / "google_api_key"
    key_file.write_text("  test_key_with_spaces  \n")

    key = get_google_api_key(key_loc=str(tmp_path), key_file="google_api_key")

    assert key == "test_key_with_spaces"


# --- Test get_hours_until_first_time_check ---

@patch('utils.datetime')
def test_get_hours_until_first_time_check_monday_before(mock_datetime):
    """Test calculation on Monday before first check time"""
    # Monday 6:00 AM (before 7:00 AM check)
    mock_now = datetime(2026, 1, 12, 6, 0, 0)  # Monday
    mock_datetime.now.return_value = mock_now

    hours = get_hours_until_first_time_check()

    assert hours == 1.0  # 1 hour until 7:00 AM


@patch('utils.datetime')
def test_get_hours_until_first_time_check_monday_after(mock_datetime):
    """Test calculation on Monday after first check time"""
    # Monday 8:00 AM (after 7:00 AM check)
    mock_now = datetime(2026, 1, 12, 8, 0, 0)  # Monday
    mock_datetime.now.return_value = mock_now

    hours = get_hours_until_first_time_check()

    assert hours == 167.0  # Next Monday at 7:00 AM (7 days)


@patch('utils.datetime')
def test_get_hours_until_first_time_check_friday(mock_datetime):
    """Test calculation on Friday"""
    # Friday 10:00 AM
    mock_now = datetime(2026, 1, 16, 10, 0, 0)  # Friday
    mock_datetime.now.return_value = mock_now

    hours = get_hours_until_first_time_check()

    assert hours == 69.0  # 3 days - 3 hours until Monday 7:00 AM


# --- Test get_zip_data ---

def test_get_zip_data_success(mock_zip_csv, tmp_path, monkeypatch):
    """Test successful ZIP data loading with filtering"""
    # Create mock CSV file
    csv_file = tmp_path / "test_zip.csv"
    csv_file.write_text(mock_zip_csv)

    # Patch ZIP_DATA_FILE constant
    monkeypatch.setattr('utils.ZIP_DATA_FILE', str(csv_file))
    monkeypatch.setattr('utils.TARGET_STATES', ['MA'])

    df = get_zip_data(states=['MA'])

    # Should only include MA STANDARD non-decommissioned zips
    assert len(df) == 2  # 02421, 02420 (excludes missing town, decom, CT)
    assert all(df['State'] == 'MA')
    assert '02421' in df['Zip'].values
    assert '02420' in df['Zip'].values


def test_get_zip_data_missing_file(tmp_path, monkeypatch):
    """Test handling of missing ZIP database file"""
    monkeypatch.setattr('utils.ZIP_DATA_FILE', str(tmp_path / "nonexistent.csv"))

    with pytest.raises(SystemExit) as exc_info:
        get_zip_data()

    assert exc_info.value.code == 1


def test_get_zip_data_filters_decommissioned(mock_zip_csv, tmp_path, monkeypatch):
    """Test that decommissioned ZIPs are filtered out"""
    csv_file = tmp_path / "test_zip.csv"
    csv_file.write_text(mock_zip_csv)

    monkeypatch.setattr('utils.ZIP_DATA_FILE', str(csv_file))

    df = get_zip_data(states=['MA'])

    # 01195 is decommissioned and should be excluded
    assert '01195' not in df['Zip'].values


def test_get_zip_data_missing_coordinates(mock_zip_csv, tmp_path, monkeypatch):
    """Test handling of missing Lat/Long (logged but not dropped)"""
    csv_file = tmp_path / "test_zip.csv"
    csv_file.write_text(mock_zip_csv)

    monkeypatch.setattr('utils.ZIP_DATA_FILE', str(csv_file))

    df = get_zip_data(states=['MA'])

    # 99999 has missing coordinates but valid Zip/Town/State
    # Should be included but with NaN for Lat/Long
    assert len(df) == 2


def test_get_zip_data_zero_padding(mock_zip_csv, tmp_path, monkeypatch):
    """Test that ZIP codes are zero-padded to 5 digits"""
    csv_file = tmp_path / "test_zip.csv"
    csv_file.write_text(mock_zip_csv)

    monkeypatch.setattr('utils.ZIP_DATA_FILE', str(csv_file))

    df = get_zip_data(states=['MA'])

    assert all(df['Zip'].str.len() == 5)


def test_check_api_budget_under_limit(tmp_path, monkeypatch):
    """Test budget check when under monthly limit"""
    tier_file = tmp_path / "usage_by_tier.txt"

    # Setup tier tracking file with current month
    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', False)  # Basic tier

    # Patch datetime BEFORE writing file so month_str matches
    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        mock_dt.strftime = datetime.strftime  # Keep strftime working

        # Write file using the same mocked datetime
        month_str = mock_dt.now.return_value.strftime('%Y-%m')
        tier_file.write_text(
            f"{month_str},basic,5000\n{month_str},advanced,0\n"
        )

        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 5000


def test_check_api_budget_at_limit(tmp_path, monkeypatch):
    """Test budget check when at monthly limit"""
    tier_file = tmp_path / "usage_by_tier.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', False)  # Basic tier
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 10000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        mock_dt.strftime = datetime.strftime

        month_str = mock_dt.now.return_value.strftime('%Y-%m')
        tier_file.write_text(
            f"{month_str},basic,10000\n{month_str},advanced,0\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            check_api_budget(100)

    assert exc_info.value.code == 1


def test_check_api_budget_missing_file(tmp_path, monkeypatch):
    """Test budget check with no existing usage file"""
    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE',
                       str(tmp_path / "nonexistent.txt"))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 20000)
    monkeypatch.setattr('utils.USE_TRAFFIC', False)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 0


def test_check_api_budget_new_month(tmp_path, monkeypatch):
    """Test budget resets for new month"""
    tier_file = tmp_path / "usage_by_tier.txt"
    tier_file.write_text("2025-12,basic,9000\n2025-12,advanced,0\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', False)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 0  # Reset for new month


# --- Test load_csv_with_zip ---

def test_load_csv_with_zip_success(tmp_path):
    """Test loading CSV with ZIP code handling"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Zip,Town\n421,Lexington\n1730,Bedford")

    df = load_csv_with_zip(str(csv_file))

    assert len(df) == 2
    assert df['Zip'].iloc[0] == '00421'  # Zero-padded
    assert df['Zip'].iloc[1] == '01730'


def test_load_csv_with_zip_missing_file(tmp_path):
    """Test handling of missing CSV file"""
    df = load_csv_with_zip(str(tmp_path / "nonexistent.csv"))

    assert df.empty


# --- Test get_zips_within_range ---

@patch('utils.googlemaps.Client')
def test_get_zips_within_range_success(mock_client, tmp_path, monkeypatch,
                                       mock_distance_matrix_response):
    """Test successful range check with mocked API"""
    # Setup tier tracking file
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,0\n{month_str},advanced,0\n")

    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 20000)
    monkeypatch.setattr('utils.USE_TRAFFIC', False)
    monkeypatch.setattr('utils.PROCESSED_DIR', str(processed_dir))
    monkeypatch.setattr('utils.CHUNK_SIZE', 3)
    monkeypatch.setattr('utils.PROXY_ON', False)

    # Mock API
    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = mock_distance_matrix_response
    mock_client.return_value = mock_instance

    # Create test data
    zip_data = pd.DataFrame({
        'Zip': ['02421', '02420', '01730'],
        'Town': ['Lexington', 'Lexington', 'Bedford'],
        'State': ['MA', 'MA', 'MA'],
        'Lat': [42.44, 42.46, 42.48],
        'Long': [-71.23, -71.22, -71.26]
    })

    with patch('utils.get_google_api_key', return_value='test_key'):
        with patch('utils.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)

            result = get_zips_within_range(
                "244 Wood St, Lexington, MA",
                zip_data,
                max_range=30
            )

    # Should return only zips within 30 miles (5mi and 50mi, but 50>30)
    assert len(result) == 1
    assert 'Lexington, MA 02421' in result


@patch('utils.googlemaps.Client')
def test_get_zips_within_range_filters_no_coords(mock_client, tmp_path,
                                                 monkeypatch):
    """Test that ZIPs without coordinates are excluded"""
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,0\n{month_str},advanced,0\n")

    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 20000)
    monkeypatch.setattr('utils.USE_TRAFFIC', False)
    monkeypatch.setattr('utils.PROCESSED_DIR', str(processed_dir))
    monkeypatch.setattr('utils.PROXY_ON', False)

    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = {'status': 'OK', 'rows': []}
    mock_client.return_value = mock_instance

    # Mix of valid and invalid coordinates
    zip_data = pd.DataFrame({
        'Zip': ['02421', '99999'],
        'Town': ['Lexington', 'Test'],
        'State': ['MA', 'MA'],
        'Lat': [42.44, None],
        'Long': [-71.23, None]
    })

    with patch('utils.get_google_api_key', return_value='test_key'):
        with patch('utils.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)

            result = get_zips_within_range(
                "244 Wood St, Lexington, MA",
                zip_data,
                max_range=30
            )

    # Should only process 02421 (has coordinates)
    call_args = mock_instance.distance_matrix.call_args
    assert len(call_args[1]['origins']) == 1
    assert 'Lexington, MA 02421' in call_args[1]['origins'][0]


@patch('utils.googlemaps.Client')
def test_get_zips_within_range_api_error(mock_client, tmp_path, monkeypatch):
    """Test handling of API errors"""
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,0\n{month_str},advanced,0\n")

    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 20000)
    monkeypatch.setattr('utils.USE_TRAFFIC', False)
    monkeypatch.setattr('utils.PROCESSED_DIR', str(processed_dir))
    monkeypatch.setattr('utils.PROXY_ON', False)

    # Mock API error
    mock_instance = MagicMock()
    mock_instance.distance_matrix.side_effect = \
        googlemaps.exceptions.ApiError("API Error")
    mock_client.return_value = mock_instance

    zip_data = pd.DataFrame({
        'Zip': ['02421'],
        'Town': ['Lexington'],
        'State': ['MA'],
        'Lat': [42.44],
        'Long': [-71.23]
    })

    with patch('utils.get_google_api_key', return_value='test_key'):
        with patch('utils.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)

            result = get_zips_within_range(
                "244 Wood St, Lexington, MA",
                zip_data,
                max_range=30
            )

    # Should return empty list on error
    assert len(result) == 0


def test_get_zips_within_range_no_api_key(tmp_path, monkeypatch):
    """Test handling of missing API key"""
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,0\n{month_str},advanced,0\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT_BASIC', 20000)
    monkeypatch.setattr('utils.USE_TRAFFIC', False)

    zip_data = pd.DataFrame({
        'Zip': ['02421'],
        'Town': ['Lexington'],
        'State': ['MA'],
        'Lat': [42.44],
        'Long': [-71.23]
    })

    with patch('utils.get_google_api_key', return_value=None):
        with pytest.raises(SystemExit) as exc_info:
            get_zips_within_range(
                "244 Wood St, Lexington, MA",
                zip_data,
                max_range=30
            )

    assert exc_info.value.code == 1


# --- Test Tier-Specific Tracking ---

def test_update_api_usage_by_tier_basic(tmp_path, monkeypatch):
    """Test updating basic tier usage"""
    tier_file = tmp_path / "usage_by_tier.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', None)  # Basic tier

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        basic, advanced, tier = update_api_usage_by_tier(100)

    assert tier == 'basic'
    assert basic == 100
    assert advanced == 0
    assert tier_file.exists()

    # Verify file contents
    content = tier_file.read_text()
    assert '2026-01,basic,100' in content
    assert '2026-01,advanced,0' in content


def test_update_api_usage_by_tier_advanced(tmp_path, monkeypatch):
    """Test updating advanced tier usage"""
    tier_file = tmp_path / "usage_by_tier.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', True)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        basic, advanced, tier = update_api_usage_by_tier(50)

    assert tier == 'advanced'
    assert basic == 0
    assert advanced == 50


def test_update_api_usage_by_tier_accumulates(tmp_path, monkeypatch):
    """Test that tier usage accumulates across multiple calls"""
    tier_file = tmp_path / "usage_by_tier.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', None)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        # First call
        basic1, advanced1, _ = update_api_usage_by_tier(100)
        assert basic1 == 100

        # Second call
        basic2, advanced2, _ = update_api_usage_by_tier(50)
        assert basic2 == 150  # Should accumulate
        assert advanced2 == 0


def test_update_api_usage_by_tier_mixed(tmp_path, monkeypatch):
    """Test updating both basic and advanced in same month"""
    tier_file = tmp_path / "usage_by_tier.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', False)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        # Basic tier call
        basic1, advanced1, _ = update_api_usage_by_tier(
            100,
            use_traffic=False
        )
        assert basic1 == 100
        assert advanced1 == 0

        # Advanced tier call
        basic2, advanced2, _ = update_api_usage_by_tier(
            50,
            use_traffic=True
        )
        assert basic2 == 100  # Unchanged
        assert advanced2 == 50


def test_update_api_usage_by_tier_new_month(tmp_path, monkeypatch):
    """Test that usage resets for new month"""
    tier_file = tmp_path / "usage_by_tier.txt"
    tier_file.write_text("2025-12,basic,5000\n2025-12,advanced,2000\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.USE_TRAFFIC', False)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        basic, advanced, _ = update_api_usage_by_tier(100)

    # Should reset for new month
    assert basic == 100
    assert advanced == 0


def test_get_current_usage_by_tier_empty(tmp_path, monkeypatch):
    """Test getting usage when no tracking file exists"""
    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE',
                        str(tmp_path / "nonexistent.txt"))

    usage = get_current_usage_by_tier()

    assert usage['basic'] == 0
    assert usage['advanced'] == 0
    assert usage['basic_remaining'] == 10000
    assert usage['advanced_remaining'] == 5000
    assert usage['total'] == 0


def test_get_current_usage_by_tier_with_data(tmp_path, monkeypatch):
    """Test getting usage with existing data"""
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(
        f"{month_str},basic,3000\n{month_str},advanced,2000\n"
    )

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    usage = get_current_usage_by_tier()

    assert usage['basic'] == 3000
    assert usage['advanced'] == 2000
    assert usage['basic_remaining'] == 7000
    assert usage['advanced_remaining'] == 3000
    assert usage['total'] == 5000


def test_calculate_tier_costs_all_free(tmp_path):
    """Test cost calculation when under free tier"""
    costs = calculate_tier_costs(basic_count=5000, advanced_count=3000)

    assert costs['basic_cost'] == 0.0
    assert costs['advanced_cost'] == 0.0
    assert costs['total_cost'] == 0.0


def test_calculate_tier_costs_basic_paid(tmp_path):
    """Test cost calculation when basic exceeds free tier"""
    # 12,000 basic = 2,000 billable @ $5/1000 = $10
    costs = calculate_tier_costs(basic_count=12000, advanced_count=0)

    assert costs['basic_cost'] == 10.0
    assert costs['advanced_cost'] == 0.0
    assert costs['total_cost'] == 10.0


def test_calculate_tier_costs_advanced_paid(tmp_path):
    """Test cost calculation when advanced exceeds free tier"""
    # 7,000 advanced = 2,000 billable @ $10/1000 = $20
    costs = calculate_tier_costs(basic_count=0, advanced_count=7000)

    assert costs['basic_cost'] == 0.0
    assert costs['advanced_cost'] == 20.0
    assert costs['total_cost'] == 20.0


def test_calculate_tier_costs_both_paid(tmp_path):
    """Test cost calculation when both tiers exceed free tier"""
    # 12,000 basic = 2,000 billable @ $5/1000 = $10
    # 7,000 advanced = 2,000 billable @ $10/1000 = $20
    # Total = $30
    costs = calculate_tier_costs(basic_count=12000, advanced_count=7000)

    assert costs['basic_cost'] == 10.0
    assert costs['advanced_cost'] == 20.0
    assert costs['total_cost'] == 30.0


def test_validate_local_tracking_with_tiers(tmp_path, monkeypatch):
    """Test validation includes tier breakdown"""
    # Setup tier tracking file
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(
        f"{month_str},basic,3000\n{month_str},advanced,2000\n"
    )

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    # Mock get_monthly_element_usage_from_google
    with patch('utils.get_monthly_element_usage_from_google') as mock_google:
        mock_google.return_value = (3000, 2000, 5000)  # basic, adv, total

        validation = validate_local_tracking()

    assert validation['local_basic'] == 3000
    assert validation['local_advanced'] == 2000
    assert validation['local_total'] == 5000
    assert validation['google'] == 5000
    assert validation['discrepancy'] == 0
    assert 'costs' in validation
    assert 'tier_usage' in validation


def test_update_api_usage_by_tier_file_permission_error(
        tmp_path, monkeypatch
):
    """Test handling of file permission errors"""
    tier_file = tmp_path / "usage_by_tier.txt"
    tier_file.write_text("dummy")
    tier_file.chmod(0o444)  # Read-only

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.TRAFFIC_MODEL', None)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        with pytest.raises(IOError):
            update_api_usage_by_tier(100)

    # Cleanup
    tier_file.chmod(0o644)


def test_update_api_usage_by_tier_corrupted_file(tmp_path, monkeypatch):
    """Test handling of corrupted tracking file"""
    tier_file = tmp_path / "usage_by_tier.txt"
    tier_file.write_text("corrupted,data,here,extra,fields\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.TRAFFIC_MODEL', None)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)

        # Should handle corruption gracefully and start fresh
        basic, advanced, tier = update_api_usage_by_tier(100)

    assert basic == 100
    assert advanced == 0


def test_malformed_tier_file_logs_warning(tmp_path, caplog, monkeypatch):
    """Verify malformed lines are logged"""
    tier_file = tmp_path / "usage.txt"
    tier_file.write_text("2026-02,basic,5,249\n")  # Malformed

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.WARNING, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Malformed line" in caplog.text
    assert "expected 3 fields, got 4" in caplog.text


def test_malformed_tier_file_logs_warning(tmp_path, caplog, monkeypatch):
    """Verify malformed lines are logged"""
    tier_file = tmp_path / "usage.txt"
    tier_file.write_text("2026-02,basic,5,249\n")  # Malformed: 4 fields

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.WARNING, logger='utils'):
        usage = get_current_usage_by_tier()

    # Verify warning was logged
    assert "Malformed line" in caplog.text
    assert "expected 3 fields, got 4" in caplog.text
    assert "2026-02,basic,5,249" in caplog.text


def test_critical_discrepancy_logs_error(tmp_path, caplog, monkeypatch):
    """Verify large discrepancies (>50%) trigger ERROR logs"""
    # Setup tier file with low count
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,100\n{month_str},advanced,0\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    # Mock Google reporting much higher count
    with patch('utils.get_monthly_element_usage_from_google') as mock_google:
        mock_google.return_value = (0, 0, 10000)  # Google shows 10k

        with caplog.at_level(logging.ERROR, logger='utils'):
            validation = validate_local_tracking()

    # Verify ERROR level was used
    assert "CRITICAL" in caplog.text
    assert "severely out of sync" in caplog.text
    assert validation['discrepancy_ratio'] > 0.5


def test_zero_counts_warning(tmp_path, caplog, monkeypatch):
    """Verify warning when both counts are zero despite file existing"""
    tier_file = tmp_path / "usage.txt"
    # Old month data that won't match current month
    tier_file.write_text("2025-01,basic,1000\n2025-01,advanced,500\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.WARNING, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Both tier counts are zero despite reading file" in caplog.text
    assert "corrupted or for wrong month" in caplog.text


def test_write_confirmation_logged(tmp_path, caplog, monkeypatch):
    """Verify write operations are logged at DEBUG level"""
    tier_file = tmp_path / "usage.txt"

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    # Must mock datetime to ensure consistent month string
    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 2, 13)
        mock_dt.strftime = datetime.strftime  # Keep strftime working

        with caplog.at_level(logging.DEBUG, logger='utils'):
            basic, advanced, tier = update_api_usage_by_tier(
                100,
                use_traffic=False
            )

    # Check for write confirmation
    assert "Wrote tier tracking to" in caplog.text
    assert "basic=100" in caplog.text
    assert str(tier_file) in caplog.text


def test_moderate_discrepancy_logs_warning(tmp_path, caplog, monkeypatch):
    """Verify moderate discrepancies (10-50%) trigger WARNING logs"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,1000\n{month_str},advanced,0\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    # Mock Google reporting 20% more (1200 vs 1000)
    with patch('utils.get_monthly_element_usage_from_google') as mock_google:
        mock_google.return_value = (0, 0, 1200)  # 20% discrepancy

        with caplog.at_level(logging.WARNING, logger='utils'):
            validation = validate_local_tracking()

    assert "Significant discrepancy detected" in caplog.text
    # Check for percentage in output (could be formatted different ways)
    assert "%" in caplog.text
    assert validation['discrepancy_ratio'] > 0.1
    assert validation['discrepancy_ratio'] < 0.5


def test_acceptable_discrepancy_logs_info(tmp_path, caplog, monkeypatch):
    """Verify small discrepancies log at INFO level with success message"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,1000\n{month_str},advanced,0\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))
    monkeypatch.setattr('utils.MAX_ACCEPTABLE_DISCREPANCY', 100)

    # Mock Google reporting nearly same count (within tolerance)
    with patch('utils.get_monthly_element_usage_from_google') as mock_google:
        mock_google.return_value = (0, 0, 1050)  # Only 50 difference

        with caplog.at_level(logging.INFO, logger='utils'):
            validation = validate_local_tracking()

    assert "Tracking validation passed" in caplog.text
    assert validation['discrepancy'] <= 100


def test_invalid_count_value_logged(tmp_path, caplog, monkeypatch):
    """Verify invalid numeric values trigger ERROR logs"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,not_a_number\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.ERROR, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Invalid count value" in caplog.text
    assert "not_a_number" in caplog.text


def test_unknown_tier_logged(tmp_path, caplog, monkeypatch):
    """Verify unknown tier names trigger WARNING logs"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},premium,500\n")  # Unknown tier

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.WARNING, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Unknown tier" in caplog.text
    assert "premium" in caplog.text


def test_malformed_line_includes_line_number(tmp_path, caplog, monkeypatch):
    """Verify line numbers are included in malformed line warnings"""
    tier_file = tmp_path / "usage.txt"
    tier_file.write_text(
        "2026-02,basic,100\n"  # Line 1: OK
        "2026-02,advanced,200,extra\n"  # Line 2: Malformed
    )

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.WARNING, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "line 2" in caplog.text
    assert "Malformed line" in caplog.text


def test_read_summary_logged(tmp_path, caplog, monkeypatch):
    """Verify read summary is logged showing lines read and malformed count"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(
        f"{month_str},basic,100\n"  # Line 1: OK
        f"{month_str},advanced,200,x\n"  # Line 2: Malformed
    )

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.DEBUG, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Tier file read complete" in caplog.text
    assert "2 lines" in caplog.text
    assert "1 malformed" in caplog.text


def test_current_usage_summary_logged(tmp_path, caplog, monkeypatch):
    """Verify summary of current usage is logged at INFO level"""
    tier_file = tmp_path / "usage.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,1234\n{month_str},advanced,5678\n")

    monkeypatch.setattr('utils.API_TIER_TRACKING_FILE', str(tier_file))

    with caplog.at_level(logging.INFO, logger='utils'):
        usage = get_current_usage_by_tier()

    assert "Current usage:" in caplog.text
    assert "Basic=1,234" in caplog.text  # Formatted with commas
    assert "Advanced=5,678" in caplog.text
    assert "Total=6,912" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
