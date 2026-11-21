"""Distribution tests copied into an empty directory by scripts/check_wheel.py.

The filename deliberately avoids normal repository pytest discovery: these
checks must run against an installed wheel, without tests/conftest.py.
"""

import importlib
import importlib.metadata
import json
import os
import pkgutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest

import qb_cubie
from qb_cubie import EBT, TempFS, WorldState
from qb_cubie.core.protocols import ReviewData
from qb_cubie.core.rbt import RBT


def test_imports_and_distribution():
    assert sys.prefix != sys.base_prefix
    package = Path(qb_cubie.__file__).resolve()
    assert package.is_relative_to(Path(sys.prefix).resolve())
    distribution = importlib.metadata.distribution("qb-cubie")
    assert distribution.metadata["Name"] == "qb-cubie"
    assert distribution.metadata["License-Expression"] == "MIT"
    assert distribution.metadata["Author"] == "Dominick Wirzba"
    assert distribution.metadata.get_all("License-File") == ["LICENSE"]
    assert "Copyright (c) 2026 Dominick Wirzba" in distribution.read_text("licenses/LICENSE")
    assert importlib.util.find_spec("cubie") is None
    assert package == Path(distribution.locate_file("qb_cubie/__init__.py")).resolve()
    direct_url = json.loads(distribution.read_text("direct_url.json"))
    assert direct_url["url"].endswith(".whl")
    assert not direct_url.get("dir_info", {}).get("editable", False)
    assert all(hasattr(qb_cubie, name) for name in qb_cubie.__all__)
    for module in pkgutil.walk_packages(qb_cubie.__path__, "qb_cubie."):
        importlib.import_module(module.name)
    assert not (package.parent / "arenas/arena_envs").exists()
    assert importlib.util.find_spec("qb_cubie.core.arenas.arena_envs") is None
    assert not qb_cubie.PyVenv().env_path.resolve().is_relative_to(package.parent.resolve())


def test_ebt_accepts_matching_result():
    trace = EBT(target=sum, pre=WorldState(args=([1, 2, 3],)),
                post=WorldState(returns=6)).run()
    assert trace.evaluation is True


def test_ebt_rejects_wrong_result():
    with pytest.raises(AssertionError, match="EBT-Assert failed"):
        EBT(target=sum, pre=WorldState(args=([1, 2, 3],)),
            post=WorldState(returns=7)).run()


@pytest.mark.parametrize("accepted", [True, False])
def test_rbt_with_explicit_reviewer(accepted):
    class Reviewer:
        def review(self, target, check):
            return ReviewData(passed=accepted, report={"text": "wheel review"})

    review = RBT(target="example.py", check="Review", reviewer=Reviewer())
    if accepted:
        review.run()
    else:
        with pytest.raises(AssertionError, match="wheel review"):
            review.run()


