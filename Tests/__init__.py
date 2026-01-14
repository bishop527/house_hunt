"""
Test suite for House Hunt Project

This package contains unit and integration tests organized by component.

Test modules:
- test_utils: Tests for utility functions in utils.py
- Commute/test_collect_commute_data: Tests for commute data collection

Run all tests:
    pytest Tests/ -v

Run with coverage:
    pytest Tests/ --cov=. --cov-report=html
"""

__version__ = "1.0.0"
__all__ = ["test_utils", "Commute"]