from pathlib import Path

CURRENT_DIR = Path(__file__).parent
EMPTY_TEST_ENV = CURRENT_DIR / "empty_test_env"
__all__ = ["EMPTY_TEST_ENV"]
