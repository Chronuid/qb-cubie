import re
from pathlib import Path
from typing import Any

from qb_cubie import CloudpickleCodec, EBT, ExceptionExpectation, TempFS, WorldState
from qb_cubie.arenas.pyvenv import ArenaBuilder
from qb_cubie.services import CUBIE_DOC_STYLE, DocEnsurance


def _run_with_arena(
    doc: str, arena: Any, pre_state: WorldState | None = None
) -> dict[str, Any]:
    """Executes DocEnsurance with a custom arena and projects the report for EBT."""
    report = DocEnsurance(
        target=doc, pattern=CUBIE_DOC_STYLE, arena=arena, pre_state=pre_state, reporter=None
    ).run()
    return {
        "passed": report.passed,
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [(d.rule_id, d.line, d.message) for d in report.diagnostics],
    }


# ======================================================================================================================
# SZENARIO 1: PRE-STATE HYDRATION & ROLLBACK-ISOLATION ZWISCHEN SESSIONS (TEMPFS)
# ======================================================================================================================
def _hydrated_fs_scenario(leak_assumption: bool) -> dict[str, Any]:
    """Hydrates a seed file via pre_state and runs two separate sessions against it."""
    seed = Path("seed_config.txt")
    seed.write_text("v1", encoding="utf-8")
    expected_second = "v1-mutated" if leak_assumption else "v1"
    doc = (
        "Session A liest die hydratisierte Datei und mutiert sie im Workspace.\n\n"
        "```python session=alpha\n"
        "from pathlib import Path\n"
        "p = Path('config.txt')\n"
        "p.write_text(p.read_text(encoding='utf-8') + '-mutated', encoding='utf-8')\n"
        "print(p.read_text(encoding='utf-8'))\n"
        "```\n\n<details>\n<summary>Ergebnis</summary>\n\n```text\nv1-mutated\n```\n</details>\n\n"
        "Session B läuft in einer frischen Arena und muss wieder das Original sehen.\n\n"
        "```python session=beta\n"
        "from pathlib import Path\n"
        "print(Path('config.txt').read_text(encoding='utf-8'))\n"
        f"```\n\n<details>\n<summary>Ergebnis</summary>\n\n```text\n{expected_second}\n```\n</details>"
    )
    pre = WorldState(fs={"config.txt": str(seed.resolve())})
    return _run_with_arena(doc, arena=TempFS(), pre_state=pre)


def test_ebt_arena_pre_state_rollback_and_leak_alarm() -> None:
    """Verifies that pre_state files reset between sessions and false leak assumptions trigger DOC-OUT."""
    EBT(
        target=_hydrated_fs_scenario,
        arena=TempFS(),
        pre=WorldState(args=(False,)),
        post=WorldState(returns={"passed": True, "outputs": [["v1-mutated"], ["v1"]], "diagnostics": []}),
    ).run()
    EBT(
        target=_hydrated_fs_scenario,
        arena=TempFS(),
        pre=WorldState(args=(True,)),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [["v1-mutated"], ["v1"]],
                "diagnostics": [("DOC-OUT", int, re.compile(r".*expected 'v1-mutated', got 'v1'"))],
            }
        ),
    ).run()


# ======================================================================================================================
# SZENARIO 2: PYVENV, MSGSPEC-CODEC & DECONTAMS-PHANTOM-ALARM
# ======================================================================================================================
def _pyvenv_decontam_scenario(declare_raises: bool) -> dict[str, Any]:
    """Runs DocEnsurance inside a PyVenv arena with a decontaminated stdlib module."""
    fence = "```python raises=TypeError\n" if declare_raises else "```python\n"
    doc = (
        "Prüft das Verhalten der Dokumentation, wenn ein gesperrtes Modul aufgerufen wird.\n\n"
        f"{fence}"
        "import statistics\n"
        "print(statistics.mean([1, 2, 3]))\n"
        "```\n\n<details>\n<summary>Ergebnis</summary>\n\n"
        "```text\nTypeError: PhantomObject 'statistics.mean' cannot be called; install the real dependency.\n```\n</details>"
    )
    arena = ArenaBuilder(".venv_doc_test").build(codec=CloudpickleCodec())
    arena._decontams = ["statistics"]
    return _run_with_arena(doc, arena=arena)


