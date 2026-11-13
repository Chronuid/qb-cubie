import re
from pathlib import Path
from typing import Any

from qb_cubie import (
    EBT,
    WorldState,
    ExceptionExpectation,
    TempFS,
    PytestReporter,
)
from qb_cubie.services.doc_ensurance import (
    CUBIE_DOC_STYLE,
    DocEnsurance,
    ExamplePattern,
    Explanation,
    CodeSnippet,
    CollapsibleResult,
    TaggedScope,
    IsolatedScope,
)


# ---------- Standard-Pattern für die Test-Suite -----------------------------------------------------------------------
CUBIE_PATTERN = ExamplePattern(
    name="cubie-standard",
    pre=[Explanation(min_chars=15)],
    anchor=CodeSnippet(lang="python"),
    post=[CollapsibleResult(summary="Ergebnis")],
)


def run_ensurance(
    markdown_or_path: str | Path,
    pattern: ExamplePattern = CUBIE_PATTERN,
    scope: Any = None,
    reporter: Any = None,
) -> dict[str, Any]:
    """Stateless Test-Adapter: Führt DocEnsurance aus und projiziert den Trace auf ein EBT-Prüf-Dict."""
    service = DocEnsurance(
        target=markdown_or_path,
        pattern=pattern,
        scope=scope or TaggedScope(),
        arena=TempFS(),
        reporter=reporter,
    )
    report = service.run()
    return {
        "passed": report.passed,
        "session_count": len(report.sessions),
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [
            {"rule_id": d.rule_id, "line": d.line, "message": d.message}
            for d in report.diagnostics
        ],
    }


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: POSITIVE INVARIANZ UNTER FREIEM MARKDOWN
# ======================================================================================================================
def test_ebt_valid_single_and_interleaved_markdown():
    """
    Gesetz: Beliebige Markdown-Elemente (Überschriften, Listen, Fließtext) außerhalb der
    direkten Anker-Nachbarschaft (Pre/Post) dürfen weder Fehlalarme auslösen noch die
    Code-Ausführung beeinflussen.
    """
    minimal_valid = (
        "Dies ist eine ausreichend lange Erklärung für das erste Snippet.\n\n"
        "```python\n"
        "print(21 * 2)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
    )

    rich_markdown_between = (
        "# Hauptkapitel\n\n"
        "Einleitender Fließtext, der nichts mit dem Code-Block zu tun hat.\n\n"
        "- Aufzählungspunkt 1\n"
        "- Aufzählungspunkt 2\n\n"
        "Hier folgt nun die eigentliche Erklärung direkt vor dem Anker-Block.\n\n"
        "```python\n"
        "items = ['a', 'b']\n"
        "print(len(items) * 21)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>\n\n"
        "## Fazit\n\n"
        "Weiterer regulärer Text am Ende des Dokuments ohne Code-Beispiele."
    )

    EBT(
        target=run_ensurance,
        pre=[
            WorldState(args=(minimal_valid,)),
            WorldState(args=(rich_markdown_between,)),
        ],
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "outputs": [["42"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_valid_markdown_invariance",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: STRUKTURELLE MUSTER-BRÜCHE AM ANKER (PRE & POST)
# ======================================================================================================================
def test_ebt_structural_pattern_violations():
    """
    Gesetz: Jeder Python-Ankerblock, dem die geforderte Pre-Erklärung oder das
    nachfolgende Post-Ergebnis fehlt, erzeugt eine strukturelle Diagnose mit Zeilenbezug.
    """
    missing_pre_explanation = (
        "```python\n"
        "print('ohne erklärung')\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nohne erklärung\n```\n</details>"
    )

    too_short_pre_explanation = (
        "Zu kurz.\n\n"
        "```python\n"
        "print('kurz')\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nkurz\n```\n</details>"
    )

    missing_post_collapsible = (
        "Eine vollständige Erklärung vor dem Code-Snippet.\n\n"
        "```python\n"
        "print('kein ergebnis-block')\n"
        "```\n\n"
        "Hier folgt statt <details> einfach nur ein normaler Textabsatz."
    )

    EBT(
        target=run_ensurance,
        pre=[
            WorldState(args=(missing_pre_explanation,)),
            WorldState(args=(too_short_pre_explanation,)),
            WorldState(args=(missing_post_collapsible,)),
        ],
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 0,
                "outputs": [],
                "diagnostics": [
                    {
                        "rule_id": re.compile(r"^DOC-(PRE|POST)$"),
                        "line": int,
                        "message": re.compile(r".+"),
                    }
                ],
            }
        ),
        custom_id="doc_structural_violations",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: EXPLIZITES SESSION-TAGGING VS. ISOLATION (RAM & TEMPFS)
# ======================================================================================================================
def test_ebt_explicit_session_state_sharing_and_interleaving():
    """
    Gesetz:
    1. Blöcke mit identischem `session=<id>` teilen sich Variablen, Imports und das
       Dateisystem (CWD in TempFS) über beliebiges Zwischen-Markdown hinweg.
    2. Verschiedene Sessions (`session=a` vs. `session=b`) und ungetaggte Blöcke
       bleiben voneinander isoliert.
    """
    interleaved_sessions_doc = (
        "Startet Session A und schreibt eine Datei in den Arena-Workspace.\n\n"
        "```python session=alpha\n"
        "from pathlib import Path\n"
        "Path('alpha.txt').write_text('state_a', encoding='utf-8')\n"
        "counter = 10\n"
        "print(counter)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>\n\n"
        "### Zwischenkapitel mit ungetaggtem, isoliertem Snippet\n\n"
        "Dieses Snippet hat kein Session-Tag und darf `counter` aus `alpha` nicht kennen.\n\n"
        "```python\n"
        "print('counter' in dir())\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nFalse\n```\n</details>\n\n"
        "### Fortsetzung von Session A\n\n"
        "Greift wieder auf `counter` und die Datei `alpha.txt` aus Schritt 1 zu.\n\n"
        "```python session=alpha\n"
        "counter += 5\n"
        "print(f\"{counter}:{Path('alpha.txt').read_text(encoding='utf-8')}\")\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n15:state_a\n```\n</details>"
    )

    EBT(
        target=run_ensurance,
        pre=WorldState(args=(interleaved_sessions_doc,)),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 2,  # Session 1: 'alpha' (2 Schritte), Session 2: isoliert (1 Schritt)
                "outputs": [["10", "15:state_a"], ["False"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_session_tagging_and_isolation",
    ).run()

    EBT(
        target=run_ensurance,
        pre=WorldState(args=(interleaved_sessions_doc,), kwargs={"scope": IsolatedScope()}),
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 3,
                "outputs": [["10"], ["False"], [""]],
                "diagnostics": [
                    {
                        "rule_id": "DOC-EXEC",
                        "line": int,
                        "message": re.compile(r".*NameError"),
                    }
                ],
            }
        ),
        custom_id="doc_isolated_scope_ignores_session_tags",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: PROTOKOLL-INJEKTION (CUSTOM DEVELOPER PATTERN)
# ======================================================================================================================
def test_ebt_custom_developer_pattern_injection():
    """
    Gesetz: Andere Entwickler können ein eigenes Muster (z.B. ohne Erklärung,
    Output als ```text-Block statt <details>) in DocEnsurance einspeisen.
    """
    custom_pattern = ExamplePattern(
        name="minimal-fence-pattern",
        pre=[],
        anchor=CodeSnippet(lang="python"),
        post=[CodeSnippet(lang="text")],
    )

    custom_doc = (
        "# Kurze API-Referenz\n\n"
        "```python\n"
        "print('custom pattern works')\n"
        "```\n\n"
        "```text\n"
        "custom pattern works\n"
        "```"
    )

    EBT(
        target=run_ensurance,
        pre=WorldState(args=(custom_doc, custom_pattern)),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "outputs": [["custom pattern works"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_custom_pattern_injection",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: FUNKTIONALE LAUFZEIT-VERIFIKATION & REPORTER-INTEGRATION
# ======================================================================================================================
def test_ebt_runtime_mismatch_and_exception_detection():
    """
    Gesetz: Weicht der reale stdout vom dokumentierten Ergebnis ab oder wirft das
    Snippet einen unerwarteten Laufzeitfehler, schlägt der Check fehl; mit aktivem
    PytestReporter wird ein AssertionError ausgelöst.
    """
    wrong_output_doc = (
        "Diese Berechnung verspricht 100, liefert aber 99.\n\n"
        "```python\n"
        "print(99)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n100\n```\n</details>"
    )

    crashing_snippet_doc = (
        "Dieses Beispiel wirft zur Laufzeit einen ZeroDivisionError.\n\n"
        "```python\n"
        "print(1 / 0)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n0\n```\n</details>"
    )

    # 5a. Prüfung der strukturierten Diagnose (ohne Reporter-Assert)
    EBT(
        target=run_ensurance,
        pre=[
            WorldState(args=(wrong_output_doc,)),
            WorldState(args=(crashing_snippet_doc,)),
        ],
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 1,
                "outputs": list,
                "diagnostics": [
                    {
                        "rule_id": re.compile(r"^DOC-(OUT|EXEC)$"),
                        "line": int,
                        "message": re.compile(r".+"),
                    }
                ],
            }
        ),
        custom_id="doc_runtime_failures_diagnostics",
    ).run()

    # 5b. Prüfung der PytestReporter-Integration (delegiert via AssertionError)
    EBT(
        target=run_ensurance,
        pre=[
            WorldState(
                args=(wrong_output_doc,),
                kwargs={"reporter": PytestReporter()},
            ),
            WorldState(
                args=(crashing_snippet_doc,),
                kwargs={"reporter": PytestReporter()},
            ),
        ],
        post=WorldState(
            raises=ExceptionExpectation(AssertionError, match=r"DOC-(OUT|EXEC)")
        ),
        custom_id="doc_runtime_failures_pytest_reporter",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: DATEISYSTEM-SCOPES & STATE-GUARDS
# ======================================================================================================================
def test_ebt_state_guards_on_invalid_inputs():
    """
    Gesetz: Ungültige Eingaben (nicht existierende Pfade, falscher Target-Typ, leerer String)
    werden vor dem Start der Arena durch explizite STATE-GUARDs abgefangen.
    """
    EBT(
        target=run_ensurance,
        pre=WorldState(args=(Path("non_existent_guide_12345.md"),)),
        post=WorldState(
            raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")
        ),
        custom_id="doc_state_guards_missing_path",
    ).run()

    EBT(
        target=run_ensurance,
        pre=WorldState(args=(12345,)),  # Weder Markdown-String noch Path
        post=WorldState(
            raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")
        ),
        custom_id="doc_state_guards_invalid_type",
    ).run()

    EBT(
        target=run_ensurance,
        pre=WorldState(args=("   ",)),
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")
        ),
        custom_id="doc_state_guards_empty_markdown",
    ).run()

# ======================================================================================================================
# 7. ÄQUIVALENZKLASSE: DEKLARIERTE NEGATIV-BEISPIELE (raises=<Exception>)
# ======================================================================================================================
def test_ebt_expected_exceptions_in_docs():
    """
    Gesetz:
    1. Mit `raises=<Exc>` getaggte Snippets bestehen, wenn die Exception (oder eine Subklasse)
       geworfen wird und ihre Textrepräsentation dem <details>-Ergebnis entspricht.
    2. Eine aktive Session (`session=alpha`) bleibt nach einer erwarteten Exception intakt.
    3. Bleibt die erwartete Exception aus oder hat sie den falschen Typ, meldet DocEnsurance `DOC-RAISE`.
    """
    valid_raises_in_session = (
        "Schritt 1 legt eine Liste in der Session `alpha` an.\n\n"
        "```python session=alpha\n"
        "values = [10, 20]\n"
        "print(len(values))\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n2\n```\n</details>\n\n"
        "Schritt 2 demonstriert einen erwarteten IndexError in derselben Session.\n\n"
        "```python session=alpha raises=IndexError\n"
        "print(values[99])\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n"
        "```text\nIndexError: list index out of range\n```\n</details>\n\n"
        "Schritt 3 beweist, dass `values` in Session `alpha` weiterhin existiert.\n\n"
        "```python session=alpha\n"
        "values.append(30)\n"
        "print(sum(values))\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n60\n```\n</details>"
    )

    missing_expected_exception = (
        "Dieses Snippet kündigt einen ValueError an, läuft aber fehlerfrei durch.\n\n"
        "```python raises=ValueError\n"
        "print('alles ok')\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nValueError: boom\n```\n</details>"
    )

    wrong_exception_type = (
        "Dieses Snippet kündigt einen TypeError an, wirft aber einen KeyError.\n\n"
        "```python raises=TypeError\n"
        "data = {}\n"
        "print(data['missing'])\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nTypeError: wrong\n```\n</details>"
    )

    # 7a. Positiv-Vertrag: Erwartete Exception + Überleben der Session
    EBT(
        target=run_ensurance,
        pre=WorldState(args=(valid_raises_in_session,)),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "outputs": [
                    [
                        "2",
                        "IndexError: list index out of range",
                        "60",
                    ]
                ],
                "diagnostics": [],
            }
        ),
        custom_id="doc_expected_raises_session_survival",
    ).run()

    # 7b. Negativ-Vertrag: Ausbleibende oder falsche Exception -> DOC-RAISE
    EBT(
        target=run_ensurance,
        pre=[
            WorldState(args=(missing_expected_exception,)),
            WorldState(args=(wrong_exception_type,)),
        ],
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 1,
                "outputs": list,
                "diagnostics": [
                    {
                        "rule_id": "DOC-RAISE",
                        "line": int,
                        "message": re.compile(r"Expected exception"),
                    }
                ],
            }
        ),
        custom_id="doc_expected_raises_violations",
    ).run()


