<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->
<div align="center">

# Qualitätssicherung mit Cubie

![Cubie](.assets/cubie-banner.png)

**Ein Handbuch für Einsteiger und Experten zu deklarativen Verträgen, Test-Guided Development (TGD) und lebendiger Verifikation.**

Cubie bündelt beispielbasierte Verhaltensverträge (`EBT`), isolierte Ausführungs-Arenen (`TempFS`, `PyVenv`), statische Syntaxbaum-Analysen (`AstLinter`, `CstLinter`, `Pylint`, `MyPy`), selbstverifizierende Dokumentation (`DocEnsurance`) und strukturierte Reviews (`RBT`) unter einer gemeinsamen Orchestrierung. Für die exakten Auswertungsregeln bildet die [Vertragssemantik](GUIDE_Contract-Semantics.md) die technische Referenz.

---

> [!Note]
> **Hinweis (Disclaimer):**  
> Dieses Handbuch zur Qualitätssicherung befindet sich derzeit unter aktiver Mutation und Überarbeitung und könnte daher Fehler, Unvollständigkeiten oder veraltete Angaben enthalten.

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Warum wir testen: Klarheit und orthogonale Schichten

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

### Grundkurs: So funktioniert ein EBT-Vertrag

Ein `EBT`-Vertrag funktioniert wie eine kleine Vereinbarung in drei Teilen: **Vorher (`pre`)** stehen die Eingaben, in der **Mitte (`target`)** steht die Funktion, die du prüfen willst, und **Nachher (`post`)** steht das Ergebnis, das herauskommen muss. Im einfachsten Fall prüfst du genau einen Aufruf:

```python
from qb_cubie import EBT, WorldState


def double(x: int) -> int:
    return x * 2


trace = EBT(
    target=double,
    pre=WorldState(args=3),
    post=WorldState(returns=6),
).run()

print(f"Vertrag erfüllt: {trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Vertrag erfüllt: True
```
</details>

Damit Verträge auch bei mehreren Testfällen, Verboten und komplexeren Regeln verlässlich bleiben, baut Cubie auf drei einfachen Grundbausteinen auf:

### Baustein A: Klare Paare statt Mischmasch (Eindeutigkeit & Kopplung)

Wenn du mehrere Wertepaare prüfen willst (zum Beispiel `3 -> 6` und `5 -> 10`), gib **jedem Paar seinen eigenen Vertrag** – entweder als eigene Test-Funktion oder kompakt mit `@pytest.mark.parametrize`.

* **Die häufigste Einsteiger-Falle:** Schreibst du `[3, 5]` gemeinsam in `pre` und `[6, 10]` gemeinsam in `post`, ordnet Cubie die Listen **nicht** paarweise zu (`3 -> 6`, `5 -> 10`). Stattdessen wird *jeder* Eingang gegen *jedes* Ergebnis geprüft ($2 \times 2 = 4$ Prüfungen). Dann bestünde sogar eine kaputte Funktion, die immer `6` zurückgibt oder die Antworten vertauscht.
* **Einfache Faustregel:** Mehrere Eingänge gehören nur dann zusammen in ein `pre`, wenn für **alle** dasselbe Ziel in `post` gilt (etwa wenn `" TEXT "` und `"TeXt"` beide `"text"` ergeben müssen).

👉 **Ausführliche Beispiele und Anti-Patterns:** [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md)

### Baustein B: Erlaubtes und Verbotenes steuern (`expect`-Flags)

Standardmäßig bedeutet `expect=True`: *„Genau das soll passieren.“* Mit `expect=False` kannst du gezielt sagen, was **nicht** passieren darf – und zwar auf zwei Ebenen:

1. **Auf einem `WorldState` in `post` (Verbot):** Du legst fest, was herauskommen muss (`expect=True`), und verbietest gleichzeitig gefährliche Werte (`expect=False`, z. B. negative Preise). Hat ein alter Test versehentlich einen Bug als gültig abgespeichert, drehst du ihn mit `expect=False` um und ergänzt das echte Soll-Ziel: Sofort wird der Test ehrlich rot, bis der Bug behoben ist.
2. **Auf `EBT(..., expect=False)` (Gegenprobe):** Du kehrst das Ergebnis des gesamten Vertrags um. So beweist du in der Red-Phase, dass dein Vertrag bei einem bekannten Fehler tatsächlich anschlägt.

> [!CAUTION]
> **Vorsicht vor der „einsamen Negation“ (*Vacuous Pass*):** Schreibst du in `post` *nur* ein Verbot (`expect=False`) ohne mindestens ein positives Soll-Ziel (`expect=True`), schlüpfen völlig falsche Werte (wie `None`) unbemerkt durch – weil sie technisch gesehen nicht der verbotene Wert sind.

👉 **Alle Muster, Reparatur-Beispiele und Warnhinweise:** [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md)

### Baustein C: „Alle“ oder „mindestens eines“ gezielt wählen (`all` vs. `exists`)

