<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation

![Cubie](../.assets/cubie-logo-written.png)

Dokumentationen veralten oft genau dann, wenn sich Signaturen, Rückgabewerte oder Exceptions im Code ändern, die Code-Beispiele in den Markdown-Guides aber unbemerkt auf dem alten Stand bleiben. **`DocEnsurance`** aus `qb_cubie.core.services` löst dieses Problem, indem es Markdown-Dokumente sowohl **strukturell** (Layout-Konvention), **statisch** (pluggable Check-Regeln & Linter) als auch **funktional** (echte Ausführung in einer `Arena`) absichert.

---

> [!NOTE]
> 
> **Wichtiger Disclaimer (Garantieumfang & Abgrenzung):**  
> Auch wenn `DocEnsurance` überprüft, ob jedes Code-Beispiel durchläuft und die dokumentierte Ausgabe tatsächlich erzeugt wird, ist dies **noch keine generelle Testabdeckung** und **keine Garantie für die inhaltliche Korrektheit der Informationen** in den Dokumentationen:
> * **Kein Ersatz für systematische Tests:** Ein einzelnes Positiv-Beispiel im Guide beweist nur diesen einen konkreten Aufruf, ersetzt aber keine Äquivalenzklassen-, Randfall- und Negativ-Prüfungen über `EBT`-Verträge in der Test-Suite.
> * **Keine semantische Prüfung des Fließtextes:** `DocEnsurance` prüft, *ob* eine Erklärung vor dem Code-Block existiert und ob definierte Text-Regeln (`ExplanationRule`) eingehalten werden, kann aber nicht bewerten, ob die Aussagen im Text fachlich vollständig oder zutreffend sind.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
>
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ...heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Schnelleinstieg (Minimal-Setup in der Test-Suite)

In der Praxis reicht ein einziger Aufruf in der Test-Suite (wie in `tests/test_styleguide.py`), um das gesamte Projekt abzusichern. Da `DocEnsurance` standardmäßig das Projekt-Root ab `pyproject.toml` scannt und den `PytestReporter` nutzt, werden neben `pattern` und `rules=CUBIE_DOC_RULES` nur noch Verzeichnisse oder Arbeitsdokumente in `excludes` angegeben, die nicht dem Doku-Standard unterliegen:

```python
import pytest
from qb_cubie.core.services import CUBIE_DOC_RULES, CUBIE_DOC_STYLE, DocEnsurance

service = DocEnsurance(
    pattern=CUBIE_DOC_STYLE,
    rules=CUBIE_DOC_RULES,
    excludes=("experiments", "GUTACHTEN.md"),
)


@pytest.mark.slow
def test_docs_code_examples() -> None:
    """Verifies that all documentation code examples follow CUBIE_DOC_STYLE and execute cleanly."""
    service.run()


print(f"Pattern: {service.pattern.name} | Regeln: {[r.rule_id for r in service.rules]}")
```

<details>
<summary>Ergebnis</summary>

```text
Pattern: cubie-doc-style | Regeln: ['DOC-OUT', 'DOC-NO-OUTPUT', 'DOC-HIGH-COMPLEXITY', 'DOC-LARGE-OUTPUT', 'DOC-RAW-TRACEBACK']
```
</details>

---

## 2. API-Quick-Lookup (`DocEnsurance`)

Die Signatur von `DocEnsurance` bündelt Ziel-Auflösung, strukturelles Pattern-Matching, einhängbare Check-Regeln, Ausführungs-Arena und Prozess-Limits in einer flachen Konfiguration:

```text
DocEnsurance(
    target: str | Path | None = None,
    pattern: DocPatternProtocol | None = None,
    scope: DocScopeProtocol | None = None,
    arena: Arena | None = None,
    reporter: Reporter[DocReport] | None = PytestReporter(),
    pre_state: WorldState | None = None,
    excludes: Sequence[str] | None = None,
    rules: Sequence[DocRuleProtocol | Linter | type] | None = None,
    *,
    timeout: float | None = 10.0,
)
```

