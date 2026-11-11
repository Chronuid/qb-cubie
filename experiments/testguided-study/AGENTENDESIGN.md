# Agenten iterativ entwickeln, anschließend Nutzen messen

Status: Die Basisverträge D01–D08 und ihre Anbindung an Freeze, Session und
Bericht sind implementiert. Die hier beschriebenen ersten beiden Piloten bleiben
historische v1-Versuche. Inzwischen liegt mit `20261111-163110` ein abgeschlossener
Pilot des Kerns v2 vor; die [aktuelle Pilotanalyse](PILOTANALYSE-20261111.md)
dokumentiert seine Ergebnisse und das daraus entwickelte v3-Konzept.
Die folgenden Befund- und Entwurfsabschnitte dokumentieren den Ausgangspunkt;
der Umsetzungsstand am Ende beschreibt die damaligen Änderungen.

## Befund am bestehenden Aufbau

`launch.py` orchestriert Auswahl, Aufbereitung, Imagebau, Zulassung, Freeze und
Ausführung. `admission.py`, `backend.py` und `workspace.py` trennen sichtbare
Aufgabenarbeit von privaten Referenz- und Regressionstests. `artifacts.py` friert
Eingaben, Guides, Reihenfolge, Seeds und Implementierungshashes ein.
`execution.py` führt gepaarte Läufe durch; `telemetry.py`, Monitor und `report.py`
sichern Beobachtbarkeit und Ergebnisbelege. Diese Infrastruktur weiterverwenden.

Die zwei Agenten sind aktuell zwei Bedingungen derselben Funktion
`agent.develop`: gleicher Prompt und JSON-Aktionsraum aus `design.py`, jeweils
mit Guide aus `guides/pytest.md` oder `guides/cubie.md`. Das ist für einen
kontrollierten Vergleich sinnvoll. Als Entwicklungsarchitektur fehlen jedoch
explizite, unabhängig identifizierbare Varianten von Kern und Spezialisierung.
`VERSION` ist ein Label; es wird kein konfigurierbares Designobjekt aufgelöst.
Änderungen verlangen heute Änderungen am gemeinsamen Python-Code oder Guide.

Die Schleife lässt das Modell pro Aufruf eine Aktion wählen. Sie hat keine
persistente Arbeitshypothese, Fortschrittskontrolle oder begrenzte Reparatur
ungültiger Aktionen. `stage` ist ausdrücklich nur ein Modelllabel. `messages()`
behält die Aufgabe und jüngste vollständige Austausche, verwirft aber ältere
Erkenntnisse. Das Bytebudget ersetzt keine Tokenmessung; auch der nachträglich
angehängte Auslassungshinweis wird nicht erneut gegen dieses Budget geprüft.
Dateien werden vollständig überschrieben. Suche ist global und literal, auf
80 Treffer begrenzt; lange Ergebnisse werden als abgeschnittener JSON-Text
zurückgegeben. Das erschwert gezielte Navigation und kleine Änderungen.

Profil `pilot.toml`: Gemma4:12b, 24 Modell- und Werkzeugaufrufe, 600 Sekunden,
40.000 Kontextbytes, 12.000 Ausgabezeichen. Allein längere Budgets adressieren
keine wiederholten Aktionen ohne neue Erkenntnis.

Konkrete Belege aus `runs/20261111-132401/frozen/runs` (erster Pilot):

| Lauf | Bedingung / Aufgabe | Beobachtung | Ende |
| --- | --- | --- | --- |
| 0001 | Cubie / fastapi_9425 | 24 Suchen | model_budget |
| 0002 | pytest / fastapi_9425 | 22 Suchen, 2 Leseaktionen | model_budget |
| 0003 | pytest / requests_6589 | 20 Testläufe, 4 Such-/Leseaktionen | model_budget |
| 0004 | Cubie / requests_6589 | 20 Testläufe, 4 Such-/Leseaktionen | model_budget |
| 0005 | Cubie / rich_3278 | 5 Suchen, 2 Leseaktionen | invalid_output |
| 0006 | pytest / rich_3278 | 12 Testläufe, 12 Such-/Leseaktionen | model_budget |