def test_ebt_pyvenv_phantom_hook_alarm_and_catch() -> None:
    """Verifies that calling a decontaminated module in PyVenv triggers DOC-EXEC unless raises=TypeError is set."""
    EBT(
        target=_pyvenv_decontam_scenario,
        arena=TempFS(),
        pre=WorldState(args=(False,)),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [[""]],
                "diagnostics": [("DOC-EXEC", int, re.compile(r".*PhantomObject 'statistics\.mean'"))],
            }
        ),
    ).run()
    EBT(
        target=_pyvenv_decontam_scenario,
        arena=TempFS(),
        pre=WorldState(args=(True,)),
        post=WorldState(
            returns={"passed": True, "outputs": [[re.compile(r"^TypeError: PhantomObject")]], "diagnostics": []}
        ),
    ).run()


# ======================================================================================================================
# SZENARIO 3: DOGFOODING / ARENA-IN-ARENA (EBT-VERTRAG INNERHALB DER DOKU SCHLÄGT FEHL)
# ======================================================================================================================
def test_ebt_nested_ebt_failure_inside_documentation_triggers_alarm() -> None:
    """Verifies that a failing EBT contract documented inside a guide triggers a DOC-EXEC alarm."""
    broken_ebt_guide = (
        "Dieses Doku-Beispiel zeigt einen EBT-Lauf, dessen Post-State im Guide veraltet ist.\n\n"
        "```python\n"
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=abs, pre=WorldState(args=(-5,)), post=WorldState(returns=999)).run()\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
    )
    EBT(
        target=_run_with_arena,
        pre=WorldState(args=(broken_ebt_guide, TempFS())),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [[""]],
                "diagnostics": [("DOC-EXEC", int, re.compile(r"^Unhandled AssertionError: EBT-Assert failed"))],
            }
        ),
    ).run()


# ======================================================================================================================
# SZENARIO 4: KASKADIERENDER SESSION-BRUCH + KOMBINIERTE STRUKTUR- & LAUFZEIT-ALARME
# ======================================================================================================================
def test_ebt_cascading_session_failure_and_multi_diagnostics() -> None:
    """Verifies that structural errors and cascading session crashes are all reported with exact lines."""
    complex_broken_doc = (
        "Kurz.\n\n"
        "```python\nprint('unexplained')\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nunexplained\n```\n</details>\n\n"
        "Schritt 1 der Session initialisiert den Basiswert erfolgreich.\n\n"
        "```python session=cascade\nbase = 10\nprint(base)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>\n\n"
        "Schritt 2 crasht mitten im Block, bevor `derived` zugewiesen werden kann.\n\n"
        "```python session=cascade\n_ = 1 / 0\nderived = base * 2\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n20\n```\n</details>\n\n"
        "Schritt 3 verlässt sich auf `derived` und muss nun mit NameError als Folgefehler scheitern.\n\n"
        "```python session=cascade\nprint(derived)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n20\n```\n</details>"
    )
    EBT(
        target=_run_with_arena,
        pre=WorldState(args=(complex_broken_doc, TempFS())),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [["10", "", ""]],
                "diagnostics": [
                    ("DOC-PRE", 3, re.compile(r".*explanation")),
                    ("DOC-EXEC", int, re.compile(r"^Unhandled ZeroDivisionError")),
                    ("DOC-EXEC", int, re.compile(r"^Unhandled NameError: name 'derived' is not defined")),
                ],
            }
        ),
    ).run()


# ======================================================================================================================
# SZENARIO 5: HARTE POSIX-ARENA-LIMITS (ENDLOSSCHLEIFE & OUTPUT-FLOODING IN DEN DOCS)
# ======================================================================================================================
def test_ebt_arena_timeout_and_output_budget_alarms() -> None:
    """Verifies that infinite loops or output floods in doc snippets are killed by POSIX arena limits."""
    infinite_loop_doc = (
        "Dieses Snippet hängt versehentlich in einer Endlosschleife fest.\n\n"
        "```python\nwhile True:\n    pass\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
    )
    flood_doc = (
        "Dieses Snippet flutet stdout über das konfigurierte Arena-Budget hinaus.\n\n"
        "```python\nimport os\nos.write(1, b'x' * 4096)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
    )
    EBT(
        target=_run_with_arena,
        pre=WorldState(args=(infinite_loop_doc, TempFS(timeout=0.15))),
        post=WorldState(raises=ExceptionExpectation(TimeoutError, match=r"timed out")),
    ).run()
    EBT(
        target=_run_with_arena,
        pre=WorldState(args=(flood_doc, TempFS(max_output_bytes=256))),
        post=WorldState(raises=ExceptionExpectation(RuntimeError, match=r"output limit exceeded")),
    ).run()