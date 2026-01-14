"""
Unit tests for collect_commute_data.py

Tests commute data collection logic with mocked API calls.
Run with: python -m pytest Tests/Commute/test_collect_commute_data.py -v
"""
import os
import sys
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Ensure project root is in path
# This file is at: house_hunt/Tests/Commute/test_collect_commute_data.py
# Project root is: house_hunt/
current_file = os.path.abspath(__file__)
tests_commute_dir = os.path.dirname(current_file)
tests_dir = os.path.dirname(tests_commute_dir)
project_root = os.path.dirname(tests_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from collect_commute_data import (
    determine_direction,
    fetch_commute_times,
    process_element,
    load_historical_data,
    update_statistics
)


# --- Fixtures ---

@pytest.fixture
def mock_addresses():
    """Sample addresses for testing"""
    return [
        "Lexington, MA 02421",
        "Bedford, MA 01730",
        "Concord, MA 01742"
    ]


@pytest.fixture
def mock_api_response_morning():
    """Mock API response for morning commute (Home -> Work)"""
    return {
        'status': 'OK',
        'rows': [
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 8046},  # meters
                        'duration': {'value': 600},   # seconds
                        'duration_in_traffic': {'value': 780}  # 13 min
                    }
                ]
            },
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 16093},
                        'duration': {'value': 900},
                        'duration_in_traffic': {'value': 1200}  # 20 min
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


@pytest.fixture
def mock_historical_csv():
    """Sample historical stats CSV content"""
    return """Town,State,Zip,Distance,Total_Runs,Last_Run_Date,Min_Time,Max_Time,Average_Time
Lexington,MA,02421,5.0,10,2026-01-10,12.5,18.3,15.2
Bedford,MA,01730,10.0,5,2026-01-09,18.0,25.0,21.0"""


# --- Test determine_direction ---

@patch('collect_commute_data.datetime')
def test_determine_direction_morning(mock_datetime):
    """Test morning direction detection (before noon)"""
    mock_datetime.now.return_value = datetime(2026, 1, 12, 8, 30, 0)

    direction = determine_direction()

    assert direction == 'morning'


@patch('collect_commute_data.datetime')
def test_determine_direction_afternoon(mock_datetime):
    """Test afternoon direction detection (after noon)"""
    mock_datetime.now.return_value = datetime(2026, 1, 12, 17, 30, 0)

    direction = determine_direction()

    assert direction == 'afternoon'


@patch('collect_commute_data.datetime')
def test_determine_direction_exactly_noon(mock_datetime):
    """Test direction at exactly noon"""
    mock_datetime.now.return_value = datetime(2026, 1, 12, 12, 0, 0)

    direction = determine_direction()

    assert direction == 'afternoon'


# --- Test process_element ---

def test_process_element_ok_status():
    """Test processing element with OK status"""
    address = "Lexington, MA 02421"
    element = {
        'elements': [
            {
                'status': 'OK',
                'distance': {'value': 8046},  # ~5 miles
                'duration': {'value': 600},
                'duration_in_traffic': {'value': 780}  # 13 minutes
            }
        ]
    }
    results = []

    process_element(address, element, results)

    assert len(results) == 1
    assert results[0]['address'] == address
    assert results[0]['distance_miles'] == 5.0
    assert results[0]['duration_minutes'] == 13.0
    assert results[0]['status'] == 'OK'


def test_process_element_zero_results():
    """Test processing element with ZERO_RESULTS status"""
    address = "Unknown, MA 99999"
    element = {
        'elements': [
            {
                'status': 'ZERO_RESULTS'
            }
        ]
    }
    results = []

    process_element(address, element, results)

    assert len(results) == 1
    assert results[0]['address'] == address
    assert results[0]['distance_miles'] is None
    assert results[0]['duration_minutes'] is None
    assert results[0]['status'] == 'ZERO_RESULTS'


def test_process_element_not_found():
    """Test processing element with NOT_FOUND status"""
    address = "InvalidAddress"
    element = {
        'elements': [
            {
                'status': 'NOT_FOUND'
            }
        ]
    }
    results = []

    process_element(address, element, results)

    assert len(results) == 1
    assert results[0]['status'] == 'NOT_FOUND'


def test_process_element_no_traffic_data():
    """Test processing when duration_in_traffic not present"""
    address = "Lexington, MA 02421"
    element = {
        'elements': [
            {
                'status': 'OK',
                'distance': {'value': 8046},
                'duration': {'value': 600}
                # No duration_in_traffic
            }
        ]
    }
    results = []

    process_element(address, element, results)

    # Should fall back to regular duration
    assert results[0]['duration_minutes'] == 10.0


