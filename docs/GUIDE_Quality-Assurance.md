<center>

# Qualitätssicherung mit Cubie

![Cubie](.assets/cubie-banner.png)

**Ein Handbuch für Einsteiger und Experten zu deklarativen Verträgen, Test-Guided Development (TGD) und lebendiger Verifikation.**

Cubie bündelt beispielbasierte Verhaltensverträge (`EBT`), isolierte Ausführungs-Arenen (`TempFS`, `PyVenv`), statische Syntaxbaum-Analysen (`AstLinter`, `CstLinter`, `Pylint`, `MyPy`), selbstverifizierende Dokumentation (`DocEnsurance`) und strukturierte Reviews (`RBT`) unter einer gemeinsamen Orchestrierung. Für die exakten Auswertungsregeln bildet die [Vertragssemantik](GUIDE_Contract-Semantics.md) die technische Referenz.

---

</center>

## 1. Warum wir testen: Vertrauen, Klarheit und orthogonale Schichten

Qualitätssicherung ist kein bürokratisches Pflichtprogramm am Ende eines Sprints, sondern das Sicherheitsnetz, das mutiges Refactoring, saubere Architektur-Schnitte und schnelle Iterationen überhaupt erst möglich macht. Wer eine gute Test-Suite besitzt, muss keine Angst vor Änderungen am eigenen Code haben: Jede gebrochene Annahme meldet sich sofort mit Ort, Ursache und Kontext zu Wort.

Damit dieses Sicherheitsnetz im Alltag trägt, verfolgt Cubie zwei Grundprinzipien:

1. **Deklarative Verträge statt verstreuter Boilerplate-Logik:** Statt Setup-Schleifen, temporäre Ordner, Prozessgrenzen und `assert`-Kaskaden in jedem Test neu auszuschreiben, trennt Cubie das **Was** (Eingangswelt, Zieloperation, erwartete Ausgangswelt) vom **Wie** (Ausführung, Isolation, Prozess-Transport und Fehler-Aufbereitung).
2. **Orthogonale Prüf-Schichten ohne gegenseitiges Stummschalten:** Keine einzelne Prüfmethode findet jede Klasse von Fehlern. Erst das Zusammenspiel unabhängiger Schichten erzeugt hohe Verlässlichkeit – und keine Schicht darf eine andere stummschalten:

| Prüf-Schicht | Werkzeug in `qb_cubie` | Leitfrage | Typische Funde |
| :--- | :--- | :--- | :--- |
| **1. Dynamisches Verhalten** | `EBT` + `WorldState` | Liefert die Operation für repräsentative Eingaben und Kantenfälle das erwartete Ergebnis oder die geforderte Schutz-Exception? | Logikfehler, kaputte Invarianten, fehlende `STATE-GUARD`s |
| **2. Umgebungs-Isolation** | `TempFS` / `PyVenv` | Arbeitet der Code sauber ohne versteckte Abhängigkeiten vom Host-Dateisystem, `os.chdir()` oder globalen Variablen? | Zustand-Leaks zwischen Läufen, fehlende Paket-Abhängigkeiten |
| **3. Statische Struktur** | `AstLinter` / `CstLinter` / `MyPy` / `Pylint` | Hält der Quellcode Typverträge, Stilgesetze und strukturelle Leitplanken (z. B. Funktionsgrößen) ein? | Typbrüche, verbotene Aufrufe, aufgeblähte Funktionen |
| **4. Lebende Dokumentation** | `DocEnsurance` + `CUBIE_DOC_RULES` | Laufen alle Code-Beispiele in den Markdown-Guides tatsächlich durch und stimmen ihre dokumentierten Ausgaben? | Veraltete Signaturen in Tutorials, stille Doku-Abweichungen |
| **5. Semantisches Urteil** | `RBT` (`HeadlessReviewer`, `HumanReviewer`) | Erfüllt das Artefakt qualitative, fachliche oder gestalterische Kriterien, die sich nicht rein syntaktisch prüfen lassen? | Unverständliche Fehlermeldungen, unklare API-Ergonomie |

