"""
Unit tests for optimized collect_commute_data.py

Tests the optimized version with:
- Cache-first address loading
- Unified budget checking
- Single GCP validation call

Run with: python -m pytest Tests/Commute/test_collect_commute_data.py -v
"""
import os
import sys
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from Commute.collect_commute_data import (
    determine_direction,
    fetch_commute_times,
    _process_element,
    load_historical_data,
    update_statistics,
    _check_budget_once,
    _load_addresses_within_range
)


# --- Fixtures (mostly unchanged) ---

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
                        'distance': {'value': 8046},
                        'duration': {'value': 600},
                        'duration_in_traffic': {'value': 780}
                    }
                ]
            },
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 16093},
                        'duration': {'value': 900},
                        'duration_in_traffic': {'value': 1200}
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


# --- Existing tests (unchanged) ---

@patch('Commute.collect_commute_data.datetime')
def test_determine_direction_morning(mock_datetime):
    """Test morning direction detection (before noon)"""
    mock_datetime.now.return_value = datetime(2026, 1, 12, 8, 30, 0)
    direction = determine_direction()
    assert direction == 'morning'


@patch('Commute.collect_commute_data.datetime')
def test_determine_direction_afternoon(mock_datetime):
    """Test afternoon direction detection (after noon)"""
    mock_datetime.now.return_value = datetime(2026, 1, 12, 17, 30, 0)
    direction = determine_direction()
    assert direction == 'afternoon'


def test_process_element_ok_status():
    """Test processing element with OK status"""
    address = "Lexington, MA 02421"
    element = {
        'elements': [
            {
                'status': 'OK',
                'distance': {'value': 8046},
                'duration': {'value': 600},
                'duration_in_traffic': {'value': 780}
            }
        ]
    }
    results = []
    _process_element(address, element, results)

    assert len(results) == 1
    assert results[0]['address'] == address
    assert results[0]['distance_miles'] == 5.0
    assert results[0]['duration_minutes'] == 13.0
    assert results[0]['status'] == 'OK'


def test_check_budget_once_under_limit(tmp_path, monkeypatch):
    """Test unified budget check when under limit"""
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,5000\n{month_str},advanced,0\n")

    monkeypatch.setattr('Commute.collect_commute_data.API_TIER_TRACKING_FILE',
                       str(tier_file))
    monkeypatch.setattr('Commute.collect_commute_data.USE_TRAFFIC', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_MONTHLY_LIMIT_BASIC',
                       10000)

    with patch('Commute.collect_commute_data.get_current_usage_by_tier') as mock_usage:
        mock_usage.return_value = {
            'basic': 5000,
            'advanced': 0,
            'total': 5000,
            'basic_remaining': 5000,
            'advanced_remaining': 5000
        }

        result = _check_budget_once(100)

    assert result['can_proceed'] is True
    assert result['current_usage'] == 5000
    assert result['estimated'] == 100
    assert result['projected'] == 5100


def test_check_budget_once_at_limit(tmp_path, monkeypatch):
    """Test unified budget check when at limit"""
    monkeypatch.setattr('Commute.collect_commute_data.USE_TRAFFIC', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_MONTHLY_LIMIT_BASIC',
                       10000)

    with patch('Commute.collect_commute_data.get_current_usage_by_tier') as mock_usage:
        mock_usage.return_value = {
            'basic': 10000,
            'advanced': 0,
            'total': 10000,
            'basic_remaining': 0,
            'advanced_remaining': 5000
        }

        result = _check_budget_once(100)

    assert result['can_proceed'] is False
    assert result['current_usage'] == 10000


def test_check_budget_once_exceeds_with_user_abort(tmp_path, monkeypatch):
    """Test budget check with user declining to proceed"""
    monkeypatch.setattr('Commute.collect_commute_data.USE_TRAFFIC', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_MONTHLY_LIMIT_BASIC',
                       10000)

    with patch('Commute.collect_commute_data.get_current_usage_by_tier') as mock_usage:
        mock_usage.return_value = {
            'basic': 9500,
            'advanced': 0,
            'total': 9500,
            'basic_remaining': 500,
            'advanced_remaining': 5000
        }

        with patch('builtins.input', return_value='no'):
            result = _check_budget_once(1000)

    assert result['can_proceed'] is False
    assert result['projected'] == 10500


def test_check_budget_once_exceeds_with_user_confirm(tmp_path, monkeypatch):
    """Test budget check with user confirming to proceed"""
    monkeypatch.setattr('Commute.collect_commute_data.USE_TRAFFIC', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_MONTHLY_LIMIT_BASIC',
                       10000)

    with patch('Commute.collect_commute_data.get_current_usage_by_tier') as mock_usage:
        mock_usage.return_value = {
            'basic': 9500,
            'advanced': 0,
            'total': 9500,
            'basic_remaining': 500,
            'advanced_remaining': 5000
        }

        with patch('builtins.input', return_value='yes'):
            with patch('sys.stdin.isatty', return_value=True):
                result = _check_budget_once(1000)

    assert result['can_proceed'] is True
    assert result['projected'] == 10500


