<center>

# Verbindliche Vertragssemantik

![Cubie](.assets/cubie-logo-written.png)

Diese Referenz beschreibt die vorhandene Implementierung von Cubie 0.0.3, abgeglichen mit `src/qb_cubie/ebt.py`, `protocols.py`, `rbt.py` und den Arenen. Sie unterscheidet die Auswertungsregel von bekannten Fehlern und berücksichtigt die Produktivkorrekturen zu Abschnitt 9.1 des [Gutachtens vom 10. November 2026](../GUTACHTEN.md).

---

</center>

## Begriffe und Felder

| Begriff / API | Bedeutung im vorhandenen Code |
| --- | --- |
| EBT-Vertrag | Endliche Menge konkreter Ausführungen mit gemeinsamen erlaubten/verbotenen Zielmustern. Kein Korrektheitsbeweis. |
| `WorldState` | Veränderliche Dataclass mit `args`, `kwargs`, `arena`, `fs`, `returns`, `expect`, `raises`, `exception`. Kein allgemein bewiesenes Zustandsprädikat und keine eingefrorene Momentaufnahme. |
| `pre` | Ein `WorldState` oder eine nichtleere Liste davon. Für jeden Eintrag wird das Target einmal aufgerufen. `None` wird zu `[WorldState()]`; `[]` führt zu `ValueError`. Ungültige Typen und Listeneinträge führen zu `TypeError`. |
| `post` | Ein `WorldState` oder eine nichtleere Liste gemeinsamer Zielmuster mit denselben Validierungsregeln wie `pre`. `None` wird zu `[WorldState()]`; es gibt keine Inferenz von `post=42` zu `WorldState(returns=42)`. |
| `args` | `None` ergibt keine Positionsargumente. Listen und Tupel werden in Positionsargumente entpackt; andere Objekte werden als ein Argument übergeben. `args=[1, 2]` ruft `f(1, 2)` auf; `args=([1, 2],)` ruft `f([1, 2])` auf; `args=(None,)` ruft `f(None)` auf. |
| `kwargs` | Ein Dictionary mit Schlüsselwortargumenten; `None` wird zu `{}`. Andere Werte führen zu `TypeError`. |
| `post.returns` | Erwarteter Rückgabewert oder Muster. Ausgelassen oder `qb_cubie.UNSPECIFIED` bedeutet „nicht prüfen“; explizites `None` erwartet den Wert `None`. |
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
| `post.raises` | `ExceptionExpectation(exception_type, match=None)` fordert einen Target-Fehler des Typs oder einer Unterklasse mit optionalem Meldungsregex. Darf im selben Zustand nicht mit `returns` kombiniert werden. |
| `outcome.exception` | Beobachtete Target-Exception oder `None`. Bei einer Exception ist `outcome.returns is UNSPECIFIED`. PyVenv liefert eine beschreibende `RemoteException`. |
| Exceptions | Ohne `post.raises` propagieren Target-Fehler weiterhin; `expect=False` fängt sie nicht ab. Mit Ausnahmevertrag werden normale Rückgabe, Typ und Meldung verglichen. Infrastrukturfehler bleiben Ausführungsabbrüche. |
| `stdout` / `stderr` | Keine `WorldState`-Felder und keine EBT-Rückgabemuster. `returns` bezeichnet ausschließlich den Python-Rückgabewert. |
| Reporter | Standardmäßig wertet `PytestReporter` das Ergebnis per Assertion aus. `reporter=None` unterdrückt diese Assertion; Target-, Aufbau- und Vergleichsfehler können weiterhin Exceptions auslösen. |
| `JsonReporter(path)` | Schreibt einen abgeschlossenen EBT-Lauf als versioniertes JSON, auch bei `evaluation=False`; erhebt selbst keine fachliche Assertion. Schreibfehler propagieren. |
| Traces | Unabhängige Momentaufnahmen für Vergleiche (`EvaluationTrace`) und Gesamtergebnis (`RunTrace`). Die Dataclasses bleiben durch den Empfänger veränderbar. Workspace-Pfade können nach dem Aufräumen nicht mehr existieren. |
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

