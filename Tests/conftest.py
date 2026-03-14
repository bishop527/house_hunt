"""
Shared pytest fixtures and configuration for all tests.

This file is automatically discovered by pytest and makes fixtures
available to all test files in the Tests/ directory.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add parent directory to path so tests can import source modules
# This works for both Tests/test_*.py and Tests/Commute/test_*.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Also ensure we can import from project root when running from subdirectories
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Provides a temporary directory for test data that persists
    for the entire test session.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def clean_env(monkeypatch):
    """
    Provides a clean environment by removing any environment
    variables that might affect tests.
    """
    # Remove any API-related env vars
    for key in list(os.environ.keys()):
        if 'API' in key or 'GOOGLE' in key:
            monkeypatch.delenv(key, raising=False)

    yield


@pytest.fixture
def sample_zip_data():
    """
    Returns sample ZIP code data for testing without file I/O.
    """
    import pandas as pd

    return pd.DataFrame({
        'Zip': ['02421', '02420', '01730', '01742'],
        'Town': ['Lexington', 'Lexington', 'Bedford', 'Concord'],
        'State': ['MA', 'MA', 'MA', 'MA'],
        'Lat': [42.44, 42.46, 42.48, 42.45],
        'Long': [-71.23, -71.22, -71.26, -71.35]
    })


@pytest.fixture
def mock_google_response_success():
    """
    Returns a mock successful Google Distance Matrix API response.
    """
    return {
        'status': 'OK',
        'destination_addresses': ['123 Main St, Anytown, MA 00000, USA'],
        'origin_addresses': [
            'Lexington, MA 02421, USA',
            'Bedford, MA 01730, USA'
        ],
        'rows': [
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 8046, 'text': '5.0 mi'},
                        'duration': {'value': 600, 'text': '10 mins'},
                        'duration_in_traffic': {'value': 780, 'text': '13 mins'}
                    }
                ]
            },
            {
                'elements': [
                    {
                        'status': 'OK',
                        'distance': {'value': 16093, 'text': '10.0 mi'},
                        'duration': {'value': 1200, 'text': '20 mins'},
                        'duration_in_traffic': {'value': 1500, 'text': '25 mins'}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_google_response_error():
    """
    Returns a mock error response from Google Distance Matrix API.
    """
    return {
        'status': 'OVER_QUERY_LIMIT',
        'error_message': 'You have exceeded your rate-limit for this API.'
    }


# Configure pytest logging
def pytest_configure(config):
    """
    Custom pytest configuration.
    """
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "api: marks tests that would make real API calls if not mocked"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test items after collection.

    Automatically adds 'unit' marker to tests that don't have
    integration or slow markers.
    """
    for item in items:
        # Auto-mark tests in test_utils.py as unit tests
        if "test_utils" in str(item.fspath):
            if not any(mark.name in ['integration', 'slow']
                      for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)

        # Auto-mark Commute tests
        if "Commute" in str(item.fspath):
            if not any(mark.name in ['integration', 'slow']
                      for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)

        # Auto-mark Housing tests
        if "Housing" in str(item.fspath):
            if not any(mark.name in ['integration', 'slow']
                       for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)

        # Auto-mark Score tests
        if "Score" in str(item.fspath):
            if not any(mark.name in ['integration', 'slow']
                       for mark in item.iter_markers()):
                item.add_marker(pytest.mark.unit)

        # Auto-mark API-related tests
        if "api" in item.name.lower() or "google" in item.name.lower():
            item.add_marker(pytest.mark.api)
