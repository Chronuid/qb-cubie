# Eigene Agenten und Szenarien: Nutzungsexperiment zu 10.3

Stand: 10. November 2026. Urteil aus Nutzerperspektive: Abschnitt 10.3 ist im
Kern gut umgesetzt. Ein eigener echter Modellagent und eigene Aufgaben lassen
sich ohne Core-Änderung anbinden, auch aus einer Wheel-Installation außerhalb
des Repositorys. Eine uneingeschränkte Abnahme würde ich wegen eines beobachteten
Fehlurteils im Rot-Prozess und einiger Lücken bei Diagnose und Reproduzierbarkeit
noch nicht geben.

Ich habe die öffentliche Anleitung als Einstieg verwendet, mit `init-scenario`
eine Entwicklungsvorlage und mit `init-example` die JSONL-Protokollvorlage
exportiert. Die eigentliche Implementierung liegt unter
[examples/ollama-user-benchmark](../examples/ollama-user-benchmark/README.md).
Cubies Produktcode und vorhandene Tests wurden nicht verändert. Die Untersuchung
ist ein praktischer Nutzungstest, keine umfassende Prüfung aller Zusagen in 10.3.

## Versuchsaufbau und Reproduktion

Getestet wurde qb-cubie 0.0.3 aus einem frisch lokal gebauten Wheel, Python 3.14.3,
Ollama 0.40.2 und `gemma4:12b` mit Q4_K_M, Modelldigest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
Das Wheel wurde mit `uv build --wheel --out-dir /tmp/cubie-user-wheel` gebaut
und mit `uv pip install --python /tmp/cubie-user-env/bin/python
'/tmp/cubie-user-wheel/qb_cubie-0.0.3-py3-none-any.whl[benchmarks]'` installiert.
Die Bibliothek stammt damit aus diesem Arbeitsstand, nicht aus einer eigens
geprüften PyPI-Veröffentlichung.

Das Beispiel wurde nach `/tmp/cubie-user-external` kopiert und dort ausgeführt.
`validate-agent`, `validate --check-references`, `plan`, `run` und `compare`
wurden verwendet; `guide` war ebenfalls aus der Installation verfügbar.
Die Referenzprüfung akzeptierte beide Lösungen und ihre gezielten Mutanten.
Auswahl über `types_any=["business_rules"]` und `tags_all=["boundary"]` ergab
exakt zwei Versuche. Ein Agent, eine Wiederholung, ausschließlich Bedingung
`cubie`; kein zweiter Agent und kein Produktvergleich waren nötig.