Keiner dieser Läufe schrieb oder löschte eine Datei; alle sechs privaten
Evaluationen ergaben `resolved=false`. Bei 0005 meldet Ollama `length`: eine
sehr lange Suchanfrage erschöpfte die Ausgabe. FastAPI-Suchen liefern teilweise
abgeschnittene Ergebnisse aus Dokumentation. Die bereits abgeschlossenen Läufe
0001–0005 des zweiten Piloten `20261111-160158` zeigten bei der Sichtung erneut
keine Dateiänderung. Das ist eine Zwischenbeobachtung, keine abschließende
Auswertung dieses laufenden Versuchs.

Die Daten begründen vorrangig bessere Navigation, Fortschrittsfeedback und
Aktionsreparatur. Sie isolieren weder einen Modell- noch einen Guidefehler als
alleinige Ursache. Eine höhere Lösungsquote durch v2 ist erst nachzuweisen.

## Zielarchitektur

Ein Design ist die Zusammensetzung eines gemeinsamen Kerns und einer
Frameworkspezialisierung. Beide bestehen aus versionierten, validierten Daten.

- `CoreSpec`: Basisprompt, erlaubte Tools, gemeinsame Ablaufpolitik,
  Kontextstrategie. Der Inhalt wird kanonisch gehasht.
- `SpecializationSpec`: Framework, Guide, Beispiele und eigene Revision. Keine
  versteckten Überschreibungen von Tools, Budgets oder gemeinsamer Ablaufpolitik.
- `ResolvedDesign`: unveränderlicher Snapshot beider Komponenten samt SHA-256;
  Run-ID und Design-ID sind getrennte Identitäten.
- `AgentSession`: führt den aufgelösten Entwurf mit injizierten Ports für
  Modell, Workspace, Uhr und Belegsicherung aus. Kein Zugriff auf private Tasks.
- `Campaign`: Entwicklungsversuche oder festgeschriebener Vergleich, mit
  Taskpool, Seeds, Budgets, konkreten Designs und Herkunft der Varianten.

Die bisherigen Sicherheitsgrenzen, Evaluationsregeln und freie Bearbeitbarkeit
sichtbarer Tests bleiben erhalten. Spezialisierungen dürfen die Herangehensweise
an pytest bzw. EBT verbessern, einschließlich der Beispiele für Rückgaben,
Exceptions und Dateisystemverhalten. Gemeinsame Navigation, Aktionsreparatur und
Kontextpflege werden einmal entwickelt und für beide Bedingungen genutzt.

Für den eigentlichen Nutzenvergleich bleibt ein gemeinsamer Kern verpflichtend.
Das Ergebnis misst dann Cubie samt seiner Anleitung gegenüber pytest samt
seiner Anleitung. Vergleiche unterschiedlicher Kerne sind Entwicklungsversuche;
sie erlauben keine isolierte Zuschreibung an Cubie. Eine zusätzliche Guideablation
wäre ein eigener vorab definierter Vergleich.

## Arbeitszyklus und Werkzeugergonomie

1. Sichtbare Aufgabe und relevante Dateien lokalisieren; gezielten Bestandstest
   ausführen. Kurzes Arbeitsledger: Hypothese, relevante Dateien, Testbeleg,
   nächste Aktion und offene Fragen.
2. Fehlendes Verhalten durch einen gezielten Test ausdrücken. Collection-/Import-
   und Syntaxfehler führen zur Testreparatur; beobachtetes Assertion-Rot zur
   Implementierung. Kein starres Verbot späterer Teständerungen.
3. Kleine Änderung, gezielter Test, relevante Regression, begründete Abgabe.
   Beobachtungen bestimmen Feedback; Modelllabels beweisen keinen Fortschritt.
4. Gleiche Aktion und gleiches Ergebnis bei unverändertem Workspace lösen nach
   drei Wiederholungen einen gezielten Hinweis aus. Nach einer begrenzten
   weiteren erfolglosen Umplanung beendet die Session mit `stalled`. Auch
   wechselnde Suchbegriffe können Stillstand bedeuten; zunächst getrennt messen.