`WorldState()` lässt den Rückgabewert offen, `WorldState(returns=None)` fordert dagegen `None`.
Wer bisher `returns=None` zum Überspringen der Prüfung verwendet hat, muss das Argument weglassen oder `UNSPECIFIED` aus `qb_cubie` importieren und setzen.
Der Sentinel deaktiviert nur als oberster `returns`-Wert die Prüfung; er ist kein rekursives Wildcard-Muster.

Die Reihenfolge der Mustererkennung ist relevant:

| Muster in `returns` | Vergleich |
| --- | --- |
| Ausgelassen / oberstes `qb_cubie.UNSPECIFIED` | Deaktiviert die Rückgabeprüfung. |
| `None` | Erwartet den Rückgabewert `None`. |
| `typing.Any` | Akzeptiert jeden Wert. Ein Dictionary-Schlüssel muss trotzdem vorhanden sein. |
| Union (`Union[...]` oder `A \| B`) | Mindestens eine Alternative muss passen. Enthaltenes `None` wird rekursiv als Wert verglichen. |
| Klasse / Typ | `isinstance(actual, expected)`, einschließlich der Python-Unterklassenbeziehungen. |
| `re.Pattern` | `pattern.match(str(actual))`; `actual=None` passt nicht. Kein implizites `fullmatch`: für ein vollständiges Format ein Ende wie `$` angeben. |
| Callable | Wahrheitswert von `predicate(actual)`. `TypeError`, `ValueError`, `AttributeError`, `KeyError`, `IndexError` zählen als Mismatch; andere Exceptions propagieren. |
| Dictionary | Exakt gleiche Schlüsselmenge, danach rekursiver Vergleich der Werte. |
| Liste / Tupel | Gleiche Länge und rekursiver Vergleich nach Position. Listen und Tupel sind dabei austauschbar. |
| Sonstiger Wert | Python-Gleichheit (`==`), kein strikter Typvergleich. |

Ein `EvaluationTrace.evaluation` beschreibt den rohen Match auch für ein verbotenes Muster. Erst die Aggregation berücksichtigt `post.expect`.

## Ausnahmeverträge

`WorldState(raises=ExceptionExpectation(ValueError, match=r"^invalid order: \d+$"))`
verlangt eine geworfene `ValueError` oder Unterklasse. Das optionale Stringmuster
verwendet `re.search` auf `str(exception)`; Traceback-Notizen gehören nicht zur
verglichenen Meldung. Typ und Meldung müssen gemeinsam passen. Ein zurückgegebenes
Exception-Objekt ist weiterhin eine normale Rückgabe.

`raises` verlangt eine Unterklasse von `Exception`, keine Instanz und kein
`BaseException`. Ungültige Typen, Regex und gleichzeitig spezifizierte
`returns`/`raises` führen vor Target-Ausführung zu `TypeError` oder `ValueError`.
EBT validiert die veränderlichen Zustände vor jedem Lauf erneut.

Für „Rückgabe oder Exception“ werden zwei positive Post-Zustände angegeben.
Ein Post-Zustand ohne `raises` passt ausschließlich zu normaler Beendigung,
auch wenn `returns` ausgelassen ist. `raises` und `fs` im selben Zustand müssen
beide passen. Nach einer erfassten Exception wird der FS-Zustand vor dem
Aufräumen verglichen. Negative Ausnahmezustände verwenden dieselbe Match- und
Aggregationsregel wie negative Rückgabezustände.

Die Erfassung umschließt nur den eigentlichen Target-Aufruf. Import-/Auflösungs-,
Transport-, Arena-, Vergleichs- und Aufräumfehler erfüllen keinen Ausnahmevertrag.
`KeyboardInterrupt` und `SystemExit` werden nicht erfasst; in PyVenv bleiben
Prozessabbrüche wie bisher Arena-Systemfehler.

Direkte Ausführung und TempFS bewahren die transportierbare Exception-Instanz.
PyVenv überträgt mit allen drei Codecs Typnamen, Meldung und qualifizierte
Klassen-MRO als `RemoteException` (öffentlich aus `qb_cubie` importierbar).
`type_name`, `message` und `type_mro` beschreiben den entfernten Fehler; dessen
Klasse wird auf dem Host weder importiert noch instanziiert. Das Typmatching
verwendet dort die qualifizierten MRO-Namen. Dynamisch registrierte virtuelle
ABC-Unterklassen sind damit keine transportierte Unterklassenbeziehung.
Pytest-Bericht und JSON verwenden den beobachteten ursprünglichen Typnamen.

