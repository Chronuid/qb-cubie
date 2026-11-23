<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->
<div align="center">

# Qualitätssicherung mit Cubie

![Cubie](.assets/cubie-banner.png)

**Ein Handbuch für Einsteiger und Experten zu deklarativen Verträgen, Test-Guided Development (TGD) und lebendiger Verifikation.**

Cubie bündelt beispielbasierte Verhaltensverträge (`EBT`), isolierte Ausführungs-Arenen (`TempFS`, `PyVenv`), statische Syntaxbaum-Analysen (`AstLinter`, `CstLinter`, `Pylint`, `MyPy`), selbstverifizierende Dokumentation (`DocEnsurance`) und strukturierte Reviews (`RBT`) unter einer gemeinsamen Orchestrierung. Für die exakten Auswertungsregeln bildet die [Vertragssemantik](core/GUIDE_Contract-Semantics.md) die technische Referenz.

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

**Kurz erklärt für Programmier- und Python-Einsteiger:**
* **`def double(x: int) -> int:`** definiert in Python eine **Funktion** (wie eine kleine Küchenmaschine): Oben wirfst du eine ganze Zahl `x` (`int`) hinein, drinnen rechnet sie `x * 2`, und mit **`return`** gibt sie das fertige Ergebnis zurück.
* **`WorldState(...)`** ist dein **Wunschzettel (Zustandsbeschreibung)**: In **`pre=WorldState(args=3)`** steht, welches Argument (`args=3`) wir oben in die Funktion hineinstecken. In **`post=WorldState(returns=6)`** steht, welchen Rückgabewert (`returns=6`) wir unten erwarten.
* **`EBT(...).run()`** führt den Vertrag aus und gibt das Prüfprotokoll **`trace`** zurück. Darin zeigt **`trace.evaluation`** als Wahrheitswert (`True` = bestanden, `False` = durchgefallen), ob der Vertrag eingehalten wurde.

Damit Verträge auch bei mehreren Testfällen, Verboten und komplexeren Regeln verlässlich bleiben, baut Cubie auf drei einfachen Grundbausteinen auf:

### Baustein A: Klare Paare statt Mischmasch (Eindeutigkeit & Kopplung)

Wenn du mehrere Wertepaare prüfen willst (zum Beispiel `3 -> 6` und `5 -> 10`), gib **jedem Paar seinen eigenen Vertrag** – entweder als eigene Test-Funktion oder kompakt mit `@pytest.mark.parametrize`.

* **Die häufigste Einsteiger-Falle:** Schreibst du `[3, 5]` gemeinsam in `pre` und `[6, 10]` gemeinsam in `post`, ordnet Cubie die Listen **nicht** paarweise zu (`3 -> 6`, `5 -> 10`). Stattdessen wird *jeder* Eingang gegen *jedes* Ergebnis geprüft ($2 \times 2 = 4$ Prüfungen). Dann bestünde sogar eine kaputte Funktion, die immer `6` zurückgibt oder die Antworten vertauscht.
* **Einfache Faustregel:** Mehrere Eingänge gehören nur dann zusammen in ein `pre`, wenn für **alle** dasselbe Ziel in `post` gilt (etwa wenn `" TEXT "` und `"TeXt"` beide `"text"` ergeben müssen).

👉 **Ausführliche Beispiele und Anti-Patterns:** [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md)

### Baustein B: Erlaubtes und Verbotenes steuern (`expect`-Flags)

Standardmäßig bedeutet `expect=True`: *„Genau das soll passieren.“* Mit `expect=False` (strikt `bool`: `True` oder `False`) kannst du gezielt sagen, was **nicht** passieren darf – und zwar auf zwei klar getrennten Ebenen, ohne dass jemals ein Quantor heimlich überschrieben wird:

1. **Auf einem `WorldState` in `post` (Verbot unter `"quantor": "all"`):** Du legst fest, was herauskommen muss (`expect=True`), und verbietest gleichzeitig gefährliche Werte (`expect=False`, z. B. negative Preise). Weil Soll-Ziel **und** Verbot gleichzeitig gelten müssen (UND-Checkliste), stehen solche Zustände immer in **`post={"quantor": "all", "states": [...]}`**. Im Standard-ODER-Modus (`post="exists"`) sowie in `pre` blockiert Cubies `STATE-GUARD` jedes `WorldState(..., expect=False)` sofort mit einem `ValueError`.
2. **Auf `EBT(..., expect=False)` (Gegenprobe auf Vertragsebene):** Du kehrst das fertige Gesamtergebnis des gesamten Vertrags am Ende um. So beweist du in der Red-Phase, dass dein Soll-Vertrag bei einem bekannten Fehler tatsächlich anschlägt.

