<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Vertragsaufbau: Eindeutigkeit & Kopplung

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch zeigt, wie `EBT`-Verträge eindeutig und wartbar aufgebaut werden: Warum jedes konkrete Ein-/Ausgabepaar einen eigenen Vertrag braucht, wie `@pytest.mark.parametrize` sauber skaliert und wie man Unterspezifikation durch gedankenloses Mischen von `pre`- und `post`-Listen vermeidet. Die formalen Auswertungsregeln stehen in der [Vertragssemantik](GUIDE_Contract-Semantics.md).

---

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Best Practice: Ein Vertrag pro Wertepaar in klaren Test-Funktionen

Am eindeutigsten liest sich ein Test, wenn jedes konkrete Ein-/Ausgabepaar (hier `3 -> 6` und `5 -> 10` für eine einfache Verdopplungsfunktion) einen eigenen `EBT`-Vertrag in einer eigenen Test-Funktion erhält – so wird pro Test exakt ein Paar (insgesamt 2 Paare) geprüft:

```python
from qb_cubie import EBT, WorldState


def double(x: int) -> int:
    return x * 2


def test_double_three() -> None:
    trace = EBT(
        target=double,
        pre=WorldState(args=3),
        post=WorldState(returns=6),
    ).run()
    print(f"3 -> 6:  Vertrag erfüllt: {trace.evaluation} | Geprüfte Paare: {len(trace.traces)}")


def test_double_five() -> None:
    trace = EBT(
        target=double,
        pre=WorldState(args=5),
        post=WorldState(returns=10),
    ).run()
    print(f"5 -> 10: Vertrag erfüllt: {trace.evaluation} | Geprüfte Paare: {len(trace.traces)}")


test_double_three()
test_double_five()
```

<details>
<summary>Ergebnis</summary>

```text
3 -> 6:  Vertrag erfüllt: True | Geprüfte Paare: 1
5 -> 10: Vertrag erfüllt: True | Geprüfte Paare: 1
```
</details>

### Saubere Skalierung mit `@pytest.mark.parametrize`

Möchte man für mehrere zusammengehörige Wertepaare dichteren Code schreiben, ohne die Test-Funktion zu wiederholen, empfiehlt sich `@pytest.mark.parametrize`:

```python
import pytest
from qb_cubie import EBT, WorldState


def double(x: int) -> int:
    return x * 2


@pytest.mark.parametrize(
    "value, expected", [
        (3, 6),
        (5, 10),
    ])
def test_double(value: int, expected: int) -> None:
    trace = EBT(
        target=double,
        pre=WorldState(args=value),
        post=WorldState(returns=expected),
    ).run()
    print(f"{value} -> {expected}: Vertrag erfüllt: {trace.evaluation} | Geprüfte Paare: {len(trace.traces)}")


for val, exp in [(3, 6), (5, 10)]:
    test_double(val, exp)
```

<details>
<summary>Ergebnis</summary>

```text
3 -> 6: Vertrag erfüllt: True | Geprüfte Paare: 1
5 -> 10: Vertrag erfüllt: True | Geprüfte Paare: 1
```
</details>

---

## 2. Anti-Pattern: Gedankenlose Quantoren-Kombination (Unterspezifikation)

Ein häufiger Fehler besteht darin, mehrere unterschiedliche Eingaben in `pre` und ihre jeweiligen Einzel-Ergebnisse gemeinsam in `post` innerhalb eines einzigen `EBT`-Aufrufs zu übergeben – in der Annahme, `EBT` würde `pre[0]` nur mit `post[0]` (`3 -> 6`) und `pre[1]` nur mit `post[1]` (`5 -> 10`) vergleichen:

```python
from qb_cubie import EBT, WorldState

def double(x: int) -> int:
    return x * 2

trace = EBT(
    target=double,
    pre=[
        WorldState(args=3),
        WorldState(args=5),
    ],
    post=[
        WorldState(returns=6),
        WorldState(returns=10),
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

Warum hier **4 statt 2 Paare** geprüft werden und warum dies ein **Anti-Pattern** ist, folgt direkt aus den Quantoren von `EBT` (siehe [Vertragssemantik](GUIDE_Contract-Semantics.md#endliche-auswertungsregel)):

* **Jeder gegen Jeden statt Paar-Zuordnung:** `pre` wirkt als Allquantor (*für jede Eingabe*) und die positiven Zustände in `post` wirken als Existenzquantor (*muss mindestens eines der Ergebnisse aus `post` passen*). `EBT` prüft also sowohl für `3` als auch für `5` jeweils gegen `6` **und** gegen `10` ($2 \times 2 = 4$ geprüfte Paare in `trace.traces`).
* **Gefährliche Unterspezifikation:** Da für jede Eingabe nur *irgendein* Wert aus `{6, 10}` herauskommen muss, geht die feste Zuordnung verloren. Selbst eine kaputte Funktion, die immer stur `6` zurückgibt (`return 6`) oder die Ergebnisse vertauscht (`3 -> 10` und `5 -> 6`), würde diesen Test grün bestehen.

---

## 3. Wann mehrere Eingänge in einen Vertrag gehören

**Faustregel für Listen in `pre` und `post`:** Mehrere `pre`-Einträge gehören nur dann in denselben `EBT`-Aufruf, wenn für **alle** Eingaben **dasselbe** Zielmuster in `post` gilt – zum Beispiel wenn unterschiedliche Schreibweisen alle auf `"text"` normiert werden müssen:

```python
from qb_cubie import EBT, WorldState


def normalize(text: str) -> str:
    return text.strip().lower()


trace = EBT(
    target=normalize,
    pre=[
        WorldState(args=" TEXT "),
        WorldState(args="text"),
        WorldState(args="TeXt"),
    ],
    post=WorldState(returns="text"),
).run()

print(f"Normierung erfüllt: {trace.evaluation} | Geprüfte Eingänge: {len(trace.traces)}")
```

<details>
<summary>Ergebnis</summary>

```text
Normierung erfüllt: True | Geprüfte Eingänge: 3
```
</details>

> [!TIP]
> **Weiterführende Handbücher:** Wie du erwartete und verbotene Ergebnisse über `expect`-Flags kombinierst, erklärt [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md). Wie du die Quantoren `"all"` und `"exists"` gezielt umdrehst, zeigt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

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