def test_load_addresses_cache_hit(tmp_path, monkeypatch):
    """Test loading addresses from cache (optimization path, Work2 disabled)"""
    # Setup cache file
    cache_file = tmp_path / "towns_within_40mi.csv"
    cache_df = pd.DataFrame({
        'Full_Address': ['Lexington, MA 02421', 'Bedford, MA 01730'],
        'Distance_Miles': [5.0, 10.0]
    })
    cache_df.to_csv(cache_file, index=False)

    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR', str(tmp_path))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    # Disable Work2 filter so we test Work1 cache path in isolation
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', False)

    # Should NOT call get_zip_data or get_locations_within_range
    with patch('Commute.collect_commute_data.get_zip_data') as mock_zip:
        with patch('Commute.collect_commute_data.get_locations_within_range') as mock_range:
            addresses = _load_addresses_within_range()

    # Verify cache was used (functions not called)
    mock_zip.assert_not_called()
    mock_range.assert_not_called()

    # Verify correct addresses loaded
    assert len(addresses) == 2
    assert 'Lexington, MA 02421' in addresses


def test_load_addresses_cache_miss(tmp_path, monkeypatch):
    """Test loading addresses when cache doesn't exist (Work2 disabled)"""
    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR',
                       str(tmp_path / 'nonexistent'))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', False)

    mock_zip_df = pd.DataFrame({
        'Zip': ['02421', '01730'],
        'Town': ['Lexington', 'Bedford'],
        'State': ['MA', 'MA'],
        'Lat': [42.44, 42.48],
        'Long': [-71.23, -71.26]
    })

    # Should call both get_zip_data and get_locations_within_range
    with patch('Commute.collect_commute_data.get_zip_data',
               return_value=mock_zip_df) as mock_zip:
        with patch('Commute.collect_commute_data.get_locations_within_range',
                   return_value=['Lexington, MA 02421', 'Bedford, MA 01730']) as mock_range:
            addresses = _load_addresses_within_range()

    # Verify both functions were called
    mock_zip.assert_called_once()
    mock_range.assert_called_once()

    assert len(addresses) == 2


def test_load_addresses_cache_corrupted(tmp_path, monkeypatch, caplog):
    """Test handling of corrupted cache file (Work2 disabled)"""
    import logging

    # Create corrupted cache
    cache_file = tmp_path / "towns_within_40mi.csv"
    cache_file.write_text("corrupted,data,here\nno,proper,format")

    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR', str(tmp_path))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', False)

    mock_zip_df = pd.DataFrame({
        'Zip': ['02421'],
        'Town': ['Lexington'],
        'State': ['MA'],
        'Lat': [42.44],
        'Long': [-71.23]
    })

    # Should fall back to full pipeline
    with patch('Commute.collect_commute_data.get_zip_data',
               return_value=mock_zip_df):
        with patch('Commute.collect_commute_data.get_locations_within_range',
                   return_value=['Lexington, MA 02421']):
            with caplog.at_level(logging.WARNING):
                addresses = _load_addresses_within_range()

    assert len(addresses) == 1
    assert 'Lexington, MA 02421' in addresses


def test_load_addresses_work2_filter_applied(tmp_path, monkeypatch):
    """Work2 filter removes addresses outside Work Address 2 range."""
    # Setup Work1 cache with 3 towns
    cache_file = tmp_path / "towns_within_40mi.csv"
    cache_df = pd.DataFrame({
        'Full_Address': [
            'Lexington, MA 02421',   # in Work2 range
            'Bedford, MA 01730',     # in Work2 range
            'Worcester, MA 01602',   # NOT in Work2 range
        ],
        'Distance_Miles': [5.0, 10.0, 38.0]
    })
    cache_df.to_csv(cache_file, index=False)

    # Setup Work2 distances file with only 2 of the 3 zips
    work2_file = tmp_path / "work2_distances.csv"
    work2_df = pd.DataFrame({
        'Town': ['Lexington', 'Bedford'],
        'State': ['MA', 'MA'],
        'Zip': ['02421', '01730'],
        'Distance': [8.0, 12.0]
    })
    work2_df.to_csv(work2_file, index=False)

    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR', str(tmp_path))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', True)
    monkeypatch.setattr('Commute.collect_commute_data.WORK2_DISTANCES_FILE', str(work2_file))
    monkeypatch.setattr('Commute.collect_commute_data.WORK2_MAX_RANGE', 40)

    addresses = _load_addresses_within_range()

    assert len(addresses) == 2
    assert 'Lexington, MA 02421' in addresses
    assert 'Bedford, MA 01730' in addresses
    assert 'Worcester, MA 01602' not in addresses


