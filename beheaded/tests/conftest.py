# MISSION: Support final testing status.
# STATUS: Prodction
# VERSION: 1.0.0
# NOTES: Uses pytest.
# Pytest hook to print a success message when the entire test session passes.
# Place this file in the tests/ directory so pytest will pick it up automatically.
# DATE: 2026-01-18 03:59:42
# FILE: conftest.py
# AUTHOR: Randall Nagy

def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finishes.
    exitstatus == 0 means all tests passed.
    """
    if exitstatus == 0:
        # Print to stdout so the message is visible at the end of the run.
        print("\nTESTING SUCCESS")
