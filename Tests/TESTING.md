# Testing Guide - House Hunt Commute Analysis

## Overview

Comprehensive test suite for the commute analysis component with **zero API costs** through mocking.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
./run_tests.sh

# Run with coverage report
pytest -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py -v
```

## Test Structure

```
house_hunt/
├── tests/
│   ├── __init__.py                  # Makes tests a package
│   ├── test_utils.py                # Tests for utils.py
│   └── test_collect_commute_data.py # Tests for collect_commute_data.py
├── utils.py
├── collect_commute_data.py
├── constants.py
├── pytest.ini                       # Pytest configuration
├── requirements-test.txt            # Test dependencies
└── run_tests.sh                     # Test runner script
```

## Test Files

### `Tests/test_utils.py`
Tests for core utility functions in utils.py
- ✅ **API Key Management** - File reading, error handling
- ✅ **Time Calculations** - Schedule timing logic
- ✅ **ZIP Data Loading** - CSV parsing, filtering, validation
- ✅ **Budget Tracking** - Monthly usage limits, file operations
- ✅ **Range Checking** - Google Maps API integration (mocked)
- ✅ **Edge Cases** - Missing coords, decommissioned ZIPs, invalid data

**Test Count:** 20+ tests  
**Coverage Target:** 85%+

### `Tests/Commute/test_collect_commute_data.py`
Tests for commute data collection in collect_commute_data.py
- ✅ **Direction Logic** - Morning/afternoon detection
- ✅ **API Fetching** - Chunking, error handling, retries
- ✅ **Result Processing** - Status handling, data extraction
- ✅ **Statistics Updates** - Historical data, running averages
- ✅ **File Operations** - CSV reading/writing, permissions

**Test Count:** 15+ tests  
**Coverage Target:** 80%+

## Running Tests

### All Tests
```bash
# Verbose with coverage
pytest -v --cov=. --cov-report=term-missing

# Quick run (no coverage)
pytest -q
```

### Specific Test Categories
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Individual Test Files
```bash
# Test utils only
pytest tests/test_utils.py -v

# Test commute collection only
pytest tests/test_collect_commute_data.py -v
```

### With Test Runner Script
```bash
# Default (all tests with coverage)
./run_tests.sh

# Skip coverage reporting
./run_tests.sh --no-coverage

# Only unit tests
./run_tests.sh --unit

# Fast tests only
./run_tests.sh --fast
```

## Key Test Features

### 1. **Zero API Costs**
All Google Maps API calls are mocked - no actual API requests are made during testing.

```python
@patch('utils.googlemaps.Client')
def test_get_zips_within_range_success(mock_client, ...):
    mock_instance = MagicMock()
    mock_instance.distance_matrix.return_value = mock_response
    # Test logic here - no API call made
```

### 2. **Comprehensive Edge Cases**
- Missing coordinates (Lat/Long)
- Decommissioned ZIP codes
- API errors and rate limits
- File permission issues
- Invalid data formats
- Network timeouts

### 3. **Fixtures for Reusability**
```python
@pytest.fixture
def mock_zip_csv():
    """Reusable test data"""
    return """zip,type,decommissioned,..."""
```

### 4. **Temporary Files**
Tests use `tmp_path` fixture to avoid polluting filesystem:
```python
def test_api_usage_tracking(tmp_path):
    counter_file = tmp_path / "usage_counter.txt"
    # Test logic - file automatically cleaned up
```

## Coverage Reports

### Generate Coverage
```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report
pytest --cov=. --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Targets
- **utils.py:** 85%+ coverage
- **collect_commute_data.py:** 80%+ coverage
- **Overall:** 70%+ (enforced by pytest.ini)

## Common Test Patterns

### Testing with Mocked API
```python
@patch('module.googlemaps.Client')
def test_function(mock_client):
    mock_instance = MagicMock()
    mock_instance.method.return_value = expected_response
    mock_client.return_value = mock_instance
    # Test function that uses googlemaps.Client
```

### Testing with Temporary Files
```python
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")
    # Use test_file in test
```

### Testing Time-Dependent Logic
```python
@patch('module.datetime')
def test_time_function(mock_datetime):
    mock_datetime.now.return_value = datetime(2026, 1, 12, 8, 0)
    # Test time-dependent logic
```

## Troubleshooting

### Import Errors
```bash
# Ensure parent directory is in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Coverage Not Working
```bash
# Install coverage separately
pip install pytest-cov

# Verify pytest-cov is installed
pytest --version
```

### Tests Pass Locally But Fail in CI
- Check Python version compatibility
- Ensure all dependencies in requirements-test.txt
- Verify timezone assumptions in time-based tests

### Permission Errors
```bash
# Make test runner executable
chmod +x run_tests.sh
```

## Test Maintenance

### Adding New Tests
1. Add test function to appropriate file
2. Use descriptive name: `test_function_name_scenario`
3. Add docstring explaining what's tested
4. Use fixtures for common setup
5. Mock external dependencies (APIs, files)

### Updating Existing Tests
When code changes:
1. Run full test suite: `pytest -v`
2. Update affected tests
3. Verify coverage remains above target
4. Update fixtures if data structure changed

### Before Committing
```bash
# Run full test suite with coverage
./run_tests.sh

# Check for any skipped/failed tests
pytest -v

# Verify coverage report
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Best Practices

1. **Always mock external APIs** - Never make real API calls in tests
2. **Use tmp_path for file operations** - Keeps filesystem clean
3. **Test edge cases** - Not just happy path
4. **Keep tests fast** - Mock slow operations
5. **Descriptive test names** - Clear what's being tested
6. **One assertion per test** - Unless related assertions
7. **Cleanup in fixtures** - Use yield for teardown
8. **Test error conditions** - Not just success cases

## Test Metrics

Current test suite statistics:
- **Total Tests:** 35+
- **Average Runtime:** <5 seconds (all tests)
- **Code Coverage:** 80%+
- **API Mocking:** 100% (zero costs)
- **Edge Cases Covered:** 15+

## Next Steps

To add more tests:
1. Identify untested code paths in coverage report
2. Add tests for new features as they're implemented
3. Consider integration tests for full workflow
4. Add performance/load tests if needed

## Questions?

Check the main project documentation or reach out to project maintainers.