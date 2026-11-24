<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Vertragsaufbau: Eindeutigkeit & Kopplung

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch zeigt, wie `EBT`-Verträge eindeutig und wartbar aufgebaut werden: Warum jedes konkrete Ein-/Ausgabepaar einen eigenen Vertrag braucht, wie `@pytest.mark.parametrize` sauber skaliert und wie man Unterspezifikation durch gedankenloses Mischen von `pre`- und `post`-Listen vermeidet. Die formalen Auswertungsregeln stehen in der [Vertragssemantik](core/GUIDE_Contract-Semantics.md).

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Best Practice: Ein Vertrag pro Wertepaar in klaren Test-Funktionen

**Einfach erklärt (für Einsteiger):** Im folgenden Beispiel testen wir eine kleine Funktion `double(x)`, die eine Zahl verdoppelt (`x * 2`). Für jedes konkrete Wertepaar schreiben wir eine eigene Test-Funktion (`test_double_three` für `3 -> 6` und `test_double_five` für `5 -> 10`). Weil jeder `EBT`-Aufruf genau **1** Eingabe (`pre`) und **1** Erwartung (`post`) enthält, gibt `len(trace.traces)` (*Anzahl der durchgeführten Einzelvergleiche*) pro Lauf genau `1` aus.

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

**Einfach erklärt (für Einsteiger):** Wenn du nicht bloß zwei, sondern zehn Wertepaare testen willst, wäre es mühsam, zehnmal fast dieselbe `def test_double_...()`-Funktion untereinander zu kopieren. In `pytest` gibt es dafür den sogenannten **Decorator** `@pytest.mark.parametrize` (erkennbar am `@`-Zeichen über der Funktion). Er funktioniert wie eine automatische Stempelmaschine: Du gibst ihm die Namen der beiden Variablen (`"value, expected"`) und eine Liste von Paaren (`[(3, 6), (5, 10)]`). Pytest führt die Funktion `test_double` dann für jedes Paar **einzeln und komplett getrennt** aus – so erhältst du weiterhin genau `1` eindeutiges Prüfpaar pro Lauf:

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

Warum hier **4 statt 2 Paare** geprüft werden und warum dies ein **Anti-Pattern** ist, folgt direkt aus den reinen Standard-Quantoren von `EBT` (siehe [Vertragssemantik](core/GUIDE_Contract-Semantics.md#endliche-auswertungsregel)):

* **Einfach erklärt (Die Speisekarten-Verwechslung):** Stell dir vor, zwei Gäste bestellen im Restaurant: Gast 1 bestellt für Eingabe `3` (erwartet Gericht `6`), Gast 2 bestellt für Eingabe `5` (erwartet Gericht `10`). Wenn du beide Bestellungen `[3, 5]` in `pre` und beide Gerichte `[6, 10]` gemeinsam in `post` wirfst, weiß Cubie **nicht**, welches Gericht zu welchem Gast gehört! Stattdessen legt Cubie beiden Gästen einfach die gemeinsame Speisekarte `{6, 10}` hin und prüft für jeden Gast nur: *„Stand das servierte Gericht irgendwo auf der Karte?“* Selbst wenn die Küche die Teller komplett vertauscht (`3 -> 10` und `5 -> 6`) oder jedem Gast stur `6` hinstellt (`return 6`), steht `6` auf der Karte – und der Test wird trotz kaputter Küche **grün**!
* **Technisch & formal (Kartesisches Kreuzprodukt $N \times M$):** Standardmäßig wirkt `pre` als **reiner Allquantor (`"all"`, *für jede Eingabe*)** und `post` als **reiner Existenzquantor (`"exists"`, *muss mindestens eines der Zielmuster aus `post` passen*)**. `EBT` bildet daher das Kreuzprodukt aus allen `pre`- und `post`-Einträgen und prüft sowohl `3` als auch `5` jeweils gegen `6` **und** gegen `10` ($2 \times 2 = 4$ Vergleiche in `trace.traces`, Formel: $\forall p \in \text{pre} : \exists q \in \text{post} : \text{match}(p, q)$).
* **Automatischer Schutz in der Cubie-Suite (Meta-Gate 2):** In Cubies eigener Test-Suite erkennt der statische Syntaxbaum-Wächter **`META-EBT-CROSS-PRODUCT`** (`tests/tests_meta/test_gate_2.py`) solche unbegründeten $N \times M$-Kreuzprodukte (`len(pre) > 1` und `len(post) > 1` unter `post="exists"`) automatisch.

---

## 3. Wann mehrere Eingänge in einen Vertrag gehören

**Einfach erklärt (Äquivalenzklasse & Normierung):** Alle drei Eingaben `' TEXT '`, `'text'` und `'TeXt'` gehören in dieselbe Gruppe (**Äquivalenzklasse**), weil bei allen dreien am Ende exakt dasselbe Wort `'text'` herauskommen muss. In Python schneidet `.strip()` die Leerzeichen am Rand ab und `.lower()` macht alle Buchstaben klein.

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
> **Weiterführende Handbücher:** Wie du erwartete Soll-Ziele und verbotene Ergebnisse (`expect=False`) innerhalb eines konjunktiven `post={"quantor": "all", ...}`-Vertrags kombinierst, erklärt [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md). Wie du die Standard-Quantoren `"all"` und `"exists"` gezielt umdrehst, zeigt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./README.md)  
[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./dev/README.md)  
[↦ | Core-Internals | ↤](./dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
