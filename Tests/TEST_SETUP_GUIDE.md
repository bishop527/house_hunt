# Test Setup Guide

Quick guide to set up and run tests for the House Hunt Commute Analysis project.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Project source code

## 1. Directory Structure Setup

Create the test directory structure:

```bash
# From project root
mkdir -p Tests/Commute
mkdir -p Commute
```

Your structure should look like:
```
house_hunt/
├── Tests/                      # Test directory
│   ├── .coverage              # Coverage data (generated)
│   ├── htmlcov/               # Coverage HTML report (generated)
│   ├── __init__.py
│   ├── conftest.py            # Root test configuration
│   ├── test_utils.py          # Tests for utils.py
│   └── Commute/               # Commute-specific tests
│       ├── __init__.py
│       ├── conftest.py        # Commute test configuration
│       └── test_collect_commute_data.py
├── Commute/                    # Commute package
│   ├── __init__.py            # Makes Commute a package
│   └── collect_commute_data.py
├── Data/
│   ├── Raw/
│   ├── Processed/
│   └── Results/
├── utils.py
├── constants.py
├── pytest.ini                  # Pytest configuration
├── .coveragerc                 # Coverage configuration
└── .gitignore                 # Git ignore file
```

**Note:** Coverage artifacts (`.coverage`, `htmlcov/`) are now stored in `Tests/` 
directory to keep the project root clean.

## 2. Install Test Dependencies

```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Or install individually
pip install pytest pytest-cov pytest-mock
```

### Verify Installation
```bash
pytest --version
# Should show: pytest 7.4.0 or higher
```

## 3. Create Required Package Files

### **Make Commute a Package**

Create an empty `__init__.py` file in the `Commute/` directory:

```bash
touch Commute/__init__.py
```

This allows tests to import: `from Commute.collect_commute_data import ...`

### **Create Test Package Files**

Ensure `__init__.py` files exist in test directories:

```bash
touch Tests/__init__.py
touch Tests/Commute/__init__.py
```

## 4. Configuration Files

### **pytest.ini** - Place in project root

