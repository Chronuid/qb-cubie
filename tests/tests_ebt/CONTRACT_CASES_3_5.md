# Soll-Cases zu Gutachten, Abschnitt 8, Priorität 3.5

Bezug: [GUTACHTEN.md](../../GUTACHTEN.md), „Rückgaben, Ausnahmeerwartungen,
FS-Topologie und persistente Berichte eindeutig modellieren“.

Die ursprüngliche Änderung ergänzte zunächst ausschließlich Tests. Die dabei
entworfene API ist inzwischen im Produktivcode implementiert. Dieses Dokument
bewahrt den ersten roten Befund unten als historischen Ausgangspunkt. Die
[Vertragsreferenz](../../docs/GUIDE_Contract-Semantics.md) beschreibt den aktuellen
Stand einschließlich der PyVenv-Exception-Beobachtungen und des JSON-Formats.

Alle Cases prüfen das Ergebnis mit unabhängigen pytest-Assertions. Fehlende APIs
werden weder durch Testadapter ersetzt noch mit `xfail` oder bedingtem Überspringen
verdeckt. Imports neuer Modelle erfolgen innerhalb der Cases, damit die übrigen
Tests weiterhin gesammelt und ausgeführt werden können.

## Abdeckung und festgelegte Bedeutung

| Datei | Vertrag und Gegenproben |
| --- | --- |
| [test_ebt_contract_returns.py](test_ebt_contract_returns.py) | Verschachteltes `None` verlangt einen vorhandenen Schlüssel mit `None`; verschachteltes `UNSPECIFIED` ist kein Wildcard. Zurückgegebene Exceptions sind Werte. Bestehende Python-Gleichheit, Unterklassen- und Listen-/Tupelmuster bleiben erhalten. Jeweils direkt und mit TempFS. |
| [test_ebt_exception_contracts.py](test_ebt_exception_contracts.py) | Ausnahme nach Typ und Meldung, Unterklassen, falscher Typ/falsche Meldung, fehlende Exception, zurückgegebenes Exception-Objekt, positive Alternativen und verbotene Exceptions. Kombination mit FS, mehrere Eingänge und Prozesspool, ungültige Verträge, Prozesssteuerungs- und Arena-Fehler, Reporter und Aufräumen. |
| [test_ebt_directory_topology.py](test_ebt_directory_topology.py) | Gleiche, fehlende, zusätzliche und verschachtelte leere Verzeichnisse; Datei-/Verzeichniswechsel; ignorierte Teilbäume, begrenzte Vergleichspfade und fehlende explizite Verzeichnisse. Direkte Beobachtung des Targets als zusätzliche Kontrolle. |
| [test_ebt_persistent_reports.py](test_ebt_persistent_reports.py) | Versioniertes JSON mit typisierten Rückgaben, ausgelassenem Rückgabevertrag, Mustern, Exception-Erwartung und Beobachtung, allen Eingangs-/Zielvergleichen und negativen Zuständen. Verzögerte Ausgabe nach Teardown und Löschen der Referenz, Lesen im frischen Prozess, stabile getrennte Laufberichte und Schreibfehler. |

## Entwurf: Ausnahmeverträge

```python
from qb_cubie import EBT, WorldState
from qb_cubie.protocols import ExceptionExpectation

EBT(
    target=reject_order,
    post=WorldState(
        raises=ExceptionExpectation(ValueError, match=r"^invalid order: \d+$"),
    ),
).run()
```

- `ExceptionExpectation(exception_type, match=None)` verlangt eine Klasse unterhalb
  von `Exception`. Unterklassen der erwarteten Klasse passen. `match` ist ein
  optionaler Regex auf `str(exception)` mit `re.search`-Semantik; `^` und `$`
  begrenzen die vollständige Meldung. Transportierte Traceback-Notizen verändern
  die verglichene Meldung nicht.
- `post.raises` und eine explizite `post.returns`-Erwartung im selben Zustand sind
  widersprüchlich. Für „Rückgabe oder Exception“ dienen getrennte Post-Zustände.
  Ein gültiger Post-Zustand mit `raises` darf zusätzlich `fs` verlangen; beide
  Bedingungen müssen passen.
- `outcome.exception` enthält die beobachtete Exception oder `None`. Bei PyVenv
  wird sie mit allen drei Codecs als `RemoteException` mit qualifiziertem Typ,
  Meldung und MRO beschrieben, ohne die entfernte Klasse auf dem Host zu laden.
  Bei einer
  Exception bleibt `outcome.returns is UNSPECIFIED`; eine normale Rückgabe von
  `None` oder eines Exception-Objekts bleibt davon unterscheidbar.