| Parameter | Standardwert | Funktion & Verhalten |
| :--- | :--- | :--- |
| **`target`** | `None` (Projekt-Root) | Bestimmt die zu prüfende Quelle: `None` scannt ab Projekt-Root (`pyproject.toml` / `CWD`); akzeptiert zudem Ordnerpfade (`"docs"`), Einzeldateien (`"docs/GUIDE.md"`) oder mehrzeilige In-Memory-Markdown-Strings. |
| **`pattern`** | `CUBIE_DOC_STYLE` | Legt das strukturelle Muster um jeden Code-Anker fest (`Explanation` $\to$ `CodeSnippet` $\to$ `CollapsibleResult`). |
| **`scope`** | `TaggedScope()` | Steuert die Arena-Gruppierung: `TaggedScope()` gruppiert Snippets mit identischem `session=<id>` pro Datei und isoliert ungetaggte Snippets jeweils in einer eigenen Arena. |
| **`arena`** | `TempFS(timeout=10.0)` | Ausführungs-Umgebung für jede Session (`TempFS` oder `PyVenv`). Nach jeder Session wird der Workspace vollständig abgeräumt (`teardown`). |
| **`reporter`** | `PytestReporter()` | Konsumiert den erzeugten `DocReport`. `PytestReporter()` gibt für Diagnosen mit `severity="warning"` eine `UserWarning` aus und löst nur bei `severity="error"` einen `AssertionError` aus; `reporter=None` gibt still den `DocReport` zurück. |
| **`pre_state`** | `WorldState()` | Hydratisiert vor jeder Session definierte Dateien oder Ordner in den Arena-Workspace (z. B. `WorldState(fs={"config.ini": "ReadMe.md"})`). |
| **`excludes`** | `DEFAULT_EXCLUDES` | Ergänzt die Standard-Ausschlüsse (`.venv`, `__pycache__`, `.git`) um Ordnernamen (`"experiments"`), Dateinamen (`"GUTACHTEN.md"`) oder relative Teilpfade (`"docs/drafts"`). |
| **`rules`** | `DEFAULT_DOC_RULES` | Registriert zusätzliche oder überschreibende Check-Regeln (`DocRuleProtocol`) und Linter (`CstLinter`, `AstLinter`, `Pylint`, `MyPy`) für Erklärung, Code und Ausgabe. |
| **`timeout`** | `10.0` (Keyword-only) | Maximale Laufzeit (TTL) in Sekunden pro Session auf POSIX-Systemen; verhindert Endlosschleifen oder blockierende `input()`-Aufrufe. `None` deaktiviert das Limit. |

### Wichtige Konfigurations-Details für die Praxis

* **Gezielte Einzel- und Ordnerprüfung (`target` & `excludes`):**
  Nicht existierende Datei- oder Ordnerpfade (auch als String wie `target="docs_typo"`) werden sofort vor dem Arena-Start durch einen `FileNotFoundError`-`STATE-GUARD` abgefangen. Sind in einem Zielverzeichnis durch `excludes` sämtliche `.md`-Dateien ausgeschlossen, greift ein `ValueError`-`STATE-GUARD`.
* **Regeln dynamisch nachregistrieren (`register_rule`):**
  Über die Fluent-Methode `service.register_rule(*rules)` lassen sich beliebige `DocRuleProtocol`-Instanzen, Regel-Klassen oder `Linter` auch nach der Initialisierung einhängen. Regeln mit identischer `rule_id` überschreiben bestehende Standardregeln deterministisch.
* **TTL-Timeout-Vorrang (`timeout` vs. `arena.timeout`):**
  Übergibt man eine unkonfigurierte Arena (z. B. `arena=TempFS()`), übernimmt diese automatisch das `timeout` von `DocEnsurance` (Standard: `10.0s`). Besitzt die übergebene Arena bereits ein explizites Limit (z. B. `arena=TempFS(timeout=0.5)`), hat das spezifische Arena-Limit immer Vorrang vor dem Service-Parameter.
* **Einsatz von `PyVenv` als Arena:**
  Da `PyVenv` standardmäßig den `MSGspecCodec` nutzt (der im isolierten Venv das Modul `qb_cubie` importieren muss), empfiehlt sich für schlanke Test-Venvs ohne vorinstalliertes `qb-cubie` die Initialisierung mit dem `CloudpickleCodec` (`ArenaBuilder(path).build(codec=CloudpickleCodec())`).
