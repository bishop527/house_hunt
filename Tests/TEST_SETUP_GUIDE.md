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
```

Your structure should look like:
```
house_hunt/
├── Tests/               # Create this
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_utils.py
│   └── Commute/         # Create this subdirectory
│       ├── __init__.py
│       └── test_collect_commute_data.py
├── utils.py
├── collect_commute_data.py
├── constants.py
└── ...
```

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

## 3. Create Test Files

Copy the test files into the `Tests/` directory:

1. **Tests/__init__.py** - Makes Tests a package
2. **Tests/conftest.py** - Shared fixtures
3. **Tests/test_utils.py** - Tests for utils.py
4. **Tests/Commute/__init__.py** - Makes Commute a package
5. **Tests/Commute/test_collect_commute_data.py** - Tests for collect_commute_data.py

## 4. Configuration Files

Place these in the project root:

1. **pytest.ini** - Pytest configuration
2. **requirements-test.txt** - Test dependencies
3. **run_tests.sh** - Test runner script

### Make Test Runner Executable
```bash
chmod +x run_tests.sh
```

## 5. Run Tests

### Quick Test
```bash
# Run all tests
pytest

# Should see output like:
# ==================== test session starts ====================
# collected 35 items
#
# Tests/test_utils.py ..................... [ 60%]
# Tests/Commute/test_collect_commute_data.py ............... [100%]
#
# ==================== 35 passed in 2.34s ====================
```

### With Coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### Using Test Runner
```bash
./run_tests.sh
```

## 6. Verify Everything Works

### Run Full Test Suite
```bash
./run_tests.sh
```

Expected output:
```
========================================
House Hunt Project - Test Suite
========================================

Running tests...
Command: pytest -v --cov=. --cov-report=term-missing --cov-report=html

...
==================== 35 passed in 2.34s ====================

========================================
All tests passed!
========================================

Coverage report saved to: htmlcov/index.html
```

### Check Coverage Report
```bash
# Open in browser
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 7. Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'utils'"

**Solution:**
```bash
# Ensure you're running from project root
cd /path/to/house_hunt
pytest tests/
```

### Issue: "pytest: command not found"

**Solution:**
```bash
# Install pytest
pip install pytest

# Or use python -m
python -m pytest tests/
```

### Issue: "No tests collected"

**Solution:**
```bash
# Check test discovery
pytest --collect-only

# Ensure files start with test_
ls tests/test_*.py
```

### Issue: Import errors in tests

**Solution:**
Check that `Tests/conftest.py` contains:
```python
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
```

### Issue: "Permission denied" for run_tests.sh

**Solution:**
```bash
chmod +x run_tests.sh
```

## 8. Daily Workflow

### Before Committing Code
```bash
# Run full test suite
./run_tests.sh

# Ensure all tests pass
# Check coverage is above 70%
```

### After Changing Source Code
```bash
# Run relevant tests
pytest Tests/test_utils.py -v  # If changed utils.py
pytest Tests/Commute/ -v       # If changed commute code

# Or run all tests
pytest
```

### Adding New Features
```bash
# 1. Write tests first (TDD)
# Edit Tests/test_utils.py or Tests/Commute/test_collect_commute_data.py

# 2. Run tests (they should fail)
pytest Tests/ -v

# 3. Implement feature
# Edit utils.py or collect_commute_data.py

# 4. Run tests again (they should pass)
pytest Tests/ -v
```

## 9. Test Commands Cheat Sheet

```bash
# Basic runs
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -q                       # Quiet output

# Specific tests
pytest Tests/test_utils.py      # One file
pytest Tests/Commute/           # All Commute tests
pytest Tests/test_utils.py::test_get_api_key_success  # One test

# With coverage
pytest --cov=.                  # Coverage report
pytest --cov=. --cov-report=html  # HTML coverage

# By marker
pytest -m unit                  # Unit tests only
pytest -m "not slow"            # Skip slow tests

# Debugging
pytest -s                       # Show print() output
pytest --pdb                    # Drop into debugger on failure
pytest -x                       # Stop on first failure

# Using test runner
./run_tests.sh                  # All tests
./run_tests.sh --unit           # Unit tests
./run_tests.sh --no-coverage    # Skip coverage
./run_tests.sh --fast           # Skip slow tests
```

## 10. Next Steps

✅ Tests installed and working  
✅ Coverage report generated  
✅ Test runner configured

**Now you can:**
1. Review `TESTING.md` for detailed testing guide
2. Review `TEST_STRUCTURE.md` for structure details
3. Start adding new tests for new features
4. Set up CI/CD pipeline (optional)

## Quick Validation Checklist

- [ ] `Tests/` directory created
- [ ] `Tests/Commute/` subdirectory created
- [ ] All test files in place (`__init__.py`, `conftest.py`, etc.)
- [ ] `pytest.ini` in project root (testpaths = Tests)
- [ ] `requirements-test.txt` installed
- [ ] `run_tests.sh` executable
- [ ] `pytest` command works
- [ ] All 35+ tests pass
- [ ] Coverage report generated
- [ ] Coverage above 70%

If all checkboxes are checked, you're ready to go! 🎉

## Getting Help

- **Pytest docs:** https://docs.pytest.org
- **Coverage docs:** https://coverage.readthedocs.io
- **Project docs:** See `TESTING.md` and `TEST_STRUCTURE.md`