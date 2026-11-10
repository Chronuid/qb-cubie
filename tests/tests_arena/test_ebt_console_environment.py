"""GUTACHTEN 9.2 / B7: a copied CLI must use the clone or be rejected early."""

import json
import os
import subprocess
import venv
from pathlib import Path

import pytest

from qb_cubie import EBT, PickleCodec, PyVenv, WorldState
from qb_cubie.arenas._requirements import _environment_python

CLI = (
    "import json, os, sys\n"
    "import cubie_environment_marker as marker\n"
    "print(json.dumps({'prefix': sys.prefix, 'marker': marker.VALUE, "
    "'virtual_env': os.environ.get('VIRTUAL_ENV')}))\n"
)


@pytest.fixture(params=["base", "base with spaces"], ids=["shebang", "shell-trampoline"])
def cli_base(tmp_path, request):
    base = tmp_path / request.param
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(base)
    python = _environment_python(base)
    probe = subprocess.run(
        [str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    packages = Path(probe.stdout.strip())
    (packages / "cubie_environment_marker.py").write_text("VALUE = 'base'\n", encoding="utf-8")
    (packages / "cubie_environment_cli.py").write_text(CLI, encoding="utf-8")
    # Standard shell trampoline used for POSIX entry points with spaces in the interpreter path.
    console = python.parent / "cubie-env-probe"
    header = (f"#!/bin/sh\n'''exec' '{python}' \"$0\" \"$@\"\n' '''\n"
              if " " in str(python) else f"#!{python}\n")
    console.write_text(header + CLI, encoding="utf-8")
    console.chmod(0o755)
    return base, packages


@pytest.mark.parametrize("launch", ["module", "path", "absolute"])
@pytest.mark.skipif(os.name == "nt", reason="POSIX console-script launcher; Windows needs a native launcher case")
def test_cli_uses_clone_dependencies_or_is_explicitly_rejected_before_target(
    tmp_path, cli_base, launch,
):
    base, packages = cli_base
    # First establish independently that the launcher works and identifies its base.
    original = subprocess.run(
        [str(_environment_python(base).parent / "cubie-env-probe")],
        capture_output=True, text=True, timeout=15, check=True,
    )
    assert json.loads(original.stdout)["marker"] == "base"
    assert Path(json.loads(original.stdout)["prefix"]).resolve() == base.resolve()
    if launch == "module":
        # Keep a positive control even if the implementation rejects unsafe bases entirely.
        (_environment_python(base).parent / "cubie-env-probe").unlink()
    started = tmp_path / "target-started"
    target = tmp_path / "console_target.py"
    target.write_text(
        "def run(launch, marker_relative, started):\n"
        "    import json, os, shutil, subprocess, sys\n"
        "    from pathlib import Path\n"
        "    Path(started).write_text('started', encoding='utf-8')\n"
        "    marker = Path(sys.prefix) / marker_relative\n"
        "    marker.write_text(\"VALUE = 'clone'\\n\", encoding='utf-8')\n"
        "    console = shutil.which('cubie-env-probe')\n"
        "    command = [sys.executable, '-m', 'cubie_environment_cli']\n"
        "    if launch != 'module': command = ['cubie-env-probe' if launch == 'path' else console]\n"
        "    child = subprocess.run(command, capture_output=True, text=True, timeout=10, check=True)\n"
        "    return {'prefix': sys.prefix, 'virtual_env': os.environ['VIRTUAL_ENV'],\n"
        "            'console': console, 'child': json.loads(child.stdout)}\n",
        encoding="utf-8",
    )
    arena = PyVenv(str(base), codec=PickleCodec(), timeout=20)
    reports = []

    class Reporter:
        def report(self, result):
            reports.append(result)

    def uses_clone(value):
        clone = Path(value["prefix"]).resolve()
        return (clone != base.resolve() and Path(value["virtual_env"]).resolve() == clone
                and (launch == "module" or Path(value["console"]).resolve().is_relative_to(clone))
                and Path(value["child"]["prefix"]).resolve() == clone
                and Path(value["child"]["virtual_env"]).resolve() == clone
                and value["child"]["marker"] == "clone")

    case = EBT(target="console_target:run", arena=arena,
               pre=WorldState(fs={target.name: str(target)}, args=(
                   launch, str((packages / "cubie_environment_marker.py").relative_to(base)), str(started),
               )), post=WorldState(returns=uses_clone), reporter=Reporter())
    try:
        result = case.run()
        observed = result.traces[0].outcome.returns
        assert started.exists()
        assert Path(observed["prefix"]).resolve() != base.resolve()
        assert result.evaluation is True, observed
        assert reports == [result]
    finally:
        assert arena.workspace_path is None and arena.virtual_path is None
        assert (packages / "cubie_environment_marker.py").read_text(encoding="utf-8") == "VALUE = 'base'\n"


@pytest.mark.parametrize("launcher", ["native.exe", "custom-shell"])
def test_unsupported_launchers_are_rejected_before_target_or_reporting(cli_base, launcher):
    base, _ = cli_base
    script = _environment_python(base).parent / launcher
    content = f"#!/bin/sh\nexec '{_environment_python(base)}' \"$@\"\n".encode()
    script.write_bytes(content)
    script.chmod(0o755)
    calls = []

    class Reporter:
        def report(self, trace):
            calls.append("report")

    arena = PyVenv(str(base), codec=PickleCodec())
    case = EBT(target=lambda: calls.append("target"), arena=arena, reporter=Reporter())
    with pytest.raises(RuntimeError, match="Unsupported console entry point"):
        case.run()
    assert calls == [] and case.run_trace is None
    assert arena.workspace_path is None and arena.virtual_path is None
    assert script.read_bytes() == content


@pytest.mark.skipif(os.name == "nt", reason="POSIX script symlinks")
@pytest.mark.parametrize("external", [False, True], ids=["internal-link", "external-link"])
def test_script_links_preserve_clone_execution_or_fail_before_target(tmp_path, cli_base, external):
    base, _ = cli_base
    scripts = _environment_python(base).parent
    body = (tmp_path if external else base) / "alias-body.py"
    original = (scripts / "cubie-env-probe").read_bytes()
    body.write_bytes(original)
    body.chmod(0o755)
    (scripts / "cubie-alias").symlink_to(body)
    arena = PyVenv(str(base), codec=PickleCodec())
    case = EBT(target="subprocess:check_output", arena=arena,
               pre=WorldState(args=(["cubie-alias"],), kwargs={"text": True, "timeout": 10}),
               post=WorldState(returns=lambda text: (
                   Path(json.loads(text)["prefix"]).resolve() != base.resolve()
                   and json.loads(text)["prefix"] == json.loads(text)["virtual_env"]
               )))
    if external:
        with pytest.raises(RuntimeError, match="Unsupported console entry point"):
            case.run()
        assert case.run_trace is None
    else:
        assert case.run().evaluation is True
    assert arena.workspace_path is None
    assert body.read_bytes() == original