## Dateisystem und Arenen

`EvaluationTrace.diffs["fs"]` gliedert Abweichungen nach dem Zielpfad des Mappings.
Die Listen `missing`, `unexpected` und `modified` enthalten Pfade relativ zum
jeweiligen Vergleichsobjekt. Bei einer einzeln gemappten Datei bezeichnet `"."`
die Datei selbst, beispielsweise
`{"out/report.csv": {"modified": ["."]}}`. Zuvor stand hier der Basename der
Host-Referenz; Verbraucher strukturierter Einzeldatei-Diffs müssen diese Änderung
berücksichtigen. Verzeichnis-Diffs enthalten weiterhin die relativen Dateipfade.
Nicht ausführbare Vergleiche besitzen einen `error`-Eintrag mit dem Fehlergrund.

Der Pytest-Reporter führt FS-Abweichungen zu Workspace-Pfaden zusammen und zählt
gleiche Pfade innerhalb einer Kategorie nur einmal, auch bei überlappenden
Mappings. Die Pfade werden innerhalb der Kategorien sortiert. `max_diff_items`
begrenzt die ausgegebene Dateiliste; die Gesamtzahlen bleiben vollständig.
Vergleichsfehler erscheinen mit Zielpfad und Grund unabhängig von dieser Grenze
und von der Verbosity. Ein ausschließlich fehlgeschlagener Vergleich liefert
keine irreführende Zusammenfassung mit null Abweichungen. Die Formatierung greift
nicht erneut auf die Vergleichsdateien zu und funktioniert auch nach deren Löschung.

Einzelne gemappte Dateien werden byteweise verglichen. Bei gemappten Verzeichnissen vergleicht EBT rekursiv relative Datei- und Verzeichnispfade sowie Dateiinhalte, einschließlich leerer Unterverzeichnisse. Fehlende, zusätzliche und geänderte Einträge zählen als Abweichung. Ein Wechsel Datei ↔ Verzeichnis innerhalb eines gemappten Verzeichnisses am gleichen relativen Pfad wird als `modified` erfasst. Ein Typkonflikt des explizit gemappten Vergleichsobjekts selbst bleibt ein Vergleichsfehler mit `error`-Eintrag. Die Diff-Listen sind sortiert. Pfade außerhalb der angegebenen Vergleichspfade bleiben ungeprüft. `fs={".": "fixtures/post"}` vergleicht den gesamten Workspace gegen die Vorlage.

Die Existenz eines ausdrücklich gemappten Verzeichnisses wird geprüft. Metadaten, Rechte und Symlink-Identität werden nicht verglichen; Symlinks werden entsprechend dem aufgelösten Datei-/Verzeichnistyp behandelt, unaufgelöste Links nicht erfasst. `FS_IGNORES` filtert Pfadsegmente samt Teilbaum. Beim Arena-Vergleich gelten `ARENA_IGNORES` und zusätzliche Filter für `.pyc` und `.dist-info`. Ein gleicher Dateibestand beweist weder identisches Laufzeitverhalten noch identische Abhängigkeiten.

Dateiinhalte werden bei jedem Vergleich neu in begrenzten Byteblöcken gelesen. Es gibt keinen persistenten, von Größe oder mtime abhängigen Vergleichscache. Das gilt für Einzeldateien, Verzeichnisbäume und Arena-Vergleiche. Gleichzeitig veränderte Dateien werden dadurch nicht zu einer atomaren Momentaufnahme; Referenzen müssen während des Vergleichs stabil bleiben.

Sammlungen von Hostpfaden werden nach Basename zusammengeführt. Unterschiedliche Quellen mit gleichem Basename führen vor Arena-Aufbau und Target-Ausführung zu `ValueError`. Die Meldung nennt Zustandsfeld, Index, Zielnamen und beide Quellen. Verwende für solche Fälle explizite, unterschiedliche Zielpfade, etwa `{"left/config.json": "a/config.json", "right/config.json": "b/config.json"}`. Wiederholungen desselben Pfads sind erlaubt; der Pfadvergleich erfolgt lexikalisch mit `pathlib.Path`, ohne Auflösung von Symlinks oder `..`.