* **Programmatische Auswertung über `DocReport` (`reporter=None`):**
  Für eigene Analysen oder gezielte EBT-Tests lässt sich der Reporter deaktivieren, um den zurückgegebenen `DocReport` (`target`, `passed`, `sessions`, `diagnostics`) direkt zu inspizieren.

Das folgende Beispiel prüft einen mehrzeiligen In-Memory-Markdown-String mit einem verkürzten TTL-Timeout von `2.0` Sekunden und wertet den `DocReport` direkt ohne Reporter-Assertion aus:

```python
from qb_cubie.core.services import DocEnsurance

sample_doc = (
    "Eine erklärende Einleitung mit mindestens zwanzig Zeichen.\n\n"
    "```python\n"
    "print('TTL-Check erfolgreich')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\nTTL-Check erfolgreich\n```\n</details>"
)

report = DocEnsurance(target=sample_doc, reporter=None, timeout=2.0).run()
print(f"Passed: {report.passed} | Outputs: {report.sessions[0].actual_outputs}")
```

<details>
<summary>Ergebnis</summary>

```text
Passed: True | Outputs: ('TTL-Check erfolgreich',)
```
</details>

## 3. Grundprinzip: Das Anker-Modell $\{P\}\ S\ \{Q\}$

Analog zum Hoare-Tripel $\{P\}\ S\ \{Q\}$ aus `EBT` betrachtet `DocEnsurance` jedes Code-Beispiel in einer Markdown-Datei als dreiteiligen Vertrag rund um einen **Anker-Block**:

* **Pre-Block ( $P$ – Erklärung):** Vor dem Code-Block muss ein erklärender Textabsatz stehen, der das Beispiel einordnet.
* **Anchor-Block ( $S$ – Code-Snippet):** Ein ausführbarer `python`-Code-Block triggert die Prüfung.
* **Post-Block ( $Q$ – Erwartetes Ergebnis):** Direkt unter dem Code-Block dokumentiert ein aufklappbarer `<details>`-Block die erwartete Konsolenausgabe (`stdout`) oder Fehlermeldung.

Reguläres Markdown außerhalb dieser unmittelbaren Nachbarschaft – wie Kapitelüberschriften, Aufzählungslisten, Architekturskizzen oder weiterführende Absätze – wird vom Scanner automatisch übersprungen.

Die vorkonfigurierte Standard-Konvention `CUBIE_DOC_STYLE` prüft genau dieses Dreier-Muster (Erklärung mit mindestens 20 Zeichen, `python`-Snippet und aufklappbares `<details>`-Ergebnis):

```python
from qb_cubie.core.services import CUBIE_DOC_STYLE

print(
    f"Pattern: {CUBIE_DOC_STYLE.name} | "
    f"Pre-Regeln: {len(CUBIE_DOC_STYLE.pre)} | "
    f"Post-Regeln: {len(CUBIE_DOC_STYLE.post)}"
)
```

<details>
<summary>Ergebnis</summary>

```text
Pattern: cubie-doc-style | Pre-Regeln: 1 | Post-Regeln: 1
```
</details>

## 4. Ziel-Auflösung (`target` & `excludes`) und Einzelprüfung

`DocEnsurance` ist so vorkonfiguriert, dass es ohne Boilerplate-Pfade sofort das gesamte Projekt absichert, sich bei Bedarf aber auch gezielt auf einzelne Dateien oder Strings richten lässt:

* **`target=None` (Standard):** Durchsucht standardmäßig das gesamte Projektverzeichnis rekursiv nach `*.md`-Dateien (unter automatischer Beachtung von `DEFAULT_EXCLUDES` wie `.venv`, `.git` und `__pycache__`).
* **`excludes=(...)`:** Schließt zusätzliche Ordner, Dateien oder relative Teilpfade (wie `"experiments"`, `"docs/drafts"` oder `"GUTACHTEN.md"`) relativ zum Zielverzeichnis vom Scan aus.
* **`target=Path(...)` oder `str`:** Akzeptiert wahlweise ein spezifisches Unterverzeichnis, eine einzelne `.md`-Datei oder einen mehrzeiligen In-Memory-Markdown-String. Nicht existierende Datei- oder Ordnerpfade werden sofort durch einen `FileNotFoundError`-`STATE-GUARD` abgefangen.
* **`reporter=PytestReporter()` (Standard):** Emittiert bei Warnungen (`severity="warning"`) eine `UserWarning` und löst bei Fehlern (`severity="error"`) direkt einen formatierten `AssertionError` für `pytest` aus. Mit `reporter=None` lässt sich das `DocReport`-Ergebnis programmatisch auswerten.

Das folgende Beispiel legt im aktuellen Workspace eine einzelne Markdown-Datei an und wertet deren `DocReport` direkt aus:

```python
from pathlib import Path
from qb_cubie.core.services import CUBIE_DOC_STYLE, DocEnsurance

