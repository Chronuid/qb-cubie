import pytest, sys
from pathlib import Path

import cubie.arenas.pyvenv
from cubie.linter import AstLinter, ruff, pylint
from cubie.protocols import WorldState
from cubie.ebt import EBT
from cubie import TempFS, PyVenv

def test_astlinter_clean_memory_string():
    EBT(
        target=AstLinter(linter=[ruff()]).check,
        pre=WorldState(kwargs={"target": "x = 1\ny = 2\nprint(x + y)\n"}),
        post=WorldState(returns=[]) # Erwartung: Keine Diagnostics
    ).run()

def _contains_errors_from_both(diagnostics: list) -> bool:
    has_ruff = any(d.linter_name == "Ruff" for d in diagnostics)
    has_pylint = any(d.linter_name == "Pylint" for d in diagnostics)
    return has_ruff and has_pylint and len(diagnostics) >= 2

def test_astlinter_aggregation_with_predicates():
    bad_code = "import sys\neval('1+1')\n"
    EBT(
        target=AstLinter(linter=[ruff(), pylint()]).check,
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=_contains_errors_from_both) # Dynamische Auswertung via Prädikat
    ).run()


@pytest.fixture
def lint_host_fs(tmp_path: Path) -> Path:
    """
    Fixture-Builder: Baut die benötigten Host-Dateien vorab auf
    und übergibt den Pfad an die Tests.
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
    EBT(
        target=AstLinter(linter=[ruff()]).check,
        arena=TempFS(),  # Aufruf ohne String-Argument umgeht den mkdir-Bug
        pre=WorldState(
            kwargs={"target": Path("src")},
            fs={
                # Mappt den virtuellen Arena-Pfad auf den dynamisch erzeugten Host-Pfad
                "src/bad_module.py": str(lint_host_fs / "bad_module.py")
            }
        ),
        post=WorldState(
            # Erwartung: Linter findet Regelverstöße in der isolierten Arena
            returns=lambda diag: isinstance(diag, list) and len(diag) > 0
        )
    ).run()


def test_astlinter_universal_clean_inputs(lint_host_fs: Path):
    EBT(
        target=AstLinter(linter=[ruff()]).check,
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
        post=WorldState(returns=[]),  # Alle müssen zwingend fehlerfrei durchlaufen
        tags=["universal"]
    ).run()


# Absolute Pfade zu den geschmuggelten Tools (relativ zum Projekt-Root)
# resolve() macht die Pfade absolut, was Subprozesse robuster macht
SMUGGLED_RUFF = Path("src/cubie/linters/ruff-x86_64-unknown-linux-gnu/ruff").resolve()

# Bei Pylint via --target liegt das ausführbare Skript im 'bin'-Ordner (bzw. 'Scripts' unter Windows)
SMUGGLED_PYLINT_SCRIPT = Path("src/cubie/linters/pylint_tool/bin/pylint").resolve()


def test_smuggled_ruff_payload():
    """Prüft, ob das direkt aufgerufene Ruff-Binary funktioniert."""
    # Der Linter muss existieren, sonst ist der Payload nicht da
    assert SMUGGLED_RUFF.exists(), "Geschmuggeltes Ruff-Binary fehlt!"

    EBT(
        # Wir übergeben den absoluten Pfad als String
        target=AstLinter(linter=[ruff(executable=str(SMUGGLED_RUFF))]).check,
        pre=WorldState(kwargs={"target": "x = 1\n"}),
        post=WorldState(returns=[])  # Fehlerfreier Code = leere Liste
    ).run()


def test_smuggled_pylint_payload():
    """
    Prüft Pylint. Da es als Modul geschmuggelt wurde, rufen wir es
    über den aktuellen sys.executable auf, um Berechtigungsprobleme (chmod +x) zu umgehen.
    """
    assert SMUGGLED_PYLINT_SCRIPT.exists(), "Geschmuggeltes Pylint-Skript fehlt!"
    exe_cmd = [sys.executable, str(SMUGGLED_PYLINT_SCRIPT)]
    EBT(
        target=AstLinter(linter=[pylint(executable=exe_cmd)]).check,
        pre=WorldState(kwargs={"target": "x = 1\n"}),
        post=WorldState(
            # Pylint meckert hier z.B. über "missing-module-docstring" (C0114)
            returns=lambda diagnostics: len(diagnostics) > 0
        )
    ).run()


def test_executable_override_is_strict():
    """
    Beweist, dass die Parameter-Übergabe WIRKLICH den Standard-Fallback blockiert.
    Wenn wir einen Fake-Pfad übergeben, MUSS der Subprozess mit einem
    FileNotFoundError abstürzen, anstatt heimlich das System-Ruff zu nutzen.
    """
    fake_path = "/absoluter/fake/pfad/zu/ruff_nirvana"
    with pytest.raises(FileNotFoundError):
        linter = AstLinter(linter=[ruff(executable=fake_path)])
        linter.check("x = 1\n")




# Zentraler Pfad für die isolierte Test-Umgebung
ARENA_PATH = "tests/.arenas/linter_env"


@pytest.fixture(scope="module", autouse=True)
def setup_linter_arena():
    """
    Globale Provisionierung der Base-Arena (Idempotent).
    Baut das Environment mit den nötigen Paketen auf, bevor die Tests starten[cite: 3].
    """
    cubie.arenas.pyvenv.ArenaBuilder(ARENA_PATH).with_packages(["ruff", "pylint"]).build()


# --- 1. Markdown-Artefakte (Soll fehlschlagen) ---

def test_astlinter_markdown_artifacts():
    """
    Szenario: Ein LLM-Agent liefert Code in Markdown-Blöcken zurück.
    Erwartung: Da wir noch keinen Markdown-Stripper integriert haben, wird
    Ruff die Backticks als SyntaxError (E999) interpretieren.
    Der Test WIRD (und soll) fehlschlagen, da wir eine leere Fehlerliste fordern.
    """
    llm_output = "Hier ist die Lösung:\n```python\na = 42\nb = 12\n```\n"

    EBT(
        target=AstLinter(linter=[ruff()]).check,
        arena=PyVenv(ARENA_PATH),
        pre=WorldState(kwargs={"target": llm_output}),
        post=WorldState(
            returns=[]  # Fordert 0 Fehler -> Schlägt fehl, solange der Stripper fehlt!
        )
    ).run()


# --- 2. Cross-Module Dependency Tracking ---

@pytest.fixture
def cross_module_fs(tmp_path: Path) -> Path:
    """Fixture-Builder für verschränkte Python-Module."""
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
    Szenario: Pylint scannt einen Ordner und muss Importe projektweit auflösen.
    Erwartung: Pylint wirft keinen 'import-error' (E0401), da die Arena
    den virtuellen Workspace für den isolierten Subprozess korrekt bereitstellt.
    """
    EBT(
        target=AstLinter(linter=[pylint()]).check,
        arena=PyVenv(ARENA_PATH),
        pre=WorldState(
            kwargs={"target": Path("src")},
            fs={
                "src/main.py": str(cross_module_fs / "src" / "main.py"),
                "src/utils/__init__.py": str(cross_module_fs / "src" / "utils" / "__init__.py"),
                "src/utils/math.py": str(cross_module_fs / "src" / "utils" / "math.py")
            }
        ),
        post=WorldState(
            # Pylint muss die Abhängigkeiten in der PyVenv-Arena fehlerfrei auflösen können
            returns=[]
        )
    ).run()