# ======================================================================================================================
# 8. ÄQUIVALENZKLASSE: REKURSIVER VERZEICHNIS-SCAN & DATEI-ISOLATION
# ======================================================================================================================
def run_directory_ensurance() -> dict[str, Any]:
    """Legt im aktuellen CWD (TempFS) zwei Docs und einen ignorierten .venv-Ordner an."""
    docs_dir = Path("docs")
    (docs_dir / "sub").mkdir(parents=True, exist_ok=True)
    (docs_dir / ".venv").mkdir(parents=True, exist_ok=True)

    # Datei 1 definiert x = 10 in session=demo
    (docs_dir / "guide_a.md").write_text(
        "Erklärung in Guide A für Session demo.\n\n"
        "```python session=demo\n"
        "x = 10\n"
        "print(x)\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>",
        encoding="utf-8",
    )

    # Datei 2 nutzt ebenfalls den Namen session=demo, darf x aus guide_a.md aber NICHT sehen
    (docs_dir / "sub" / "guide_b.md").write_text(
        "Erklärung in Guide B mit gleichnamiger Session demo.\n\n"
        "```python session=demo\n"
        "print('x' in dir())\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nFalse\n```\n</details>",
        encoding="utf-8",
    )

    # Datei 3 liegt in .venv (DEFAULT_EXCLUDES) und wäre ein Strukturfehler, muss aber ignoriert werden
    (docs_dir / ".venv" / "broken.md").write_text(
        "```python\nprint('unexplained in venv')\n```",
        encoding="utf-8",
    )

    return run_ensurance(docs_dir)


