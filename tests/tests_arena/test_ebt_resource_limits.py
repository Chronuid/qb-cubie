"""Executable resource contracts for GUTACHTEN.md, priority 3.1.

See resource_cases/README.md for the execution limits and watchdog contract.
Linux is required for PID identity checks in the independent cleanup watchdog.
"""

import importlib.metadata
import json
import os
import shutil
import signal
import subprocess
import sys
import sysconfig
import time
import venv
from pathlib import Path

import cloudpickle
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Independent process-tree watchdog uses /proc",
)
RUNNER = Path(__file__).with_name("resource_cases") / "runner.py"
ROOT = Path(__file__).resolve().parents[2]


def _same_live_process(identity):
    pid, started = identity
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return False
    # Zombies no longer execute or hold pipes open; their parent must reap them.
    return fields[19] == started and fields[0] != "Z"


def _identities(directory):
    return {
        name: json.loads(path.read_text())
        for name in ("target", "child", "grandchild")
        if (path := directory / f"{name}.json").exists()
    }


def _probe(directory, config, *, watchdog=15):
    """Never use Cubie's own timeout or cleanup to protect the test runner."""
    directory.mkdir()
    config = dict(config, directory=str(directory))
    config_path = directory / "config.json"
    config_path.write_text(json.dumps(config))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.Popen(
        [sys.executable, str(RUNNER), str(config_path)],
        cwd=ROOT, env=environment, start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        try:
            process.wait(timeout=watchdog)
        except subprocess.TimeoutExpired:
            pytest.fail(f"Independent watchdog expired after {watchdog}s: {config}")
        report = directory / "result.json"
        assert process.returncode == 0 and report.is_file(), "Probe failed before reporting"
        observations = json.loads(report.read_text())
        # Observe BEFORE emergency cleanup, otherwise leaked descendants pass.
        identities = _identities(directory)
        deadline = time.monotonic() + 1
        while any(_same_live_process(value) for value in identities.values()):
            if time.monotonic() >= deadline:
                break
            time.sleep(0.01)
        observations["alive"] = [
            name for name, value in identities.items() if _same_live_process(value)
        ]
        observations["started"] = sorted(identities)
        observations["tree_ready"] = (directory / "tree_ready").exists()
        workspace = directory / "workspace"
        observations["workspace_removed"] = (
            workspace.exists() and not Path(workspace.read_text()).exists()
        )
        return observations
    finally:
        # Arena runners may create their own session. Explicit PID cleanup
        # covers those as well as the watchdog's original process group.
        for identity in reversed(list(_identities(directory).values())):
            if _same_live_process(identity):
                try:
                    os.kill(identity[0], signal.SIGKILL)
                except ProcessLookupError:
                    pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


@pytest.fixture(scope="module")
def codec_base(tmp_path_factory):
    """Build a small real venv offline, without copying the development venv."""
    base = tmp_path_factory.mktemp("resource-codec-base")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(base)
    site = Path(sysconfig.get_path("purelib", vars={"base": str(base), "platbase": str(base)}))
    shutil.copytree(Path(cloudpickle.__file__).parent, site / "cloudpickle")
    distribution = importlib.metadata.distribution("cloudpickle")
    metadata = next(
        entry for entry in distribution.files
        if entry.name == "METADATA" and entry.parent.name.endswith(".dist-info")
    )
    shutil.copytree(distribution.locate_file(metadata).parent, site / metadata.parent.name)
    return str(base)


@pytest.fixture(params=["tempfs", "pyvenv"])
def run_case(request, tmp_path):
    config = {"arena": request.param, "limits": {}, "mode": "quiet"}
    if request.param == "pyvenv":
        config["base"] = request.getfixturevalue("codec_base")

    def run(**changes):
        return _probe(tmp_path / "probe", dict(config, **changes))

    return run


def _assert_clean(result):
    assert result["started"], result
    assert result["alive"] == [], result
    assert result["workspace_reset"] and result["workspace_removed"], result
    assert result["scratch_entries"] == [], result


def _assert_timeout(result):
    assert result.get("is_timeout") is True, result
    assert result["run_trace_present"] is False, result
    assert "timeout" in result["message"].lower() or "timed out" in result["message"].lower(), result
    _assert_clean(result)


def _assert_output_limit(result):
    assert result.get("is_runtime_error") is True, result
    assert "output" in result["message"].lower() and "limit" in result["message"].lower(), result
    assert result["run_trace_present"] is False, result
    # The error itself must not duplicate unbounded captured output.
    assert len(result["message"].encode()) < 8192, result
    _assert_clean(result)


def test_unlimited_control_executes_target_and_checks_return(run_case):
    result = run_case()
    assert "error_type" not in result, result
    assert result["evaluation"] is True and result["trace_count"] == 1, result
    _assert_clean(result)


def test_limits_allow_successful_ebt_run(run_case):
    result = run_case(mode="output", bytes=128, streams=[1, 2],
                      limits={"timeout": 5, "max_output_bytes": 1024})
    assert "error_type" not in result, result
    assert result["evaluation"] is True and result["trace_count"] == 1, result
    _assert_clean(result)


@pytest.mark.parametrize("expect", [True, False])
def test_hanging_target_times_out_even_for_negated_ebt(run_case, expect):
    result = run_case(mode="sleep", expect=expect, limits={"timeout": 1})
    _assert_timeout(result)
    assert result["elapsed"] < 8, result


@pytest.mark.parametrize("streams", [[1], [2], [1, 2]], ids=["stdout", "stderr", "combined"])
def test_output_overflow_fails_even_when_target_returns_expected_value(run_case, streams):
    # Combined case: each stream alone stays below 1024, their sum exceeds it.
    result = run_case(mode="output", streams=streams,
                      bytes=768 if len(streams) == 2 else 2048,
                      limits={"max_output_bytes": 1024})
    _assert_output_limit(result)


def test_output_limit_aborts_before_target_completion(run_case):
    result = run_case(mode="output", hang_after_output=True,
                      limits={"timeout": 5, "max_output_bytes": 1024})
    _assert_output_limit(result)
    assert result["elapsed"] < 4, result


@pytest.mark.parametrize("byte_count, overflows", [(1024, False), (1026, True)])
def test_output_budget_counts_utf8_bytes_and_allows_exact_limit(run_case, byte_count, overflows):
    result = run_case(mode="output", bytes=byte_count,
                      limits={"timeout": 5, "max_output_bytes": 1024})
    if overflows:
        _assert_output_limit(result)
    else:
        assert "error_type" not in result and result["evaluation"] is True, result
        _assert_clean(result)


@pytest.mark.parametrize("stubborn", [False, True], ids=["ordinary", "ignores-sigterm"])
@pytest.mark.parametrize("reason", ["timeout", "output"])
def test_abort_stops_target_child_and_grandchild(run_case, reason, stubborn):
    limits = {"timeout": 3, "max_output_bytes": 1024}
    result = run_case(mode=f"tree_{reason}", stubborn=stubborn, limits=limits)
    assert result["tree_ready"], result
    assert result["started"] == ["child", "grandchild", "target"], result
    if reason == "timeout":
        _assert_timeout(result)
    else:
        _assert_output_limit(result)
    assert result["elapsed"] < 8, result


def test_timeout_kills_descendants_after_runner_has_exited(run_case):
    result = run_case(mode="tree_success", stubborn=True,
                      limits={"timeout": 2, "max_output_bytes": 1024})
    assert result["tree_ready"], result
    assert result["started"] == ["child", "grandchild", "target"], result
    _assert_timeout(result)


@pytest.mark.parametrize("reason", ["timeout", "output"])
def test_standalone_run_also_cleans_up_after_abort(run_case, reason):
    result = run_case(entrypoint="run", mode="sleep" if reason == "timeout" else "output",
                      limits={"timeout": 1, "max_output_bytes": 1024})
    if reason == "timeout":
        _assert_timeout(result)
    else:
        _assert_output_limit(result)


@pytest.mark.parametrize("mode, byte_count", [("quiet", 0), ("output", 2)])
def test_zero_output_budget_allows_only_silent_targets(run_case, mode, byte_count):
    result = run_case(mode=mode, bytes=byte_count,
                      limits={"timeout": 5, "max_output_bytes": 0})
    if mode == "output":
        _assert_output_limit(result)
    else:
        assert "error_type" not in result and result["evaluation"] is True, result
        _assert_clean(result)


def test_watchdog_rejects_unlimited_hang_and_kills_descendants(tmp_path):
    directory = tmp_path / "watchdog"
    with pytest.raises(pytest.fail.Exception, match="Independent watchdog expired"):
        _probe(directory, {"arena": "tempfs", "limits": {}, "mode": "tree_timeout",
                           "stubborn": True}, watchdog=3)
    assert (directory / "tree_ready").exists(), "Self-test never started its descendants"
    identities = _identities(directory)
    deadline = time.monotonic() + 2
    while any(_same_live_process(value) for value in identities.values()):
        assert time.monotonic() < deadline, "Watchdog leaked a live process"
        time.sleep(0.01)


def test_watchdog_observes_leaks_before_emergency_cleanup(tmp_path):
    directory = tmp_path / "leaks"
    result = _probe(directory, {
        "arena": "tempfs", "limits": {}, "mode": "tree_success", "stubborn": True,
    })
    assert "error_type" not in result and result["evaluation"] is True, result
    assert result["tree_ready"], result
    assert result["alive"] == ["child", "grandchild"], result
    # Emergency cleanup has now run, but the returned observation retains the
    # violation. A harness that checked only afterwards would report success.
    deadline = time.monotonic() + 2
    while any(_same_live_process(value) for value in _identities(directory).values()):
        assert time.monotonic() < deadline, "Emergency cleanup leaked a live process"
        time.sleep(0.01)
