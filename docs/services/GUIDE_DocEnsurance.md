# GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation

Dokumentationen veralten oft genau dann, wenn sich Signaturen, Rückgabewerte oder Exceptions im Code ändern, die Code-Beispiele in den Markdown-Guides aber unbemerkt auf dem alten Stand bleiben. **`DocEnsurance`** aus `qb_cubie.services` löst dieses Problem, indem es Markdown-Dokumente sowohl **strukturell** (Layout-Konvention) als auch **funktional** (echte Ausführung in einer isolierten `Arena`) absichert.

> [!NOTE]
> 
> **Wichtiger Disclaimer (Garantieumfang & Abgrenzung):**
> Auch wenn `DocEnsurance` überprüft, ob jedes Code-Beispiel durchläuft und die dokumentierte Ausgabe tatsächlich erzeugt wird, ist dies **noch keine generelle Testabdeckung** und **keine Garantie für die inhaltliche Korrektheit der Informationen** in den Dokumentationen:
> * **Kein Ersatz für systematische Tests:** Ein einzelnes Positiv-Beispiel im Guide beweist nur diesen einen konkreten Aufruf, ersetzt aber keine Äquivalenzklassen-, Randfall- und Negativ-Prüfungen über `EBT`-Verträge in der Test-Suite.
> * **Keine semantische Prüfung des Fließtextes:** `DocEnsurance` prüft, *ob* eine Erklärung vor dem Code-Block existiert, kann aber nicht bewerten, ob die Aussagen im Text fachlich vollständig oder zutreffend sind.

In einer bestehenden Test-Suite (wie `tests/test_styleguide.py`) genügt ein einziger Aufruf, um sämtliche Markdown-Dokumente des Projekts automatisch zu verifizieren:

```python
from qb_cubie.services import CUBIE_DOC_STYLE, DocEnsurance


def test_docs_code_examples() -> None:
    """Verifies that all documentation code examples follow CUBIE_DOC_STYLE and execute cleanly."""
    DocEnsurance(
        pattern=CUBIE_DOC_STYLE,
        excludes=("experiments", "docs_tmp", "GUTACHTEN.md"),
    ).run()
```

<details>
<summary>Ergebnis</summary>

```text

```
</details>

## 1. Grundprinzip: Das Anker-Modell $\{P\}\ S\ \{Q\}$

Analog zum Hoare-Tripel $\{P\}\ S\ \{Q\}$ aus `EBT` betrachtet `DocEnsurance` jedes Code-Beispiel in einer Markdown-Datei als dreiteiligen Vertrag rund um einen **Anker-Block**:

* **Pre-Block ($P$ – Erklärung):** Vor dem Code-Block muss ein erklärender Textabsatz stehen, der das Beispiel einordnet.
* **Anchor-Block ($S$ – Code-Snippet):** Ein ausführbarer `python`-Code-Block triggert die Prüfung.
* **Post-Block ($Q$ – Erwartetes Ergebnis):** Direkt unter dem Code-Block dokumentiert ein aufklappbarer `<details>`-Block die erwartete Konsolenausgabe (`stdout`) oder Fehlermeldung.

Reguläres Markdown außerhalb dieser unmittelbaren Nachbarschaft – wie Kapitelüberschriften, Aufzählungslisten, Architekturskizzen oder weiterführende Absätze – wird vom Scanner automatisch übersprungen.

Die vorkonfigurierte Standard-Konvention `CUBIE_DOC_STYLE` prüft genau dieses Dreier-Muster (Erklärung mit mindestens 20 Zeichen, `python`-Snippet und aufklappbares `<details>`-Ergebnis):

```python
from qb_cubie.services import CUBIE_DOC_STYLE

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

## 2. Ziel-Auflösung (`target` & `excludes`) und Einzelprüfung

`DocEnsurance` ist so vorkonfiguriert, dass es ohne Boilerplate-Pfade sofort das gesamte Projekt absichert, sich bei Bedarf aber auch gezielt auf einzelne Dateien oder Strings richten lässt:

* **`target=None` (Standard):** Durchsucht standardmäßig das gesamte Projektverzeichnis rekursiv nach `*.md`-Dateien (unter automatischer Beachtung von `DEFAULT_EXCLUDES` wie `.venv`, `.git` und `__pycache__`).
* **`excludes=(...)`:** Schließt zusätzliche Ordner, Dateien oder relative Teilpfade (wie `"experiments"`, `"docs/drafts"` oder `"GUTACHTEN.md"`) relativ zum Zielverzeichnis vom Scan aus.
* **`target=Path(...)` oder `str`:** Akzeptiert wahlweise ein spezifisches Unterverzeichnis, eine einzelne `.md`-Datei oder einen mehrzeiligen In-Memory-Markdown-String. Nicht existierende Datei- oder Ordnerpfade werden sofort durch einen `FileNotFoundError`-`STATE-GUARD` abgefangen.
* **`reporter=PytestReporter()` (Standard):** Löst bei strukturellen Verstößen oder abweichenden Ausgaben direkt einen formatierten `AssertionError` für `pytest` aus. Mit `reporter=None` lässt sich das `DocReport`-Ergebnis programmatisch auswerten.

Das folgende Beispiel legt im aktuellen Workspace eine einzelne Markdown-Datei an und wertet deren `DocReport` direkt aus:

```python
from pathlib import Path
from qb_cubie.services import CUBIE_DOC_STYLE, DocEnsurance

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

