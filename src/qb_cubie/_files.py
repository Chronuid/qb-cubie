"""Compare current file contents without persistent stat-based comparison caches."""

from pathlib import Path


def same_contents(left: Path, right: Path) -> bool:
    """Compare file bytes in bounded chunks on every call."""
    with left.open("rb") as first, right.open("rb") as second:
        while True:
            chunk = first.read(128 * 1024)
            if chunk != second.read(128 * 1024):
                return False
            if not chunk:
                return True
