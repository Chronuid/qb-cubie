<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Fortgeschrittene Quantoren (`all` vs. `exists`)

![Cubie](.assets/cubie-logo-written.png)

Dieses Handbuch zeigt, wie sich Cubies Standard-Quantoren (`pre="all"`, `post="exists"`) gezielt umkehren lassen: mehrere Bedingungen gleichzeitig mit `post` auf `"all"` erzwingen (UND-Verknüpfung) oder alternative Eingabe-Routen mit `pre` auf `"exists"` zulassen (ODER-Verknüpfung). Die vollständigen Vertragsregeln stehen in der [Vertragssemantik](GUIDE_Contract-Semantics.md).

---

> [!Note]  
> Dieses Handbuch zur Qualitätssicherung befindet sich derzeit unter aktiver Mutation und Überarbeitung und könnte daher Fehler, Unvollständigkeiten oder veraltete Angaben enthalten.

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Standardregeln vs. explizite Quantor-Steuerung

Normalerweise wendet Cubie zwei feste Standardregeln an:

* Für **`pre`** gilt **„alle“ (`"all"`)**: Jede angegebene Eingabe muss den Test bestehen.
* Für **`post`** gilt **„mindestens eines“ (`"exists"`)**: Die Rückgabe muss zu mindestens einem der erlaubten Zielmuster passen.

Manchmal braucht man es genau andersherum. Dafür packt man die Zustände einfach in ein kleines Dictionary mit `"quantor"` (`"all"` oder `"exists"`) und `"states"` (als Liste oder als einzelnen `WorldState`).

---

## 2. Muster 1: Alle Bedingungen gleichzeitig erzwingen (`post` mit `"all"`)

Das ist nützlich, wenn ein Ergebnis mehrere Regeln auf einmal einhalten muss – zum Beispiel *„eine ganze Zahl **und** positiv **und** gerade“* (Typ-, Bereichs- und Paritätsprüfung). Verbotene Werte (`expect=False`) bleiben dabei natürlich weiterhin strikte Verbote:

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

---

## 3. Muster 2: Alternative Eingabe-Routen erlauben (`pre` mit `"exists"`)

Das ist nützlich, wenn von mehreren Kandidaten oder Eingabe-Routen **mindestens eine** zum Erfolg führen muss:

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

## 4. Leitplanken, `STATE-GUARD`s und Abgrenzung

> [!TIP]
> **Kurz gemerkt:** Als `"quantor"` sind nur `"all"` und `"exists"` erlaubt, und `"states"` darf niemals leer sein. Außerdem akzeptiert das Wrapper-Dictionary ausschließlich die Schlüssel `"quantor"` und `"states"`. Wenn etwas davon nicht stimmt, stoppt Cubie den Testlauf sofort mit einer klaren `STATE-GUARD`-Fehlermeldung, bevor überhaupt Code ausgeführt wird. Die wirksamen Quantoren stehen anschließend als `trace.pre_quantor` und `trace.post_quantor` im `RunTrace`.

Wichtig für die Abgrenzung zu [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md):

* **`post` mit `"all"` ersetzt keine Paar-Zuordnung:** Alle positiven Zustände in `post` gelten gemeinsam für *jeden* ausgeführten Eingang aus `pre`. Wenn zwei unterschiedliche Eingaben (`3` und `5`) unterschiedliche Rückgaben (`6` und `10`) verlangen, gehören sie weiterhin in getrennte Verträge (oder in `@pytest.mark.parametrize`).
* **Erwartungssteuerung kombinierbar:** Auch in `post={"quantor": "all", ...}` lassen sich explizite Verbote via `WorldState(..., expect=False)` einstreuen; alle Details dazu beschreibt [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).

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
