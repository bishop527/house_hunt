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
