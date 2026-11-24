<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# WorldState

![Cubie](../../.assets/cubie-logo-written.png)

`WorldState` ist eine veränderliche Dataclass, die konkrete Aufrufdaten oder erwartete Ergebnismuster beschreibt. Sie besitzt keine eigene Ausführungs- oder Beweislogik. Die Bedeutung der Felder hängt von ihrer Verwendung in `pre`, `post` oder einem erfassten Ergebnis ab. Die verbindlichen Regeln stehen in der [Semantikreferenz](../../core/GUIDE_Contract-Semantics.md).

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

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

`returns` enthält im Ergebnis den Python-Rückgabewert und in `post` dessen Sollwert oder Muster. Es erfasst keine Konsolenausgaben. `returns=None` erwartet explizit `None`. Ausgelassenes `returns` verwendet den Sentinel `qb_cubie.UNSPECIFIED` und deaktiviert die Rückgabeprüfung. Der Sentinel kann auch ausdrücklich gesetzt werden. `stdout` und `stderr` sind keine `WorldState`-Felder. Für erwartete Target-Exceptions existiert `raises: ExceptionExpectation | None = None` (und `exception: Exception | None = None` für beobachtete Ausnahmen im Outcome); `validate_exception_contract()` stellt sicher, dass `returns` und `raises` niemals im selben Zustand kombiniert werden.

`fs` nimmt ein Dictionary `{Zielpfad: Hostquelle}` oder eine Sammlung von Hostpfaden auf. EBT normalisiert Sammlungen nach Basename; einzelne Pfadstrings werden nicht unterstützt. In `pre` kopiert die aktive Arena die Vorlagen, in `post` vergleicht EBT die benannten Pfade oder ruft ein Pfad-Prädikat auf. Eine Arena muss ausdrücklich gewählt werden. Die Normalisierung verändert den Zustand; gleichnamige Quellen können sich überschreiben.

`arena` ist kontextabhängig: In `pre` kann ein ausführbares Arena-Objekt die globale Arena ersetzen. Ein String überschreibt die Basis einer bereits aktiven `PyVenv`. In `post` dient ein String oder `env_path` eines Objekts als Vergleichspfad. In erfassten Arena-Ergebnissen enthält das Feld gegebenenfalls den tatsächlichen Umgebungspfad. Es ist keine universelle String-Referenz auf eine Sicherheits-Sandbox.

`expect: bool = True` wird bereits in `__post_init__` (sowie vor jedem Lauf in `EBT._arrange()`) über `validate_expect()` / `validate_bool_expect()` strikt auf `type(self.expect) is bool` geprüft (`TypeError("STATE-GUARD: ...")` bei `None`, `0`, `1` usw.). In `post` unterscheidet `expect` unter `post={"quantor": "all", ...}` geforderte (`True`) und verbotene (`False`) Muster. Es negiert nicht selbst den gesamten Lauf; dafür gibt es `EBT.expect`. In `pre` sowie unter `post_quantor="exists"` ist `expect=False` unzulässig und wird von `EBT` vor der Ausführung mit `ValueError("STATE-GUARD: ...")` abgewiesen.

Ein `WorldState` ist weder ein bewiesenes Zustandsprädikat noch eine vollständige Abbildung aller Seiteneffekte. Änderungen an enthaltenen Objekten bleiben möglich; auch ein eingefrorener `EBTContext`, der solche Objekte referenziert, verhindert das nicht.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../README.md)  
[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../README.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  

[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  

</div>
<!-- /qb:frame -->
