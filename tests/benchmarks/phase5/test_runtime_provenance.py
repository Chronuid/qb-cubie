"""Keep checkout declarations separate from observed environment identity."""

import subprocess

from cubie_benchmarks.measurement.provenance import capture


def test_installed_runtime_has_no_fabricated_repository_or_lock(tmp_path):
    value = capture(tmp_path / "installed/module.py")
    assert value["repository_commit"] is None
    assert value["dependency_lock_sha256"] is None
    assert value["dependency_lock_verified"] is False
    assert len(value["installed_distributions_sha256"]) == 64


def test_checkout_records_commit_dirty_state_and_lock_separately(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    git("init")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    lock = tmp_path / "uv.lock"
    lock.write_text("version = 1\n")
    git("add", "uv.lock")
    git("commit", "-m", "fixture")
    before = capture(tmp_path / "src/module.py")
    assert before["repository_dirty"] is False
    lock.write_text("version = 2\n")
    after = capture(tmp_path / "src/module.py")
    assert before["repository_commit"] == after["repository_commit"]
    assert after["repository_dirty"] is True
    assert before["repository_diff_sha256"] != after["repository_diff_sha256"]
    assert before["dependency_lock_sha256"] != after["dependency_lock_sha256"]
    assert after["dependency_lock_verified"] is False
