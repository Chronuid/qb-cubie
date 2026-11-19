<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Erwartungssteuerung & Safety (`expect`-Flags)

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch beschreibt den gezielten Einsatz von `expect=True` und `expect=False` auf `WorldState`- und `EBT`-Ebene: Wie man Soll-Ziele und Negativ-Filter im selben `post` kombiniert, kaputte grüne Tests ehrlich rot macht, Red-Phase-Gegenproben schreibt und die gefährliche „einsame Negation“ (*Vacuous Pass*) vermeidet. Die formalen Auswertungsregeln definiert die [Vertragssemantik](GUIDE_Contract-Semantics.md).

---

> [!Note]  
> Dieses Handbuch zur Qualitätssicherung befindet sich derzeit unter aktiver Mutation und Überarbeitung und könnte daher Fehler, Unvollständigkeiten oder veraltete Angaben enthalten.

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Zwei Ebenen für `expect` (Standardwert: `True`)

In Cubie existiert das explizite Flag `expect` (Standardwert jeweils `True`) auf **zwei unterschiedlichen Ebenen**, die sich sauber ergänzen – ganz ohne zusätzliche Sonder-Tags:

| Ebene | Bedeutung von `expect=True` (Standard) | Bedeutung von `expect=False` | Typischer Einsatz |
| :--- | :--- | :--- | :--- |
| **`WorldState(..., expect=...)`** (in `post`) | **Erlaubtes Zielmuster ($Q^+$):** Mindestens ein positives Muster muss zutreffen. | **Verbotenes Muster ($Q^-$):** Dieses Muster darf **nicht** zutreffen. | Ein positives Soll-Ergebnis fordern und gleichzeitig gefährliche Rückgaben explizit ausschließen (oder bewusst eine reine Negativ-Invariante markieren). |
| **`EBT(..., expect=...)`** (auf dem Vertrag) | Der gesamte `EBT`-Lauf muss bestehen (`evaluation == lauf_ok`). | Kehrt das Gesamtergebnis um (`evaluation == not lauf_ok`). | Red-Phase-Nachweise und Gegenproben: beweisen, dass ein Vertrag bei einem bekannten Fehler tatsächlich rot anschlägt. |