5. Ungültige JSON-/Schemaausgabe erhält höchstens eine Reparaturchance mit
   konkretem Validatorfehler, innerhalb derselben Aufruf-/Zeitbudgets. Transport-
   fehler und fehlende Infrastruktur werden nicht als Modellfehler repariert.

Suchwerkzeuge um Pfadfilter und Fortsetzung erweitern, strukturierte Ergebnisse
an Eintragsgrenzen begrenzen und Fortsetzung anzeigen. Ein exakt verankertes
Ersetzungswerkzeug soll kleine Änderungen ohne komplette Dateireproduktion
ermöglichen: nur bei eindeutig passendem alten Text schreiben, sonst Fehler
und unveränderter Workspace. Alle Operationen laufen weiter im Container.
Diese Werkzeuge in beiden Bedingungen identisch anbieten und separat durch
Workspace-Verträge testen, bevor sie in einen Vergleich aufgenommen werden.

Kontextaufbau reserviert Platz für Aufgabe, System/Guide, Ledger und die jüngste
vollständige Aktion mit Beobachtung. Ältere Austausche werden ganz entfernt.
Jede tatsächlich gesendete Anfrage bleibt unter dem UTF-8-Bytebudget;
Tokenizer-/Providerzählwerte zusätzlich archivieren. Passt der Pflichtkontext
nicht, expliziter Kontextabbruch. Ledger ist sichtbare, überprüfbare Arbeitsnotiz,
keine Quelle für private Referenzinformationen.

## Entwicklungs- und Freigabeprozess

Entwicklung nutzt ausschließlich Pilot-/Entwicklungsaufgaben, inklusive kleiner
synthetischer Aufgaben und ausgewählter realer Aufgaben. Pro Iteration eine
Hypothese, Elternrevision, Änderung und festgelegtes Abnahmekriterium speichern.
Gemeinsamen Kern zunächst an beiden Frameworks prüfen, danach Spezialisierungen
mit eingefrorenem Kern verbessern. Regressionen pro Aufgabentyp betrachten.

Vor einer Hauptmessung einen eigenen Qualifikationsplan festschreiben, etwa
mindestens zwei verschiedene reale Entwicklungsaufgaben je Bedingung unabhängig
lösen, mit mindestens einem beobachteten verhaltensprüfenden Testzyklus und ohne
fehlende technische Ergebnisse. Schwellen und Aufgaben vor der Qualifikation
wählen. Eine Bool-Angabe im unten beschriebenen API ist nur die Projektion eines
archivierten Qualifikationsnachweises, keine manuelle Erfolgserklärung.

Entwicklungsaufgaben und verwandte Fixgruppen sperren für die Hauptmessung.
Nach jeder Anpassung infolge einer Messaufgabe gilt auch diese als verbraucht.
Erst nach bestandener Qualifikation beide Designs, Budgets und unberührten
Aufgabenpool einfrieren. Unterschiede der Erfolgsquote dürfen nicht durch
Nachziehen besonders passender Aufgaben optimiert werden. Kein automatischer
Gewinner aus Entwicklungsdaten.

Entwicklungsberichte gruppieren nach Design-ID und Phase. Falsche Lösungen,
fehlende Infrastruktur, Kontext-/Zeit-/Aufruflimits, ungültige Aktionen und
Stillstand unterscheiden. Null-Erfolge bleiben wertvolle Diagnostik, erlauben
aber noch keinen aussagekräftigen Vergleich des beabsichtigten Nutzens.

## Ausführbare EBT-Anforderungen

Die regulär gesammelte Suite liegt unter
`tests/testguided_study_design/test_iteration_ebt.py`. Sie formuliert bewusst
rote Sollverträge ohne Skip, xfail oder Ersatzimplementierung. Imports erfolgen
im einzelnen Fall, damit fehlende APIs nicht die übrige Sammlung verhindern.
Die vorgeschlagene Fassade `testguided_study.iteration` bündelt folgende
Schnittstellen; intern können die Verantwortlichkeiten getrennte Module werden.