Die Hydrierung von `pre.fs` begrenzt Schreibziele auf den Workspace. Absolute
Zielpfade, ausbrechende `..`-Komponenten und Symlinks oder Verzeichnis-Junctions,
die Schreibzugriffe nach außen umleiten, führen zu `ValueError`. Die Meldung nennt
das betroffene Mapping. Das gilt für EBT und direkte `arena.run()`-Aufrufe,
unabhängig von `expect=False` und `reporter=None`. Das Target startet bei einem
Hydrierungsfehler nicht; diese Aufrufe räumen den Workspace auch im Fehlerfall auf.
Bereits kopierte Workspace-Inhalte werden nicht atomar zurückgerollt.

Dateiquellen dürfen absolut oder relativ zum Host-CWD angegeben werden und müssen
vertrauenswürdig sein. Als Quelle ausdrücklich angegebene Symlinks werden beim
Kopieren dereferenziert. Symlinks innerhalb kopierter Verzeichnisbäume bleiben
erhalten, sofern sie auch am Ziel innerhalb des Workspace aufgelöst werden können.
Das gilt ebenfalls für interne Links auf noch nicht existierende Dateien.
Ausbrechende oder zyklische Linkketten werden vor Target-Ausführung abgewiesen;
auch spätere Mappings dürfen frühere Links nicht nach außen umlenken. Die Prüfung
gilt für die FS-Hydrierung, nicht für `post.fs`-Vergleiche oder Target-Dateizugriffe.
Die separat geklonte PyVenv-Basis bleibt eine vertrauenswürdige Eingabe; ihre
Interpreter-Links werden nicht pauschal verboten, aber auch nicht als Schreibziele
nach außen zugelassen.

`TempFS` und `PyVenv` erhalten Benutzerrechte, verfügbare Netzwerkzugänge und Hostzugriffsmöglichkeiten. Temporäre Arbeitsordner und virtuelle Umgebungen sind keine OS-Sicherheitsgrenzen. Auch der Codec schafft keine solche Grenze. Pickle/Cloudpickle können bei der Deserialisierung Code ausführen. `CloudpickleCodec(isolation=1)` ruft einen leeren Platzhalter auf und bietet keine zusätzliche Dependency-Isolation.

`PyVenv(decontams=[...])` ersetzt ausschließlich ausdrücklich benannte Module.
Phantom-Aufrufe, Kontextmanager und Wahrheitswertprüfungen lösen `TypeError` aus.
Installierte Abhängigkeiten werden standardmäßig unverändert importiert.
Fehlt pytest, erlaubt eine begrenzte Importhilfe `fixture`, `mark` und `param`
im Modulrumpf, damit unabhängige Targets aus Testmodulen geladen werden können.
Diese Hilfe wird vor dem Target-Aufruf aus dem Importcache entfernt; lokale
Laufzeitimports sehen wieder die tatsächlichen Abhängigkeiten. Bereits im
Testmodul gebundene Platzhalter verweigern Laufzeitaufrufe. Importhilfen sind
keine Implementierung der ersetzten Bibliothek und entziehen keine OS-Rechte.

Die Arenen sind für vertrauenswürdige Konfigurationen, Targets und Rückgaben
vorgesehen. Die Pfadprüfung schützt vor Fehlkonfigurationen beim Kopieren; sie
schützt nicht gegen konkurrierende Manipulationen des Dateisystems. Nicht
vertrauenswürdiger generierter Code benötigt eine separate Sicherheitsgrenze mit
eigenen Zugriffsrechten. MessagePack ändert diese Anforderung nicht.

