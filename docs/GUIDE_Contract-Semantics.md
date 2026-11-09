<center>

# Verbindliche Vertragssemantik

![Cubie](.assets/cubie-logo-written.png)

Diese Referenz beschreibt die vorhandene Implementierung von Cubie 0.0.3, abgeglichen mit `src/cubie/ebt.py`, `protocols.py`, `rbt.py` und den Arenen. Sie unterscheidet die Auswertungsregel von bekannten Fehlern. Änderungen an der Dokumentation beheben diese Fehler nicht. Die Befunde stammen aus dem [Gutachten vom 9. November 2026](../GUTACHTEN.md), insbesondere Abschnitte 3, 5–7.

---

</center>

## Begriffe und Felder

| Begriff / API | Bedeutung im vorhandenen Code |
| --- | --- |
| EBT-Vertrag | Endliche Menge konkreter Ausführungen mit gemeinsamen erlaubten/verbotenen Zielmustern. Kein Korrektheitsbeweis. |
| `WorldState` | Veränderliche Dataclass mit `args`, `kwargs`, `arena`, `fs`, `returns`, `expect`. Kein allgemein bewiesenes Zustandsprädikat und keine eingefrorene Momentaufnahme. |
| `pre` | Ein `WorldState` oder eine Liste davon. Für jeden Eintrag wird das Target einmal aufgerufen. `None` wird zu `[WorldState()]`; `[]` bleibt leer. |
| `post` | Ein `WorldState` oder eine Liste gemeinsamer Zielmuster. `None` wird zu `[WorldState()]`; es gibt keine Inferenz von `post=42` zu `WorldState(returns=42)`. |
| `args` | `None` ergibt keine Positionsargumente. Listen und Tupel werden in Positionsargumente entpackt; andere Objekte werden als ein Argument übergeben. `args=[1, 2]` ruft `f(1, 2)` auf; `args=([1, 2],)` ruft `f([1, 2])` auf; `args=(None,)` ruft `f(None)` auf. |
| `kwargs` | Ein Dictionary mit Schlüsselwortargumenten; `None` wird zu `{}`. Andere Werte führen zu `TypeError`. |
| `post.returns` | Erwarteter Rückgabewert oder Muster. Aktuell bedeutet ein oberstes `None` „nicht prüfen“, auch wenn `None` ausdrücklich angegeben wurde. |
| `post.expect=True` | Erlaubtes Zielmuster. Alle in diesem Zustand aktivierten Prüfungen müssen passen. |
| `post.expect=False` | Verbotenes Zielmuster. Kein solches Muster darf vollständig passen. `pre.expect` steuert die EBT-Auswertung nicht. |
| `EBT(expect=False)` | Negiert das aggregierte Ergebnis aller Eingangsschritte. Erwartet weder eine Exception noch das Scheitern jedes einzelnen Schritts. |
| `EBT.arena` | Ausführbare Arena oder `None`. Ohne Arena wird das Callable direkt im aufrufenden Prozess ausgeführt. Es wird keine Arena automatisch aus `fs` abgeleitet. |
| `pre.arena` | Ein Objekt mit `setup` überschreibt die globale Arena. Ein String dient bei aktiver `PyVenv` als Pfad zur Basisumgebung; er erzeugt selbst keine Arena. |
| `post.arena` | Ein String oder ein Objekt mit `env_path` liefert den Vergleichspfad für den Arena-Dateiabgleich. Andere Objekte liefern keine solche Vergleichsvorlage. |
| `fs` | Dictionary `{Zielpfad: Hostquelle}` oder Sammlung von Hostpfaden (`set`, `list`, `tuple`), die EBT nach Basename zu einem Dictionary normalisiert. Einzelne Pfadstrings werden nicht unterstützt. Die Normalisierung verändert den übergebenen `WorldState`. |
| `pre.fs` | Kopiervorlage für die explizit gewählte Arena. Quellen dürfen Dateien oder Verzeichnisse sein. |
| `post.fs` | Vergleichsvorlage für die angegebenen Pfade oder Prädikate, die einen `pathlib.Path` erhalten. Leeres `fs` aktiviert keine Prüfung auf einen leeren Workspace. |
| `target` | Ohne Arena und in `TempFS` ein Callable. `PyVenv` unterstützt zusätzlich String-Referenzen; ihre Auflösung übernimmt der Codec. Ein Aufruf wie `target=my_func()` führt die Funktion schon beim Aufbau des Tests aus. |
| Exceptions | Target-Fehler propagieren. Es gibt kein eigenes Feld für erwartete Exceptions; `expect=False` fängt sie nicht ab. |
| `stdout` / `stderr` | Keine `WorldState`-Felder und keine EBT-Rückgabemuster. `returns` bezeichnet ausschließlich den Python-Rückgabewert. |
| Reporter | Standardmäßig wertet `PytestReporter` das Ergebnis per Assertion aus. `reporter=None` unterdrückt diese Assertion; Target-, Aufbau- und Vergleichsfehler können weiterhin Exceptions auslösen. |
| Traces | Veränderliche Dataclasses für Vergleiche (`EvaluationTrace`) und Gesamtergebnis (`RunTrace`). Workspace-Pfade können nach dem Aufräumen nicht mehr existieren. |
| RBT | Synchrone Übergabe von Zielbezeichnung und Prüfregel an `reviewer.review(...)`; keine automatische Target-Ausführung, Quellenbeschaffung oder Beweisführung. |