fence = "```"
markdown_content = (
    "Diese Erklärung beschreibt das folgende Berechnungsbeispiel ausführlich.\n\n"
    f"{fence}python\n"
    "print(21 * 2)\n"
    f"{fence}\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    f"{fence}text\n42\n{fence}\n"
    "</details>"
)

guide_file = Path("sample_guide.md")
guide_file.write_text(markdown_content, encoding="utf-8")

report = DocEnsurance(target=guide_file, pattern=CUBIE_DOC_STYLE, reporter=None).run()
print(f"passed={report.passed}, outputs={report.sessions[0].actual_outputs}")
```

<details>
<summary>Ergebnis</summary>

```text
passed=True, outputs=('42',)
```
</details>

## 5. Fortgeschrittene Markdown-Features

### 5.1 Geteilter Zustand über `session=<id>`

Standardmäßig läuft jedes Code-Snippet komplett isoliert in einer eigenen Arena-Session. Oft möchte man in einem Tutorial jedoch ein Szenario Schritt für Schritt aufbauen, dazwischen reguläres Markdown zur Erklärung einfügen und im nächsten Code-Block auf denselben Variablen, Imports und Dateien weiterarbeiten.

Über das Fence-Attribut `session=<id>` teilen sich alle Snippets mit derselben ID innerhalb einer Datei denselben `globals`-Namensraum sowie dasselbe Arbeitsverzeichnis in der Arena (`TempFS` oder `PyVenv`).

Im ersten Schritt der Session `guide_demo` legen wir eine Datei im temporären Workspace und einen Zähler im Speicher an:

```python session=guide_demo
from pathlib import Path

state_file = Path("workflow_state.txt")
state_file.write_text("active", encoding="utf-8")
step_counter = 1
print(f"Schritt {step_counter}: Datei existiert={state_file.exists()}")
```

<details>
<summary>Ergebnis</summary>

```text
Schritt 1: Datei existiert=True
```
</details>

Zwischen den Schritten einer Session kann beliebig viel reguläres Markdown stehen:

* Aufzählungen und Architektur-Hinweise werden vom Pattern-Scanner ignoriert.
* Ungetaggte Code-Blöcke zwischen den Session-Schritten laufen weiterhin streng isoliert.
* Sessions sind immer auf ihre jeweilige Markdown-Datei begrenzt, sodass gleichnamige Sessions in anderen Dateien niemals kollidieren.

Im zweiten Schritt derselben Session `guide_demo` greifen wir direkt auf `step_counter` und `state_file` aus dem ersten Block zu:

```python session=guide_demo
step_counter += 1
status = state_file.read_text(encoding="utf-8")
print(f"Schritt {step_counter}: Status={status}")
```

<details>
<summary>Ergebnis</summary>

```text
Schritt 2: Status=active
```
</details>

### 5.2 Erwartete Exceptions dokumentieren mit `raises=<Exception>`

Gute Dokumentation zeigt nicht nur den Happy Path, sondern auch, wie Schutzmechanismen (wie `STATE-GUARD`s) auf fehlerhafte Eingaben reagieren. Deklariert man `raises=<ExceptionType>` im Code-Fence-Header, erwartet `DocEnsurance` genau diesen Fehlertyp (oder eine Subklasse davon) und vergleicht die formatierte Meldung `"<Typ>: <Nachricht>"` mit dem `<details>`-Block.

Wird `raises=<Exception>` innerhalb einer aktiven Session genutzt, fängt der Runner die Exception kontrolliert ab, sodass der Session-Zustand für nachfolgende Schritte vollständig erhalten bleibt:

```python raises=ValueError
from qb_cubie import EBT

