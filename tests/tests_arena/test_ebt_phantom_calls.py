"""GUTACHTEN 9.1 / B2: imports may not erase relevant runtime checks.

The child uses the host's installed dependencies through an explicit .pth file.
No provisioning, network access, or repository-local arena base is needed.
Only the child process receives PyVenv's phantom import hook.
"""

import importlib
import subprocess
import sys
import sysconfig
import venv
from pathlib import Path

import pytest

from qb_cubie import EBT, MSGspecCodec, PickleCodec, PyVenv, WorldState
from qb_cubie.arenas._requirements import _environment_python


@pytest.fixture(scope="module")
def base_environment(tmp_path_factory):
    base = tmp_path_factory.mktemp("phantom-base") / "venv"
    venv.EnvBuilder(with_pip=False).create(base)
    child_packages = Path(sysconfig.get_path("purelib", vars={"base": str(base), "platbase": str(base)}))
    # system-site-packages points at the base interpreter, not an active host venv.
    (child_packages / "host-dependencies.pth").write_text(
        sysconfig.get_path("purelib") + "\n", encoding="utf-8",
    )
    probe = subprocess.run(
        [str(_environment_python(base)), "-I", "-c", "import pytest, msgspec"],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert probe.returncode == 0, probe.stderr
    return base


@pytest.fixture(params=["module", "function"], ids=["module-import", "runtime-import"])
def target_module(request, tmp_path, monkeypatch):
    name = f"cubie_phantom_regression_{request.param}"
    source = tmp_path / f"{name}.py"
    prefix = "import pytest\n\n" if request.param == "module" else ""
    local_import = "    import pytest\n" if request.param == "function" else ""
    source.write_text(
        prefix
        + "def explicit_failure():\n" + local_import
        + "    pytest.fail('explicit target rejection')\n"
        + "    return 'accepted'\n\n"
        + "def required_exception():\n" + local_import
        + "    with pytest.raises(ValueError):\n"
        + "        pass\n"
        + "    return 'accepted'\n\n"
        + "def import_only():\n" + local_import
        + "    return 'accepted'\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module(name)
    try:
        yield module, source
    finally:
        # Each parametrized case must import its own source, even on the host.
        monkeypatch.delitem(sys.modules, name, raising=False)


@pytest.mark.parametrize("codec_type", [MSGspecCodec, PickleCodec], ids=["default-codec", "pickle"])
@pytest.mark.parametrize("check", ["explicit_failure", "required_exception"])
def test_pyvenv_must_preserve_checks_even_when_their_return_value_is_ignored(
    base_environment, target_module, codec_type, check,
):
    module, source = target_module
    target = getattr(module, check)
    # An independent host execution establishes that the same check really fails.
    with pytest.raises(pytest.fail.Exception):
        target()
    arena = PyVenv(str(base_environment), codec=codec_type(), timeout=15)
    case = EBT(target=f"{module.__name__}:{check}", arena=arena,
               pre=WorldState(fs={source.name: str(source)}),
               post=WorldState(returns="accepted"), reporter=None)
    rejection = "explicit target rejection" if check == "explicit_failure" else "DID NOT RAISE"
    with pytest.raises(RuntimeError, match=rf"{rejection}|[Pp]hantom"):
        case.run()
    assert case.run_trace is None
    assert arena.workspace_path is None


@pytest.mark.parametrize("codec_type", [MSGspecCodec, PickleCodec], ids=["default-codec", "pickle"])
def test_unused_test_import_does_not_prevent_an_independent_target_from_running(
    base_environment, target_module, codec_type,
):
    module, source = target_module
    assert module.import_only() == "accepted"
    arena = PyVenv(str(base_environment), codec=codec_type(), timeout=15)
    result = EBT(target=f"{module.__name__}:import_only", arena=arena,
                 pre=WorldState(fs={source.name: str(source)}),
                 post=WorldState(returns="accepted")).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == "accepted"
    assert arena.workspace_path is None