Das folgende Einstiegsbeispiel zeigt das Grundmuster eines deklarativen `EBT`-Vertrags anhand der Standardfunktion `divmod` für zwei Eingabepaare:

```python
from qb_cubie import EBT, WorldState

trace = EBT(
    target=divmod,
    pre=[WorldState(args=(17, 5)), WorldState(args=(20, 4))],
    post=[
        WorldState(returns=(3, 2)),
        WorldState(returns=(5, 0)),
    ],
    reporter=None,
).run()
print(f"Vertrag erfüllt: {trace.evaluation} | Geprüfte Paare: {len(trace.traces)}")
```

<details>
<summary>Ergebnis</summary>

```text
Vertrag erfüllt: True | Geprüfte Paare: 4
```
</details>

---

## 2. Die gefährlichste Falle der Qualitätssicherung: Charakterisierung ( $Q_{\text{Ist}}$ ) vs. Spezifikation ( $Q_{\text{Soll}}$ )

Eine der wichtigsten Erfahrungen aus der praktischen Arbeit mit Test-Suiten – egal ob man Tests von Hand schreibt oder explorative Analysen durchführt – betrifft den Unterschied zwischen **Beobachtung ( $Q_{\text{Ist}}$ )** und **Gesetz ( $Q_{\text{Soll}}$ )**.

Wenn wir bestehenden Code auf überraschende Randfälle abklopfen (etwa mit einem kurzen Kommandozeilen-Snippet), beobachten wir zunächst das tatsächliche Ist-Verhalten des Systems. Enthält das System in einem Randfall einen Bug und wir übernehmen dieses beobachtete Verhalten unreflektiert als erwarteten `post`-Zustand in unseren Test, passiert etwas Fatales:

* **Der Bug wird zum Gesetz erhoben:** Die Test-Suite leuchtet komplett grün (`PASSED`), obwohl der Fehler mitten im System steckt.
* **Reparaturen brechen den Test:** Sobald jemand den Bug später behebt, schlägt der Test fehl, weil er das kaputte Verhalten verteidigt.

### Die Lösung: Vertrags-Inversion mit `expect=False`

In Cubie besitzt jeder `WorldState` das Flag `expect` (Standard: `expect=True`). Setzt man in einem `post`-Zustand **`expect=False`**, dreht sich die Bedeutung um: Dieser Zustand beschreibt ein **explizit verbotenes Fehlersymptom**.

Damit lässt sich ein beobachteter Bug eins zu eins in den Test übernehmen und mit `expect=False` invertieren:

1. **In der Red-Phase (Bug ist noch im Code):** Das Zielobjekt liefert genau das verbotene Symptom. Da `expect=False` verletzt wird, meldet `EBT` sofort `Validation: Matched` auf dem verbotenen Zustand und bricht den Testlauf rot ab (`evaluation=False` bzw. `AssertionError`).
2. **In der Green-Phase (Bug ist behoben):** Sobald die Implementierung repariert ist, tritt das verbotene Symptom nicht mehr auf. Derselbe `expect=False`-Zustand bleibt als dauerhafte Regressions-Schranke im Test stehen und wird um den positiven Soll-Zustand (`expect=True`) ergänzt.

Wir demonstrieren diesen Zyklus in einer zweistufigen Session. Im ersten Schritt entlarven wir eine fehlerhafte Funktion `normalize_tag`, die durch den unvorsichtigen Einsatz von `.strip("v_ ")` auch das `'v'` am Anfang des Wortes `'version'` abschneidet, mithilfe von `expect=False`:

```python session=tgd_inversion
from qb_cubie import EBT, WorldState


def normalize_tag_buggy(raw: str) -> str:
    return raw.strip("v_ ")


red_trace = EBT(
    target=normalize_tag_buggy,
    pre=WorldState(args=("v_version",)),
    post=WorldState(returns="ersion", expect=False),
    reporter=None,
).run()
print(f"Red-Phase (Bug aktiv): evaluation={red_trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Red-Phase (Bug aktiv): evaluation=False
```
</details>

Im zweiten Schritt derselben Session ersetzen wir `.strip("v_ ")` durch `.strip().removeprefix("v_")` und sichern die Funktion gleichzeitig positiv (`expect=True`) wie negativ (`expect=False`) ab:

```python session=tgd_inversion
def normalize_tag_fixed(raw: str) -> str:
    return raw.strip().removeprefix("v_")


green_trace = EBT(
    target=normalize_tag_fixed,
    pre=WorldState(args=("v_version",)),
    post=[
        WorldState(returns="version", expect=True),
        WorldState(returns="ersion", expect=False),
    ],
    reporter=None,
).run()
print(f"Green-Phase (Bug behoben): evaluation={green_trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Green-Phase (Bug behoben): evaluation=True
```
</details>

---

## 3. Test-Guided Development (TGD) in fünf Schritten

Test-Guided Development erweitert klassisches TDD um explorative System-Audits, zustandsfreie Projektions-Adapter und die strikte Trennung orthogonaler Prüf-Ebenen. Dieser fünfstufige Ablauf hat sich bei der Entwicklung des Cubie-Kerns besonders bewährt:

### Schritt 1: Baseline & Exploratives Audit
Bevor neue Regeln oder Features entstehen, wird der Ist-Zustand vermessen: Laufen bestehende Suiten grün? Welche impliziten Annahmen trifft der Code an seinen Grenzen (leere Eingaben, ungewöhnliche Pfadnamen, mehrstufige Sessions, Timeouts, Prozessgrenzen)? Explorative Mini-Experimente legen überraschende Kantenfälle frei, noch bevor eine Zeile Produktionscode geändert wird.

### Schritt 2: Schlanke, zustandsfreie Test-Adapter (`Stateless Adapters`)
Wenn das zu prüfende Subsystem komplexe Report-Objekte mit vielen internen Feldern zurückgibt, sollte der Test nicht an irrelevanten Implementierungsdetails kleben. Bewährt hat sich ein kurzer, zustandsfreier Test-Adapter (meist 5–12 Zeilen), der das Subsystem aufruft und das Ergebnis auf ein kanonisches Prüf-Dictionary projiziert (z. B. `{"passed": report.passed, "rules": [d.rule_id for d in report.diagnostics]}`). Dadurch bleiben die `WorldState`-Definitionen im `EBT`-Aufruf kompakt und selbsterklärend.

### Schritt 3: Äquivalenzklassen & Kantenfälle statt Daten-Flut
Zwanzig fast identische Happy-Path-Werte erhöhen die Laufzeit, aber nicht die Aussagekraft. Besser ist die gezielte Partitionierung in fachliche Äquivalenzklassen:
* **Positiv-Invarianz:** Repräsentative Normalfälle unter realistischem Umgebungsrauschen.
* **Exakte Schwellenwerte (Off-by-One):** Wenn eine Grenze bei $20$ Zeichen oder $30$ Zeilen liegt, prüfe gezielt $19$ vs. $20$ bzw. $30$ vs. $31$.
* **Explizite `STATE-GUARD`s:** Ungültige Typen, leere Strings oder Werte außerhalb des Definitionsbereichs müssen frühzeitig mit einer klaren Fehlermeldung abgewiesen werden.

### Schritt 4: Red-Phase vor dem Fix erzwingen
Jeder gefundene Bug wird zuerst als fehlschlagender `EBT`-Vertrag (über das Soll-Gesetz $Q_{\text{Soll}}$ oder invertiert über `expect=False`) in der Test-Suite verankert. Erst wenn der Test sichtbar rot fehlschlägt, ist bewiesen, dass der Test den Fehler tatsächlich detektiert.

### Schritt 5: Orthogonale Reparatur & Stil-Verifikation
Bei der anschließenden Reparatur im Quellcode gilt das Gesetz der Orthogonalität: Ein struktureller Fehler darf statische Regeln nicht blind abschalten, und eine benutzerdefinierte Regel darf wichtige Standard-Checks nicht unbemerkt verdrängen. Den Abschluss bildet der Lauf über alle Ebenen (`pytest`, `AstLinter`/`CstLinter` und `DocEnsurance`).

Das folgende Beispiel zeigt das Zusammenspiel aus einem schlanken Adapter, Typ-/Regex-Mustern im `WorldState` und einer expliziten `ExceptionExpectation` für `STATE-GUARD`-Prüfungen:

```python
import re
from typing import Any
from qb_cubie import EBT, ExceptionExpectation, WorldState


def parse_batch_size(raw: str) -> dict[str, Any]:
    value = int(raw.strip())
    if value < 1:
        raise ValueError(f"STATE-GUARD: batch_size must be >= 1; got {value}")
    return {"status": f"batch:{value}", "count": value}


EBT(
    target=parse_batch_size,
    pre=[WorldState(args=(" 1 ",)), WorldState(args=("64",))],
    post=WorldState(returns={"status": re.compile(r"^batch:\d+$"), "count": int}),
).run()

EBT(
    target=parse_batch_size,
    pre=[WorldState(args=("0",)), WorldState(args=("-10",))],
    post=WorldState(raises=ExceptionExpectation(ValueError, match=r"^STATE-GUARD:")),
).run()
print("Äquivalenzklassen (1/64 vs. 0/-10) erfolgreich verifiziert.")
```

<details>
<summary>Ergebnis</summary>

```text
Äquivalenzklassen (1/64 vs. 0/-10) erfolgreich verifiziert.
```
</details>

---

## 4. Praxis-Tutorials: Vom Einsteiger zum Experten

### 4.1 Für Einsteiger: Nebenwirkungsfreie Dateisystem-Tests mit `TempFS`

Tests, die Dateien lesen, ändern oder das Arbeitsverzeichnis wechseln (`os.chdir`), verschmutzen ohne Isolation schnell das Projektverzeichnis oder beeinflussen nachfolgende Tests. Mit `arena=TempFS()` erhält jeder `pre`-Zustand einen eigenen, frischen Kindprozess samt temporärem Arbeitsverzeichnis, das nach dem Schritt automatisch aufgeräumt wird.

Über `WorldState(fs=...)` lassen sich zudem benötigte Ausgangsdateien vorab in die Arena hydratisieren (entweder als Mapping `{"ziel.txt": "quelle.txt"}` oder als Listen-Kurzform `["quelle.txt"]`).

Das folgende Beispiel beweist, dass zwei aufeinanderfolgende `pre`-Schritte in `TempFS` komplett voneinander und vom Host-Verzeichnis isoliert laufen:

```python
from pathlib import Path
from qb_cubie import EBT, TempFS, WorldState


def record_step(filename: str) -> str:
    target = Path(filename)
    history = target.read_text(encoding="utf-8") if target.exists() else "start"
    target.write_text(f"{history}->run", encoding="utf-8")
    return target.read_text(encoding="utf-8")


trace = EBT(
    target=record_step,
    arena=TempFS(),
    pre=[WorldState(args=("state.log",)), WorldState(args=("state.log",))],
    post=WorldState(returns="start->run"),
    reporter=None,
).run()
outputs = [t.outcome.returns for t in trace.traces]
print(f"Ausgaben: {outputs} | Host unberührt: {not Path('state.log').exists()}")
```

<details>
<summary>Ergebnis</summary>

```text
Ausgaben: ['start->run', 'start->run'] | Host unberührt: True
```
</details>

### 4.2 Für Fortgeschrittene: Eigene Architektur-Gesetze mit `CstRule` & `CstLinter`

Wenn ein Team feststellt, dass bestimmte Code-Muster (wie `eval()`, ungeschützte `print()`-Aufrufe im Produktionscode oder überlange Funktionen) immer wieder in Reviews auffallen, sollten diese Regeln nicht mühsam von Hand geprüft werden. Mit `CstRule` und `CstLinter` auf Basis von `libcst` lassen sich eigene statische Prüfregeln inklusive exakter Zeilen- und Spaltennummern in wenigen Zeilen definieren und sowohl über `AstLinter` auf ganze Verzeichnisse als auch über `DocEnsurance` auf Doku-Snippets anwenden.

Das folgende Beispiel definiert eine eigene `CstRule`, die den Aufruf von `eval()` verbietet, und prüft ein Code-Snippet direkt im Speicher:

```python
import libcst as cst
from qb_cubie import AstLinter, CstLinter, CstRule


class DisallowEvalRule(CstRule):
    """Verbietet den Einsatz von eval() aus Gründen der Nachvollziehbarkeit."""

    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(node, "ARCH-NO-EVAL", "Verwende sicheres Parsing statt eval().")


suite = AstLinter(CstLinter(rules=[DisallowEvalRule()]))
diagnostics = suite.check("value = 21\nresult = eval('value * 2')\n")
diag = diagnostics[0]
print(f"Linter: {suite.name} | Code: {diag.rule_id} | Zeile: {diag.line}")
```

<details>
<summary>Ergebnis</summary>

```text
Linter: AST-Linter(CST-Linter) | Code: ARCH-NO-EVAL | Zeile: 2
```
</details>

### 4.3 Für Experten: Lebende Dokumentation & orthogonale Regeln mit `DocEnsurance`

Mit `DocEnsurance` wird jede Markdown-Datei im Projekt selbst zu einer ausführbaren Spezifikation. Rund um jeden `python`-Code-Block prüft `CUBIE_DOC_STYLE` das dreiteilige Strukturmuster (`Explanation` $\to$ `CodeSnippet` $\to$ `CollapsibleResult`), führt den Code in einer isolierten Arena aus und vergleicht den realen `stdout` mit dem dokumentierten `<details>`-Block.

Darüber lassen sich didaktische Qualitätsregeln (`CUBIE_DOC_RULES` wie `NoOutput`, `HighComplexity`, `LargeOutput`, `RawTraceback`), eigene `ExplanationRule`-, `CodeRule`- oder `OutputRule`-Prädikate sowie statische Linter (`CstLinter`, `AstLinter`, `MyPy`, `Pylint`) legen. Alle Schichten arbeiten orthogonal: Warnungen (`severity="warning"`) informieren über Verbesserungspotenziale, ohne den Lauf abzubrechen (`passed=True`), während Fehler (`severity="error"`) den Test gezielt stoppen.

Das folgende Beispiel kombiniert die Standard-Didaktikregeln `CUBIE_DOC_RULES` mit einer eigenen `ExplanationRule` und prüft ein kleines In-Memory-Dokument:

```python
from qb_cubie.services import CUBIE_DOC_RULES, DocEnsurance, ExplanationRule

fence = "```"
guide_snippet = (
    "WIP: Diese Erklärung beschreibt ein sauberes Berechnungsbeispiel im Guide.\n\n"
    f"{fence}python\nitems = [10, 20, 12]\nprint(sum(items))\n{fence}\n\n"
    f"<details>\n<summary>Ergebnis</summary>\n\n{fence}text\n42\n{fence}\n</details>"
)