- Bei deklariertem Ausnahmevertrag führen falscher Typ, falsche Meldung und normale
  Rückgaben zu Mismatches mit einem `raises`-Diff. Der Pytest-Reporter zeigt
  erwarteten Typ/Meldungsmuster und beobachteten Typ/Meldung.
- Ohne Ausnahmevertrag propagieren Target-Exceptions weiterhin, auch bei
  `expect=False` und `reporter=None`. Negative Post-Zustände verwenden dieselbe
  rohe Match-Bedeutung wie bisher; erst die Aggregation verbietet den Match.
- Ungültiger Typ, Exception-Instanz, `BaseException`, ungültiger Regex oder
  gleichzeitig spezifizierte Rückgabe werden vor Target-Ausführung mit
  `TypeError` beziehungsweise `ValueError` abgewiesen.
- `KeyboardInterrupt` und `SystemExit` sowie Fehler aus Arena-Aufbau, Ausführung,
  Zustandserfassung und Aufräumen propagieren. Ihre Herkunft darf nicht allein
  anhand des Exception-Typs als Target-Ergebnis interpretiert werden. Die Cases
  schreiben dafür keine interne Transportimplementierung vor.

## Entwurf: FS-Topologie

Gemappte Verzeichnisse vergleichen Dateien **und Verzeichnisse**, einschließlich
leerer Unterverzeichnisse. Fehlende Einträge stehen unter `missing`, zusätzliche
unter `unexpected`. Ein Wechsel Datei ↔ Verzeichnis innerhalb eines gemappten
Verzeichnisses am gleichen relativen Pfad
steht unter `modified`; eine leere Datei ersetzt kein leeres Verzeichnis.
Die bestehenden nach Mapping-Pfad gegliederten Diffs bleiben erhalten.

`FS_IGNORES` schließt ein passendes Pfadsegment samt Teilbaum aus. Pfade außerhalb
des Mappings bleiben ungeprüft. Die explizite Existenzprüfung eines gemappten
Verzeichnisses bleibt erhalten. Der Standard `fs={}` erhält hier keine neue
Bedeutung als „Workspace muss leer sein“.

Ein Typkonflikt des explizit gemappten Vergleichsobjekts selbst bleibt wie bisher
ein Vergleichsfehler mit `error`-Eintrag.

Diese erste Fallgruppe definiert reguläre Dateien und Verzeichnisse. Symlink-
Identität, Rechte, Zeitstempel und andere Metadaten sind nicht Teil dieses
Entwurfs; die Cases beanspruchen keinen vollständigen OS-Dateisystemvergleich.

## Entwurf: persistenter Bericht

`qb_cubie.reporter.JsonReporter(path)` implementiert das bestehende Reporter-
Protokoll. `report(run_trace)` schreibt einen einzelnen abgeschlossenen Lauf als
UTF-8-JSON. Ein fachliches Mismatch wird als `evaluation=false` persistiert und
löst in diesem Reporter keine Assertion aus. Schreibfehler propagieren als
`OSError`. Getrennte Zielpfade bewahren getrennte Läufe.

Der von den Cases verlangte minimale Austauschvertrag:

- Dokument: `schema_version: 1`, `run_id`, `expect`, `evaluation`, `traces`.
- Jeder Vergleich: `step_id`, `evaluation`, `post`, `outcome` und vorhandene `diffs`;
  `post.expect` bewahrt die Polarität. Kein Weglassen nicht passender Alternativen
  oder zusätzlicher Eingänge.
- `returns` unterscheidet `{"kind": "unspecified"}` von
  `{"kind": "value", "type": "builtins.NoneType", "value": null}`.
- Konkrete JSON-kompatible Rückgaben tragen `kind`, qualifizierten Python-Typ und
  `value`. Leere Tupel verwenden `value: []` mit `type: "builtins.tuple"`;
  `False`, `0`, leere Strings, Listen und Dictionaries behalten ihre Typen.
- Typ-, Regex- und Callable-Muster verwenden `kind: "pattern"`, `type` und eine
  nichtleere `description`. Der Bericht benötigt keine ausführbare
  Serialisierung, keinen Import des Targets und kein erneutes Ausführen von
  Prädikaten. Er beschreibt Beobachtungen; er ist kein wieder ausführbarer Test.
- `post.raises` enthält qualifizierten `type` und `match`;
  `outcome.exception` enthält qualifizierten `type` und `message`.
- FS-Diffs enthalten die beim Lauf ermittelten relativen Pfade und Kategorien.
  Berichtsausgabe und Lesen benötigen weder Workspace noch Referenzdateien.
  Die Dateien selbst werden dadurch nicht archiviert.

