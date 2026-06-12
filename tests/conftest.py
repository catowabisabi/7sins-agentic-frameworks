"""
pytest configuration for 7Sins Project.

Setup:
  - Auto-injects repo root into sys.path at session start, so test files
    can import project modules without hardcoded paths.

Fixtures:
  - reset_sys_path (autouse=True): Saves sys.path before each test and
    restores it after, preventing test-to-test pollution.
"""
import os
import sys

import pytest

# Repo root — add once at session start
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture(autouse=True)
def reset_sys_path():
    """Ensure every test starts with a clean sys.path."""
    original = sys.path.copy()
    yield
    sys.path[:] = original