no_wip_warning = ExplanationRule(
    rule_id="DOC-EXP-NO-WIP",
    message="Erklärung enthält noch einen WIP-Marker.",
    check_fn=lambda text: "WIP:" not in text,
    severity="warning",
)
report = DocEnsurance(
    target=guide_snippet,
    rules=[*CUBIE_DOC_RULES, no_wip_warning],
    reporter=None,
).run()
print(f"Passed: {report.passed} | Output: {report.sessions[0].actual_outputs[0]} | Diagnose: {report.diagnostics[0].rule_id}")
```

<details>
<summary>Ergebnis</summary>

```text
Passed: True | Output: 42 | Diagnose: DOC-EXP-NO-WIP
```
</details>

---

## 5. Methodische Ehrlichkeit: Beobachtung, Abdeckung und Beweis

Gute Ingenieurskunst zeichnet sich dadurch aus, dass sie die Leistungsfähigkeit ihrer Werkzeuge kennt – aber ihre Aussagen niemals überdehnt. Auch eine zu 100 % grüne Test-Suite unterliegt klaren erkenntnistheoretischen Grenzen:

* **Beobachtete Konformität statt Allgemeinbeweis:** Ein bestandener `EBT`- oder `DocEnsurance`-Lauf zeigt, dass die konkret ausgeführten Beispiele unter den jeweiligen Testbedingungen zu den deklarierten Sollmustern passen. Er ist eine starke empirische Evidenz gegen Regressionen, ersetzt aber keinen mathematischen Korrektheitsbeweis über alle denkbaren Eingaben aus $\Sigma^*$.
* **Die Hoare-Analogie $\{P\}\ S\ \{Q\}$ als Strukturmodell:** Die Anordnung `pre` ($\{P\}$), `target` ($S$) und `post` ($\{Q\}$) in `EBT` ist eine bewusste architektonische und didaktische Analogie zum Hoare-Tripel. Ein `WorldState` ist dabei ein konkreter Datensatz oder ein Prädikat-Muster, und die Auswertung prüft endliche, explizite Zustandslisten: Jeder ausgeführte Eingang aus `pre` muss mindestens einen positiven Zustand aus `post` (`expect=True`) erfüllen und darf keinen negativen Zustand (`expect=False`) verletzen. Details regelt die [Vertragssemantik](GUIDE_Contract-Semantics.md).
* **Vielfalt von Beispielen vs. formale Abdeckung:** Unterschiedliche Beispiele aus verschiedenen Äquivalenzklassen verbessern die praktische Abdeckung erheblich; ihre bloße Anzahl belegt jedoch noch keine mathematische Orthogonalität unabhängiger Merkmalsdimensionen und verhindert für sich genommen kein Overfitting.
* **Einordnung von Reviews (`RBT`):** `RBT` übergibt eine sprachliche Prüfregel und eine Zielbezeichnung an einen menschlichen oder automatisierten Reviewer (`HeadlessReviewer`, `HumanReviewer` oder eigene `Reviewer`-Implementierungen). Ein positives Review dokumentiert ein qualifiziertes Urteil zum Prüfzeitpunkt, misst aber keine Laufzeit- oder Speicherbudgets automatisch.
* **Isolations- statt Sicherheitsgrenze bei Arenen:** `TempFS` und `PyVenv` schützen hervorragend vor versehentlicher Verschmutzung des Arbeitsverzeichnisses und vor ungewollten Paket-Leaks aus der Host-Umgebung. Sie bilden jedoch keine Betriebssystem-Sandbox gegen aktiv schädlichen Code – führe in Arenen daher nur vertrauenswürdigen Projekt- und Testcode aus.

---

## 6. Herzliche Empfehlungen für den QS-Alltag

Zum Abschluss einige persönliche Leitlinien, die sich in der täglichen Arbeit mit Cubie immer wieder auszahlen:

1. **Vertraue keinem Test, den du nicht hast scheitern sehen:** Wenn du einen neuen Vertrag schreibst, provoziere kurz den Bruch (oder nutze `expect=False` auf dem Ist-Symptom), um sicherzugehen, dass der Test bei einem Fehler auch wirklich anschlägt.
2. **Halte Code-Beispiele in der Doku klein und fokussiert:** Wenn ein Beispiel im Guide mehr als 30 Zeilen benötigt (`DOC-HIGH-COMPLEXITY`), teile es über `session=<id>` in logische Zwischenschritte mit erklärendem Text auf und gib in jedem Schritt ein kurzes, sprechendes Zwischenergebnis mit `print(...)` aus.
3. **Nutze Warnungen als konstruktiven Kompass:** Nicht jede Regel muss sofort den Build brechen. Mit `severity="warning"` lassen sich didaktische Hinweise (wie `CUBIE_DOC_RULES`) oder neue Stil-Konventionen sanft einführen, bevor sie später auf `severity="error"` geschärft werden.
4. **Schreibe Fehlermeldungen für dein zukünftiges Ich:** Ein `STATE-GUARD` mit einer klaren Aussage, *welcher* Parameter *warum* abgewiesen wurde und *was* stattdessen erwartet wird, spart beim Debugging Stunden an Suchzeit.
5. **Lass die Werkzeuge für dich arbeiten:** Kombiniere `EBT` für die Fachlogik, `AstLinter`/`CstLinter` für die Code-Hygiene und `DocEnsurance` für deine Markdown-Guides – dann bleibt deine Dokumentation genauso lebendig und verlässlich wie dein Code.

---

---

<center>

![Error while trying to load the image](.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Handbuch & Methodik | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  
[↦ | DocEnsurance: Lebende Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  

[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>