EBT(target=len, max_workers=0)
```

<details>
<summary>Ergebnis</summary>

```text
ValueError: max_workers must be a positive integer or None
```
</details>

## 6. Pluggable Check-Regeln (`rules`), Linter-Integration & Severity-Steuerung

Genau wie bei `AstLinter` und `CstLinter` lassen sich in `DocEnsurance` beliebige Prüfregeln für die **Erklärung**, den **Code** und die **Ausgabe** registrieren. Jede Regel und jeder Struktur-Baustein unterstützt dabei zwei fein abgestufte Severity-Stufen (`VALID_SEVERITIES = ("error", "warning")`):

* **`severity="warning"`:** Die Verletzung wird im `DocReport.diagnostics` protokolliert und vom `PytestReporter` als `UserWarning` ausgegeben. Die Session und der Gesamtlauf bestehen jedoch weiterhin (`passed=True`).
* **`severity="error"`:** Die Verletzung markiert die Session und den `DocReport` als fehlgeschlagen (`passed=False`), sodass der `PytestReporter` nach Ausgabe etwaiger Warnungen einen `AssertionError` auslöst.

### 6.1 Eigene Checks für Erklärung, Code und Ausgabe einhängen

Für eigene Konventionen stellt `qb_cubie.core.services` drei deklarative Regel-Bausteine bereit, die entweder über `rules=[...]` beim Start, über `.register_rule(...)` oder direkt am jeweiligen Pattern-Baustein (`Explanation(rules=...)`, `CodeSnippet(rules=...)`, `CollapsibleResult(rules=...)`) eingehängt werden können:

* **`ExplanationRule(rule_id, message, check_fn, severity="error")`:** Prüft den extrahierten Erklärungstext mit einem Prädikat `Callable[[str], bool]`.
* **`CodeRule(rule_id, message, check_fn, severity="error")`:** Prüft den Python-Quellcode des Snippets mit einem Prädikat `Callable[[str], bool]`.
* **`OutputRule(rule_id, message, check_fn, severity="error")`:** Prüft die Kombination aus `(expected_output, actual_output)` über ein Prädikat `Callable[[str | None, str | None], bool]`.

Das folgende Beispiel definiert zuerst drei eigene Regeln (`ExplanationRule` als Warnung bei offenen `TODO`-Markern, `CodeRule` für die maximale Zeilenzahl und `OutputRule` für nicht-leere Ausgaben) sowie ein passendes Beispieldokument:

```python session=custom_rules
from qb_cubie.core.services import CodeRule, DocEnsurance, ExplanationRule, OutputRule