| ID | API und verbindliche Beispiele |
| --- | --- |
| D01 | `compose(core, specialization)` kopiert die Komponenten nach `core` und `specialization`, ohne Eingaben zu verändern; beide Frameworks |
| D02 | Fremdfelder der Spezialisierung (`tools`, `policy`, `prompt`, `context`) ergeben `ValueError` mit `specialization` |
| D03 | `identity(design)` ergibt kanonisches SHA-256-Hex; jede getestete inhaltliche Änderung ändert es, Schlüsselreihenfolge nicht |
| D04 | `context(system, issue, exchanges, ledger, capacity)` ergibt Chatnachrichten: System, Aufgabe samt Ledger, vollständige jüngste Austausche; vollständige Serialisierung innerhalb des Bytebudgets; unmöglicher Pflichtkontext ergibt `ValueError` mit `context` |
| D05 | `progress(events, repeat_limit)` ergibt nach drei gleichen Such-/Grün-Belegen bei gleichem Workspace `redirect`, bei invalidem Testlauf `repair_test`, bei Assertion-Rot `implement`; neuer Workspace unterbricht Wiederholungen (`continue`) |
| D06 | `validate_campaign(config)` ergibt `None` für zulässige Kampagnen, sonst `ValueError` mit Grund; Messung verlangt gemeinsamen Kern, gleiche Budgets, Qualifikation, keine Entwicklungsaufgaben oder verwandten Gruppen; Entwicklung erlaubt unterschiedliche unqualifizierte Kerne |
| D07 | `summarize_trials(rows)` trennt Design und Phase und zählt geplant, gelöst und nicht verfügbar; `False` und `None` werden unterschieden |
| D08 | `freeze_design(design, path)` schreibt neues JSON mit `design` und `identity`; `load_design(path)` validiert Hash und liefert Design; Quellmutation beeinflusst Snapshot nicht, Überschreiben und Manipulation werden abgewiesen |

Die Fassade soll von Freeze, Session und Report tatsächlich verwendet werden;
parallel geführte, nur für Tests implementierte Logik erfüllt die Überarbeitung
nicht. Die Cases sichern diese Basisverträge, noch keine bessere Modellleistung.

## Reihenfolge der Umsetzung und weitere Abnahmen

1. D01–D03, D08: Designauflösung und Freeze einführen, bisheriges v1-Verhalten als
   explizite Variante erhalten. Keine laufenden Archive migrieren. Danach Freeze-
   und Lifecycle-Integration auf Design-IDs erweitern, inklusive manipulierter
   Snapshots und einer neuen Variante ohne Änderung alter Belege.
2. D04–D05: Kontext-/Fortschrittskomponenten an `develop` anschließen. Ein
   deterministisches Session-Replay muss wiederholte Suche → Hinweis → Lesen →
   Test → Änderung → Grün → Abgabe belegen. Zweites Replay muss nach weiterem
   Stillstand begrenzt enden; drittes repariert eine ungültige Ausgabe und zählt
   auch diesen Modellaufruf. Anschließend echte Docker-Gegenprobe.
3. D06–D07: Entwicklungsmodus, Vergleichszulassung und getrennte Berichte in
   CLI und Launcher integrieren. Qualifikationsnachweise an konkrete Design-,
   Aufgaben-, Evaluator- und Budgetidentitäten binden; keine Freigabe bei Drift.
4. Navigation und verankerte Änderungen mit realen Workspace-Tests ergänzen.
   Anschließend neue lokale Entwicklungsversuche, dann Qualifikation. Keine
   Behauptung erfolgreicher Agentenoptimierung aus deterministischen Replays.

Die jetzige Änderung liefert den Entwurf und die 29 konkreten EBT-Beispiele für
seine Basisverträge. Die hier benannten Integrationsabnahmen sind zusätzliche
Arbeit bei der Implementierung, keine bereits bestandenen Tests.

