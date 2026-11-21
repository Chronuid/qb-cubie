<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Erwartungssteuerung & Safety (`expect`-Flags)

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch beschreibt den gezielten Einsatz von `expect=True` und `expect=False` auf `WorldState`- und `EBT`-Ebene: Wie man Soll-Ziele und Negativ-Filter in einem konjunktiven `post={"quantor": "all", ...}`-Vertrag kombiniert, kaputte grüne Tests ehrlich rot macht, Red-Phase-Gegenproben schreibt und die gefährliche „einsame Negation“ (*Vacuous Pass*) vermeidet. Die formalen Auswertungsregeln definiert die [Vertragssemantik](core/GUIDE_Contract-Semantics.md).

---

> [!Note]  
> Dieses Handbuch zur Qualitätssicherung befindet sich derzeit unter aktiver Mutation und Überarbeitung und könnte daher Fehler, Unvollständigkeiten oder veraltete Angaben enthalten.

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Zwei Ebenen für `expect` (Standardwert: `True`)

**Einfach erklärt (für Einsteiger):** Beim Testen möchtest du manchmal sagen: *„Genau dieses Ergebnis wünsche ich mir“* (`expect=True`, der Standard). Manchmal möchtest du aber auch das Gegenteil ausdrücken: *„Dieser gefährliche Wert darf auf keinen Fall herauskommen!“* oder *„Dieser ganze Testlauf muss bei einem Fehler rot anschlagen!“* Dafür nutzt du den Schalter `expect=False`. In Python sind `True` (*Wahr / Ja*) und `False` (*Falsch / Nein*) die beiden einzigen echten Wahrheitswerte (`bool`).

In Cubie existiert das Flag `expect` (Standardwert jeweils `True`) auf **zwei klar getrennten Ebenen**, die niemals die Quantoren (`"all"` oder `"exists"`) heimlich umschreiben:

| Ebene | Bedeutung von `expect=True` (Standard) | Bedeutung von `expect=False` | Typischer Einsatz & Quantor-Regel |
| :--- | :--- | :--- | :--- |
| **`WorldState(..., expect=...)`** (in `post`) | **Gefordertes / erlaubtes Zielmuster:** Alle in diesem `WorldState` angegebenen Prüfungen müssen zutreffen (`sat(q) = match(q)`). | **Verbotenes Muster (Negativ-Filter):** Dieses Muster darf **nicht** zutreffen (`sat(q) = not match(q)`). | Ein positives Soll-Ergebnis fordern und gleichzeitig gefährliche Rückgaben ausschließen. **Zwingend mit `post={"quantor": "all", "states": [...]}` nutzen!** |
| **`EBT(..., expect=...)`** (auf dem Vertrag) | Der gesamte `EBT`-Lauf muss bestehen (`evaluation == lauf_ok`). | Kehrt das fertige Gesamtergebnis am Ende um (`evaluation == not lauf_ok`). | Red-Phase-Nachweise und Gegenproben: beweisen, dass ein Soll-Vertrag bei einem bekannten Fehler tatsächlich rot anschlägt. |

### Warum `WorldState(..., expect=False)` immer `post={"quantor": "all", ...}` erfordert

Standardmäßig prüft `post` nach der **ODER-Regel** (`post_quantor="exists"`): Es reicht, wenn *mindestens ein* Zustand aus `post` erfüllt ist. Ein Verbot (`expect=False`) in einer solchen ODER-Liste wäre jedoch eine logische Falle:

* **Einfach erklärt (Die Türsteher-ODER-Falle):** Stell dir vor, du gibst einem Türsteher eine **ODER-Liste** (`"exists"`): *„Einlass, wenn das Ergebnis eine ganze Zahl ist **ODER** wenn es nicht `99` ist.“*
  * Kommt jetzt die verbotene Zahl `99` heraus, stimmt zwar die zweite Bedingung nicht – aber die erste Bedingung (*„ist eine ganze Zahl“*) stimmt! Weil bei **ODER** ein einziger Treffer genügt, winkt der Türsteher die verbotene `99` einfach grün durch.
  * Kommt stattdessen ein völlig kaputter Wert wie `"absturz"` oder `None` heraus, stimmt die zweite Bedingung (*„ist nicht `99`“*) – und der Türsteher winkt auch diesen Fehler grün durch!
  * Damit ein Soll-Ziel **und** ein Verbot gemeinsam wirken (*„Muss eine ganze Zahl sein **UND** darf nicht `99` sein“*), brauchst du zwingend eine **UND-Checkliste**: `post={"quantor": "all", "states": [...]}`.
* **Für Experten (Prädikatenlogik & Tautologie-Schutz):** Unter dem Existenzquantor ($\exists q \in Q : \text{sat}(q, y)$) erzeugt jedes Verbot $q^-$ innerhalb des positiven Zielbereichs ($\{y \mid m(q^-, y)\} \subseteq \{y \mid m(q^+, y)\}$) die unbedingte Tautologie $m(q^+, y) \lor \neg m(q^-, y) \equiv \top$ für alle $y \in \text{Any}$ (bzw. bei disjunktem Sollwert dessen logische Subsumtion). Unter dem Allquantor ($\forall q \in Q : \text{sat}(q, y)$) hingegen wirkt dieselbe Formel als reine Konjunktion $(\forall q \in Q^+ : m(q, y)) \land (\forall q \in Q^- : \neg m(q, y))$, ohne dass `expect=False` jemals das Quantor-Verhalten überschreibt.

> [!IMPORTANT]
> **Drei harte `STATE-GUARD`-Schutzregeln im Cubie-Core:**
> 1. **Kein `WorldState(expect=False)` unter `post="exists"`:** Übergibst du `WorldState(..., expect=False)` im Standard-`post` (oder unter explizitem `"quantor": "exists"`), bricht Cubie sofort vor der Target-Ausführung mit `ValueError("STATE-GUARD: ...")` ab.
> 2. **Kein `WorldState(expect=False)` in `pre`:** Vorbedingungen beschreiben Eingaben, die ausgeführt werden sollen – kein Verbot. `pre` mit `expect=False` wird ebenfalls sofort mit `ValueError("STATE-GUARD: ...")` abgewiesen.
> 3. **Strikt nur echte `bool`-Werte (`True` oder `False`):** Sowohl `WorldState.expect` als auch `EBT.expect` lehnen `None` (*„Nichts“*), Zahlen wie `0` oder `1` (in Python ist `bool` technisch eine Unterklasse von `int`!) oder Strings sofort mit `TypeError("STATE-GUARD: ...")` ab. Außerdem fängt `EBT(..., expect=False)` keine unbehandelten Target-Exceptions (Programm-Abstürze) ab – dafür dient `post=WorldState(raises=...)`.

---

## 2. Best Practice 1: Soll-Ziel und Negativ-Filter im selben `post`

Wenn du in einem Fachtest sowohl festlegen möchtest, **was** herauskommen muss (`expect=True`), als auch, **was** unter keinen Umständen passieren darf (`expect=False`), packst du beide `WorldState`-Einträge in eine explizite **UND-Checkliste** (`post={"quantor": "all", "states": [...]}`).

* **Python-Lesehilfe für Einsteiger:**
  * Das geschweifte Klammerpaar `{"quantor": "all", "states": [...]}` ist ein Python-**Dictionary** (wie ein kleines Formular mit zwei beschrifteten Feldern: `"quantor": "all"` schaltet auf den UND-Modus um, und `"states"` enthält die Liste der Prüfregeln).
  * `lambda value: value < 0` ist eine einzeilige Mini-Prüffunktion in Python: Sie nimmt das beobachtete Ergebnis (`value`) entgegen und prüft, ob es kleiner als `0` (also ein negativer Preis) ist. Zusammen mit `expect=False` bedeutet das: *„Ein Ergebnis `< 0` ist verboten!“*

