<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Fortgeschrittene Quantoren (`all` vs. `exists`)

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch zeigt, wie sich Cubies Standard-Quantoren (`pre="all"`, `post="exists"`) gezielt umkehren lassen: mehrere Bedingungen gleichzeitig mit `post` auf `"all"` erzwingen (UND-Verknüpfung) oder alternative Eingabe-Routen mit `pre` auf `"exists"` zulassen (ODER-Verknüpfung). Die vollständigen Vertragsregeln stehen in der [Vertragssemantik](core/GUIDE_Contract-Semantics.md).

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

## 1. Standardregeln vs. explizite Quantor-Steuerung

**Einfach erklärt (Was ist überhaupt ein „Quantor“?):** Das Wort *Quantor* stammt aus der Logik und beantwortet beim Testen eine ganz einfache Alltagsfrage: **„Wie viele Punkte auf meiner Prüfliste müssen klappen, damit der Test gewonnen hat?“** Es gibt genau zwei Möglichkeiten:

* **`"all"` (der Allquantor $\forall$ — die UND-Checkliste):** Wie beim Sicherheitscheck vor einem Flugzeugstart muss **jeder einzelne Punkt** (`alle`) erfüllt sein (`Bedingung 1 UND Bedingung 2 UND ...`). Scheitert auch nur ein Punkt, ist der Check nicht bestanden.
* **`"exists"` (der Existenzquantor $\exists$ — die ODER-Auswahlliste):** Wie an einer Supermarktkasse, die *„Bargeld ODER EC-Karte ODER Kreditkarte“* akzeptiert, reicht es völlig aus, wenn **mindestens eine** Option (`existiert mindestens eine`) passt (`Option 1 ODER Option 2 ODER ...`).

Ohne besondere Angabe wendet Cubie zwei feste, **100 % reine Standardregeln** an:

* Für **`pre` (Eingaben)** gilt standardmäßig **`"all"` (Allquantor / UND)**: Jede angegebene Eingabe wird ausgeführt und muss den Test bestehen.
* Für **`post` (Erwartungen)** gilt standardmäßig **`"exists"` (Existenzquantor / ODER)**: Die Rückgabe muss zu mindestens einem der angegebenen Zielmuster passen.

> [!IMPORTANT]
> **Grundgesetz der Quantoren-Reinheit:** Die Standard-Quantoren (`pre="all"`, `post="exists"`) werden **niemals** heimlich durch ein `expect`-Flag überschrieben! Wenn du die Quantoren ändern möchtest (oder in `post` ein Verbot mit `WorldState(..., expect=False)` einsetzen willst), legst du den Quantor immer **explizit** über ein kleines Python-Dictionary mit den beiden Schlüsseln `"quantor"` (`"all"` oder `"exists"`) und `"states"` (ein einzelner `WorldState` oder eine Liste von `WorldState`-Objekten) fest.

---

## 2. Muster 1: Alle Bedingungen gleichzeitig erzwingen (`post` mit `"all"`)

Mit `post={"quantor": "all", "states": [...]}` schaltest du `post` von der Standard-ODER-Auswahl auf eine **strikte UND-Checkliste** um. Das brauchst du in zwei typischen Situationen:

1. **Mehrere Eigenschaften gleichzeitig prüfen:** Ein Ergebnis soll mehrere Teilregeln auf einmal einhalten – zum Beispiel *„muss eine ganze Zahl (`int`) sein **UND** größer als `0` (`value > 0`) **UND** durch `2` teilbar (`value % 2 == 0`, also eine gerade Zahl)“*.
2. **Soll-Ziele mit Verboten (`expect=False`) kombinieren:** Weil `post` auf `"all"` steht, werden erlaubte Ziele (`expect=True`) und Verbote (`expect=False`) völlig einheitlich mit **UND** (`all(...)`) verknüpft: Jedes positive Muster muss zutreffen, und kein verbotenes Muster darf eintreten (siehe [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md)).

Im folgenden Beispiel verdoppelt `double(4)` die Zahl zu `8` und wird gegen alle drei UND-Bedingungen in `post` geprüft:

```python
from qb_cubie import EBT, WorldState


def double(x: int) -> int:
    return x * 2


trace = EBT(
    target=double,
    pre={"quantor": "all", "states": WorldState(args=4)},
    post={
        "quantor": "all",
        "states": [
            WorldState(returns=int),
            WorldState(returns=lambda value: value > 0),
            WorldState(returns=lambda value: value % 2 == 0),
        ],
    },
).run()

print(f"Alle Regeln erfüllt: {trace.evaluation} | pre={trace.pre_quantor} | post={trace.post_quantor}")
```

<details>
<summary>Ergebnis</summary>

```text
Alle Regeln erfüllt: True | pre=all | post=all
```
</details>