def test_tempfs_runner_and_files(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("wheel", encoding="utf-8")

    def transform():
        text = Path("input.txt").read_text(encoding="utf-8").upper()
        Path("output.txt").write_text(text, encoding="utf-8")
        return text

    arena = TempFS()
    trace = EBT(
        target=transform, arena=arena,
        pre=WorldState(fs={"input.txt": str(source)}),
        post=WorldState(returns="WHEEL", fs={
            "output.txt": lambda path: path.read_text(encoding="utf-8") == "WHEEL",
        }),
    ).run()
    assert trace.evaluation is True
    assert arena.workspace_path is None
    assert source.read_text(encoding="utf-8") == "wheel"


def test_pyvenv_runner_and_packaged_phantom_hook(tmp_path, monkeypatch):
    base = tmp_path / "base"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(base)
    monkeypatch.setenv("QB_CUBIE_DEFAULT_ARENA", str(base))
    arena = qb_cubie.PyVenv(codec=qb_cubie.PickleCodec())
    assert arena.env_path == base
    trace = EBT(target="builtins:sum", arena=arena,
                pre=WorldState(args=([1, 2, 3],)),
                post=WorldState(returns=6)).run()
    assert trace.evaluation is True
    assert arena.workspace_path is None


def test_linter_runtime_dependencies():
    if os.environ["QB_CUBIE_WHEEL_PROFILE"] == "core":
        for name in ("libcst", "mypy", "pylint"):
            assert importlib.util.find_spec(name) is None
        with pytest.raises(RuntimeError, match="qb-cubie\\[linters\\]"):
            qb_cubie.CstLinter([])
        with pytest.raises(RuntimeError, match="qb-cubie\\[linters\\]"):
            qb_cubie.MyPy().check("value: int = 'wrong'\n")
        return
    for name in ("libcst", "mypy", "pylint"):
        assert importlib.util.find_spec(name) is not None
    diagnostics = qb_cubie.AstLinter(qb_cubie.MyPy()).check("value: int = 'wrong'\n")
    assert any(diagnostic.rule_id == "assignment" for diagnostic in diagnostics)
    assert qb_cubie.CstLinter([]).check("value = 1\n") == []
    diagnostics = qb_cubie.AstLinter(qb_cubie.Pylint()).check("print(undefined_wheel_name)\n")
    assert any(diagnostic.rule_id == "E0602" for diagnostic in diagnostics)


@pytest.mark.parametrize("invalid", [True, False], ids=["assignment-error", "clean-file"])
def test_mypy_with_native_absolute_file_path(tmp_path, invalid):
    source = (tmp_path / "absolute path with spaces.py").resolve()
    source.write_text("value: int = " + ("'wrong'" if invalid else "42") + "\n", encoding="utf-8")
    case = EBT(target=qb_cubie.MyPy().check, pre=WorldState(args=(source,)),
               post=WorldState(returns=lambda diagnostics: (
                   len(diagnostics) == 1 and diagnostics[0].rule_id == "assignment"
                   and diagnostics[0].severity == "error" and diagnostics[0].line == 1
                   and Path(os.path.normcase(os.path.realpath(diagnostics[0].file_path)))
                   == Path(os.path.normcase(os.path.realpath(source)))
               ) if invalid else diagnostics == []))
    if os.environ["QB_CUBIE_WHEEL_PROFILE"] == "core":
        with pytest.raises(RuntimeError, match="qb-cubie\\[linters\\]"):
            case.run()
        assert case.run_trace is None
    else:
        assert case.run().evaluation is True


@pytest.mark.parametrize("missing", ["tkinter", "_tkinter"])
@pytest.mark.parametrize("feature", [
    "guard", "imports", "ebt", "tempfs", "headless", "gui-unavailable",
])
def test_installed_core_without_tk(tmp_path, feature, missing):
    process = subprocess.run(
        [sys.executable, "-I", str(Path(__file__).with_name("tk_contract.py")), feature, missing],
        cwd=tmp_path, capture_output=True, text=True, timeout=20, check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_doc_ensurance_installed_service(tmp_path):
    from qb_cubie.core.services import CUBIE_DOC_STYLE, DocEnsurance

    doc = tmp_path / "GUIDE.md"
    doc.write_text(
        "Diese Erklaerung beschreibt ein kleines installiertes Beispiel.\n\n"
        "```python\nprint(21 * 2)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>\n",
        encoding="utf-8",
    )
    report = DocEnsurance(target=doc, pattern=CUBIE_DOC_STYLE, reporter=None, timeout=2.0).run()
    assert report.passed is True
    assert report.sessions[0].actual_outputs == ("42",)


def test_docframe_cli_installed_entrypoint(tmp_path):
    project = tmp_path / "repo"
    (project / "docs" / ".assets").mkdir(parents=True)
    (project / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (project / "docs" / ".assets" / "cubie-logo-written.png").write_bytes(b"png")
    (project / "docs" / ".assets" / "cubie-small.png").write_bytes(b"png")
    readme = project / "README.md"
    readme.write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
        'Body\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    command = Path(sys.executable).parent / ("qb-cubie.exe" if os.name == "nt" else "qb-cubie")
    assert command.is_file(), "Installed qb-cubie console script is missing"
    result = subprocess.run(
        [str(command), "docframe", "update", str(project), "--format", "json"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["updated_files"] == ["README.md"]
