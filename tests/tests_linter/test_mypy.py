import pytest
from pathlib import Path
from qb_cubie import PyVenv, EBT, WorldState, AstLinter, MyPy, CloudpickleCodec

# --- 1. In-Memory String Parsing ---

def test_mypy_in_memory_type_error():
    """
    Szenario: LLM-Code mit einem offensichtlichen Typ-Fehler wird als String übergeben.
    Erwartung: MyPy parst den String via '-c', und unser Regex extrahiert
    die Koordinaten und den spezifischen Fehlercode (z. B. 'operator' oder 'assignment').
    """
    bad_code = """
def calculate_sum(a: int, b: int) -> int:
    return a + "b"  # TypeError: int + str
"""
    def validate_diagnostics(diagnostics: list) -> bool:
        if len(diagnostics) != 1:
            return False
        d = diagnostics[0]
        return d.file_path == "<string>" and d.severity == "error" and d.line == 3
    EBT(
        target=AstLinter(MyPy()).check,
        arena=PyVenv(codec=CloudpickleCodec()),
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=validate_diagnostics)
    ).run()


# --- 2. Cross-Module Dependency (Projektweite Inferenz) ---

@pytest.fixture
def cross_module_fs(tmp_path: Path) -> Path:
    """Fixture: Zwei Dateien, bei denen die eine den falschen Typ aus der anderen importiert."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "math_utils.py").write_text(
        "def get_prefix() -> str:\n    return 'ID_'\n",
        encoding="utf-8"
    )
    (src / "main.py").write_text(
        "from math_utils import get_prefix\nuser_id: int = get_prefix()\n",
        encoding="utf-8"
    )
    return tmp_path


def test_mypy_cross_module_inference(cross_module_fs: Path):
    """
    Szenario: MyPy scannt ein Verzeichnis.
    Erwartung: MyPy versteht, dass `get_prefix()` einen `str` zurückgibt 
    und meldet einen Fehler, weil `user_id` als `int` deklariert ist.
    """
    def validate_cross_module(diagnostics: list) -> bool:
        if not diagnostics:
            return False
        d = diagnostics[0]
        return "main.py" in d.file_path and d.rule_id == "assignment"
    EBT(
        target=AstLinter(MyPy()).check,
        arena=PyVenv(codec=CloudpickleCodec()),
        pre=WorldState(
            kwargs={"target": Path("src")},
            fs={
                "src/math_utils.py": str(cross_module_fs / "src" / "math_utils.py"),
                "src/main.py": str(cross_module_fs / "src" / "main.py")
            }
        ),
        post=WorldState(returns=validate_cross_module)
    ).run()


# --- 3. Ignore-Mechanismen (.venv Exclusion) ---

@pytest.fixture
def mypy_venv_fs(tmp_path: Path) -> Path:
    """Fixture: Ein Workspace mit defekten Typen in Cache-Ordnern."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "bad_types.py").write_text("x: int = ['list']\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "clean.py").write_text("y: float = 1.0\n", encoding="utf-8")
    return tmp_path


def test_mypy_ignores_venv_directory(mypy_venv_fs: Path):
    """
    Szenario: AstLinter injiziert DEFAULT_EXCLUDES.
    Erwartung: Die Methode `_build_command` in MyPy wandelt '.venv' 
    korrekt in das Flag `--exclude (?i).venv` um. Es dürfen 0 Fehler gemeldet werden.
    """
    EBT(
        target=AstLinter(MyPy()).check,
        arena=PyVenv(codec=CloudpickleCodec()),
        pre=WorldState(
            kwargs={"target": Path(".")},  # Scannt Root, inklusive .venv
            fs={
                ".venv/bad_types.py": str(mypy_venv_fs / ".venv" / "bad_types.py"),
                "src/clean.py": str(mypy_venv_fs / "src" / "clean.py")
            }
        ),
        post=WorldState(returns=[])  # Leere Liste bestätigt, dass .venv ignoriert wurde
    ).run()
