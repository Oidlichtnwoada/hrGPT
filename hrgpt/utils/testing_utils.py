import os


def is_test_running() -> bool:
    return os.getenv("PYTEST_CURRENT_TEST") is not None