def test_load_addresses_work2_file_missing(tmp_path, monkeypatch):
    """When Work2 file is missing, falls back to full Work1 list with a warning."""
    cache_file = tmp_path / "towns_within_40mi.csv"
    cache_df = pd.DataFrame({
        'Full_Address': ['Lexington, MA 02421', 'Bedford, MA 01730'],
        'Distance_Miles': [5.0, 10.0]
    })
    cache_df.to_csv(cache_file, index=False)

    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR', str(tmp_path))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', True)
    # Point to a file that doesn't exist
    monkeypatch.setattr('Commute.collect_commute_data.WORK2_DISTANCES_FILE',
                        str(tmp_path / 'nonexistent_work2.csv'))

    addresses = _load_addresses_within_range()

    # Should return the full Work1 list as a safe fallback (no crash)
    assert addresses is not None
    assert len(addresses) == 2
    assert 'Lexington, MA 02421' in addresses
    assert 'Bedford, MA 01730' in addresses


# --- Integration test for optimized flow ---

@patch('Commute.collect_commute_data.googlemaps.Client')
def test_collect_commute_data_optimized_flow(mock_client, tmp_path, monkeypatch):
    """Test complete optimized flow with cache hit"""

    # Setup cache (Work2 disabled so full Work1 list is used)
    cache_file = tmp_path / "towns_within_40mi.csv"
    cache_df = pd.DataFrame({
        'Full_Address': ['Lexington, MA 02421'],
        'Distance_Miles': [5.0]
    })
    cache_df.to_csv(cache_file, index=False)

    # Setup tier tracking
    tier_file = tmp_path / "usage_by_tier.txt"
    month_str = datetime.now().strftime('%Y-%m')
    tier_file.write_text(f"{month_str},basic,100\n{month_str},advanced,0\n")

    stats_file = tmp_path / "commute_stats.csv"

    # Monkeypatch paths
    monkeypatch.setattr('Commute.collect_commute_data.PROCESSED_DIR', str(tmp_path))
    monkeypatch.setattr('Commute.collect_commute_data.LOCATION_GROUPING', 'town')
    monkeypatch.setattr('Commute.collect_commute_data.MAX_RANGE', 40)
    monkeypatch.setattr('Commute.collect_commute_data.ENABLE_SECOND_WORK_ADDRESS', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_TIER_TRACKING_FILE',
                       str(tier_file))
    monkeypatch.setattr('Commute.collect_commute_data.COMMUTE_STATS_FILE',
                       str(stats_file))
    monkeypatch.setattr('Commute.collect_commute_data.USE_TRAFFIC', False)
    monkeypatch.setattr('Commute.collect_commute_data.API_MONTHLY_LIMIT_BASIC', 10000)
    monkeypatch.setattr('Commute.collect_commute_data.CHUNK_SIZE', 25)
    monkeypatch.setattr('Commute.collect_commute_data.PROXY_ON', False)

    # Mock API
    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = {
        'status': 'OK',
        'rows': [{
            'elements': [{
                'status': 'OK',
                'distance': {'value': 8046},
                'duration': {'value': 600},
                'duration_in_traffic': {'value': 780}
            }]
        }]
    }
    mock_client.return_value = mock_instance

    # Patches
    with patch('Commute.collect_commute_data.get_google_api_key',
               return_value='test_key'):
        with patch('Commute.collect_commute_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 12, 8, 0, 0)
            with patch('Commute.collect_commute_data.get_zip_data') as mock_zip:
                with patch('Commute.collect_commute_data.validate_local_tracking') as mock_validate:
                    mock_validate.return_value = {
                        'local_basic': 101,
                        'local_advanced': 0,
                        'local_total': 101,
                        'google': 101,
                        'discrepancy': 0,
                        'discrepancy_ratio': 0.0,
                        'costs': {'basic_cost': 0, 'advanced_cost': 0, 'total_cost': 0},
                        'tier_usage': {
                            'basic': 101,
                            'advanced': 0,
                            'total': 101,
                            'basic_remaining': 9899,
                            'advanced_remaining': 5000
                        }
                    }

                    from Commute.collect_commute_data import collect_commute_data
                    collect_commute_data()

    # Verify optimizations:
    # 1. get_zip_data was NOT called (cache hit)
    mock_zip.assert_not_called()

    # 2. validate_local_tracking called only ONCE (at end)
    assert mock_validate.call_count == 1

    # 3. Stats file was created
    assert stats_file.exists()

    # 4. API was called
    assert mock_instance.distance_matrix.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])