def test_ebt_directory_crawling_and_cross_file_session_isolation():
    """
    Gesetz: Beim Scannen eines Verzeichnisses werden alle *.md-Dateien außerhalb von
    DEFAULT_EXCLUDES geprüft, wobei gleichnamige Session-Tags (`session=demo`) in
    unterschiedlichen Dateien strikt getrennte Arena-Sessions erhalten.
    """
    EBT(
        target=run_directory_ensurance,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 2,
                "outputs": [["10"], ["False"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_directory_scan_and_file_isolation",
    ).run()


def _doc_snippet(output: str) -> str:
    return (
        "Ausreichend lange Erklärung für den Standard-Lauf.\n\n"
        "```python\n"
        f"print({output!r})\n"
        "```\n\n"
        f"<details>\n<summary>Ergebnis</summary>\n\n```text\n{output}\n```\n</details>"
    )


def run_string_path_ensurance(target: str | Path) -> dict[str, Any]:
    """Hydrates a docs/ folder in CWD and runs DocEnsurance on an explicit string path."""
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "guide.md").write_text(_doc_snippet("42"), encoding="utf-8")
    (Path("README.md")).write_text(_doc_snippet("root"), encoding="utf-8")
    report = DocEnsurance(target=target, pattern=CUBIE_DOC_STYLE, reporter=None).run()
    return {"passed": report.passed, "outputs": [list(s.actual_outputs) for s in report.sessions]}


def run_default_project_ensurance(with_pyproject: bool = False, start_in_subdir: bool = False) -> dict[str, Any]:
    """Hydrates multiple project folders in CWD and runs DocEnsurance with target=None."""
    import os

    root = Path.cwd().resolve()
    if with_pyproject:
        (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "guides").mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text(_doc_snippet("root"), encoding="utf-8")
    (root / "docs" / "guide.md").write_text(_doc_snippet("docs"), encoding="utf-8")
    (root / "guides" / "extra.md").write_text(_doc_snippet("guides"), encoding="utf-8")
    if start_in_subdir:
        os.chdir(root / "docs")
    report = DocEnsurance(target=None, pattern=CUBIE_DOC_STYLE, reporter=None).run()
    return {
        "passed": report.passed,
        "target_is_root": Path(report.target).resolve() == root,
        "outputs": [list(s.actual_outputs) for s in report.sessions],
    }


def test_ebt_default_project_and_string_path_resolution():
    """
    Gesetz: DocEnsurance löst target=None standardmäßig auf das gesamte Projekt-Root
    (alle Ordner inkl. Root-Dateien) auf, während einzeilige Pfad-Strings ('docs',
    'docs/guide.md') gezielt nur das angegebene Dateisystemziel prüfen.
    """
    EBT(
        target=run_string_path_ensurance,
        arena=TempFS(),
        pre=[
            WorldState(args=("docs",)),
            WorldState(args=("docs/guide.md",)),
        ],
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [["42"]],
            }
        ),
        custom_id="doc_string_path_resolution",
    ).run()

    EBT(
        target=run_default_project_ensurance,
        arena=TempFS(),
        pre=[
            WorldState(args=(False, False)),
            WorldState(args=(True, False)),
            WorldState(args=(True, True)),
        ],
        post=WorldState(
            returns={
                "passed": True,
                "target_is_root": True,
                "outputs": [["root"], ["docs"], ["guides"]],
            }
        ),
        custom_id="doc_default_project_all_folders",
    ).run()