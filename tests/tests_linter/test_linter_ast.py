import pytest, sys
from pathlib import Path
import cubie.arenas.pyvenv
from cubie.protocols import WorldState
from cubie.ebt import EBT
from cubie import TempFS, PyVenv, AstLinter, Pylint

def test_astlinter_clean_memory_string():
    EBT(
        target=AstLinter(Pylint(disable=["C0114", "C0103"])).check,
        pre=WorldState(kwargs={"target": "x = 1\ny = 2\nprint(x + y)\n"}),
        post=WorldState(returns=[]) # Expectation: No diagnostics
    ).run()

def _contains_errors(diagnostics: list) -> bool:
    has_pylint = any(d.linter_name == "Pylint" for d in diagnostics)
    return has_pylint and len(diagnostics) >= 1

def test_astlinter_aggregation_with_predicates():
    bad_code = "import sys\neval('1+1')\n"
    EBT(
        target=AstLinter(Pylint()).check,
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=_contains_errors)
    ).run()


@pytest.fixture
def lint_host_fs(tmp_path: Path) -> Path:
    """
    Fixture-Builder: Builds the required host files in advance and passes the path to the tests.
    """
    pre_dir = tmp_path / "fixtures" / "pre"
    pre_dir.mkdir(parents=True)
    bad = pre_dir / "bad_module.py"
    bad.write_text("import sys\neval('1+1')\n", encoding="utf-8")
    clean = pre_dir / "clean.py"
    clean.write_text("a = 42\n", encoding="utf-8")
    (pre_dir / "empty_dir").mkdir()
    return pre_dir


def test_astlinter_filesystem_routing(lint_host_fs: Path):
    any_diagnosis = lambda diag: isinstance(diag, list) and len(diag) > 0
    EBT(
        target=AstLinter(Pylint()).check,
        arena=TempFS(),
        pre=WorldState(
            kwargs={"target": Path("src")},
            fs={"src/bad_module.py": str(lint_host_fs / "bad_module.py")}
        ),
        post=WorldState(returns=any_diagnosis)
    ).run()


def test_astlinter_universal_clean_inputs(lint_host_fs: Path):
    EBT(
        target=AstLinter(Pylint(disable=["C0114", "C0103"])).check,
        arena=TempFS(),
        pre=[
            WorldState(kwargs={"target": "a = 42\n"}),  # String Input
            WorldState(
                kwargs={"target": Path("clean.py")},
                fs={"clean.py": str(lint_host_fs / "clean.py")}
            ),
            WorldState(
                kwargs={"target": Path("empty_dir")},
                fs={"empty_dir/": str(lint_host_fs / "empty_dir")}
            )
        ],
        post=WorldState(returns=[])
    ).run()


def test_custom_pylint_executable_command():
    """
    Runs Pylint with an explicit executable command list.
    """
    exe_cmd = [sys.executable, "-m", "pylint"]
    EBT(
        target=AstLinter(Pylint(executable=exe_cmd)).check,
        pre=WorldState(kwargs={"target": "x = 1\n"}),
        post=WorldState(returns=lambda diagnostics: len(diagnostics) > 0)
    ).run()


def test_executable_override_is_strict():
    """
    Prove that passing the parameter *really* blocks the default fallback.
    If we pass a fake path, the subprocess *must* crash with a
    FileNotFoundError instead of silently using the system `ruff`.
    """
    fake_path = "/absoluter/fake/pfad/zu/ruff_nirvana"
    with pytest.raises(FileNotFoundError):
        linter = AstLinter(Pylint(executable=fake_path))
        linter.check("x = 1\n")


ARENA_PATH = "tests/.arenas/linter_env"
@pytest.fixture(scope="module", autouse=True)
def setup_linter_arena(): cubie.arenas.pyvenv.ArenaBuilder(ARENA_PATH).with_packages(["pylint"]).build()


# --- 1. Markdown artifacts (Should fail) ---