Achtung beim laufenden Pilot: `artifacts.sources()` hasht sämtliche Python-Dateien
unterhalb des Experimentverzeichnisses, einschließlich seiner Tests.
`execution.run()` prüft vor jedem Lauf erneut. Deshalb stehen die neuen Python-
Cases außerhalb dieses Baums. Markdown wird dort nicht gehasht. Die breit
angelegte Quellhashprüfung sollte später durch ein explizites Manifest relevanter
Laufzeitmodule ersetzt werden; eingefrorene historische Belege bleiben erhalten.

## Verifikation dieser Anforderungsänderung

- `.venv/bin/python -m pytest tests/testguided_study_design --collect-only -q`:
  29 Cases regulär gesammelt.
- `.venv/bin/python -m pytest tests/testguided_study_design -q --tb=no`:
  29 rot, weil `testguided_study.iteration` noch fehlt. Keine Aussage über eine
  bereits umgesetzte v2-Architektur.
- `.venv/bin/python -m pytest experiments/testguided-study/tests -q`:
  57 bestanden, 3 Docker-Integrationstests übersprungen.
- `.venv/bin/ruff check tests/testguided_study_design`: bestanden.

Die erste Implementierungsaufgabe ist damit die vorgeschlagene Fassade; danach
werden die einzelnen Verhaltensverträge wirksam. Ein grüner Import allein genügt
nicht: Alle Rückgaben, Exceptions und Dateieffekte bleiben verbindlich geprüft.

## Umsetzungsstand Produktcode

`iteration.py` implementiert D01–D08. `design.py` liefert einen gemeinsamen
Standardkern v2, pro Framework eine Spezialisierung und den aus dem Design
abgeleiteten Aktionsraum. Eigene aufgelöste Designs sind über `[designs]` in der
TOML auswählbar. `artifacts.freeze` erstellt inhaltsadressierte Snapshots und
bindet Design-, Kern-ID und Phase an jede Zeile des Laufplans.

`agent.develop` verwendet diese Snapshots, die Kontextfunktion und das
beobachtungsbasierte Feedback. Die Arbeitsnotiz kann mit `update_ledger`
aktualisiert werden. Nach drei unveränderten Aktionen erscheint ein Hinweis;
nach sechs endet der Lauf mit `stalled`. Pytest-Zeitangaben und das Modelllabel
`stage` erzeugen keinen künstlichen Fortschritt. Ungültige Modellausgaben werden
höchstens einmal repariert; dieser Aufruf zählt gegen die bisherigen Grenzen.
Die optional injizierbare Uhr erlaubt deterministische Deadline-Abnahmen.

Die Werkzeuge `search_files(path, query, start)` und
`replace_text(path, old, new, reason)` bieten pfadbezogene, fortsetzbare Suche
und exakt verankerte Änderungen innerhalb der bestehenden Workspacegrenzen.
Ausgabebegrenzungen erhalten strukturierte Treffer und Fortsetzungspositionen.

`campaign.py` verbindet die Vergleichszulassung mit archivierten Belegen statt
mit selbst deklarierten Boolwerten. Feste Schwelle: zwei reale unabhängige
Aufgabengruppen pro Bedingung, privat gelöst und mit einem beobachteten
Assertion-Rot-/Grün-Zyklus für dieselben Testziele bei geändertem Workspace.
Vollständige Verfügbarkeit, konkrete Designs und gleiche Umgebung/Budgets sind
verpflichtend. Im Messungs-Preflight wird die tatsächliche Modell-/Image- und
swegemma-Identität erneut verglichen. Qualifikationsprojektion, Aufgaben,
Ergebnisse und Belegmanifeste werden im neuen Freeze gesichert.

`phase = "development"` erlaubt Entwicklungsversuche mit Pilot-/Entwicklungs-
aufgaben und unterschiedlichen Kernen. Ein Messungs-Freeze ohne Kampagnenbelege
wird abgelehnt. Die Liste der verbrauchten Entwicklungsarchive bleibt eine
explizite Herkunftsangabe; es gibt keine automatische globale Taskverbrauchs-
datenbank. `report.by_design` trennt Varianten und Phasen sowie falsche und
nicht verfügbare Ergebnisse.