## Endliche Auswertungsregel

Seien `P` die deklarierten Eingänge, `Q+` die positiven und `Q−` die negativen Zielmuster. `match(p, q)` bedeutet: Das bei der Ausführung von `p` beobachtete Ergebnis erfüllt alle in `q` aktivierten Vergleiche.

Für jeden Eingang gilt:

```text
schritt_ok(p) = (Q+ ist leer ODER mindestens ein q aus Q+ passt)
               UND (kein q aus Q− passt)
lauf_ok      = alle schritt_ok(p)
evaluation   = lauf_ok, falls EBT.expect=True, sonst NICHT lauf_ok
```

Sind ausschließlich negative Zielmuster angegeben, ist kein positives Match erforderlich. Das schließt nur die benannten Muster aus. Sind positive Muster vorhanden, reicht das Vermeiden negativer Muster allein nicht aus.

Jeder Eingang wird gegen dieselbe gesamte Zielmenge verglichen. `pre=[1, 2]` und `post=[2, 4]` sind hier nur Kurznotation für die Mengenidee, **keine gültige API-Schreibweise**: Tatsächlich werden `WorldState`-Objekte benötigt. Auch mit diesen Objekten würde eine gemeinsame Zielmenge `{2, 4}` eine vertauschte Zuordnung akzeptieren. Für `f(1)=2` und `f(2)=4` sind getrennte Verträge nötig.

Die Quantoren beziehen sich nur auf die endlichen Listen und die jeweils beobachteten Ausführungen. Bei nichtdeterministischen Targets belegt ein Match weder alle möglichen Ausgaben noch deren Häufigkeit. Die Auswertungsregel ist kein Beweiskalkül und misst keine Testabdeckung.

## Rückgabevergleich

Die Reihenfolge der Mustererkennung ist relevant:

| Muster in `returns` | Vergleich |
| --- | --- |
| Oberstes `None` | Deaktiviert derzeit die gesamte Rückgabeprüfung. Für einen echten `None`-Sollwert: `lambda value: value is None`. |
| `typing.Any` | Akzeptiert jeden Wert. Ein Dictionary-Schlüssel muss trotzdem vorhanden sein. |
| Union (`Union[...]` oder `A \| B`) | Mindestens eine Alternative muss passen. Enthaltenes `None` wird rekursiv als Wert verglichen. |
| Klasse / Typ | `isinstance(actual, expected)`, einschließlich der Python-Unterklassenbeziehungen. |
| `re.Pattern` | `pattern.match(str(actual))`; `actual=None` passt nicht. Kein implizites `fullmatch`: für ein vollständiges Format ein Ende wie `$` angeben. |
| Callable | Wahrheitswert von `predicate(actual)`. `TypeError`, `ValueError`, `AttributeError`, `KeyError`, `IndexError` zählen als Mismatch; andere Exceptions propagieren. |
| Dictionary | Exakt gleiche Schlüsselmenge, danach rekursiver Vergleich der Werte. |
| Liste / Tupel | Gleiche Länge und rekursiver Vergleich nach Position. Listen und Tupel sind dabei austauschbar. |
| Sonstiger Wert | Python-Gleichheit (`==`), kein strikter Typvergleich. |

Ein `EvaluationTrace.evaluation` beschreibt den rohen Match auch für ein verbotenes Muster. Erst die Aggregation berücksichtigt `post.expect`.