def test_astlinter_markdown_artifacts():
    """
    Scenario: An LLM agent returns code in Markdown blocks.
    Expectation: Since we haven't integrated a Markdown stripper yet,
    Ruff will interpret the backticks as a SyntaxError (E999).
    The test WILL (and should) fail, as we require an empty error list.
    """
    llm_output = "Here is the solution: \n```python\na = 42\nb = 12\n```\n"
    EBT(
        target=AstLinter(Pylint(disable=["E0001"])).check,
        arena=PyVenv(ARENA_PATH, codec=cubie.CloudpickleCodec()),
        pre=WorldState(kwargs={"target": llm_output}),
        post=WorldState(returns=[])
    ).run()


# --- 2. Cross-Module Dependency Tracking ---

@pytest.fixture
def cross_module_fs(tmp_path: Path) -> Path:
    """Fixture builder for intertwined Python modules."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("from utils.math import add\nprint(add(1, 2))\n", encoding="utf-8")
    utils = src / "utils"
    utils.mkdir()
    (utils / "__init__.py").touch()
    (utils / "math.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    return tmp_path


def test_astlinter_cross_module_dependency(cross_module_fs: Path):
    """
    Scenario: Pylint scans a folder and needs to resolve imports project-wide.
    Expectation: Pylint does not raise an 'import-error' (E0401), because the Arena
    correctly provides the virtual workspace for the isolated subprocess.
    """
    EBT(
        target=AstLinter(Pylint(disable=["C0114", "C0116"])).check,
        arena=PyVenv(ARENA_PATH, codec=cubie.CloudpickleCodec()),
        pre=WorldState(
            kwargs={"target": Path("src")},
            fs={
                "src/main.py": str(cross_module_fs / "src" / "main.py"),
                "src/utils/__init__.py": str(cross_module_fs / "src" / "utils" / "__init__.py"),
                "src/utils/math.py": str(cross_module_fs / "src" / "utils" / "math.py")
            }
        ),
        post=WorldState(returns=[])
    ).run()


# --- 3. Ignorierte Pfade (.venv) ---

@pytest.fixture
def venv_ignored_fs(tmp_path: Path) -> Path:
    """Fixture builder for a workspace with forbidden cache folders."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "bad_cache.py").write_text("def def def invalid_syntax!!!\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "clean.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def test_astlinter_ignores_venv_directory(venv_ignored_fs: Path):
    """
    Scenario: The linter is run on a project's root directory.
    Expectation: Standard exclusion directories such as `.venv/` are ignored,
    even if they contain syntactically completely broken code.
    """
    EBT(
        target=AstLinter(Pylint(disable=["F0010"])).check,
        arena=PyVenv(ARENA_PATH, codec=cubie.CloudpickleCodec()),
        pre=WorldState(
            kwargs={"target": Path("..")},
            fs={
                ".venv/bad_cache.py": str(venv_ignored_fs / ".venv" / "bad_cache.py"),
                "src/clean.py": str(venv_ignored_fs / "src" / "clean.py")
            }
        ),
        post=WorldState(returns=[])
    ).run()


def test_astlinter_ignores_venv_directory_in_project(venv_ignored_fs: Path):
    """
    Mirror the exclusion check with an explicit project directory.

    Unlike '..', this target avoids PyCharm's empty-module-name resolution
    and keeps arena middleware and unrelated temporary files out of the scan.
    Broken code in .venv must be ignored in both IDE and terminal runs.
    """
    EBT(
        target=AstLinter(Pylint(disable=["C0114", "C0103"])).check,
        arena=PyVenv(ARENA_PATH, codec=cubie.CloudpickleCodec()),
        pre=WorldState(
            kwargs={"target": Path("project")},
            fs={
                "project/.venv/bad_cache.py": str(venv_ignored_fs / ".venv" / "bad_cache.py"),
                "project/src/clean.py": str(venv_ignored_fs / "src" / "clean.py")
            }
        ),
        # A predicate also exposes diagnostics with the current reporter's [] handling.
        post=WorldState(returns=lambda diagnostics: diagnostics == [])
    ).run()
