"""Core features must work after setup without installers or Internet access.

Each scenario runs in a fresh interpreter. A sitecustomize audit hook also guards
Python children, including PyVenv runners and multiprocessing workers. Attempts
are logged before raising, so catching an exception cannot hide a violation.
This is a regression harness for Python execution paths, not an OS sandbox for
arbitrary native code. DockerArena/VmArena are unavailable feature drafts.
"""

import os
import subprocess
import sys
import sysconfig
import venv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUARD = r'''
import os
import shlex
import socket
import sys

def deny(reason):
    with open(os.environ["CUBIE_OFFLINE_LOG"], "a", encoding="utf-8") as log:
        log.write(reason + "\n")
    raise RuntimeError("OFFLINE CONTRACT: " + reason)

def check_command(executable, command):
    name = os.path.basename(os.fsdecode(executable)).lower()
    parts = shlex.split(command) if isinstance(command, str) else list(command)
    parts = [os.fsdecode(part) for part in parts]
    if name.startswith(("python", "pypy")):
        if "-m" in parts:
            module = parts[parts.index("-m") + 1]
            if module in {"pip", "ensurepip", "uv"}:
                deny("installer: " + repr(parts))
        if "-S" in parts or "-I" in parts or "-E" in parts:
            deny("Python child would bypass the offline hook")
        return
    if name not in {"mypy", "pylint"}:
        deny("external command: " + repr(parts))

def audit(event, args):
    if event == "subprocess.Popen":
        check_command(args[0], args[1])
    elif event in {"os.exec", "os.posix_spawn"}:
        check_command(args[0], args[1])
    elif event == "os.system":
        deny("shell command: " + repr(args[0]))
    elif event == "socket.__new__" and args[1] in {
        socket.AF_INET, socket.AF_INET6
    }:
        deny("Internet socket")
    elif event in {
        "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
        "socket.getnameinfo", "socket.sendto"
    }:
        deny("network lookup or datagram: " + event)
    elif event in {"socket.connect", "socket.bind"}:
        if args[0].family in {socket.AF_INET, socket.AF_INET6}:
            deny("Internet connection: " + event)

sys.addaudithook(audit)
'''


@pytest.fixture(scope="module")
def prepared_environment(tmp_path_factory):
    """Expose already installed project packages in a tiny local base venv.

    No installer, dependency download, or copy of the entire project venv is
    needed. The .pth file models an environment provisioned during initial setup.
    Codec requirement checks remain enabled in the production code.
    """
    root = tmp_path_factory.mktemp("cubie-offline")
    base = root / "prepared-venv"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(base)
    site_packages = Path(sysconfig.get_path(
        "purelib", vars={"base": str(base), "platbase": str(base)},
    ))
    site_packages.mkdir(parents=True, exist_ok=True)
    (site_packages / "prepared-project.pth").write_text(
        sysconfig.get_path("purelib") + "\n", encoding="utf-8",
    )
    hook = root / "hooks"
    hook.mkdir()
    (hook / "sitecustomize.py").write_text(GUARD, encoding="utf-8")
    return base, hook


def guarded_run(prepared_environment, tmp_path, code, *arguments):
    base, hook = prepared_environment
    log = tmp_path / "offline-violations.log"
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": os.pathsep.join([
            str(hook), str(PROJECT_ROOT / "src"), str(PROJECT_ROOT),
        ]),
        "CUBIE_OFFLINE_LOG": str(log),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PATH": os.pathsep.join([
            str(Path(sys.executable).parent), env.get("PATH", ""),
        ]),
        "MYPY_CACHE_DIR": str(tmp_path / "mypy-cache"),
        "PYLINTHOME": str(tmp_path / "pylint-cache"),
    })
    process = subprocess.run(
        [sys.executable, "-c", code, str(base), *arguments],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
        check=False,
    )
    violations = log.read_text(encoding="utf-8") if log.exists() else ""
    return process, violations