fence = "```"
doc_with_warnings = (
    "TODO: Diese Erklärung wird noch ergänzt, ist aber lang genug.\n\n"
    f"{fence}python\nvalue = 21 * 2\nprint(value)\n{fence}\n\n"
    f"<details>\n<summary>Ergebnis</summary>\n\n{fence}text\n42\n{fence}\n</details>"
)
custom_rules = [
    ExplanationRule(
        rule_id="DOC-EXP-NO-TODO",
        message="Offenes TODO in der Erklärung.",
        check_fn=lambda text: "TODO" not in text,
        severity="warning",
    ),
    CodeRule(
        rule_id="DOC-CODE-MAX-LINES",
        message="Snippet überschreitet 10 Zeilen.",
        check_fn=lambda code: len(code.splitlines()) <= 10,
        severity="error",
    ),
    OutputRule(
        rule_id="DOC-OUT-NON-EMPTY",
        message="Ausgabe darf nicht leer sein.",
        check_fn=lambda exp, act: bool(act),
        severity="error",
    ),
]
print([r.rule_id for r in custom_rules])
```

<details>
<summary>Ergebnis</summary>

```text
['DOC-EXP-NO-TODO', 'DOC-CODE-MAX-LINES', 'DOC-OUT-NON-EMPTY']
```
</details>

Anschließend prüft `DocEnsurance` das Dokument mit diesen Regeln in derselben Session; da nur die `warning`-Regel auslöst, bleibt `passed=True`:

```python session=custom_rules
report = DocEnsurance(target=doc_with_warnings, reporter=None, rules=custom_rules).run()
diag = report.diagnostics[0]
print(f"passed={report.passed} | rule={diag.rule_id} | severity={diag.severity}")
```

<details>
<summary>Ergebnis</summary>

```text
passed=True | rule=DOC-EXP-NO-TODO | severity=warning
```
</details>

### 6.2 Fehlende Ergebnis-Ausgaben steuern (`MissingOutputRule`)

Standardmäßig sind in `DEFAULT_DOC_RULES` zwei Ausgaberegeln vorregistriert:

1. **`MissingOutputRule(severity="warning")` (`DOC-OUT-MISSING`):** Meldet einen leeren `<details>`-Ergebnisblock standardmäßig als nicht-fatale `UserWarning` (`passed=True`), ohne dass `DOC-OUT` als harter Fehler feuert.
2. **`OutputMatchRule(severity="error")` (`DOC-OUT`):** Vergleicht jeden nicht-leeren Ergebnisblock streng mit dem tatsächlichen `stdout` der Arena.

Möchte ein Projekt fehlende Ausgaben in `<details>`-Blöcken stattdessen als harten Test-Abbruch behandeln, genügt es, `MissingOutputRule(severity="error")` in `rules=[...]` oder via `.register_rule(...)` zu übergeben. Über die identische `rule_id="DOC-OUT-MISSING"` wird die Standardregel automatisch überschrieben:

```python
from qb_cubie.core.services import DocEnsurance, MissingOutputRule

fence = "```"
empty_output_doc = (
    "Dieses Beispiel gibt Text aus, besitzt aber noch einen leeren Ergebnis-Block.\n\n"
    f"{fence}python\n"
    "print('noch nicht eingetragen')\n"
    f"{fence}\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    f"{fence}text\n{fence}\n"
    "</details>"
)

service = DocEnsurance(target=empty_output_doc, reporter=None)
default_report = service.run()
strict_report = service.register_rule(MissingOutputRule(severity="error")).run()

print(
    f"Default: passed={default_report.passed} ({default_report.diagnostics[0].severity}) | "
    f"Strict: passed={strict_report.passed} ({strict_report.diagnostics[0].severity})"
)
```

<details>
<summary>Ergebnis</summary>

```text
Default: passed=True (warning) | Strict: passed=False (error)
```
</details>

### 6.3 Statische Linter (`CstLinter`, `AstLinter`, `Pylint`, `MyPy`) in Doku-Snippets einhängen

Jeder `Linter` aus `qb_cubie` lässt sich direkt in `rules=[...]` übergeben oder über `DocLinterRule(linter=..., severity=...)` mit einer eigenen Severity versehen. `DocLinterRule` prüft den extrahierten Code-Block in-memory und rechnet die Zeilennummern des Linters automatisch auf die tatsächliche Zeilenposition innerhalb der Markdown-Datei um.

Das folgende Beispiel definiert zuerst eine eigene `CstRule` (`ForbidEvalRule`) und prüft anschließend per `DocLinterRule`, dass ein `eval()`-Aufruf exakt auf Zeile 5 des Markdown-Dokuments gemeldet wird:

```python session=cst_doc_lint
import libcst as cst
from qb_cubie import CstLinter, CstRule
from qb_cubie.core.services import DocEnsurance, DocLinterRule


class ForbidEvalRule(CstRule):
    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(node, "CST-NO-EVAL", "eval() ist in Doku-Snippets verboten.")