# --- Test fetch_commute_times ---

@patch('collect_commute_data.googlemaps.Client')
def test_fetch_commute_times_morning(mock_client, mock_addresses,
                                     mock_api_response_morning, monkeypatch):
    """Test fetching morning commute times"""
    # Setup
    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = mock_api_response_morning
    mock_client.return_value = mock_instance

    monkeypatch.setattr('collect_commute_data.CHUNK_SIZE', 25)
    monkeypatch.setattr('collect_commute_data.PROXY_ON', False)

    with patch('collect_commute_data.get_google_api_key',
               return_value='test_key'):
        results, elements = fetch_commute_times(mock_addresses, 'morning')

    # Should have 2 OK results and 1 ZERO_RESULTS
    assert len(results) == 3
    assert elements == 3

    ok_results = [r for r in results if r['status'] == 'OK']
    assert len(ok_results) == 2

    # Verify API was called with correct parameters
    call_args = mock_instance.distance_matrix.call_args
    assert call_args[1]['origins'] == mock_addresses
    assert 'Wood St' in call_args[1]['destinations']


@patch('collect_commute_data.googlemaps.Client')
def test_fetch_commute_times_afternoon(mock_client, mock_addresses,
                                       mock_api_response_morning, monkeypatch):
    """Test fetching afternoon commute times"""
    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = mock_api_response_morning
    mock_client.return_value = mock_instance

    monkeypatch.setattr('collect_commute_data.CHUNK_SIZE', 25)
    monkeypatch.setattr('collect_commute_data.PROXY_ON', False)

    with patch('collect_commute_data.get_google_api_key',
               return_value='test_key'):
        results, elements = fetch_commute_times(mock_addresses, 'afternoon')

    # Verify API was called with Work -> Home direction
    call_args = mock_instance.distance_matrix.call_args
    assert 'Wood St' in call_args[1]['origins']
    assert call_args[1]['destinations'] == mock_addresses


@patch('collect_commute_data.googlemaps.Client')
def test_fetch_commute_times_api_error(mock_client, mock_addresses,
                                       monkeypatch):
    """Test handling of API errors during fetch"""
    import googlemaps.exceptions

    mock_instance = MagicMock()
    mock_instance.distance_matrix.side_effect = \
        googlemaps.exceptions.ApiError("Test error")
    mock_client.return_value = mock_instance

    monkeypatch.setattr('collect_commute_data.CHUNK_SIZE', 25)
    monkeypatch.setattr('collect_commute_data.PROXY_ON', False)

    with patch('collect_commute_data.get_google_api_key',
               return_value='test_key'):
        results, elements = fetch_commute_times(mock_addresses, 'morning')

    # Should have counted elements but no results
    assert elements == 3
    assert len(results) == 0


@patch('collect_commute_data.googlemaps.Client')
def test_fetch_commute_times_chunking(mock_client, monkeypatch):
    """Test that large address lists are chunked properly"""
    # Create 30 addresses (should be split into 2 chunks of 25 and 5)
    addresses = [f"Town{i}, MA 0{i:04d}" for i in range(30)]

    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = {
        'status': 'OK',
        'rows': [{'elements': [{'status': 'OK', 'distance': {'value': 8046},
                                'duration': {'value': 600},
                                'duration_in_traffic': {'value': 780}}]}
                 for _ in range(25)]
    }
    mock_client.return_value = mock_instance

    monkeypatch.setattr('collect_commute_data.CHUNK_SIZE', 25)
    monkeypatch.setattr('collect_commute_data.PROXY_ON', False)

    with patch('collect_commute_data.get_google_api_key',
               return_value='test_key'):
        results, elements = fetch_commute_times(addresses, 'morning')

    # Should have made 2 API calls
    assert mock_instance.distance_matrix.call_count == 2


def test_fetch_commute_times_no_api_key():
    """Test handling of missing API key"""
    with patch('collect_commute_data.get_google_api_key', return_value=None):
        with pytest.raises(SystemExit):
            fetch_commute_times(["Lexington, MA 02421"], 'morning')


# --- Test load_historical_data ---

def test_load_historical_data_success(tmp_path, mock_historical_csv,
                                      monkeypatch):
    """Test loading existing historical data"""
    stats_file = tmp_path / "commute_stats.csv"
    stats_file.write_text(mock_historical_csv)

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    with patch('collect_commute_data.load_csv_with_zip') as mock_load:
        mock_load.return_value = pd.read_csv(stats_file, dtype={'Zip': str})
        df = load_historical_data()

    assert len(df) == 2
    assert '02421' in df['Zip'].values