FEATURES = [
    "imports", "prepared-environment", "ebt", "ebt-reporters", "tempfs",
    "pickle-processes", "loky-processes",
    "rbt", "cst", "pylint", "mypy", "linter-aggregation",
    "linter-discovery",
    "pyvenv-default", "pyvenv-pickle", "pyvenv-msgspec", "pyvenv-cloudpickle",
    "builder-reuse", "builder-reuse-packages", "virtualization-unavailable",
]


@pytest.mark.parametrize("feature", FEATURES)
def test_core_feature_requires_no_install_or_network(
    feature, prepared_environment, tmp_path,
):
    code = (
        "import sys; from tests.test_offline_core import exercise; "
        "exercise(sys.argv[2], sys.argv[1])"
    )
    process, violations = guarded_run(
        prepared_environment, tmp_path, code, feature,
    )
    assert not violations, f"{feature} violated the offline contract:\n{violations}"
    assert process.returncode == 0, (
        f"{feature} failed offline:\n{process.stdout}\n{process.stderr}"
    )


def exercise(feature, base):
    """Execute real public APIs under the audit hook, without backend mocks."""
    import cubie
    from cubie import EBT, WorldState

    if feature == "imports":
        assert all(hasattr(cubie, name) for name in cubie.__all__)
    elif feature == "prepared-environment":
        subprocess.run(
            [str(Path(base) / "bin" / "python"), "-c",
             "import msgspec, cloudpickle, libcst, mypy, pylint"],
            check=True,
        )
    elif feature == "ebt":
        trace = EBT(
            target=sum,
            pre=[WorldState(args=([1, 2],)), WorldState(args=([3],))],
            post=[WorldState(returns=3), WorldState(returns=99, expect=False)],
        ).run()
        assert trace.evaluation is True and len(trace.traces) == 4
        with pytest.raises(AssertionError):
            EBT(target=sum, pre=WorldState(args=([1],)),
                post=WorldState(returns=2)).run()
    elif feature == "ebt-reporters":
        received = []

        class Reporter:
            def report(self, trace):
                received.append(trace)

        for reporter in (Reporter(), None):
            trace = EBT(
                target=sum, pre=WorldState(args=([1],)),
                post=WorldState(returns=2), reporter=reporter,
            ).run()
            assert trace.evaluation is False
        assert len(received) == 1 and received[0].evaluation is False
    elif feature == "tempfs":
        source = Path("seed.txt")
        source.write_text("offline", encoding="utf-8")
        arena = cubie.TempFS()

        def edit_file():
            content = Path("input.txt").read_text(encoding="utf-8")
            Path("output.txt").write_text(content.upper(), encoding="utf-8")
            return content

        EBT(target=edit_file, arena=arena,
            pre=WorldState(fs={"input.txt": str(source.resolve())}),
            post=WorldState(returns="offline", fs={
                "output.txt": lambda path: path.read_text() == "OFFLINE",
            })).run()
        assert arena.workspace_path is None
    elif feature in {"pickle-processes", "loky-processes"}:
        from cubie import multiprocessors

        # Bound worker count; both real execution backends remain enabled.
        multiprocessors.os.cpu_count = lambda: 2
        worker_pid = os.getpid()
        trace = EBT(
            target=os.getpid,
            pre=[WorldState(), WorldState()],
            post=WorldState(returns=(
                (lambda value: value != worker_pid)
                if feature == "loky-processes" else int
            )),
            multiprocessing=True,
        ).run()
        assert trace.evaluation is True and len(trace.traces) == 2
        assert all(t.outcome.returns != worker_pid for t in trace.traces)
    elif feature == "rbt":
        from cubie.protocols import ReviewData
        from cubie.rbt import RBT

        class Reviewer:
            def review(self, target, check):
                assert target == "Example" and check == "Check"
                return ReviewData(passed=False, report={"text": "offline"})

        class Reporter:
            def report(self, result):
                received.append(result)

        received = []
        RBT("Check", "Example", Reviewer(), reporter=Reporter()).run()
        assert len(received) == 1 and received[0].report == {"text": "offline"}
        RBT("Check", "Example", Reviewer(), reporter=None).run()
        with pytest.raises(AssertionError, match="offline"):
            RBT("Check", "Example", Reviewer()).run()
    elif feature == "cst":
        import libcst as cst

        class ForbidEval(cubie.CstRule):
            def visit_Call(self, node):
                if isinstance(node.func, cst.Name) and node.func.value == "eval":
                    self.add_diagnostic(node, "OFF001", "eval is forbidden")

        diagnostics = cubie.CstLinter([ForbidEval()]).check("eval('1')")
        assert len(diagnostics) == 1 and diagnostics[0].rule_id == "OFF001"
    elif feature in {"pylint", "mypy", "linter-aggregation"}:
        backends = {
            "pylint": [cubie.Pylint()],
            "mypy": [cubie.MyPy()],
            "linter-aggregation": [cubie.Pylint(), cubie.MyPy()],
        }[feature]
        diagnostics = cubie.AstLinter(*backends).check("value: int = 'wrong'\n")
        assert diagnostics
        if feature != "pylint":
            assert any(d.rule_id == "assignment" for d in diagnostics)
        if feature != "mypy":
            assert any(d.linter_name == "Pylint" for d in diagnostics)
    elif feature == "linter-discovery":
        project = Path("sample")
        (project / ".venv").mkdir(parents=True)
        (project / "clean.py").write_text("value: int = 1\n", encoding="utf-8")
        (project / ".venv" / "ignored.py").write_text(
            "value: int = 'wrong'\n", encoding="utf-8",
        )
        assert cubie.AstLinter(cubie.MyPy()).check(project) == []
    elif feature.startswith("pyvenv-"):
        # Prove the required codecs are already installed before testing reuse.
        subprocess.run(
            [str(Path(base) / "bin" / "python"), "-c",
             "import msgspec, cloudpickle"],
            check=True,
        )
        codecs = {
            "pyvenv-default": None,
            "pyvenv-pickle": cubie.PickleCodec(),
            "pyvenv-msgspec": cubie.MSGspecCodec(),
            "pyvenv-cloudpickle": cubie.CloudpickleCodec(),
        }
        arena = cubie.PyVenv(env_path=base, codec=codecs[feature])
        EBT(target="builtins:sum", arena=arena,
            pre=WorldState(args=([1, 2, 3],)),
            post=WorldState(returns=6)).run()
        assert arena.workspace_path is None
    elif feature.startswith("builder-reuse"):
        from cubie.arenas.pyvenv import ArenaBuilder

        builder = ArenaBuilder(base)
        if feature == "builder-reuse-packages":
            builder.with_packages(["msgspec", "cloudpickle"])
        assert builder.build().env_path == Path(base)
    elif feature == "virtualization-unavailable":
        import importlib.util

        for name in ("DockerArena", "VmArena"):
            assert name not in cubie.__all__
            assert not hasattr(cubie, name)
        for module in ("dockerarena", "vmarena", "vm"):
            assert importlib.util.find_spec("cubie.arenas." + module) is None
    else:
        raise AssertionError(f"Unknown offline scenario: {feature}")


@pytest.mark.parametrize("probe", [
    "import subprocess; subprocess.run(['uv', 'pip', 'install', 'msgspec'])",
    "import subprocess, sys; subprocess.run([sys.executable, '-m', 'pip', 'install', 'msgspec'])",
    "import socket; socket.getaddrinfo('example.invalid', 443)",
    "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM)",
    "import socket; socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)",
    (
        "import subprocess, sys; subprocess.run([sys.executable, '-c', "
        "\"import socket; socket.getaddrinfo('example.invalid', 443)\"])"
    ),
], ids=["uv", "pip", "dns", "tcp", "udp-ipv6", "python-child"])
def test_offline_guard_detects_forbidden_operations(
    probe, prepared_environment, tmp_path,
):
    """Verify the harness itself, including propagation to child interpreters."""
    process, violations = guarded_run(prepared_environment, tmp_path, probe)
    assert violations, f"Guard missed probe: {probe}\n{process.stderr}"
    assert "OFFLINE CONTRACT" in process.stderr