linter = CstLinter(rules=[ForbidEvalRule()])
print(f"Linter bereit: {linter.name}")
```

<details>
<summary>Ergebnis</summary>

```text
Linter bereit: CST-Linter
```
</details>

Im zweiten Schritt derselben Session wird der konfigurierte `CstLinter` als Warnung (`severity="warning"`) in `DocEnsurance` eingehängt:

```python session=cst_doc_lint
fence = "```"
eval_doc = (
    "Dieses Beispiel nutzt eval() in der zweiten Zeile des Code-Blocks.\n\n"
    f"{fence}python\nx = 21 * 2\nprint(eval('x'))\n{fence}\n\n"
    f"<details>\n<summary>Ergebnis</summary>\n\n{fence}text\n42\n{fence}\n</details>"
)
report = DocEnsurance(
    target=eval_doc,
    rules=[DocLinterRule(linter=linter, severity="warning")],
    reporter=None,
).run()
diag = report.diagnostics[0]
print(f"passed={report.passed} | rule={diag.rule_id} | md_line={diag.line} | severity={diag.severity}")
```

<details>
<summary>Ergebnis</summary>

```text
passed=True | rule=CST-NO-EVAL | md_line=5 | severity=warning
```
</details>

## 7. Diagnose-Codes (`DocDiagnostic`)

Jeder Befund wird als unveränderliches `DocDiagnostic(file_path, rule_id, line, message, session_id=None, severity="error")` gespeichert. Standardmäßig vergibt `DocEnsurance` folgende Regel-Codes:

* **`DOC-PRE`:** Vor einem Anker-Block fehlt der geforderte Pre-Block (z. B. keine `Explanation` oder zu kurzer Erklärungstext). Die Severity richtet sich nach dem Pre-Baustein (`Explanation(severity=...)`).
* **`DOC-POST`:** Nach einem Anker-Block fehlt der geforderte Post-Block (z. B. kein `<details>`-Ergebnisblock). Die Severity richtet sich nach dem Post-Baustein (`CollapsibleResult(severity=...)`).
* **`DOC-EXEC`:** Das Code-Snippet ist während der Ausführung in der Arena mit einer unbehandelten Exception abgebrochen (`severity="error"`).
* **`DOC-RAISE`:** Ein Snippet mit `raises=<Exception>` hat entweder gar keine oder eine falsche Exception geworfen (`severity="error"`).
* **`DOC-OUT-MISSING`:** Der `<details>`-Ergebnisblock eines durchgelaufenen Snippets ist leer (Standard über `MissingOutputRule`: `severity="warning"`).
* **`DOC-OUT`:** Das Snippet lief durch, aber die tatsächliche Ausgabe weicht vom dokumentierten Ergebnis ab (Standard über `OutputMatchRule`: `severity="error"`).
* **`<Custom-Rule-ID>`:** Jede über `ExplanationRule`, `CodeRule`, `OutputRule` oder `DocLinterRule` eingehängte Regel meldet ihre eigene `rule_id` und `severity`.

## 8. Deep-Dive: Eigene Patterns und Protokolle entwickeln

Nicht jedes Projekt möchte dasselbe Dokumentations-Layout verwenden. Deshalb basiert `DocEnsurance` auf einer vierstufigen Protokoll-Architektur aus `qb_cubie.core.services.doc_ensurance.protocols`:

1. **`DocBlockProtocol` (Ebene 1 – Atomare Struktur-Bausteine):** Erkennt und extrahiert genau einen Markdown-Blocktyp (`MdBlock`) und definiert dessen `role`, `severity` und optionale Block-`rules`.
2. **`DocRuleProtocol` (Ebene 2 – Inhaltliche Prüfregeln):** Prüft ein extrahiertes `ExtractedExample` samt `actual_output` und liefert eine Sequenz von `DocDiagnostic`-Einträgen zurück.
3. **`DocPatternProtocol` (Ebene 3 – Sequenz-Muster):** Kombiniert beliebige `pre`-Bausteine, einen `anchor`-Baustein und `post`-Bausteine (Standard-Implementierung: `ExamplePattern`).
4. **`DocScopeProtocol` (Ebene 4 – Session-Topologie):** Gruppiert die extrahierten Beispiele in Arena-Läufe (Standard: `TaggedScope`).

### 8.1 Eigene Muster mit vorhandenen Bausteinen komponieren

Möchte ein Entwicklerteam beispielsweise auf Pflicht-Erklärungen und `<details>`-Tags verzichten und stattdessen direkt unter jedem `python`-Block einen einfachen `text`-Codeblock für den erwarteten Output verlangen, genügt eine neue `ExamplePattern`-Konfiguration:

```python
from qb_cubie.core.services import CodeSnippet, DocEnsurance, ExamplePattern