## 3. Fortgeschrittene Markdown-Features

### 3.1 Geteilter Zustand über `session=<id>`

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

### 3.2 Erwartete Exceptions dokumentieren mit `raises=<Exception>`

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

## 4. Diagnose-Codes (`DocDiagnostic`)

Schlägt eine Prüfung fehl, erzeugt `DocEnsurance` präzise `DocDiagnostic`-Einträge mit Dateipfad, Zeilennummer und einem von fünf Regel-Codes:

* **`DOC-PRE`:** Vor einem Anker-Block fehlt der geforderte Pre-Block (z. B. keine `Explanation` oder zu kurzer Erklärungstext).
* **`DOC-POST`:** Nach einem Anker-Block fehlt der geforderte Post-Block (z. B. kein `<details>`-Ergebnisblock).
* **`DOC-EXEC`:** Das Code-Snippet ist während der Ausführung in der Arena mit einer unbehandelten Exception abgebrochen.
* **`DOC-RAISE`:** Ein Snippet mit `raises=<Exception>` hat entweder gar keine oder eine falsche Exception geworfen.
* **`DOC-OUT`:** Das Snippet lief durch, aber die tatsächliche Ausgabe weicht vom dokumentierten Ergebnis ab.

## 5. Deep-Dive: Eigene Patterns und Protokolle entwickeln

Nicht jedes Projekt möchte dasselbe Dokumentations-Layout verwenden. Deshalb basiert `DocEnsurance` auf einer dreistufigen Protokoll-Architektur aus `qb_cubie.services.protocols`:

1. **`DocBlockProtocol` (Ebene 1 – Atomare Bausteine):** Erkennt und extrahiert genau einen Markdown-Blocktyp (`MdBlock`).
2. **`DocPatternProtocol` (Ebene 2 – Sequenz-Muster):** Kombiniert beliebige `pre`-Bausteine, einen `anchor`-Baustein und `post`-Bausteine (Standard-Implementierung: `ExamplePattern`).
3. **`DocScopeProtocol` (Ebene 3 – Session-Topologie):** Gruppiert die extrahierten Beispiele in Arena-Läufe (`TaggedScope` oder `IsolatedScope`).

### 5.1 Eigene Muster mit vorhandenen Bausteinen komponieren

Möchte ein Entwicklerteam beispielsweise auf Pflicht-Erklärungen und `<details>`-Tags verzichten und stattdessen direkt unter jedem `python`-Block einen einfachen `text`-Codeblock für den erwarteten Output verlangen, genügt eine neue `ExamplePattern`-Konfiguration:

```python
from qb_cubie.services import CodeSnippet, DocEnsurance, ExamplePattern

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

### 5.2 Eigene Baustein-Protokolle (`DocBlockProtocol`) schreiben

Der interne Markdown-Scanner zerlegt jedes Dokument in flache `MdBlock(kind, content, line, meta)`-Objekte mit den Grundtypen `"heading"`, `"paragraph"`, `"list"`, `"code"` und `"details"`.

Um eine völlig eigene Strukturregel zu definieren, implementiert man das `DocBlockProtocol` (Property `role` sowie die Methoden `matches(block)` und `extract(block)`). Das folgende Beispiel definiert einen eigenen Baustein `HeadingRequirement`, der verlangt, dass direkt über jedem Code-Beispiel eine `### Beispiel:`-Überschrift steht:

```python
from dataclasses import dataclass
from qb_cubie.services import CodeSnippet, DocEnsurance, ExamplePattern, MdBlock


@dataclass(frozen=True)
class HeadingRequirement:
    prefix: str = "### Beispiel:"

    @property
    def role(self) -> str:
        return "example-heading"

    def matches(self, block: MdBlock) -> bool:
        return block.kind == "heading" and block.content.startswith(self.prefix)

    def extract(self, block: MdBlock) -> str:
        return block.content[len(self.prefix) :].strip()


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

### 5.3 Eigene Gruppierungs-Strategien (`DocScopeProtocol`) und Arenen

Neben dem Pattern lassen sich über `scope` und `arena` auch die Ausführungsbedingungen frei anpassen:

* **`IsolatedScope()`:** Ignoriert etwaige `session=`-Tags und erzwingt für jedes einzelne Code-Snippet im Dokument eine eigene, frische Arena.
* **`pre_state=WorldState(fs={...})`:** Hydratisiert vor jeder Session definierte Konfigurationsdateien oder Testdaten in das Arbeitsverzeichnis der Arena.
* **`arena=PyVenv(...)`:** Führt alle Dokumentations-Beispiele in einer dedizierten virtuellen Umgebung (inklusive optionaler `decontams`-Import-Sperren oder POSIX-Timeouts) statt im `TempFS` des Host-Interpreters aus.