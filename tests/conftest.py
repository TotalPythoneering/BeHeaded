# Pytest hook to print a success message when the entire test session passes.
# Place this file in the tests/ directory so pytest will pick it up automatically.

def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finishes.
    exitstatus == 0 means all tests passed.
    """
    if exitstatus == 0:
        # Print to stdout so the message is visible at the end of the run.
        print("\nTESTING SUCCESS")