def test_load_historical_data_missing_file(tmp_path, monkeypatch):
    """Test handling of missing historical data file"""
    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(tmp_path / "nonexistent.csv"))

    with patch('collect_commute_data.load_csv_with_zip') as mock_load:
        mock_load.return_value = pd.DataFrame()
        df = load_historical_data()

    assert df.empty


# --- Test update_statistics ---

def test_update_statistics_new_location(tmp_path, monkeypatch):
    """Test updating statistics with new location"""
    stats_file = tmp_path / "commute_stats.csv"

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    results = [
        {
            'address': 'Lexington, MA 02421',
            'distance_miles': 5.0,
            'duration_minutes': 15.0,
            'status': 'OK'
        }
    ]

    with patch('collect_commute_data.load_historical_data') as mock_load:
        mock_load.return_value = pd.DataFrame()

        with patch('collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12)
            update_statistics(results)

    # Verify file was created
    assert stats_file.exists()

    df = pd.read_csv(stats_file, dtype={'Zip': str})
    assert len(df) == 1
    assert df.iloc[0]['Zip'] == '02421'
    assert df.iloc[0]['Total_Runs'] == 1
    assert df.iloc[0]['Average_Time'] == 15.0


def test_update_statistics_existing_location(tmp_path, mock_historical_csv,
                                             monkeypatch):
    """Test updating statistics for existing location"""
    stats_file = tmp_path / "commute_stats.csv"
    stats_file.write_text(mock_historical_csv)

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    results = [
        {
            'address': 'Lexington, MA 02421',
            'distance_miles': 5.0,
            'duration_minutes': 20.0,  # Different from historical avg
            'status': 'OK'
        }
    ]

    with patch('collect_commute_data.load_historical_data') as mock_load:
        hist_df = pd.read_csv(stats_file, dtype={'Zip': str})
        mock_load.return_value = hist_df

        with patch('collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12)
            update_statistics(results)

    df = pd.read_csv(stats_file, dtype={'Zip': str})
    lex_record = df[df['Zip'] == '02421'].iloc[0]

    # Total_Runs should increment
    assert lex_record['Total_Runs'] == 11  # Was 10, now 11

    # Average should be updated: (15.2 * 10 + 20.0) / 11 = 15.64
    assert round(lex_record['Average_Time'], 2) == 15.64

    # Max should be updated
    assert lex_record['Max_Time'] == 20.0


def test_update_statistics_failed_results(tmp_path, monkeypatch):
    """Test that failed API results are not processed"""
    stats_file = tmp_path / "commute_stats.csv"

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    results = [
        {
            'address': 'Lexington, MA 02421',
            'distance_miles': None,
            'duration_minutes': None,
            'status': 'ZERO_RESULTS'
        }
    ]

    with patch('collect_commute_data.load_historical_data') as mock_load:
        mock_load.return_value = pd.DataFrame()

        with patch('collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12)
            update_statistics(results)

    # File should not be created since no valid results
    assert not stats_file.exists()


def test_update_statistics_empty_results():
    """Test handling of empty results list"""
    # Should not raise an error
    update_statistics([])


def test_update_statistics_address_parsing(tmp_path, monkeypatch):
    """Test proper parsing of address components"""
    stats_file = tmp_path / "commute_stats.csv"

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    results = [
        {
            'address': 'North Cambridge, MA 02140',
            'distance_miles': 3.5,
            'duration_minutes': 12.0,
            'status': 'OK'
        }
    ]

    with patch('collect_commute_data.load_historical_data') as mock_load:
        mock_load.return_value = pd.DataFrame()

        with patch('collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12)
            update_statistics(results)

    df = pd.read_csv(stats_file, dtype={'Zip': str})
    assert df.iloc[0]['Town'] == 'North Cambridge'
    assert df.iloc[0]['State'] == 'MA'
    assert df.iloc[0]['Zip'] == '02140'


def test_update_statistics_permission_error(tmp_path, monkeypatch):
    """Test handling of file permission errors"""
    stats_file = tmp_path / "commute_stats.csv"
    stats_file.write_text("dummy")
    stats_file.chmod(0o444)  # Read-only

    monkeypatch.setattr('collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))

    results = [
        {
            'address': 'Lexington, MA 02421',
            'distance_miles': 5.0,
            'duration_minutes': 15.0,
            'status': 'OK'
        }
    ]

    with patch('collect_commute_data.load_historical_data') as mock_load:
        mock_load.return_value = pd.DataFrame()

        with patch('collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12)

            with pytest.raises(PermissionError):
                update_statistics(results)

    # Cleanup
    stats_file.chmod(0o644)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])