Der Agent verwendet die Python-Standardbibliothek und Ollamas
[Chat-API](https://docs.ollama.com/api/chat). Temperatur 0, Seed 42,
`think=false`, maximal 4096 Ausgabetokens; der Server meldete 4096 Kontexttokens.
Diese Einstellungen sind keine Garantie identischer Wiederholungen.

| Eigenes Szenario | Fachlicher Vertrag | Unabhängige Referenzprüfung |
| --- | --- | --- |
| Backup-Aufbewahrung | `expired(age_days, retention_days)`: inklusive Grenze, negative Werte ergeben ValueError | Grenze einschließlich 0, beide negativen Argumente; Mutant mit `>` statt `>=` |
| Telefonabrechnung | `billable_minutes(seconds)`: auf volle Minuten aufrunden, 0 bleibt 0, negative Werte ergeben ValueError, große Ganzzahlen exakt | 0, 1, 60, 61, `10**30+1`, negative Eingabe; Mutant mit Abrunden |

Die Aufgaben sind kleine realistische Geschäftsregeln, keine produktionsreifen
Backup- oder Telefonanlagen. Die Abnahmen sind unabhängig vom Modell geschrieben,
aber nur `author_checked`. Ein gezielter Mutant pro Aufgabe ist keine vollständige
Mutationsabdeckung. Die Ergebnisse erlauben keine allgemeine Modellrangliste.

## Experimente und beobachtete Ergebnisse

Zunächst war VRAM durch ein anderes Modell belegt. Ollama meldete für Gemma nur
128 MB GPU-Anteil bei rund 8,1 GB Modellspeicher. Zwei frühe Versuche wurden nach
der Rückmeldung des Nutzers gezielt abgebrochen; daraus leite ich kein Urteil
über Modellqualität oder Cubies Laufzeitverhalten ab. Nach Freigabe des VRAM
wurde Gemma entladen und neu geladen. `/api/ps` bestätigte anschließend
`size == size_vram == 8063046122`. Die folgenden Archive stammen aus GPU-Läufen.

| Lauf | Abrechnung | Aufbewahrung | Exitcode |
| --- | --- | --- | --- |
| V1: freies JSON mit Dateizuordnung | Infrastrukturfehler: unerwarteter Pfad | Infrastrukturfehler: zusätzliche Zeichen nach JSON | 3 |
| V2: JSON-Schema mit festem Ziel | Qualität bestanden, Prozess nicht bestanden | Qualität bestanden, Prozess nicht bestanden | 0 |

[V1-Bericht](../examples/ollama-user-benchmark/evidence/76b469c2c0ce4832afb36256e47402c6/report.md),
[V2-Bericht](../examples/ollama-user-benchmark/evidence/0553435a98a04a74a1634504eaf18465/report.md).
Beide Archive enthalten Requests, Responses, stderr, Eingaben und Ergebnisse;
V2 zusätzlich Phasensnapshots und tatsächliche Testbeobachtungen. Die externen
Skriptdateien habe ich zusätzlich als `agent-v1.py` und `agent-v2.py` gesichert.

V1 war ein Fehler meines Adapters: Das Modell lieferte bei der Abrechnung
`test_project.py` statt des erlaubten `tests/test_project.py`, beim zweiten Fall
ungültiges JSON mit nachfolgendem Spezialtoken. Der Adapter verweigerte die
Abgabe. Cubie meldete korrekt den abgebrochenen Agenten, stdout ohne Event und
Exitcode 1 des Unterprozesses. Die eigentliche Ursache fand ich im stderr-Archiv.
V2 lässt nur einen Quelltextstring im JSON-Schema erzeugen und bestimmt das Ziel
selbst. Es wurden keine Referenzlösungen eingespeist oder Modelltests nachträglich
von Hand korrigiert.

V2 benötigte rund 36,8 Sekunden für Abrechnung und 17,2 Sekunden für Aufbewahrung.
Gemessener Verbrauch: 1518/869 beziehungsweise 1045/369 Eingabe-/Ausgabetokens.
Kosten bleiben `null`. Beide Produktionsmodule bestehen die privaten Kriterien.
Bei der Abrechnung generierte Gemma jedoch zwei falsche Testorakel für große
Zahlen: Beispielsweise wird `10**18` abgerundet statt aufgerundet erwartet.
Deshalb bleiben die eingefrorenen Agententests in Grün und Refactoring rot.
Dies ist ein nachvollziehbarer Agentenfehler trotz fachlich korrekter Implementierung.

## Wichtigster Befund: fachliches Rot wird als Testfehler bewertet

Bei der Aufbewahrung scheitern in Rot zwei EBT-Assertions am fehlenden Verhalten;
drei weitere Tests melden `Failed: DID NOT RAISE ValueError`. Das sind erwartete
fachliche Fehler des Ausgangsstubs. Es gibt keinen Syntax- oder Importfehler.
Dennoch lautet `test_outcome="test_error"`, und der Prozess wird mit
`No observed assertion failure in red phase` abgelehnt. Die Assertion-Fehler sind
im selben Beleg explizit enthalten. Anschließend bestehen alle sechs Agententests
in Grün und Refactoring sowie die unabhängigen Abnahmen.

[Rot-Beobachtung](../examples/ollama-user-benchmark/evidence/0553435a98a04a74a1634504eaf18465/episodes/0002/red/observation.json),
[Prozessergebnis](../examples/ollama-user-benchmark/evidence/0553435a98a04a74a1634504eaf18465/episodes/0002/result.json).

Aus Anwendersicht ist das ein falsches negatives Prozessurteil für normale
pytest-Exceptiontests. Vor vollständiger Abnahme sollte Cubie fehlende erwartete
Exceptions als fachliches Scheitern akzeptieren und echte Testinfrastrukturfehler
weiterhin gesondert behandeln. Das Beispiel bleibt als reproduzierbarer Beleg
unverändert; ich habe den Fehler nicht durch angepasste Tests verdeckt.

## Bewertung der Zusagen und Nutzererfahrung

| Zusage aus 10.3 | Praktischer Befund |
| --- | --- |
| Eigener Prozessagent ohne Core-Änderung | Erfüllt: echter Ollama-Aufruf über eigenständigen JSONL-Prozess |
| Eigene Szenarien und Referenzvalidierung | Erfüllt für zwei Entwicklungsfälle, private Lösungen und Mutanten geprüft |
| Einstieg aus installiertem Wheel | Erfüllt mit eigenem lokal gebauten Wheel und separater Umgebung |
| Typ-/Tagfilter, ein Agent genügt | Erfüllt für positive Filter und zwei ausgewählte Fälle |
| Beobachtete Entwicklungsphasen | Belege vollständig vorhanden; Rot-Urteil bei Exceptiontests fehlerhaft |
| Laufvergleich | Archivvergleich funktioniert und meldet `full`; Textausgabe ist wenig aussagekräftig |
| Review-Agenten und alle Filtervarianten | In diesem Experiment nicht praktisch geprüft |
| Isolation, harte Kosten-/Tokenbudgets | Nicht geprüft; dokumentierte Grenzen bleiben bestehen |

Der [JSON-Laufvergleich](../examples/ollama-user-benchmark/evidence/comparison.json)
vergleicht V1 und V2 als vollständig kompatible Aufgaben. Die Textausgabe zeigt
pro Paar lediglich `{}`. Für mich fehlt hier eine sofort sichtbare Gegenüberstellung
von Infrastrukturstatus, Qualität und Prozessurteil. `full` beschreibt die
Vergleichbarkeit, keinen Erfolg und keine Leistungssteigerung. Beide Adapter
meldeten dieselbe ID und Version 1.0.0; die genauen Codevarianten sind deshalb
zusätzlich gesichert und sollten bei zukünftigen Experimenten versioniert werden.

Weitere konkrete Einstiegshürden:

- `validate-agent` bestätigte zunächst meine deklarierten Fähigkeiten; erst
  `plan` verlangte zusätzlich `cancel` und wegen des Budgets `tool_calls`.
  Das ist mit der Trennung von Handshake und Set-Prüfung erklärbar, sollte im
  Tutorial für reine Entwickleragenten ausdrücklich benannt werden.
- Ein echtes Modell benötigt einen eigenen Adapter mit Kontextaufbau,
  Ausgabevertrag, Schreibgrenzen und Tokenmessung. Das deterministische Beispiel
  hilft beim Protokoll, demonstriert diese Arbeit aber noch nicht.
- Der Bericht nennt `quality_passed`, aber das Prozessurteil muss man aus den
  Phasen und dem Erklärungstext erschließen. Ein explizites `process_passed`
  direkt neben der Qualität würde die Nutzung vereinfachen.
- Exitcode 0 trotz Prozessfehler entspricht der Anleitung, ist für CI jedoch
  leicht missverständlich. Anwender müssen die Ergebnisfelder auswerten.
- `model_id` bleibt im Ergebnis `null`; der Modellname ist nur in meinem Agenten
  und stderr dokumentiert. Modellversion, Digest, Serverversion und Adaptercode
  sollten Anwender zusätzlich sichern. Das Konfigurationsarchiv allein ersetzt
  kein vollständiges Agenten- und Providerabbild.

Meine Priorität wäre zuerst das Rot-Urteil zu korrigieren, danach ein echtes
lokales Modellbeispiel ins Tutorial aufzunehmen und Statusunterschiede im Bericht
und Vergleich sichtbar zu machen. Für eigene Entwicklungsfälle ist die Erweiterung
bereits nutzbar; ihre Prozessbewertung sollte derzeit anhand der Belege kontrolliert
werden.