* **Einfach erklärt & formal:** Für `8` stimmen alle drei Teilregeln (`isinstance(8, int)`, `8 > 0`, `8 % 2 == 0`); scheitert auch nur eine einzige Regel in dieser Konjunktion ($\forall q \in Q : \text{sat}(q, y)$), schlägt der gesamte Schritt fehl.

---

## 3. Muster 2: Alternative Eingabe-Routen erlauben (`pre` mit `"exists"`)

Mit `pre={"quantor": "exists", "states": [...]}` schaltest du die Eingabeseite von der Standard-UND-Pflicht auf eine **ODER-Auswahl** um.

* **Einfach erklärt (Notstrom-Prinzip):** Stell dir einen Server-Dienst mit einer Hauptleitung (`"/main"`) und einer Ersatzleitung (`"/backup"`) vor. Für die Verfügbarkeit des Systems reicht es, wenn **mindestens eine** der beiden Leitungen mit `"ok"` antwortet.

Selbst wenn `"/main"` gerade `"offline"` liefert, besteht der Gesamtlauf im folgenden Beispiel, sobald `"/backup"` erfolgreich `"ok"` meldet:

```python
from qb_cubie import EBT, WorldState


def check_endpoint(path: str) -> str:
    return "ok" if path == "/backup" else "offline"


trace = EBT(
    target=check_endpoint,
    pre={"quantor": "exists", "states": [WorldState(args="/main"), WorldState(args="/backup")]},
    post={"quantor": "exists", "states": WorldState(returns="ok")},
).run()

print(f"Mindestens eine Route erreichbar: {trace.evaluation} | pre={trace.pre_quantor} | post={trace.post_quantor}")
```

<details>
<summary>Ergebnis</summary>

```text
Mindestens eine Route erreichbar: True | pre=exists | post=exists
```
</details>

---

## 4. Leitplanken, `STATE-GUARD`s, Lebenszyklus und Abgrenzung

Damit sich niemals fehlerhafte oder mehrdeutige Quantor-Konfigurationen in deine Tests einschleichen, prüft Cubie vor jedem Testlauf vier harte **`STATE-GUARD`-Leitplanken**:

| Leitplanke / `STATE-GUARD` | Was wird geprüft? | Fehlertyp bei Verstoß |
| :--- | :--- | :--- |
| **1. Wrapper-Struktur** | Das Dictionary darf ausschließlich die Schlüssel `"quantor"` (`"all"` oder `"exists"`, strikt `str`) und `"states"` (ein einzelner `WorldState` oder eine nichtleere `list[WorldState]`) enthalten. | `TypeError` / `ValueError` (`STATE-GUARD`) |
| **2. Verbot unter `post="exists"` & in `pre`** | Ein `WorldState(..., expect=False)` ist **nur** unter `post={"quantor": "all", ...}` zulässig. Unter `post="exists"` (Standard oder explizit) sowie in `pre` ist `expect=False` verboten. | `ValueError` (`STATE-GUARD`) |
| **3. Strikte `bool`-Prüfung auf `expect`** | `WorldState.expect` und `EBT.expect` akzeptieren ausschließlich `True` oder `False` (`type(val) is bool`). Werte wie `None`, `0`, `1` oder `"true"` werden abgewiesen. | `TypeError` (`STATE-GUARD`) |
| **4. Wiederverwendung & Sticky-Quantor-Reset** | Führst du dasselbe `EBT`-Objekt mehrfach mit `.run()` aus (oder änderst `case.post.append(...)` in-place), bleibt der deklarierte Quantor erhalten. Weist du `case.pre = ...` oder `case.post = ...` jedoch ohne Dict-Wrapper neu zu (z. B. `case.post = [ws1, ws2]`), setzt Cubie den Quantor automatisch auf den Standard (`pre="all"`, `post="exists"`) zurück. | Automatischer Reset in `_arrange()` |

> [!TIP]
> **Kontrolle im `RunTrace` und JSON-Bericht:** Welche Quantoren in einem Lauf tatsächlich wirksam waren, kannst du jederzeit nach `.run()` über `trace.pre_quantor` und `trace.post_quantor` (sowie in den JSON-Berichten des `JsonReporter`) ablesen.

Wichtig für die Abgrenzung zu den anderen Handbüchern:

* **`post` mit `"all"` ersetzt keine Paar-Zuordnung:** Alle Zustände in `post` gelten gemeinsam für *jeden* ausgeführten Eingang aus `pre`. Wenn zwei unterschiedliche Eingaben (`3` und `5`) unterschiedliche Rückgaben (`6` und `10`) verlangen, gehören sie weiterhin in getrennte Verträge oder in `@pytest.mark.parametrize` (siehe [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md)).
* **Erwartungssteuerung gezielt kombinieren:** Wie du in `post={"quantor": "all", ...}` positive Soll-Ziele und Verbote (`WorldState(..., expect=False)`) sicher kombinierst und die „einsame Negation“ (*Vacuous Pass*) vermeidest, beschreibt [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

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