Ohne besondere Angabe arbeitet Cubie nach zwei Alltagsregeln:

* In **`pre`** müssen **alle** angegebenen Eingänge bestehen (`"all"`).
* In **`post`** reicht es, wenn **mindestens ein** erlaubtes Zielmuster passt (`"exists"`).

Manchmal brauchst du es genau umgekehrt. Dann verpackst du die Zustände einfach in `{"quantor": ..., "states": ...}`:

* **`post` mit `"all"`:** Das Ergebnis muss **alle** Regeln gleichzeitig erfüllen (z. B. *eine ganze Zahl **und** positiv **und** gerade*).
* **`pre` mit `"exists"`:** Es genügt, wenn **mindestens eine** von mehreren Eingabe-Routen zum Erfolg führt (z. B. `/main` oder `/backup` antwortet mit `"ok"`).

👉 **Alle Code-Beispiele und `STATE-GUARD`-Regeln:** [Fortgeschrittene Quantoren (`all` vs. `exists`)](GUIDE_Quantifiers.md)

### Spickzettel für den Einstieg

| Was möchtest du prüfen? | Empfohlenes Mittel | Weiterführendes Handbuch |
| :--- | :--- | :--- |
| Mehrere konkrete Ein-/Ausgabepaare (`3 -> 6`, `5 -> 10`) | Getrennte Verträge oder `@pytest.mark.parametrize` | [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md) |
| Soll-Wert fordern und gefährliche Werte verbieten | `WorldState(..., expect=True)` + `WorldState(..., expect=False)` | [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) |
| Prüfen, ob ein Vertrag bei einem Bug wirklich rot wird | `EBT(..., expect=False)` auf dem Soll-Vertrag | [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) |
| Mehrere Bedingungen gleichzeitig oder alternative Routen | `{"quantor": "all" \| "exists", "states": ...}` | [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md) |

---

---

## 2. Die gefährlichste Falle der Qualitätssicherung: Charakterisierung ( $Q_{\text{Ist}}$ ) vs. Spezifikation ( $Q_{\text{Soll}}$ )

Eine der wichtigsten Erfahrungen aus der praktischen Arbeit mit Test-Suiten – gerade nach explorativen Analysen – betrifft den Unterschied zwischen **Beobachtung ( $Q_{\text{Ist}}$ )** und **Gesetz ( $Q_{\text{Soll}}$ )** sowie den Grundsatz: **Ein einmal richtig eingestellter Prüffall wird nicht mehr manipuliert.**

Wenn wir bestehenden Code explorativ auf Randfälle abklopfen, beobachten wir zunächst das tatsächliche Ist-Verhalten des Systems. Übernimmt man dieses beobachtete Verhalten in die Test-Suite, obwohl es sich um einen Bug handelt, entsteht ein **Fehler in der Test-Suite selbst**: Weil `WorldState` standardmäßig `expect=True` setzt, wird das beobachtete Fehlersymptom fälschlicherweise als erwünschter Zustand deklariert.

Die Folgen eines solchen Fehlers in der Test-Suite sind gravierend:

* **Falscher Erfolg (False Positive):** Die Test-Suite leuchtet komplett grün (`PASSED`), obwohl der Defekt mitten im System steckt.
* **Blockierte Reparatur:** Sobald der Bug im Produktionscode behoben wird, schlägt der fehlerhaft eingestellte Test rot fehl, weil er den Bug verteidigt.

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

### Schritt 4: Prüffälle einmalig fixieren & Red-Phase prüfen
Jeder Prüffall wird vor der Code-Änderung einmalig sauber eingestellt – entweder als positives Soll-Gesetz (`expect=True`) oder, falls ein exploratives Szenario das Fehlersymptom selbst abbildet, durch Setzen von `expect=False`. Sobald dieser Prüffall steht und gegen den ungefixten Code rot anschlägt, wird der Test selbst nicht mehr verändert.

### Schritt 5: Orthogonale Reparatur & Stil-Verifikation
Bei der anschließenden Reparatur im Quellcode gilt das Gesetz der Orthogonalität: Ein struktureller Fehler darf statische Regeln nicht blind abschalten, und eine benutzerdefinierte Regel darf wichtige Standard-Checks nicht unbemerkt verdrängen. Den Abschluss bildet der Lauf über alle Ebenen (`pytest`, `AstLinter`/`CstLinter` und `DocEnsurance`).

---

## 4. Methodische Ehrlichkeit: Beobachtung, Abdeckung und Beweis

Gute Ingenieurskunst zeichnet sich dadurch aus, dass sie die Leistungsfähigkeit ihrer Werkzeuge kennt – aber ihre Aussagen niemals überdehnt. Auch eine zu 100 % grüne Test-Suite unterliegt klaren erkenntnistheoretischen Grenzen:

* **Beobachtete Konformität statt Allgemeinbeweis:** Ein bestandener `EBT`- oder `DocEnsurance`-Lauf zeigt, dass die konkret ausgeführten Beispiele unter den jeweiligen Testbedingungen zu den deklarierten Sollmustern passen. Er ist eine starke empirische Evidenz gegen Regressionen, ersetzt aber keinen mathematischen Korrektheitsbeweis über alle denkbaren Eingaben aus $\Sigma^*$.
* **Die Hoare-Analogie $\{P\}\ S\ \{Q\}$ als Strukturmodell:** Die Anordnung `pre` ( $\{P\}$ ), `target` ( $S$ ) und `post` ( $\{Q\}$ ) in `EBT` ist eine bewusste architektonische und didaktische Analogie zum Hoare-Tripel. Ein `WorldState` ist dabei ein konkreter Datensatz oder ein Prädikat-Muster, und die Auswertung prüft endliche, explizite Zustandslisten: Jeder ausgeführte Eingang aus `pre` muss mindestens einen positiven Zustand aus `post` (`expect=True`) erfüllen und darf keinen negativen Zustand (`expect=False`) verletzen. Details regelt die [Vertragssemantik](GUIDE_Contract-Semantics.md).
* **Vielfalt von Beispielen vs. formale Abdeckung:** Unterschiedliche Beispiele aus verschiedenen Äquivalenzklassen verbessern die praktische Abdeckung erheblich; ihre bloße Anzahl belegt jedoch noch keine mathematische Orthogonalität unabhängiger Merkmalsdimensionen und verhindert für sich genommen kein Overfitting.
* **Einordnung von Reviews (`RBT`):** `RBT` übergibt eine sprachliche Prüfregel und eine Zielbezeichnung an einen menschlichen oder automatisierten Reviewer (`HeadlessReviewer`, `HumanReviewer` oder eigene `Reviewer`-Implementierungen). Ein positives Review dokumentiert ein qualifiziertes Urteil zum Prüfzeitpunkt, misst aber keine Laufzeit- oder Speicherbudgets automatisch.
* **Isolations- statt Sicherheitsgrenze bei Arenen:** `TempFS` und `PyVenv` schützen hervorragend vor versehentlicher Verschmutzung des Arbeitsverzeichnisses und vor ungewollten Paket-Leaks aus der Host-Umgebung. Sie bilden jedoch keine Betriebssystem-Sandbox gegen aktiv schädlichen Code – führe in Arenen daher nur vertrauenswürdigen Projekt- und Testcode aus.

---

## 5. Herzliche Empfehlungen für den QA-Alltag

Zum Abschluss einige persönliche Leitlinien, die sich in der täglichen Arbeit mit Cubie immer wieder auszahlen:

1. **Einmal richtig eingestellte Prüffälle sind unantastbar:** Ein korrekt spezifizierter Prüffall wird zwischen Red- und Green-Phase niemals umgebaut. Nur wenn in der Test-Suite selbst ein Fehler auffällt – etwa weil ein explorativer Test ein Fehlersymptom versehentlich als gültig (`expect=True`) aufgezeichnet hat –, dreht man die Erwartung an diesem `WorldState` über `expect=False` um, ohne das Szenario selbst anzufassen.
2. **Halte Code-Beispiele in der Doku klein und fokussiert:** Wenn ein Beispiel im Guide mehr als 30 Zeilen benötigt (`DOC-HIGH-COMPLEXITY`), teile es über `session=<id>` in logische Zwischenschritte mit erklärendem Text auf und gib in jedem Schritt ein kurzes, sprechendes Zwischenergebnis mit `print(...)` aus.
3. **Nutze Warnungen als konstruktiven Kompass – aber verwechsle sie nicht mit harten Gates:** Mit `severity="warning"` lassen sich didaktische Hinweise (wie `NoOutput`, `LargeOutput` oder `RawTraceback` in `CUBIE_DOC_RULES`) sanft einführen, ohne sofort den Build zu brechen. Bedenke dabei jedoch: Eine `UserWarning` lässt `pytest` weiterhin grün (`Exit-Code 0`) und fällt in Kurz- oder IDE-Ausgaben leicht durchs Raster. Regeln, die verlässlich blockieren müssen (wie `HighComplexity` ab $> 30$ Zeilen), gehören deshalb explizit auf `severity="error"` – und genau dieser Unterschied sollte durch einen eigenen Blackbox-`EBT`-Test in der Red-Phase abgesichert werden (`expect=False` auf dem stillen Durchlauf).
4. **Schreibe Fehlermeldungen für dein zukünftiges Ich:** Ein `STATE-GUARD` mit einer klaren Aussage, *welcher* Parameter *warum* abgewiesen wurde und *was* stattdessen erwartet wird, spart beim Debugging Stunden an Suchzeit.
5. **Lass die Werkzeuge für dich arbeiten:** Kombiniere `EBT` für die Fachlogik, `AstLinter`/`CstLinter` für die Code-Hygiene und `DocEnsurance` für deine Markdown-Guides – dann bleibt deine Dokumentation genauso lebendig und verlässlich wie dein Code.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](./GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