Die Quellidentität umfasst jetzt die beiden Laufzeitpakete und `study.py`;
Teständerungen führen nicht mehr zu Laufzeitdrift. Alte Archive werden nicht
umgeschrieben. Ihre bestehende Implementierungsbindung wird nicht aufgehoben.
Die alte Promptkonstante bleibt im Quellcode erhalten; neue Standard-Freezes
verwenden v2. Ein historisch identischer v1-Lauf erfordert den historischen
Quellstand, einschließlich seiner bisherigen Implementierungsbindung.

Die 29 ursprünglichen Sollverträge bestehen nun. Zusätzliche Integrationstests
prüfen produktive Session-/Freeze-/Berichts-/Zulassungspfade und die ausgelieferte
Workspaceimplementierung. Die ursprünglichen roten Testergebnisse oben bleiben
als Dokumentation des Ausgangsstands erhalten. Kein automatischer fachlicher
Pilot wurde gestartet; Modellleistung und optimale Spezialisierungsanleitungen
bleiben empirisch zu untersuchen.

Abnahme des Produktstands:

- Studien- und Design-/Integrationstests zusammen: **128 bestanden**, drei
  Docker-Cases im normalen Lauf übersprungen.
- Die drei Docker-Cases mit der vorhandenen swegemma-Umgebung separat ausgeführt:
  **3 bestanden** (Modellantworten als Replay, echte Container und Evaluation).
- Ruff für Experiment und neue Tests sowie `git diff --check`: bestanden.


## Weiterentwicklung auf Kern v3

Das [Konzept aus dem letzten Pilot](PILOTANALYSE-20261111.md) ist inzwischen in
`controller.py`, Session, Werkzeugen und beiden Guides umgesetzt. Neue Standard-
Freezes verwenden `testguided-core-v3`; explizite Designs mit Kontextstrategie
`ledger` Version 1 bleiben als Legacy-Varianten ausführbar. Historische Archive
werden nicht migriert und bleiben an ihre ursprünglichen Laufzeitquellen gebunden.

V3 koppelt optionale kurze Notizen an echte Aktionen. Der Controller hält Fakten,
Arbeitszustand, Fehlversuche und Belegversionen separat. Zwei gleiche Versuche
lösen beim nächsten unveränderten Aufruf eine budgetierte Ablehnung aus;
anhaltender Stillstand beendet den Lauf. Änderungen an Tests bleiben erlaubt.
Die verankerte Ersetzung benötigt nun den zuvor gelesenen SHA-256-Wert.

Neue Werkzeuge: `find_paths`, `search_content`, `collect_tests`, `check_baseline`.
Testresultate enthalten einzelne Diagnosen und Laufzeitbelege der EBT-Ausführung.
Die Qualifikation für v3 bindet Rot und Grün an dieselbe Testversion und eine
Produktionsänderung oder eine beobachtete rote Ausgangscode-Gegenprobe.
Der Providerverbrauch bleibt gemessen; die Kontextreserve ist eine konservative
Schätzung ohne Garantie gegen providerseitige Trunkierung. Die Controllerzustände
und Frameworkzähler beweisen weder Oraclequalität noch universelle Korrektheit.

Die Guides verwenden vergleichbare Wert-, Exception- und Dateibeispiele.
Zusätzliche Tests führen diese Beispiele mit korrekten und falschen Funktionen
aus und prüfen echte EBT-Ergebnisse. Ein neuer fachlicher Pilot wurde durch diese
Implementierung nicht gestartet; die Wirksamkeit mit Gemma4 bleibt zu messen.


Technische Abnahme von v3:

- Studien-, Design- und Regressionstests: 145 bestanden; drei Docker-Cases im
  normalen Lauf übersprungen.
- Die drei Docker-Cases separat mit echter swegemma-Umgebung: drei bestanden,
  einschließlich EBT-Ausführung, Baseline-Reproduktion der finalen Tests und
  unabhängiger Evaluation beider Bedingungen. Nur die Modellantworten sind Replays.
- Beide Guides mit korrekten und absichtlich falschen Implementierungen geprüft.
- Ruff und `git diff --check` bestanden.