## Roter Ausgangsbefund am 10. November 2026

Python 3.13.12; Produktivcode unverändert. Die neuen Cases lassen sich so ausführen:

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/tests_ebt/test_ebt_contract_returns.py \
  tests/tests_ebt/test_ebt_exception_contracts.py \
  tests/tests_ebt/test_ebt_directory_topology.py \
  tests/tests_ebt/test_ebt_persistent_reports.py
```

| Fallgruppe | Bestanden | Fehlgeschlagen |
| --- | ---: | ---: |
| Rückgaben | 18 | 0 |
| Ausnahmeverträge | 4 | 39 |
| FS-Topologie | 4 | 5 |
| Persistente Berichte | 0 | 17 |
| **Gesamt** | **26** | **61** |

Die 61 Fehlschläge gliedern sich in 40 fehlende `ExceptionExpectation`-Imports
(einschließlich eines JSON-Integrationsfalls), 16 fehlende `JsonReporter`-Imports
und fünf mit vorhandener API reproduzierte FS-Abweichungen. Die fehlenden Imports
sind offene Implementierungsanforderungen; sie belegen noch keinen ausgeführten
Vergleich der jeweiligen neuen Semantik. Die fünf FS-Fälle zeigen:

1. Fehlendes leeres Unterverzeichnis bleibt unbemerkt.
2. Zusätzliches leeres Unterverzeichnis bleibt unbemerkt.
3. Fehlendes verschachteltes leeres Unterverzeichnis bleibt unbemerkt.
4. Verzeichnis → Datei wird als `unexpected` statt `modified` klassifiziert.
5. Datei → Verzeichnis wird als `missing` statt `modified` klassifiziert.

Zusätzlich bestanden **143 vorhandene Tests** aus `test_ebt_returns.py`,
`test_ebt_return_reporting.py` und `tests_user_workflows/test_fs_reporting.py`.
Ruff für die vier neuen Python-Dateien: **ohne Befund**. Ein vollständiger Lauf
der gesamten Repository-Testsuite wurde für diese reine Case-Erweiterung nicht
ausgeführt. Die neuen Soll-Cases ließen die Suite bis zur Implementierung bewusst
rot; sie waren weder übersprungen noch als erwartete Fehlschläge markiert.

## Implementierung und grüne Prüfung am 10. November 2026

Die ursprünglichen 87 Soll-Cases bestanden nach der Implementierung vollständig.
Die anschließende gezielte Abschlussprüfung umfasst zusätzlich echte
PyVenv-Ausführungen mit allen drei Codecs sowie vertiefte Serializer-Cases:

| Fallgruppe | Bestanden | Fehlgeschlagen |
| --- | ---: | ---: |
| Rückgaben | 18 | 0 |
| Ausnahmeverträge | 43 | 0 |
| FS-Topologie | 9 | 0 |
| Persistente Berichte | 20 | 0 |
| PyVenv/Codec-Grenzen (`tests/tests_arena/test_exception_observations.py`) | 18 | 0 |
| **Gezielte Abschlussprüfung** | **108** | **0** |

Die zusätzlichen Cases prüfen benutzerdefinierte, nur im Workspace verfügbare
Exception-Klassen, unpassende Exceptions und normale Rückgaben, FS-Nebenwirkungen
vor einer Exception sowie Import- und Serialisierungsfehler. Die PyVenv-Basis wird
lokal mit `venv` und vorhandenen Paketen vorbereitet; es erfolgt keine Installation.
Serializer-Cases prüfen rekursive Typinformation, Nicht-String-Schlüssel, Zyklen,
unveränderte vorhandene Berichte bei fehlgeschlagener Ersetzung und die
Unterscheidung eines zurückgegebenen Callables von einem erwarteten Prädikat.
Die Ausgabe führt das Prädikat nicht erneut aus.

Der vollständige Lauf mit `.venv/bin/python -m pytest -q --tb=short` ergab
**1.145 bestanden, 11 übersprungen, 6 Warnungen** in 251,31 Sekunden. Dieser Lauf
wurde vor der letzten Serializer-Verfeinerung und ihrem zusätzlichen Test
gesammelt; danach wurden sämtliche 108 gezielten Cases erneut erfolgreich geprüft.
Das neue ausführbare Dokumentationsbeispiel wurde ebenfalls erfolgreich ausgeführt.

Ruff ist für die neue Produktivdatei und alle neuen Testdateien ohne Befund.
Ein Vergleich der geänderten vorhandenen Produktivdateien gegen `HEAD` ergab
keine zusätzlichen Ruff-Befunde; vorhandene Stilbefunde wurden nicht pauschal
bereinigt. `git diff --check` ist ohne Befund.
