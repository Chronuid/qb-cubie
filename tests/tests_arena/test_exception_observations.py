"""Real PyVenv/codec boundaries must preserve target error provenance."""

import json
import sysconfig
import venv
from pathlib import Path

import pytest

from qb_cubie import (
    EBT,
    CloudpickleCodec,
    ExceptionExpectation,
    JsonReporter,
    MSGspecCodec,
    PickleCodec,
    PyVenv,
    WorldState,
)


@pytest.fixture(scope="module")
def observation_base(tmp_path_factory):
    base = tmp_path_factory.mktemp("exception-base")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(base)
    site = Path(sysconfig.get_path("purelib", vars={"base": str(base), "platbase": str(base)}))
    site.mkdir(parents=True, exist_ok=True)
    (site / "prepared.pth").write_text(sysconfig.get_path("purelib") + "\n", encoding="utf-8")
    return str(base)


@pytest.fixture(params=[PickleCodec, CloudpickleCodec, MSGspecCodec], ids=["pickle", "cloudpickle", "msgspec"])
def arena(request, observation_base):
    return PyVenv(env_path=observation_base, codec=request.param())


@pytest.fixture
def source(tmp_path):
    module = tmp_path / "order_target.py"
    module.write_text('''
from pathlib import Path

class OrderError(ValueError):
    pass

class BadTransport:
    def __reduce__(self):
        raise RuntimeError("cannot serialize result")

def reject(mode):
    Path("error.txt").write_text("invalid order", encoding="utf-8")
    if mode == "value":
        raise ValueError("invalid order: 17")
    if mode == "custom":
        raise OrderError("invalid order: 17")
    if mode == "wrong":
        raise TypeError("wrong type")
    if mode == "transport":
        return BadTransport()
    return None
''', encoding="utf-8")
    return module


@pytest.mark.parametrize("mode, accepted", [("value", True), ("custom", True), ("wrong", False), ("none", False)])
def test_expected_errors_across_every_codec(arena, source, tmp_path, mode, accepted):
    reference = tmp_path / "expected.txt"
    reference.write_text("invalid order", encoding="utf-8")
    result = EBT(
        target="order_target:reject", arena=arena,
        pre=WorldState(args=(mode,), fs={"order_target.py": str(source)}),
        post=WorldState(raises=ExceptionExpectation(ValueError, match="order: 17$"),
                        fs={"error.txt": str(reference)}), reporter=None,
    ).run()
    assert result.evaluation is accepted
    assert result.traces[0].evaluation is accepted
    assert "fs" not in (result.traces[0].diffs or {})
    assert arena.workspace_path is None
    report = tmp_path / "report.json"
    JsonReporter(report).report(result)
    observed = json.loads(report.read_text())["traces"][0]["outcome"]["exception"]
    if mode == "none":
        assert observed is None
    else:
        expected_type = {"value": "builtins.ValueError", "custom": "order_target.OrderError",
                         "wrong": "builtins.TypeError"}[mode]
        assert observed["type"] == expected_type


@pytest.mark.parametrize("fault", ["import", "transport"])
def test_resolution_and_serialization_failures_are_not_target_observations(arena, source, fault):
    case = EBT(
        target="missing_module:reject" if fault == "import" else "order_target:reject", arena=arena,
        pre=WorldState(args=("transport",), fs={"order_target.py": str(source)}),
        post=WorldState(raises=ExceptionExpectation(Exception)), reporter=None,
    )
    with pytest.raises(RuntimeError, match="Arena Error:"):
        case.run()
    assert case.run_trace is None
    assert arena.workspace_path is None