Im folgenden Beispiel zieht `apply_discount` mit dem Gutschein `"SAVE15"` genau `15` vom Preis `100` ab (`85`), während negative Preise ausdrücklich verboten sind:

```python
from qb_cubie import EBT, WorldState


def apply_discount(price: int, coupon: str) -> int:
    return price - 15 if coupon == "SAVE15" else price


trace = EBT(
    target=apply_discount,
    pre=WorldState(args=(100, "SAVE15")),
    post={
        "quantor": "all",
        "states": [
            WorldState(returns=85),
            WorldState(returns=lambda value: value < 0, expect=False),
        ],
    },
).run()

print(f"Rabatt-Vertrag erfüllt: {trace.evaluation} | Beobachtet: {trace.traces[0].outcome.returns}")
```

<details>
<summary>Ergebnis</summary>

```text
Rabatt-Vertrag erfüllt: True | Beobachtet: 85
```
</details>

---

## 3. Best Practice 2: Ehrlich-roter Bug-Nachweis (kaputte Tests reparieren)

Stell dir vor, beim Ausprobieren einer Funktion hat sich ein Fehler in deine Test-Suite eingeschlichen: Eine kaputte Rabatt-Funktion gibt fälschlicherweise `-10` zurück, und jemand hat diesen kaputten Wert `-10` versehentlich mit dem Standard `expect=True` als „gewünschtes Ergebnis“ in den Test geschrieben. In der Qualitätssicherung nennt man das eine ungeprüfte **Beobachtung des Ist-Zustands ($Q_{\text{Ist}}$)** statt einer echten **Soll-Vorgabe ($Q_{\text{Soll}}$)** (mehr dazu im [QA-Handbuch](GUIDE_Quality-Assurance.md#2-die-gefährlichste-falle-der-qualitätssicherung-charakterisierung-q_ist-vs-spezifikation-q_soll)). Die Folge: Dein Test leuchtet trügerisch **grün**, obwohl der Code kaputt ist!

Statt den Testfall wegzuwerfen, reparierst du ihn in drei klaren Schritten:

1. **Bug-Symptom verbieten:** Du setzt an dem aufgezeichneten Fehlzustand `WorldState(returns=-10, expect=False)`.
2. **Positives Soll-Gesetz ergänzen:** Du fügst das echte fachliche Ziel hinzu, etwa `WorldState(returns=lambda value: value >= 0)` (*„Der Preis muss mindestens 0 sein“*).
3. **Unter `"quantor": "all"` bündeln:** Da beide Regeln gleichzeitig gelten müssen, verpackst du sie in `post={"quantor": "all", "states": [...]}`.

* **Was dadurch passiert (TGD Red-to-Green):**
  * **Sofort ehrlich rot (Red-Phase):** Solange der Bug (`-10`) noch im Code steckt, schlägt der Test jetzt zuverlässig fehl (`trace.evaluation == False`).
  * **Automatisch grün nach der Reparatur (Green-Phase):** Sobald du `buggy_discount` im Quellcode reparierst (z. B. `return price - 15`), erfüllt das Ergebnis `85` sowohl `value >= 0` als auch `!= -10` – und derselbe Test wird ohne weitere Änderung **grün (`True`)**!

Im folgenden Beispiel nutzen wir `reporter=None` (dadurch gibt Cubie das Prüfergebnis `trace.evaluation` direkt als `False` zurück, statt den Lauf sofort mit einem `pytest`-Fehler abzubrechen):

```python
from qb_cubie import EBT, WorldState


def buggy_discount(price: int) -> int:
    return -10  # Bug: negativer Preis statt Rabatt


# Mit "quantor": "all" und expect=False verbieten wir das Bug-Symptom (-10)
# und fordern gleichzeitig das Soll-Gesetz (value >= 0) – der Test wird ehrlich rot:
trace = EBT(
    target=buggy_discount,
    pre=WorldState(args=100),
    post={
        "quantor": "all",
        "states": [
            WorldState(returns=lambda value: value >= 0),  # Eigentliches Soll-Gesetz
            WorldState(returns=-10, expect=False),          # Verbotenes Bug-Symptom
        ],
    },
    reporter=None,
).run()

print(f"Test schlägt gegen den Bug an (ehrlich rot): {trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Test schlägt gegen den Bug an (ehrlich rot): False
```
</details>

* **Der Nutzen:** Du bewahrst das konkrete Fehlerszenario (`returns=-10`) als dauerhaftes Schutzschild (Regressions-Wächter) in deinem Vertrag, während das positive Soll-Ziel (`value >= 0`) sicherstellt, dass die Funktion nach dem Fix auch wirklich einen gültigen Preis liefert.

---

## 4. Best Practice 3: Red-Phase-Gegenproben mit `EBT(..., expect=False)`

Manchmal möchtest du nicht bloß einen einzelnen Rückgabewert verbieten, sondern beweisen, dass ein **kompletter Soll-Vertrag** bei einem noch fehlenden Schutzmechanismus tatsächlich Alarm schlägt (eine sogenannte **Red-Phase-Gegenprobe** im Test-Guided Development):

* **Einfach erklärt (für Einsteiger):** Wenn jemand eine Funktion `configure_timeout(-5)` mit einer unsinnigen negativen Sekundenzahl aufruft, soll die Funktion in Python kontrolliert mit einem Fehler-Alarm (`ValueError`) stoppen, dessen Fehlermeldung das Wort `"positive"` enthält. Diesen gewünschten Fehler-Alarm beschreibt man in Cubie mit `ExceptionExpectation(ValueError, match=r"positive")`.
* Solange dieser Schutz (`STATE-GUARD`) in der Funktion aber noch **fehlt** (Red-Phase), läuft `-5` einfach durch und der Soll-Vertrag scheitert.

Setzt du nun `expect=False` außen auf **`EBT(..., expect=False)`**, sagst du zu Cubie: *„Ich erwarte, dass dieser Soll-Vertrag gegen den unfertigen Code noch scheitert!“* Da `post` hier nur ein einziges positives Ziel (`expect=True`) enthält, ist kein `"quantor": "all"` nötig:

```python
from qb_cubie import EBT, ExceptionExpectation, WorldState


def configure_timeout(seconds: int) -> int:
    return seconds  # Red-Phase: STATE-GUARD fehlt noch, -5 läuft still durch


trace = EBT(
    target=configure_timeout,
    pre=WorldState(args=-5),
    post=WorldState(raises=ExceptionExpectation(ValueError, match=r"positive")),
    expect=False,
).run()

print(f"Fehlender STATE-GUARD in der Red-Phase erkannt: {trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Fehlender STATE-GUARD in der Red-Phase erkannt: True
```
</details>

> [!TIP]
> **Kein Extra-Tag für Negativ-Invarianten nötig:** Das Flag `expect=False` drückt bereits explizit aus, dass ein Zustand verboten (`WorldState(..., expect=False)`) oder ein Vertrag als erwartetes Scheitern (`EBT(..., expect=False)`) gemeint ist. Vermeide lediglich die unabsichtliche **Doppel-Negation** (`WorldState(..., expect=False)` kombiniert mit `EBT(..., expect=False)`) außerhalb von Engine-Tests, da „nicht (nicht verboten)“ für Leser schwer zu durchschauen ist.

---

## 5. Anti-Pattern: Die „einsame Negation“ (*Vacuous Pass*)

Was passiert, wenn man in einem Test **nur** hinschreibt, was *nicht* herauskommen darf (`expect=False`), aber komplett vergisst anzugeben, was *eigentlich* herauskommen soll (`expect=True`)?

In der Qualitätssicherung nennt man das eine **„einsame Negation“** (*Lonely Negation*), und sie führt zu einem sogenannten **Vacuous Pass** (auf Deutsch: *„leerer Durchmarsch“*):

* **Einfach erklärt (für Einsteiger):** Stell dir vor, du bestellst im Restaurant eine warme Suppe, schreibst auf deinen Prüfzettel für die Küche aber nur die einzige Regel: *„Es darf kein Stein auf dem Teller liegen (`returns=-1, expect=False`).“* Wenn der Kellner dir jetzt einen komplett **leeren Teller** (`None` – in Python das Wort für *„Nichts / leer“*) hinstellt, liegt darauf tatsächlich kein Stein. Dein Test prüft: *„Ist `None` ungleich `-1`?“* – sagt *„Ja, stimmt!“* und leuchtet **grün (`True`)**, obwohl du überhaupt keine Suppe bekommen hast!
* **Zweistufiger Schutz in Cubie (für Einsteiger & Experten):**
  1. **Stufe 1 — Laufzeit-`STATE-GUARD` bei `post="exists"`:** Wenn du `post=WorldState(returns=-1, expect=False)` ohne `"quantor": "all"` schreibst, stoppt Cubie dich sofort vor dem Start mit einem `ValueError("STATE-GUARD: ...")`.
  2. **Stufe 2 — Positives Anker-Ziel in `post={"quantor": "all", ...}` (+ statisches Meta-Gate 3):** Selbst wenn du `post={"quantor": "all", "states": WorldState(returns=-1, expect=False)}` schreibst, bleibt ein einzelnes Verbot ohne positives Ziel (`lonely`) blind gegenüber völlig falschen Rückgaben wie `None` ($\forall q \in \{q^-\} : \neg m(q, \text{None}) \equiv \top$). Erst wenn du mindestens ein positives Soll-Ziel wie `WorldState(returns=int)` (*„Muss eine ganze Zahl sein“*) in dieselbe `"all"`-Liste aufnimmst (`guarded`), fliegt das kaputte `None` sofort auf (`False`). In Cubies eigener Test-Suite spürt zusätzlich der statische Code-Wächter **Meta-Gate 3 (`META-EBT-LONELY-NEGATION`)** solche einsamen Negationen automatisch auf.

Das folgende Beispiel stellt die „einsame Negation“ (`lonely`, trügerisch `True`) und den sauber verankerten Vertrag mit positivem Typ-Ziel (`guarded`, erkennt den `None`-Bug als `False`) unter `post={"quantor": "all", ...}` direkt gegenüber:

```python
from qb_cubie import EBT, WorldState


def broken_total(price: int) -> int | None:
    return None  # Bug: liefert None ("Nichts") statt eines gültigen Preises


lonely = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post={"quantor": "all", "states": WorldState(returns=-1, expect=False)},
    reporter=None,
).run()

guarded = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post={
        "quantor": "all",
        "states": [WorldState(returns=int), WorldState(returns=-1, expect=False)],
    },
    reporter=None,
).run()

print(f"Nur Verbot (Vacuous Pass): {lonely.evaluation} | Mit Positiv-Ziel: {guarded.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Nur Verbot (Vacuous Pass): True | Mit Positiv-Ziel: False
```
</details>

* **Merksatz für `expect=False`:** Nutze `WorldState(..., expect=False)` immer innerhalb von `post={"quantor": "all", "states": [...]}` und kombiniere es dort mit mindestens einem positiven Soll-Ziel (`expect=True`, z. B. Typ, Wertebereich oder Struktur), damit dein Vertrag nicht durch einen *Vacuous Pass* blind für andere Fehler wird.

> [!TIP]
> **Weiterführende Handbücher:** Wie du Verträge eindeutig auf einzelne Wertepaare schneidest, zeigt [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md). Wie du die Quantoren `"all"` und `"exists"` sowie ihren Lebenszyklus bei wiederholten Läufen steuerst, erklärt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Den vollständigen Ablauf für Red-Phase-Gegenproben, Test-Freeze und `GREEN_AUDIT` beschreibt [Test-Guided Development (TGD)](GUIDE_TGD.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

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