# --- 3. Ignorierte Pfade (.venv) ---

@pytest.fixture
def venv_ignored_fs(tmp_path: Path) -> Path:
    """Fixture-Builder für einen Workspace mit verbotenen Cache-Ordnern."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    # Krasse Syntaxfehler, die zwingend ignoriert werden müssen
    (venv / "bad_cache.py").write_text("def def def invalid_syntax!!!\n", encoding="utf-8")

    src = tmp_path / "src"
    src.mkdir()
    (src / "clean.py").write_text("x = 1\n", encoding="utf-8")

    return tmp_path


def test_astlinter_ignores_venv_directory(venv_ignored_fs: Path):
    """
    Szenario: Der Linter wird auf das Root-Verzeichnis eines Projekts angesetzt.
    Erwartung: Standard-Ausschluss-Ordner wie `.venv/` werden von Ruff
    ignoriert, selbst wenn sie syntaktisch völlig defekten Code enthalten.
    """
    EBT(
        target=AstLinter(linter=[ruff()]).check,
        arena=PyVenv(ARENA_PATH),
        pre=WorldState(
            kwargs={"target": Path(".")},  # Scannt den gesamten Workspace in der Arena
            fs={
                ".venv/bad_cache.py": str(venv_ignored_fs / ".venv" / "bad_cache.py"),
                "src/clean.py": str(venv_ignored_fs / "src" / "clean.py")
            }
        ),
        post=WorldState(
            returns=[]  # Es dürfen absolut keine Fehler aus dem .venv aufschlagen
        )
    ).run()