minimal_pattern = ExamplePattern(
    name="minimal-fence-pattern",
    pre=(),
    anchor=CodeSnippet(lang="python"),
    post=(CodeSnippet(lang="text"),),
)

fence = "```"
minimal_doc = (
    "# Kurze API-Referenz\n\n"
    f"{fence}python\nprint('minimal-style-ok')\n{fence}\n\n"
    f"{fence}text\nminimal-style-ok\n{fence}"
)

report = DocEnsurance(target=minimal_doc, pattern=minimal_pattern, reporter=None).run()
print(f"pattern={minimal_pattern.name} | passed={report.passed} | out={report.sessions[0].actual_outputs[0]}")
```

<details>
<summary>Ergebnis</summary>

```text
pattern=minimal-fence-pattern | passed=True | out=minimal-style-ok
```
</details>

### 8.2 Eigene Baustein-Protokolle (`DocBlockProtocol`) schreiben

Der interne Markdown-Scanner zerlegt jedes Dokument in flache `MdBlock(kind, content, line, meta)`-Objekte mit den Grundtypen `"heading"`, `"paragraph"`, `"list"`, `"code"` und `"details"`.

Um eine völlig eigene Strukturregel zu definieren, implementiert man das `DocBlockProtocol` (`role`, `severity`, `rules` sowie die Methoden `matches(block)` und `extract(block)`). Im ersten Schritt definieren wir den Baustein `HeadingRequirement`, der direkt über jedem Code-Beispiel eine `### Beispiel:`-Überschrift verlangt:

```python session=custom_block
from dataclasses import dataclass
from qb_cubie.core.services import CodeSnippet, DocEnsurance, DocRuleProtocol, ExamplePattern, MdBlock


@dataclass(frozen=True)
class HeadingRequirement:
    prefix: str = "### Beispiel:"
    severity: str = "error"
    rules: tuple[DocRuleProtocol, ...] = ()

    @property
    def role(self) -> str:
        return "example-heading"

    def matches(self, block: MdBlock) -> bool:
        return block.kind == "heading" and block.content.startswith(self.prefix)

    def extract(self, block: MdBlock) -> str:
        return block.content[len(self.prefix) :].strip()


print(f"Block-Role: {HeadingRequirement().role}")
```

<details>
<summary>Ergebnis</summary>

```text
Block-Role: example-heading
```
</details>

Im zweiten Schritt derselben Session komponieren wir `HeadingRequirement` in ein `ExamplePattern` und prüfen ein passendes Dokument mit `DocEnsurance`:

```python session=custom_block
heading_pattern = ExamplePattern(
    name="heading-driven-docs",
    pre=(HeadingRequirement(),),
    anchor=CodeSnippet(lang="python"),
    post=(),
)
fence = "```"
custom_doc = f"### Beispiel: Vektor-Betrag\n\n{fence}python\nprint(abs(-42))\n{fence}"
report = DocEnsurance(target=custom_doc, pattern=heading_pattern, reporter=None).run()
print(f"passed={report.passed} | output={report.sessions[0].actual_outputs[0]}")
```

<details>
<summary>Ergebnis</summary>

```text
passed=True | output=42
```
</details>

### 8.3 Eigene Gruppierungs-Strategien (`DocScopeProtocol`) und Arenen

Neben dem Pattern lassen sich über `scope` und `arena` auch die Ausführungsbedingungen frei anpassen:

* **`TaggedScope()`:** Gruppiert Snippets mit identischem `session=<id>` pro Datei in eine gemeinsame Arena, während ungetaggte Snippets einzeln isoliert werden; strukturelle Warnungen (`severity="warning"`) laufen weiterhin, während ungetaggte Snippets mit strukturellen Fehlern (`severity="error"`) die Arena-Ausführung überspringen.
* **`pre_state=WorldState(fs={...})`:** Hydratisiert vor jeder Session definierte Konfigurationsdateien oder Testdaten in das Arbeitsverzeichnis der Arena.
* **`arena=PyVenv(...)`:** Führt alle Dokumentations-Beispiele in einer dedizierten virtuellen Umgebung (inklusive optionaler `decontams`-Import-Sperren oder POSIX-Timeouts) statt im `TempFS` des Host-Interpreters aus.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