## Dateisystem und Arenen

Einzelne gemappte Dateien werden byteweise verglichen. Bei gemappten Verzeichnissen vergleicht EBT rekursiv die relativen Dateipfade und Dateiinhalte; fehlende, zusätzliche und geänderte Dateien zählen als Abweichung. Dateien außerhalb der angegebenen Vergleichspfade bleiben ungeprüft. `fs={".": "fixtures/post"}` vergleicht die Dateien des gesamten Workspace gegen die Vorlage.

Leere Unterverzeichnisse werden beim rekursiven Vergleich nicht erfasst. Die Existenz eines ausdrücklich gemappten Verzeichnisses wird geprüft; ein vollständiger Vertrag über Verzeichnisstruktur, Metadaten, Rechte oder Symlink-Identität entsteht daraus nicht. `FS_IGNORES` filtert Pfadsegmente im rekursiven Dateiscan. Beim Arena-Vergleich gelten `ARENA_IGNORES` und zusätzliche Filter für `.pyc` und `.dist-info`. Ein gleicher Dateibestand beweist weder identisches Laufzeitverhalten noch identische Abhängigkeiten.

Sammlungen von Hostpfaden werden nach Basename zusammengeführt. Gleichnamige Quellen können sich überschreiben. Verwende für solche Fälle explizite, unterschiedliche Zielpfade. Arena-Zielpfade werden derzeit nicht auf den Workspace begrenzt: Absolute Pfade und `..` können außerhalb schreiben. Verwende kontrollierte relative Pfade ohne `..`.

`TempFS` und `PyVenv` erhalten Benutzerrechte, verfügbare Netzwerkzugänge und Hostzugriffsmöglichkeiten. Temporäre Arbeitsordner und virtuelle Umgebungen sind keine OS-Sicherheitsgrenzen. Auch der Codec schafft keine solche Grenze. Pickle/Cloudpickle können bei der Deserialisierung Code ausführen. `CloudpickleCodec(isolation=1)` ruft einen leeren Platzhalter auf und bietet keine zusätzliche Dependency-Isolation. Import-Phantome verändern Importbedingungen und können Fehler verdecken.

Beide Arenen haben keine konfigurierbare Target-Ausführungsfrist. `PyVenv` puffert stdout/stderr vollständig und kann fehlende Codec-Pakete in der Basisumgebung nachinstallieren. Damit sind Netz- und Schreiboperationen während des Setups möglich.

## Bekannte Abweichungen und praktische Folgen

- `returns=None` wird übersprungen. Ein grüner Test prüft diesen Sollwert nicht; nutze das oben genannte Prädikat.
- `pre=[]` führt kein Target aus; `post=[]` erzeugt keine Vergleiche. Beide können bei `expect=True` durch `all([])` erfolgreich erscheinen. Verwende nichtleere Zustandslisten und explizite Erwartungen.
- `.run()` setzt `_outcome` und `_traces` nicht zurück. Frühere Erfolge können spätere Fehler derselben Instanz verdecken; frühere `RunTrace.traces` wachsen mit. Erzeuge pro Lauf eine neue EBT-Instanz. Ein `RunTrace` ist keine unveränderliche historische Momentaufnahme.
- Der Standardreporter kann Rückgabedetails für `0`, `False`, `[]` und `""` auslassen. Der Vergleich dieser Werte findet statt; die Fehlerdarstellung kann unvollständig sein.
- Multiprocessing-Fallback kann nach Ausführungsfehlern die gesamte Aufgabenmenge erneut ausführen und Seiteneffekte wiederholen. Die Workerzahl richtet sich nach den gemeldeten CPUs; zusätzliche Arena-Prozesse und pytest-xdist können die Last vervielfachen.
- Eine leere Linter-Diagnoseliste beweist keine Fehlerfreiheit. Insbesondere kann der MyPy-Adapter einen Prozessabbruch als leere Liste behandeln; `AstLinter` wertet bereits eine beliebige `pyproject.toml` als native Konfiguration und kann dadurch Standardausschlüsse auslassen.

Diese Einschränkungen sind offene Implementierungsbefunde. Die beschriebene Handhabung begrenzt einzelne Fehlanwendungen, macht Cubie aber nicht zu einer allgemein verlässlichen Qualitätsinstanz.

---

---

<center>

![Error while trying to load the image](.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