Die Auswertungsregel für jeden Schritt aus `pre` lautet dabei: **Mindestens ein** positives Muster ($Q^+$) muss passen *(falls welche angegeben sind)* **und kein** negatives Muster ($Q^-$) darf verletzt werden (siehe [Vertragssemantik](GUIDE_Contract-Semantics.md#endliche-auswertungsregel)). Beachte außerdem: `pre.expect` steuert die EBT-Auswertung nicht, und `EBT(..., expect=False)` fängt unbehandelte Target-Exceptions nicht ab – dafür dient `post=WorldState(raises=...)`.

---

## 2. Best Practice 1: Soll-Ziel und Negativ-Filter im selben `post`

Am saubersten kombiniert man im normalen Fachtest ein positives Soll-Muster (`expect=True`) mit einem gezielten Verbot (`expect=False`). So ist sowohl festgelegt, **was** herauskommen muss, als auch, **was** unter keinen Umständen passieren darf:

```python
from qb_cubie import EBT, WorldState


def apply_discount(price: int, coupon: str) -> int:
    return price - 15 if coupon == "SAVE15" else price


trace = EBT(
    target=apply_discount,
    pre=WorldState(args=(100, "SAVE15")),
    post=[
        WorldState(returns=85),
        WorldState(returns=lambda value: value < 0, expect=False),
    ]
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

Stell dir vor, in deiner Test-Suite hat sich ein Fehler eingeschlichen: Eine kaputte Funktion (die `-10` statt eines Rabatts zurückgibt) wurde versehentlich als gültiges Verhalten aufgezeichnet (`expect=True`) – ein klassischer Fall von beobachtetem Ist-Verhalten ($Q_{\text{Ist}}$) statt fachlichem Soll-Gesetz ($Q_{\text{Soll}}$), wie im [QA-Handbuch](GUIDE_Quality-Assurance.md#2-die-gefährlichste-falle-der-qualitätssicherung-charakterisierung-q_ist-vs-spezifikation-q_soll) erklärt. Die Test-Suite leuchtet also trügerisch **grün**, obwohl ein Bug im Code steckt.

Statt das Szenario komplett neu zu schreiben, drehst du die Erwartung an diesem `WorldState` über `expect=False` um und ergänzt das positive Soll-Gesetz:

1. **Der Test wird ehrlich rot:** Da `-10` nun als verbotenes Muster gilt und gleichzeitig ein gültiger Preis $\ge 0$ gefordert wird, schlägt der Test gegen den fehlerhaften Code sofort fehl.
2. **Der Fix macht ihn grün:** Sobald du den Bug im Quellcode behebst (sodass ein gültiger Preis $\ge 0$ zurückkommt), wird der rote Test automatisch **grün**.

Im folgenden Beispiel wird das versehentlich aufgezeichnete Bug-Symptom `-10` mit `expect=False` verboten und um das Soll-Gesetz (`value >= 0`) ergänzt (mit `reporter=None`, damit wir `trace.evaluation == False` hier direkt ausgeben können, ohne dass `PytestReporter` einen `AssertionError` wirft):

```python
from qb_cubie import EBT, WorldState


def buggy_discount(price: int) -> int:
    return -10  # Bug: negativer Preis statt Rabatt


# Vorher stand hier versehentlich WorldState(returns=-10) mit expect=True (Test war fälschlicherweise grün).
# Mit expect=False verbieten wir das Bug-Symptom und sichern das Soll-Gesetz ab – der Test wird ehrlich rot:
trace = EBT(
    target=buggy_discount,
    pre=WorldState(args=100),
    post=[
        WorldState(returns=lambda value: value >= 0),  # Eigentliches Soll-Gesetz
        WorldState(returns=-10, expect=False),          # Verbotenes Bug-Symptom
    ],
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

* **Der Nutzen:** Du musst den Testfall nicht verwerfen, wenn er ein Fehlersymptom aufgezeichnet hat. Durch `expect=False` am betroffenen `WorldState` (zusammen mit dem positiven Soll-Ziel, um einen *Vacuous Pass* auszuschließen) wird die Test-Suite sofort ehrlich rot (`False`) – und sobald der Produktionscode repariert ist, springt genau dieser Test auf grün (`True`).

---

## 4. Best Practice 3: Red-Phase-Gegenproben mit `EBT(..., expect=False)`

Wenn du beweisen möchtest, dass ein bestehender Vertrag einen bestimmten Defekt tatsächlich abfängt – etwa in der Red-Phase von Test-Guided Development (TGD), wenn bei ungültigen Eingaben noch ein `STATE-GUARD` fehlt –, bleibt dein `post`-Zustand das gewünschte Soll-Gesetz (`expect=True`), und du kehrst die Gesamtauswertung über `expect=False` am `EBT`-Aufruf selbst um:

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

Gefährlich wird `WorldState(..., expect=False)` immer dann, wenn in `post` **ausschließlich** Verbote stehen und das positive Soll-Ziel (`expect=True`) vergessen wurde. Weil bei leerem $Q^+$ der positive Teil automatisch als erfüllt gilt, besteht ein kaputtes Target diesen Test trotzdem grün – sobald man ein positives Soll-Ziel ergänzt, fliegt der Bug sofort auf:

```python
from qb_cubie import EBT, WorldState


def broken_total(price: int) -> int | None:
    return None  # Bug: liefert None statt eines gültigen Preises


lonely = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post=WorldState(returns=-1, expect=False),
    reporter=None,
).run()

guarded = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post=[WorldState(returns=int), WorldState(returns=-1, expect=False)],
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

* **Merksatz für `expect=False`:** Verbiete mit `WorldState(..., expect=False)` nur zusätzlich zu mindestens einem positiven Ziel (`expect=True`) – oder setze `expect=False` bewusst nur dort allein ein, wo fachlich tatsächlich **nur** ein Verbot gelten soll (z. B. *„darf niemals Wert X zurückgeben“*), und mache dir bewusst, dass alle anderen Werte dann akzeptiert werden.

> [!TIP]
> **Weiterführende Handbücher:** Wie du Verträge eindeutig auf einzelne Wertepaare schneidest, zeigt [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md). Wie du Quantoren gezielt auf `"all"` oder `"exists"` umstellst, erklärt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

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