Beide Arenen unterstützen unter POSIX die optionalen Limits `timeout` (Sekunden)
und `max_output_bytes` (gemeinsames stdout/stderr-Budget). Ohne explizite Limits
bleiben Laufzeit und Ausgabepufferung unbegrenzt. Überschreitungen propagieren
als `TimeoutError` beziehungsweise `RuntimeError`, auch bei `EBT(expect=False)`.
Die Überwachung beendet bei Abbruch die Prozessgruppe und räumt anschließend
Workspace und IPC-Dateien auf. Details und Plattformgrenzen stehen im
[Arena-Handbuch](GUIDE_Arena-Management.md#laufzeit-und-ausgabe-begrenzen).
`PyVenv.setup()` prüft Codec-Pakete ausschließlich lesend; fehlende Pakete müssen
vorher ausdrücklich provisioniert werden.

## Wiederholte Läufe und historische Ergebnisse

Jeder `.run()`-Aufruf beginnt mit einer neuen Lauf-ID, leeren Traces und Outcomes sowie zurückgesetzter Bewertung und Laufzeit. Eine Instanz kann nacheinander wiederverwendet werden. Nach einem Ausführungsabbruch bleibt `run_trace` leer; nach einer Reporter-Assertion ist das abgeschlossene, fehlgeschlagene Ergebnis verfügbar.

Zustandslisten werden beim Aufbau der EBT-Instanz und vor jedem Lauf geprüft. FS-Kurzformen werden vor jedem Lauf auf Namenskollisionen geprüft. Damit werden auch nachträgliche Konfigurationsänderungen validiert. Konfigurationsfehler propagieren unabhängig von `expect=False` und `reporter=None`.

Die Vorzustände werden vor der Target-Ausführung erfasst. Aufgezeichnete Zustände, verschachtelte Rückgabewerte, Diffs und die Arena-Metadaten werden mittels `deepcopy` von den gelieferten Objekten getrennt. Diese Objekte müssen tief kopierbar sein; Kopierfehler werden weitergegeben. Spätere Läufe und Änderungen an den ursprünglichen Daten verändern zurückgegebene Ergebnisse nicht. Die Ergebnis-Dataclasses sind weiterhin durch den Empfänger veränderbar. Workspace-Pfade sind keine archivierten Dateiinhalte.

Die gemeinsame Zielmenge wird nach der Zustandsnormalisierung und vor dem ersten
Target-Aufruf tief kopiert. Alle Eingänge eines Laufs verwenden diesen Stand.
Vor jedem Aufruf wird daraus die Vergleichserwartung erzeugt, die auch im Trace
steht. Änderungen an den ursprünglichen Post-Zuständen während der Ausführung
ändern weder die Vergleichsmatrix noch die Erwartungen dieses Laufs.
Prädikate erhalten den originalen Rückgabewert vor dessen historischer Kopie;
Identitätsprüfungen bleiben dadurch möglich. Funktionen werden von `deepcopy`
als Referenz übernommen: Closures, globale Variablen und externe Ressourcen
werden nicht eingefroren. Benutzerdefinierte Kopierlogik und veränderliche
Prädikate müssen entsprechend kontrolliert werden.

Proxies eines `multiprocessing.Manager`, etwa Events oder Barrieren in Argumenten, werden im Trace durch unveränderliche Referenzdaten (`resource_type`, `resource_id`) ersetzt. Das Target erhält weiterhin die lebenden Proxies. Der Trace dokumentiert deren Identität, nicht den veränderlichen Zustand des entfernten Objekts, und benötigt später keine Verbindung zum Manager.

Target und Arena werden weiterhin als übergebene Instanzen ausgeführt. Ihre eigenen Seiteneffekte, externe Ressourcen und bereits mutierte Target-Argumente werden zwischen Läufen nicht zurückgesetzt. Gleichzeitige `.run()`-Aufrufe auf derselben Instanz werden nicht unterstützt.

## Persistente EBT-Berichte

`JsonReporter(path)` speichert einen abgeschlossenen `RunTrace` als UTF-8-JSON mit
`schema_version: 1`, Lauf-ID, Target, Laufzeit, `expect`, Gesamtbewertung und allen
Vergleichsspuren einschließlich positiver und negativer Post-Zustände.
`pre`, `post`, `outcome` und aufgezeichnete Diffs bleiben nach Teardown auswertbar.
Die Ausgabe liest weder Workspace noch Referenzdateien erneut. Dateien selbst
werden nicht archiviert. Ausführungsabbrüche ohne abgeschlossenen `RunTrace`
erzeugen keinen Bericht.

Rückgaben verwenden typisierte Knoten: `kind: "unspecified"` bezeichnet den
Sentinel; `kind: "value"` enthält `type` und `value`. Dadurch bleiben `None`,
`False`, `0` und leere Container unterscheidbar. Container enthalten rekursiv
typisierte Werte. Dictionaries mit Stringschlüsseln behalten ihre Schlüssel;
andere Dictionaries werden als Liste von Schlüssel-/Wertpaaren dargestellt.
Tupel und Mengen verwenden JSON-Listen mit qualifiziertem Python-Typnamen.
Zyklen werden mit `kind: "cycle"` beschrieben. Nicht endliche Floats und sonstige
Objekte erhalten eine begrenzte Darstellung (`kind: "description"`).

Typ-, Regex- und Callable-Muster tragen `kind: "pattern"`, Typ und Beschreibung.
Prädikate werden bei der Ausgabe nicht aufgerufen. Die Daten benötigen keine
ausführbare Deserialisierung und sind kein wieder ausführbarer Testvertrag.
Diff-Kategorien und relative Pfade bleiben direkt lesbar; nicht JSON-kompatible
Diff-Werte werden ebenfalls beschrieben. Erwartete Exceptions enthalten `type`
und `match`; beobachtete Exceptions `type` und `message`.

Der Reporter erhebt keine Assertion für ein fachliches Mismatch. CI-Verbraucher
müssen `evaluation` auswerten oder anschließend `PytestReporter().report(result)`
aufrufen. Die Ausgabe ersetzt die Zieldatei erst nach vollständigem Schreiben;
Schreibfehler propagieren und eine vorhandene Datei bleibt bei fehlgeschlagener
Ersetzung erhalten. Das Elternverzeichnis muss existieren. Derselbe Pfad wird
überschrieben; für historische Läufe sind getrennte Pfade zu verwenden.

## Backend-Fallback und Wiederholungen

Bei Multiprocessing werden Task-Ausnahmen einschließlich Target-, Arena- und
Prüffehlern ohne Backendwechsel weitergegeben. Das gilt auch dann, wenn ihr Typ
einem Infrastrukturfehler entspricht. Konfigurationsfehler und Aufräumfehler
lösen ebenfalls keine Wiederholung aus.

Ein Fallback ist bei `OSError` oder `BrokenProcessPool` während des Poolaufbaus
sowie bei `BrokenProcessPool` oder `pickle.PicklingError` aus Mapping oder
Ergebnistransport zulässig. Der fehlgeschlagene Prozessor wird deaktiviert.
Ein weiteres geeignetes Backend führt **alle Eingänge erneut** aus; partielle
Ergebnisse werden verworfen. Die Warnung dokumentiert vollständige Wiederholung
und mögliche doppelte Seiteneffekte. Es gibt kein Rollback und keine
Exactly-once-Garantie. Bereits gestartete Tasks können vor dem Backendwechsel
noch fertiglaufen. Tatsächlicher Prozessverlust lässt seine Ursache im Target
nicht zuverlässig erkennen.

Sind alle geeigneten Backends ausgefallen, bleibt die letzte Infrastruktur-
Ausnahme als Ursache des abschließenden `RuntimeError` erhalten. Details für
eigene Mapper und die Anforderungen an den Exception-Transport stehen im
[Multiprocessing-Handbuch](dev/DEV-GUIDE_2-4_Multiprocessors.md#fehlerherkunft-und-wiederholungssemantik).

## Bekannte Abweichungen und praktische Folgen

- Zusätzliche Arena-Prozesse und pytest-xdist können die Last mehrerer Pools vervielfachen; `max_workers` begrenzt nur den jeweiligen EBT-Pool.
- Eine leere Linter-Diagnoseliste beweist keine allgemeine Fehlerfreiheit. Die Adapter prüfen Prozessstatus und Ausgabe gemäß dem [Linter-Handbuch](GUIDE_Linter.md). `AstLinter` wertet bereits eine beliebige `pyproject.toml` als native Konfiguration und kann dadurch Standardausschlüsse auslassen.

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
