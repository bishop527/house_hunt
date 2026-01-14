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

from utils import (
    get_google_api_key,
    get_hours_until_first_time_check,
    get_zip_data,
    get_zips_within_range,
    check_api_budget,
    update_api_usage,
    load_csv_with_zip
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


# --- Test check_api_budget ---

def test_check_api_budget_under_limit(tmp_path, monkeypatch):
    """Test budget check when under monthly limit"""
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,5000")

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 5000


def test_check_api_budget_at_limit(tmp_path, monkeypatch):
    """Test budget check when at monthly limit"""
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,20000")

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        with pytest.raises(SystemExit) as exc_info:
            check_api_budget(100)

    assert exc_info.value.code == 1


def test_check_api_budget_missing_file(tmp_path, monkeypatch):
    """Test budget check with no existing usage file"""
    monkeypatch.setattr('utils.API_MONTHLY_COUNTER',
                       str(tmp_path / "nonexistent.txt"))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 0


def test_check_api_budget_new_month(tmp_path, monkeypatch):
    """Test budget resets for new month"""
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2025-12,19000")  # Previous month

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        can_proceed, current = check_api_budget(100)

    assert can_proceed is True
    assert current == 0  # Reset for new month


# --- Test update_api_usage ---

def test_update_api_usage_new_file(tmp_path, monkeypatch):
    """Test creating new usage counter file"""
    counter_file = tmp_path / "usage_counter.txt"

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        new_total = update_api_usage(150)

    assert new_total == 150
    assert counter_file.read_text() == "2026-01,150"


def test_update_api_usage_existing_file(tmp_path, monkeypatch):
    """Test updating existing usage counter"""
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,5000")

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

    with patch('utils.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 15)
        new_total = update_api_usage(150)

    assert new_total == 5150
    assert counter_file.read_text() == "2026-01,5150"


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
    # Setup
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,0")
    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)
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
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,0")
    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)
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
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,0")
    processed_dir = tmp_path / "Processed"
    processed_dir.mkdir()

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)
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
    counter_file = tmp_path / "usage_counter.txt"
    counter_file.write_text("2026-01,0")

    monkeypatch.setattr('utils.API_MONTHLY_COUNTER', str(counter_file))
    monkeypatch.setattr('utils.API_MONTHLY_LIMIT', 20000)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