> [!CAUTION]
> **Vorsicht vor der „einsamen Negation“ (*Vacuous Pass*):** Selbst wenn du `post={"quantor": "all", "states": [...]}` nutzt, darfst du darin nicht *nur* Verbote (`expect=False`) ohne mindestens ein positives Soll-Ziel (`expect=True`) angeben. Sonst schlüpfen völlig falsche Rückgaben (wie `None`, also „Nichts“) unbemerkt grün durch, bloß weil sie technisch gesehen nicht der eine verbotene Wert sind.

👉 **Alle Muster, Reparatur-Beispiele und `STATE-GUARD`-Regeln:** [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md)

### Baustein C: „Alle“ oder „mindestens eines“ gezielt wählen (`all` vs. `exists`)

Ohne besondere Angabe arbeitet Cubie nach zwei **reinen Standardregeln**, die durch kein `expect`-Flag heimlich verändert werden:

* In **`pre`** gilt der **reine Allquantor (`"all"` — die UND-Checkliste)**: **Alle** angegebenen Eingänge müssen bestehen.
* In **`post`** gilt der **reine Existenzquantor (`"exists"` — die ODER-Auswahlliste)**: Es reicht, wenn **mindestens ein** angegebenes Zielmuster passt.

Wenn du es andersherum brauchst (oder in `post` ein Verbot mit `expect=False` kombinierst), verpackst du die Zustände explizit in das Dictionary `{"quantor": ..., "states": ...}`:

* **`post` mit `"all"` (UND-Checkliste):** Das Ergebnis muss **alle** Regeln gleichzeitig erfüllen (z. B. *eine ganze Zahl **und** positiv **und** nicht `-10`*).
* **`pre` mit `"exists"` (ODER-Auswahlliste):** Es genügt, wenn **mindestens eine** von mehreren Eingabe-Routen zum Erfolg führt (z. B. Hauptleitung `/main` **oder** Ersatzleitung `/backup` antwortet mit `"ok"`).

👉 **Alle Code-Beispiele, `STATE-GUARD`-Regeln und Lebenszyklus-Details:** [Fortgeschrittene Quantoren (`all` vs. `exists`)](GUIDE_Quantifiers.md)

### Spickzettel für den Einstieg

| Was möchtest du prüfen? | Empfohlenes Mittel | Weiterführendes Handbuch |
| :--- | :--- | :--- |
| Mehrere konkrete Ein-/Ausgabepaare (`3 -> 6`, `5 -> 10`) | Getrennte Verträge oder `@pytest.mark.parametrize` | [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md) |
| Soll-Wert fordern und gefährliche Werte verbieten | `post={"quantor": "all", "states": [WorldState(..., expect=True), WorldState(..., expect=False)]}` | [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) |
| Prüfen, ob ein Vertrag bei einem Bug wirklich rot wird | `EBT(..., expect=False)` auf dem Soll-Vertrag | [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) |
| Mehrere Bedingungen gleichzeitig oder alternative Routen | `{"quantor": "all" \| "exists", "states": ...}` | [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md) |

---

---

## 2. Die gefährlichste Falle der Qualitätssicherung: Charakterisierung ( $Q_{\text{Ist}}$ ) vs. Spezifikation ( $Q_{\text{Soll}}$ )

Eine der wichtigsten Erfahrungen aus der praktischen Arbeit mit Test-Suiten – gerade nach explorativen Analysen – betrifft den Unterschied zwischen **Beobachtung ( $Q_{\text{Ist}}$ )** und **Gesetz ( $Q_{\text{Soll}}$ )** sowie den Grundsatz: **Ein einmal richtig auf $Q_{\text{Soll}}$ eingestellter Prüffall wird in der Green-Phase nicht mehr manipuliert.**

* **Einfach erklärt ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$):**
  * **$Q_{\text{Ist}}$ (Das Foto vom Tatort / Charakterisierung):** Beschreibt, was der Code im Moment *tatsächlich tut* – inklusive seiner Fehler und Eigenheiten.
  * **$Q_{\text{Soll}}$ (Der Bauplan / Spezifikation):** Beschreibt, was der Code *eigentlich tun muss*, damit er fachlich und logisch korrekt arbeitet.
  * **Die Falle:** Wenn man bestehenden Code ausprobiert und das beobachtete Ergebnis ($Q_{\text{Ist}}$) blind mit dem Standard `expect=True` in einen Test kopiert, obwohl darin ein Bug steckt, verteidigt der Test ab sofort den Bug!

Die Folgen eines solchen Fehlers in der Test-Suite sind gravierend:

* **Falscher Erfolg (False Positive):** Die Test-Suite leuchtet komplett grün (`PASSED`), obwohl der Defekt mitten im System steckt.
* **Blockierte Reparatur:** Sobald jemand den Bug im Produktionscode beheben will, schlägt der fehlerhaft auf $Q_{\text{Ist}}$ eingestellte Test rot fehl, weil er das alte Fehlverhalten erzwingt. (Genau das zeigte sich auch bei der Härtung des Cubie-Cores: Mehrere ältere Tests hatten sich darauf verlassen, dass `WorldState(expect=False)` im Standard-`post` heimlich den Existenzquantor überschreibt – erst die Umstellung dieser Tests von der fehlerhaften $Q_{\text{Ist}}$-Gewohnheit auf die explizite $Q_{\text{Soll}}$-Deklaration `post={"quantor": "all", ...}` machte den Weg für die Core-Reparatur frei.)

---

## 3. Test-Guided Development (TGD) im Überblick

**TGD (*Test-Guided Development*)** ist im Kern klassisches **TDD** (*Phase Red* $\to$ *Phase Green*) – mit einer entscheidenden Erweiterung: **Während der Phase Green darfst du das Produkt aus Phase Red hinterfragen.** Weil auch die Qualitätssicherung fehlbar ist (Karl Poppers Epistemologie / Fallibilismus), bietet TGD eine kontrollierte Rückwärtstür statt stillem Test-Umschreiben:

1. **Phase Red (`tests/`):** Soll-Verträge ($Q_{\text{Soll}}$) schärfen, gezielt rot gegen den unreparierten Code nachweisen und die Test-Suite einfrieren.
2. **Phase Green (`src/`) + Rückwärtstür (`GREEN_AUDIT`):** Produktionscode reparieren, bis alle Tests grün laufen – bei striktem Änderungsverbot auf `tests/`. Zeigt sich unterwegs ein Fehler aus der Phase Red, wird er als nachvollziehbarer Befundbericht (`GREEN_AUDIT`) eskaliert, um geordnet zurück in die Phase Red zur Test-Reparatur zu wechseln.
3. **Phase Living-Documentation (`docs/`):** Handbücher und Code-Beispiele (`DocEnsurance` / `DocFrame`) synchronisieren, damit die Dokumentation sauber bleibt und im nächsten Zyklus wieder verlässlich genutzt werden kann.

Bei komplexen Umbauten – insbesondere mit KI-Agenten – können dem Zyklus zwei optionale **Stützräder** vorgeschaltet werden: eine **`ANALYSIS`**-Phase (erst verstehen, was gerade Sache ist) und eine **`HYPOTHESIS`**-Phase in sauberer wissenschaftlicher Sprache (Ideen prüfen und Denkfehler noch vor dem Testbau abfangen).

👉 **Ausführliche Erklärung (Einsteiger & Experten), Stützräder, der bewährte Fünf-Schritte-Ablauf und Orchestrierungs-Tipps:** [Test-Guided Development (TGD)](GUIDE_TGD.md)

---

## 4. Methodische Ehrlichkeit: Beobachtung, Abdeckung und Beweis

Gute Ingenieurskunst zeichnet sich dadurch aus, dass sie die Leistungsfähigkeit ihrer Werkzeuge kennt – aber ihre Aussagen niemals überdehnt. Auch eine zu 100 % grüne Test-Suite unterliegt klaren erkenntnistheoretischen Grenzen:

* **Beobachtete Konformität statt Allgemeinbeweis:** Ein bestandener `EBT`- oder `DocEnsurance`-Lauf zeigt, dass die konkret ausgeführten Beispiele unter den jeweiligen Testbedingungen zu den deklarierten Sollmustern passen. Er ist eine starke empirische Evidenz gegen Regressionen, ersetzt aber keinen mathematischen Korrektheitsbeweis über alle denkbaren Eingaben aus $\Sigma^*$.
* **Die Hoare-Analogie $\{P\}\ S\ \{Q\}$ als Strukturmodell:** Die Anordnung `pre` ( $\{P\}$: *Was stecken wir vorher hinein?* ), `target` ( $S$: *Welche Funktion führen wir aus?* ) und `post` ( $\{Q\}$: *Was muss nachher herauskommen?* ) in `EBT` ist eine bewusste architektonische und didaktische Analogie zum Hoare-Tripel der Informatik. Ein `WorldState` ist dabei ein konkreter Datensatz oder ein Prädikat-Muster, und die Auswertung prüft endliche, explizite Zustandslisten nach reinen Quantoren: Standardmäßig muss jeder ausgeführte Eingang aus `pre` (`pre_quantor="all"`, UND) mindestens einen Zielzustand aus `post` (`post_quantor="exists"`, ODER) erfüllen. Über `{"quantor": "all" | "exists", "states": ...}` lassen sich beide Quantoren explizit umschalten, wobei Verbote (`WorldState(..., expect=False)`) ausschließlich unter `post={"quantor": "all", ...}` zulässig sind. Alle Details regelt die [Vertragssemantik](core/GUIDE_Contract-Semantics.md).
* **Vielfalt von Beispielen vs. formale Abdeckung:** Unterschiedliche Beispiele aus verschiedenen Äquivalenzklassen verbessern die praktische Abdeckung erheblich; ihre bloße Anzahl belegt jedoch noch keine mathematische Orthogonalität unabhängiger Merkmalsdimensionen und verhindert für sich genommen kein Overfitting.
* **Einordnung von Reviews (`RBT`):** `RBT` übergibt eine sprachliche Prüfregel und eine Zielbezeichnung an einen menschlichen oder automatisierten Reviewer (`HeadlessReviewer`, `HumanReviewer` oder eigene `Reviewer`-Implementierungen). Ein positives Review dokumentiert ein qualifiziertes Urteil zum Prüfzeitpunkt, misst aber keine Laufzeit- oder Speicherbudgets automatisch.
* **Isolations- statt Sicherheitsgrenze bei Arenen:** `TempFS` und `PyVenv` schützen hervorragend vor versehentlicher Verschmutzung des Arbeitsverzeichnisses und vor ungewollten Paket-Leaks aus der Host-Umgebung. Sie bilden jedoch keine Betriebssystem-Sandbox gegen aktiv schädlichen Code – führe in Arenen daher nur vertrauenswürdigen Projekt- und Testcode aus.

---

## 5. Herzliche Empfehlungen für den QA-Alltag

Zum Abschluss einige persönliche Leitlinien, die sich in der täglichen Arbeit mit Cubie immer wieder auszahlen:

1. **Einmal richtig eingestellte Prüffälle sind in der Green-Phase unantastbar:** Ein in der Red-Phase auf $Q_{\text{Soll}}$ fixierter Prüffall wird während der Code-Reparatur niemals manipuliert (bei einem vermuteten Test-Widerspruch wird stattdessen ein transparenter Audit-Befund dokumentiert). Und falls vorab ein alter explorativer Test auffällt, der ein Fehlersymptom versehentlich als gültig (`expect=True`) aufgezeichnet hat, dreht man dieses Symptom mit `WorldState(..., expect=False)` um und kombiniert es mit dem positiven Soll-Ziel in `post={"quantor": "all", "states": [...]}` (oder negiert den gesamten Lauf über `EBT(..., expect=False)`).
2. **Halte Code-Beispiele in der Doku klein und fokussiert:** Wenn ein Beispiel im Guide mehr als 30 Zeilen benötigt (`DOC-HIGH-COMPLEXITY`), teile es über `session=<id>` in logische Zwischenschritte mit erklärendem Text auf und gib in jedem Schritt ein kurzes, sprechendes Zwischenergebnis mit `print(...)` aus.
3. **Nutze Warnungen als konstruktiven Kompass – aber verwechsle sie nicht mit harten Gates:** Mit `severity="warning"` lassen sich didaktische Hinweise (wie `NoOutput`, `LargeOutput` oder `RawTraceback` in `CUBIE_DOC_RULES`) sanft einführen, ohne sofort den Build zu brechen. Bedenke dabei jedoch: Eine `UserWarning` lässt `pytest` weiterhin grün (`Exit-Code 0`) und fällt in Kurz- oder IDE-Ausgaben leicht durchs Raster. Regeln, die verlässlich blockieren müssen (wie `HighComplexity` ab $> 30$ Zeilen), gehören deshalb explizit auf `severity="error"` – und genau dieser Unterschied sollte durch einen eigenen Blackbox-`EBT`-Test in der Red-Phase abgesichert werden (`expect=False` auf dem stillen Durchlauf).
4. **Schreibe Fehlermeldungen für dein zukünftiges Ich:** Ein `STATE-GUARD` mit einer klaren Aussage, *welcher* Parameter *warum* abgewiesen wurde und *was* stattdessen erwartet wird, spart beim Debugging Stunden an Suchzeit.
5. **Lass die Werkzeuge für dich arbeiten:** Kombiniere `EBT` für die Fachlogik, `AstLinter`/`CstLinter` für die Code-Hygiene und `DocEnsurance` für deine Markdown-Guides – dann bleibt deine Dokumentation genauso lebendig und verlässlich wie dein Code.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./dev/README.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