```ini
[tool:pytest]
addopts = --cov=. --cov-report=html:Tests/htmlcov --cov-report=term -v --tb=short --cov-config=.coveragerc
fail_under = 55
testpaths = Tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Key settings:**
- `fail_under = 55` - Tests fail if coverage drops below 55%
- `testpaths = Tests` - Only look for tests in Tests/ directory
- `--cov=.` - Measure coverage for all project files
- `--cov-report=html:Tests/htmlcov` - HTML report in Tests/htmlcov/
- `--cov-config=.coveragerc` - Use .coveragerc for coverage settings
- `-v` - Verbose output (show each test name)

### **.coveragerc** - Place in project root

```ini
[run]
data_file = Tests/.coverage
source = .
omit = Tests/*

[report]
precision = 2

[html]
directory = Tests/htmlcov
```

**Key settings:**
- `data_file = Tests/.coverage` - Coverage data stored in Tests/
- `source = .` - Measure coverage for current directory
- `omit = Tests/*` - Exclude test files from coverage measurement
- `directory = Tests/htmlcov` - HTML report directory

### **Tests/conftest.py** - Root test configuration

```python
"""
Root test configuration

Ensures project root is in sys.path for imports.
"""
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

### **Tests/Commute/conftest.py** - Commute test configuration

```python
"""
Commute test configuration

Ensures project root is in sys.path for imports.
This file runs before any tests in this directory.
"""
import os
import sys

# Add project root to path
current_file = os.path.abspath(__file__)
commute_dir = os.path.dirname(current_file)
tests_dir = os.path.dirname(commute_dir)
project_root = os.path.dirname(tests_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

### **.gitignore** - Add coverage artifacts

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Testing & Coverage (artifacts stored in Tests/ directory)
Tests/.coverage
Tests/.coverage.*
Tests/htmlcov/
Tests/.pytest_cache/
.pytest_cache/
*.cover
.hypothesis/

# Virtual Environments
venv/
env/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Data files (keep structure, ignore data)
Data/Raw/*.csv
Data/Processed/*.csv
Data/Results/*.csv
Data/Results/*.log
Data/Results/*.txt
!Data/Raw/sample-zip_code_database.csv

# API Keys
google_api_key
monitor-key.json
```

## 5. Important: Patch Paths in Tests

When using `@patch` decorators in tests, **always use the full module path** 
where the object is **used**, not where it's defined.

### **WRONG (will cause ImportError):**
```python
from collect_commute_data import determine_direction

@patch('collect_commute_data.datetime')  # ❌ Module not found
def test_morning(mock_datetime):
    ...
```

### **CORRECT:**
```python
from Commute.collect_commute_data import determine_direction

@patch('Commute.collect_commute_data.datetime')  # ✅ Full path
def test_morning(mock_datetime):
    ...
```

### **Files That Need Correct Patch Paths:**

**In `test_collect_commute_data.py`**, ensure ALL patches use 
`Commute.collect_commute_data.XXX`:

```python
# Correct patch examples:
@patch('Commute.collect_commute_data.datetime')
@patch('Commute.collect_commute_data.googlemaps.Client')

with patch('Commute.collect_commute_data.get_google_api_key', 
           return_value='test_key'):
    ...

with patch('Commute.collect_commute_data.load_historical_data'):
    ...

monkeypatch.setattr('Commute.collect_commute_data.COMMUTE_STATS_FILE', 
                   str(stats_file))
```

## 6. Run Tests

### Quick Test
```bash
# Run all tests
pytest

# Expected output:
# ==================== test session starts ====================
# collected 43 items
#
# Tests/test_utils.py ..................... [ 53%]
# Tests/Commute/test_collect_commute_data.py ............... [100%]
#
# ==================== 43 passed in 2.34s ====================
```

### With Coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### Using Test Runner (if you created run_tests.sh)
```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Note:** The `run_tests.sh` script automatically sets the `COVERAGE_FILE` environment 
variable to ensure `.coverage` is stored in `Tests/` directory.

## 7. Verify Everything Works

### Run Full Test Suite
```bash
pytest -v
```

Expected output:
```
========================================
House Hunt Project - Test Suite
========================================

Running tests...

Tests/test_utils.py::test_get_google_api_key_success PASSED
Tests/test_utils.py::test_get_google_api_key_missing_file PASSED
...
Tests/Commute/test_collect_commute_data.py::test_determine_direction_morning PASSED
...

==================== 43 passed in 2.34s ====================

Coverage:
Name                              Stmts   Miss  Cover
-----------------------------------------------------
Commute/collect_commute_data.py     150     65    57%
constants.py                         25      0   100%
utils.py                            120     50    58%
-----------------------------------------------------
TOTAL                               295    115    55%

Coverage HTML report generated in: Tests/htmlcov/index.html
```

### Check Coverage Report
```bash
# Generate HTML coverage report (stored in Tests/htmlcov/)
pytest --cov=. --cov-report=html

# Open in browser
open Tests/htmlcov/index.html        # Mac
xdg-open Tests/htmlcov/index.html    # Linux
start Tests/htmlcov/index.html       # Windows
```

## 8. Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'collect_commute_data'"

**Cause:** Missing `Commute/__init__.py` or incorrect import path

**Solution 1:** Create the package file
```bash
touch Commute/__init__.py
```

**Solution 2:** Fix imports in test files
```python
# Change from:
from collect_commute_data import determine_direction

# To:
from Commute.collect_commute_data import determine_direction
```

**Solution 3:** Fix patch decorators
```python
# Change from:
@patch('collect_commute_data.datetime')

# To:
@patch('Commute.collect_commute_data.datetime')
```

### Issue: "Coverage failure: total of 55 is less than fail-under=70"

**Cause:** Test coverage below threshold in `pytest.ini`

**Solution:** Lower the threshold temporarily
```ini
# In pytest.ini, change:
fail_under = 70

# To:
fail_under = 55
```

Then gradually add more tests to increase coverage.

### Issue: "pytest: command not found"

**Solution:**
```bash
# Install pytest
pip install pytest

# Or use python -m
python -m pytest Tests/
```

### Issue: "No tests collected"

**Solution:**
```bash
# Check test discovery
pytest --collect-only

# Ensure files start with test_
ls Tests/test_*.py
ls Tests/Commute/test_*.py

# Ensure pytest.ini has correct testpaths
cat pytest.ini | grep testpaths
# Should show: testpaths = Tests
```

### Issue: Import errors in tests

**Solution:** Verify conftest.py files exist and add project root to path:

```bash
# Check files exist
ls Tests/conftest.py
ls Tests/Commute/conftest.py

# Verify they add project root to sys.path
cat Tests/conftest.py
```

### Issue: "Permission denied" for run_tests.sh

**Solution:**
```bash
chmod +x run_tests.sh
```

### Issue: Stale `.coverage` file causing wrong results

**Solution:**
```bash
# Delete old coverage data (now in Tests/ directory)
coverage erase

# Or delete the file directly
rm Tests/.coverage

# Run tests fresh
pytest --cov=.

# Or use the clean option in run_tests.sh
./run_tests.sh --clean
```

### Issue: `.coverage` appears in project root instead of Tests/

**Cause:** Coverage environment variable not set or .coveragerc not being used

**Solution 1:** Use run_tests.sh (recommended)
```bash
./run_tests.sh
# The script sets COVERAGE_FILE=Tests/.coverage automatically
```

**Solution 2:** Set environment variable manually
```bash
COVERAGE_FILE=Tests/.coverage pytest
```

**Solution 3:** Verify .coveragerc exists
```bash
# Check .coveragerc file exists in project root
cat .coveragerc | grep data_file
# Should show: data_file = Tests/.coverage
```

### Issue: Can't find coverage report

**Solution:**
```bash
# Coverage artifacts are now in Tests/ directory
ls Tests/.coverage        # Coverage data file
ls Tests/htmlcov/         # HTML coverage report

# Open report from correct location
open Tests/htmlcov/index.html
```

## 9. Daily Workflow

### Before Committing Code
```bash
# Run full test suite
pytest -v

# Ensure all tests pass
# Check coverage is above threshold (55%)

# View detailed coverage
open Tests/htmlcov/index.html
```

### After Changing Source Code
```bash
# Run relevant tests
pytest Tests/test_utils.py -v        # If changed utils.py
pytest Tests/Commute/ -v             # If changed commute code

# Or run all tests
pytest
```

### Adding New Features (Test-Driven Development)
```bash
# 1. Write tests first (they should fail)
# Edit Tests/test_utils.py or Tests/Commute/test_collect_commute_data.py

# 2. Run tests (they should fail)
pytest Tests/ -v

# 3. Implement feature
# Edit utils.py or Commute/collect_commute_data.py

# 4. Run tests again (they should pass)
pytest Tests/ -v

# 5. Check coverage increased
pytest --cov=. --cov-report=term
open Tests/htmlcov/index.html
```

## 10. Test Commands Cheat Sheet

```bash
# Basic runs
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -q                       # Quiet output
pytest -x                       # Stop on first failure

# Specific tests
pytest Tests/test_utils.py      # One file
pytest Tests/Commute/           # All Commute tests
pytest Tests/test_utils.py::test_get_api_key_success  # One test

# With coverage
pytest --cov=.                  # Coverage report
pytest --cov=. --cov-report=html  # HTML in Tests/htmlcov/
pytest --cov=. --cov-report=term-missing  # Show missing lines

# Without coverage
pytest --no-cov                 # Skip coverage

# Debugging
pytest -s                       # Show print() output
pytest --pdb                    # Drop into debugger on failure
pytest -l                       # Show local variables on failure

# Clean coverage data (from Tests/ directory)
coverage erase                  # Delete Tests/.coverage
rm Tests/.coverage              # Or delete directly
rm -rf Tests/htmlcov            # Delete HTML report
```

## 11. Understanding Test Output

### Test Result Symbols
- `.` = Test passed
- `F` = Test failed
- `E` = Test error (exception during collection/setup)
- `s` = Test skipped
- `x` = Expected failure
- `X` = Unexpected pass

### Coverage Report Columns
```
Name                    Stmts   Miss  Cover
-------------------------------------------
utils.py                  100     30    70%
collect_commute_data.py    80     40    50%
-------------------------------------------
TOTAL                     180     70    55%

Coverage HTML report generated in: Tests/htmlcov/index.html
```

- **Stmts**: Total executable statements in file
- **Miss**: Statements not executed during tests
- **Cover**: Percentage of statements covered

### Coverage Artifacts Location

All coverage-related files are stored in `Tests/` directory:

```
Tests/
├── .coverage              # Binary coverage data
├── htmlcov/               # HTML coverage report
│   ├── index.html        # Main coverage page
│   ├── utils_py.html     # Coverage for utils.py
│   └── ...
└── .pytest_cache/         # Pytest cache
```

## 12. Next Steps

✅ Tests installed and working  
✅ Coverage report generated in Tests/htmlcov/
✅ Coverage data stored in Tests/.coverage
✅ All imports working correctly
✅ Patch paths using full module names

**Now you can:**
1. Review `TESTING.md` for detailed testing guide
2. Review `TEST_STRUCTURE.md` for structure details
3. Start adding new tests for new features
4. Gradually increase coverage threshold from 55% to 70%
5. Set up CI/CD pipeline (optional)

## Quick Validation Checklist

- [ ] `Tests/` directory created
- [ ] `Tests/Commute/` subdirectory created
- [ ] `Commute/__init__.py` exists (makes it a package)
- [ ] All test files have `__init__.py` (`Tests/`, `Tests/Commute/`)
- [ ] `Tests/conftest.py` and `Tests/Commute/conftest.py` in place
- [ ] `pytest.ini` in project root with coverage configured
- [ ] `pytest.ini` has `data_file = Tests/.coverage`
- [ ] `pytest.ini` has `--cov-report=html:Tests/htmlcov`
- [ ] `requirements-test.txt` installed
- [ ] `.gitignore` includes `Tests/.coverage`, `Tests/htmlcov/`, `Tests/.pytest_cache/`
- [ ] All `@patch` decorators use full paths (`Commute.collect_commute_data.XXX`)
- [ ] `pytest` command works
- [ ] All 43 tests pass
- [ ] Coverage report generated in `Tests/htmlcov/`
- [ ] Coverage at or above 55%

If all checkboxes are checked, you're ready to go! 🎉

## Troubleshooting Quick Reference

| Error | Quick Fix |
|-------|-----------|
| Module not found | Check `Commute/__init__.py` exists |
| Import error in tests | Check `Tests/conftest.py` adds project root to path |
| Patch not working | Use full path: `Commute.collect_commute_data.XXX` |
| Coverage too low | Lower `fail_under` in `pytest.ini` |
| Old coverage data | Run `coverage erase` or `rm Tests/.coverage` |
| Can't find coverage report | Check `Tests/htmlcov/index.html` |
| Permission denied | Run `chmod +x run_tests.sh` |

## Getting Help

- **Pytest docs:** https://docs.pytest.org
- **Coverage docs:** https://coverage.readthedocs.io
- **Mock/Patch guide:** https://docs.python.org/3/library/unittest.mock.html
- **Project docs:** See `TESTING.md` for detailed testing guide