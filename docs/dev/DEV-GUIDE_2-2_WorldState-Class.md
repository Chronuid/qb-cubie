<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# WorldState

![Cubie](../.assets/cubie-logo-written.png)

`WorldState` ist eine veränderliche Dataclass, die konkrete Aufrufdaten oder erwartete Ergebnismuster beschreibt. Sie besitzt keine eigene Ausführungs- oder Beweislogik. Die Bedeutung der Felder hängt von ihrer Verwendung in `pre`, `post` oder einem erfassten Ergebnis ab. Die verbindlichen Regeln stehen in der [Semantikreferenz](../GUIDE_Contract-Semantics.md).

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

Ein `WorldState`-Paar beschreibt Eingangsargumente (`pre`) und das erwartete Rückgabemuster (`post`):

```python
from qb_cubie import WorldState

pre = WorldState(args=([1, 2],), kwargs={"strict": True})
post = WorldState(returns=None)
print(pre.args, post.returns)
```

<details>
<summary>Ergebnis</summary>

```text
([1, 2],) None
```
</details>

`args` hält Positionsargumente. Eine äußere Liste oder ein Tupel wird entpackt; deshalb wird eine Liste als einzelnes Argument in ein zusätzliches Tupel verpackt. `kwargs` muss ein Dictionary sein oder `None`. Es gibt keine automatische Inferenz eines primitiven `pre`-Werts in diese Felder.

`returns` enthält im Ergebnis den Python-Rückgabewert und in `post` dessen Sollwert oder Muster. Es erfasst keine Konsolenausgaben. `returns=None` erwartet explizit `None`. Ausgelassenes `returns` verwendet den Sentinel `qb_cubie.UNSPECIFIED` und deaktiviert die Rückgabeprüfung. Der Sentinel kann auch ausdrücklich gesetzt werden. `stdout`, `stderr` und ein Feld für erwartete Exceptions existieren nicht.

`fs` nimmt ein Dictionary `{Zielpfad: Hostquelle}` oder eine Sammlung von Hostpfaden auf. EBT normalisiert Sammlungen nach Basename; einzelne Pfadstrings werden nicht unterstützt. In `pre` kopiert die aktive Arena die Vorlagen, in `post` vergleicht EBT die benannten Pfade oder ruft ein Pfad-Prädikat auf. Eine Arena muss ausdrücklich gewählt werden. Die Normalisierung verändert den Zustand; gleichnamige Quellen können sich überschreiben.

`arena` ist kontextabhängig: In `pre` kann ein ausführbares Arena-Objekt die globale Arena ersetzen. Ein String überschreibt die Basis einer bereits aktiven `PyVenv`. In `post` dient ein String oder `env_path` eines Objekts als Vergleichspfad. In erfassten Arena-Ergebnissen enthält das Feld gegebenenfalls den tatsächlichen Umgebungspfad. Es ist keine universelle String-Referenz auf eine Sicherheits-Sandbox.

`expect` unterscheidet in `post` erlaubte (`True`) und verbotene (`False`) Muster. Es negiert nicht selbst den gesamten Lauf; dafür gibt es `EBT.expect`. Ein Wert in `pre.expect` wirkt sich nicht auf die EBT-Aggregation aus.

Ein `WorldState` ist weder ein bewiesenes Zustandsprädikat noch eine vollständige Abbildung aller Seiteneffekte. Änderungen an enthaltenen Objekten bleiben möglich; auch ein eingefrorener `EBTContext`, der solche Objekte referenziert, verhindert das nicht.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
