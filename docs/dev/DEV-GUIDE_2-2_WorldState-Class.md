# WorldState

`WorldState` ist eine veränderliche Dataclass, die konkrete Aufrufdaten oder erwartete Ergebnismuster beschreibt. Sie besitzt keine eigene Ausführungs- oder Beweislogik. Die Bedeutung der Felder hängt von ihrer Verwendung in `pre`, `post` oder einem erfassten Ergebnis ab. Die verbindlichen Regeln stehen in der [Semantikreferenz](../GUIDE_Contract-Semantics.md).

```python
from cubie import WorldState

pre = WorldState(args=([1, 2],), kwargs={"strict": True})
post = WorldState(returns=lambda value: value is None)
```

`args` hält Positionsargumente. Eine äußere Liste oder ein Tupel wird entpackt; deshalb wird eine Liste als einzelnes Argument in ein zusätzliches Tupel verpackt. `kwargs` muss ein Dictionary sein oder `None`. Es gibt keine automatische Inferenz eines primitiven `pre`-Werts in diese Felder.

`returns` enthält im Ergebnis den Python-Rückgabewert und in `post` dessen Sollwert oder Muster. Es erfasst keine Konsolenausgaben. Ein oberstes `returns=None` deaktiviert derzeit die Prüfung. Das Beispiel verwendet ein Prädikat, um wirklich `None` zu fordern. `stdout`, `stderr` und ein Feld für erwartete Exceptions existieren nicht.

`fs` nimmt ein Dictionary `{Zielpfad: Hostquelle}` oder eine Sammlung von Hostpfaden auf. EBT normalisiert Sammlungen nach Basename; einzelne Pfadstrings werden nicht unterstützt. In `pre` kopiert die aktive Arena die Vorlagen, in `post` vergleicht EBT die benannten Pfade oder ruft ein Pfad-Prädikat auf. Eine Arena muss ausdrücklich gewählt werden. Die Normalisierung verändert den Zustand; gleichnamige Quellen können sich überschreiben.

`arena` ist kontextabhängig: In `pre` kann ein ausführbares Arena-Objekt die globale Arena ersetzen. Ein String überschreibt die Basis einer bereits aktiven `PyVenv`. In `post` dient ein String oder `env_path` eines Objekts als Vergleichspfad. In erfassten Arena-Ergebnissen enthält das Feld gegebenenfalls den tatsächlichen Umgebungspfad. Es ist keine universelle String-Referenz auf eine Sicherheits-Sandbox.

`expect` unterscheidet in `post` erlaubte (`True`) und verbotene (`False`) Muster. Es negiert nicht selbst den gesamten Lauf; dafür gibt es `EBT.expect`. Ein Wert in `pre.expect` wirkt sich nicht auf die EBT-Aggregation aus.

Ein `WorldState` ist weder ein bewiesenes Zustandsprädikat noch eine vollständige Abbildung aller Seiteneffekte. Änderungen an enthaltenen Objekten bleiben möglich; auch ein eingefrorener `EBTContext`, der solche Objekte referenziert, verhindert das nicht.
