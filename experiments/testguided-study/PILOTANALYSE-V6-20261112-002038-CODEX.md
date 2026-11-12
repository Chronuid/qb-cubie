# Deskriptive Analyse des v6-Piloten 20261112-002038

**Herkunft der Analyse: Codex, GPT-Sol-6.1**  
**Analysedatum: 12. November 2026**  
**Untersuchtes Archiv:** `runs/20261112-002038`  
**Gegenstand:** beobachtete Abläufe, Dynamiken und gemeinsame Muster der sechs Agentendurchläufe.

## Datengrundlage und Abgrenzung

Das jüngste vorhandene Laufarchiv ist `20261112-002038`. Seine `launch.json` weist den Startmodus `pilot` mit `v6.toml` aus. Die eingefrorene Konfiguration nennt `agent_version = 6`, die Studien-ID `cubie-testguided-development-v6` und die Phase `development`. „Pilot“ bezeichnet hier den Startmodus; die archivierte Studienphase lautet weiterhin `development`.

Die Analyse beruht auf dem eingefrorenen Ablaufplan und Design, dem Abschlussbericht, den sechs Team- und Agentenständen, sämtlichen 65 Aktionsprotokollen sowie ergänzenden Modellantworten, Ergebnis- und Patchdateien. Implementierungsdetails der Stagnationserkennung wurden ergänzend im aktuellen `testguided_study/team.py` nachgelesen. Dieser Arbeitsstand ist von den archivierten Beobachtungen zu unterscheiden. Es wurden keine neuen Agenten- oder Testläufe gestartet und keine Arbeitsdateien der Agenten verändert.

Der Monitor dokumentiert einen abgeschlossenen Gesamtlauf: Beginn am 12. November um 00:20:38 Uhr, letzter Stand um 00:44:26 Uhr MEZ, entsprechend 23:20:38 bis 23:44:26 UTC am Vortag. Diese Spanne umfasst den Studienablauf und ist nicht mit der Summe der reinen Agentenlaufzeiten gleichzusetzen.

Drei Aufgaben wurden mit Seed 42 jeweils unter Cubie und pytest bearbeitet. Das Modell war `gemma4:12b` mit `think = false`, Temperatur 0,15 und maximal 8192 Ausgabetokens je Antwort. Pro Teamdurchlauf galten 900 Sekunden, 48 Modell- und 96 Werkzeugaufrufe; vorgesehen waren außerdem Reserven von 180 Sekunden und sechs Modellaufrufen. Das eingefrorene Design sieht seriell arbeitende Rollen `analysis`, `qa` und `dev` im gemeinsamen Arbeitsbereich vor.

## Überblick über die Durchläufe

| Lauf | Aufgabe | Arm | Agentenzeit | Modell-/Werkzeugaufrufe | Beobachtete Aktionen | Ende |
| --- | --- | --- | ---: | ---: | --- | --- |
| 0001 | FastAPI `fastapi_9425` | Cubie | 136,63 s | 8 / 8 | 8 Textsuchen | `incomplete`, `stagnation` |
| 0002 | FastAPI `fastapi_9425` | pytest | 207,13 s | 12 / 12 | 7 Textsuchen, 5 Dateilesungen | `incomplete`, `stagnation` |
| 0003 | Requests `requests_6589` | pytest | 46,24 s | 7 / 7 | 7 Textsuchen | `incomplete`, `stagnation` |
| 0004 | Requests `requests_6589` | Cubie | 45,12 s | 7 / 7 | 7 Textsuchen | `incomplete`, `stagnation` |
| 0005 | Rich `rich_3278` | Cubie | 531,37 s | 20 / 19 | 15 Textsuchen, 4 Dateilesungen | `incomplete`, `stagnation` |
| 0006 | Rich `rich_3278` | pytest | 112,57 s | 12 / 12 | 9 Textsuchen, 3 Dateilesungen | `incomplete`, `stagnation` |

Insgesamt stehen 66 Modellaufrufe 65 Werkzeugaufrufen gegenüber: 53 Textsuchen und zwölf Dateilesungen. 33 der 53 Suchaufrufe lieferten leere Trefferlisten. Alle Werkzeugaktionen wurden von der Analyse-Rolle ausgeführt. QA und Dev verzeichnen in jedem Teamstand jeweils null Modell- und Werkzeugaufrufe.

## Allgemeiner Ablauf

In allen sechs Durchläufen blieb der Teamzustand bei `orient`, der aktive Auftrag bei `orient-1` und die Kontextrevision bei null. Der beobachtete gemeinsame Ablauf war:

1. Die Analyse-Rolle wählte eine auf das Issue bezogene Quelldatei und Suchbegriffe.
2. Sie wiederholte Suchen oder ergänzte diese um Dateilesungen. Teilweise entstanden neue Treffer und neue gelesene Ausschnitte.
3. Wiederkehrende Ergebnisse lösten jeweils einen Recovery-Hinweis aus: eine andere relevante Quelle lesen oder eine gezielte Diagnose ausführen.
4. Anschließend folgten weitere Such- beziehungsweise Leseaktionen. Bei erneutem Wiederholungsmuster endete der Durchlauf mit `stagnation`.
5. Der unabhängige Evaluator prüfte anschließend den unveränderten Produktionsstand.

Es entstand keine Rollenübergabe. `messages.json` ist in allen sechs Durchläufen leer; Teamstände enthalten keine Cases, offenen Fragen oder ausstehenden Informationsanfragen. Kontextveröffentlichung, Suiteveröffentlichung, Implementierungsübergabe und Abschlussprüfung wurden nicht ausgeführt. Die Flags `reproduced` und `verified` blieben jeweils `false`.

Die vorhandene Mehrrollenstruktur blieb damit in diesem Archiv auf die Orientierungsphase der Analyse-Rolle begrenzt. Beobachtungen zu QA-/Dev-Zusammenarbeit, Teständerungsrunden oder Konfliktbehandlung liegen hier nicht vor.

## Verläufe der drei Aufgabenpaare

### FastAPI: Suchen und Lesen innerhalb derselben Routingdatei

Der Cubie-Durchlauf suchte zunächst viermal identisch nach `def get_response_class` in `fastapi/routing.py`, jeweils ohne Treffer. Nach dem Recovery-Hinweis lieferte die breitere Suche nach `response_class` zahlreiche Fundstellen. Danach wechselten sich die bereits verwendeten Suchanfragen ab. Der neue Trefferblock führte zu keiner Dateilesung oder Übergabe.

Der pytest-Durchlauf fand zunächst `def route` und las anschließend ab Zeile 860. Danach wechselte er zwischen der Suche nach `def add_api_route` und Dateilesungen mit demselben Beginn. Die angeforderten Endzeilen wurden zunächst von 950 auf 1100 und 1200 erweitert; später wurde der bereits gelesene Bereich wiederholt. Die Suchanfragen verwendeten `start = 860` und lieferten keine Treffer. Im ergänzend gelesenen Suchwerkzeugcode ist `start` ein Treffer-Offset; beim Dateilesen bezeichnet `start` dagegen die Startzeile. Die identischen Zahlenwerte sind daher unterschiedlich zu interpretieren. Ob das Modell diese Unterscheidung beabsichtigte, lässt sich aus dem Protokoll nicht feststellen.

Beide Verläufe blieben auf `fastapi/routing.py` beschränkt. Sie unterscheiden sich in der Art der Informationsaufnahme, stimmen aber im unveränderten Teamzustand und Abschlussgrund überein.

### Requests: Variation der Suchbegriffe bei durchgehend leeren Ergebnissen

Beide Arme suchten ausschließlich in `requests/utils.py`. Der pytest-Durchlauf begann mit `def super_len(value):` und verwendete anschließend überwiegend `def super_len`, einmal auch `super_len`. Der Cubie-Durchlauf variierte stärker zwischen `def super_len`, `super_len`, `def`, `def ` und `len`.

Alle 14 Suchaktionen des Aufgabenpaars lieferten leere Trefferlisten bei Werkzeugstatus `completed`. Keiner der beiden Durchläufe las die Datei direkt, prüfte die Verzeichnisstruktur oder führte eine Diagnose aus. Beide erhielten beim vierten Werkzeugaufruf den Recovery-Hinweis und endeten nach dem siebten mit `stagnation`.

Die Protokolle belegen die leeren Suchergebnisse und das Festhalten am Suchpfad. Sie belegen für sich genommen nicht, weshalb auch die breiten Suchbegriffe keine Treffer lieferten. Eine bestimmte Ursache im Quellbestand, Dateizugriff oder Suchwerkzeug wird deshalb hier nicht zugeordnet.

### Rich: mehrere Fundstellen und Dateilesungen vor erneuten Wiederholungen

Beide Arme untersuchten ausschließlich `rich/ansi.py`. Nach anfänglichen Suchen ohne Treffer fanden sie konkrete Stellen und lasen Teile der Datei.

Der Cubie-Durchlauf erreichte unter anderem die Tokenisierung, den Ausdruck mit `0-?`, die Verarbeitung von `sgr`, `SGR_STYLE_MAP` und die Bedingung `sgr.endswith("m")`. Später wurde die Suche nach dieser Bedingung mehrfach identisch wiederholt. Nach dem Recovery-Hinweis kam mit der breiteren Suche nach `sgr` ein weiterer Trefferblock hinzu; anschließend kehrte der Agent zur bereits wiederholten Bedingung zurück.

Dieser Durchlauf enthält außerdem eine einzelne ungültige Modellantwort (`steps/0006-response.json`). Die Rohantwort zeigt eine lange repetitive Escape-/Regexfolge und endet mit `done_reason = length` bei 8192 Ausgabetokens. Der Teamstand verzeichnet eine Ausgabe-Reparatur; danach folgten wieder gültige Aktionen. Das erklärt die Differenz zwischen 20 Modell- und 19 Werkzeugaufrufen. Es ist ein zusätzliches Ereignis dieses Durchlaufs; der abschließende Grund lautet auch hier `stagnation`.

Der pytest-Durchlauf fand zunächst über `parse` eine Stelle im Decoder, las ab Zeile 150 und später ab Zeile 50. Danach wiederholten sich vor allem Suchen nach `SGR_STYLE_MAP`, eine erfolglose Suche nach `0-? ` mit abschließendem Leerzeichen und die bereits ausgeführte Dateilesung.

Damit zeigt dieses Aufgabenpaar einen längeren Abschnitt mit unterschiedlichen Quellbeobachtungen, gefolgt von wiederkehrenden Ergebnissen. Auch hier entstanden keine strukturierten Cases, Tests oder Produktionsänderungen.

## Gemeinsame Dynamiken und Muster

### Lokale Suche ohne Wechsel der Arbeitsebene

Jeder Durchlauf blieb innerhalb einer einzigen Quelldatei. Suchbegriffe und Lesebereiche variierten, aber keiner wechselte zu Repositoryübersicht, Pfadsuche, Umgebungsprüfung, Testsammlung oder Testausführung. Die Veränderung der nächsten Aktion bestand meist in einer anderen Formulierung derselben Suche oder einem erneut gelesenen Ausschnitt.

### Neue Ergebnisse unterbrachen Wiederholungen zeitweise

Leere Trefferlisten und wiederholte Fundstellen führten zum selben allgemeinen Muster. Ein gefülltes Suchergebnis allein löste keinen Wechsel zur Kontextveröffentlichung oder Rollenübergabe aus. FastAPI/Cubie und Rich/Cubie erhielten auch nach dem Recovery-Hinweis noch neue Trefferblöcke, kehrten danach jedoch zu vorherigen Suchergebnissen zurück.

Der ergänzend gelesene Controllercode zählt neue Beobachtungen anhand von Aktionstyp, normalisiertem Ergebnis und Workspaceversionen. Wechselnde Beleg-IDs oder Lesehandles werden dabei nicht als neue Information gezählt. Auch unterschiedlich formulierte Suchanfragen können deshalb bei identischem leerem Ergebnis dieselbe Fortschrittssignatur haben. Die protokollierten Recovery-Zeitpunkte sind mit dieser Regel vereinbar.

### Recovery blieb eine Aufforderung innerhalb derselben Rolle

Jeder Durchlauf verzeichnet genau eine Recovery. Der Hinweis führte weder zu einer automatischen Rollenübergabe noch zu einer erzwungenen Diagnose. Die folgenden Aktionen blieben Such- und Leseoperationen der Analyse-Rolle. Nach der implementierten Regel wird beim ersten Erreichen der Wiederholungsgrenze die Recovery aktiviert; beim erneuten Erreichen folgt `stagnation`. Der einmal aktivierte Recovery-Zustand kann dabei auch einen zwischenzeitlich neuen Befund überdauern.

### Formale Werkzeugausführung und fachlicher Fortschritt blieben getrennt

Für alle sechs Durchläufe sind Werkzeugfehler, abgelehnte Wiederholungsversuche und Editierkonflikte mit null erfasst. Trotzdem endeten alle mit `stagnation`. Der aufgezeichnete Ablauf zeigt damit akzeptierte Werkzeugaktionen, deren Ergebnisse sich wiederholten. Die einzelne ungültige Modellantwort in Rich/Cubie wurde separat als Ausgabe-Reparatur erfasst.

### Erläuterungen wurden nicht zu gemeinsamen Arbeitsartefakten

Die Aktionen enthielten aufgabenbezogene `note`-Felder mit Anforderungen, Begründungen und teilweise Implementierungshypothesen. Diese begleiteten die Informationssuche, wurden aber nicht als versionierter Kontext, Case oder Teamnachricht veröffentlicht. Für die weitere Zusammenarbeit entstand kein dokumentierter Übergabestand.

### Beendigung vor Ausschöpfung der Teambudgets

Alle Durchläufe blieben unter 900 Sekunden, 48 Modell- und 96 Werkzeugaufrufen. Die Reserve war in sämtlichen finalen Teamständen inaktiv. Das gemeinsame Ende war somit durch die Stagnationsregel bestimmt. Die ausgeschöpfte Ausgabegrenze einer einzelnen Antwort in Rich/Cubie ist davon getrennt zu betrachten.

## Tests, Patches und externe Ergebnisse

Alle sechs `full.patch`- und alle sechs `production.patch`-Dateien sind leer. Agentenseitig gab es keine Testausführung; die sichtbaren Testbeobachtungen sind leer, und alle EBT-Ausführungs- und Auswertungszähler stehen auf null. Ein erster roter Test oder eine erste Produktionsänderung wurde nicht registriert.

Die unabhängige Evaluation war dagegen für sämtliche Durchläufe verfügbar:

| Aufgabe | Cubie | pytest |
| --- | --- | --- |
| FastAPI | 1 Test fehlgeschlagen, 8 bestanden | 1 Test fehlgeschlagen, 8 bestanden |
| Requests | 1 Test fehlgeschlagen, 11 bestanden | 1 Test fehlgeschlagen, 11 bestanden |
| Rich | 16 Tests fehlgeschlagen, 7 bestanden | 16 Tests fehlgeschlagen, 7 bestanden |

Alle sechs externen Ergebnisse lauten `resolved = false`. Diese Testresultate stammen aus der anschließenden Evaluation und sind keine während der Orientierung gewonnenen Agentenbelege. Der Gesamtprozess ist beendet, während die sechs internen Teamaufträge als unvollständig abgeschlossen wurden.

## Gemeinsamkeiten und Unterschiede zwischen den Armen

Das übereinstimmende Muster umfasst alle drei Aufgabenpaare: aktive Analyse-Rolle, Zustand `orient`, Such-/Leseaktionen, eine Recovery, keine Änderungen und Abschluss durch `stagnation`.

Unterschiede bestehen in Umfang und Verlauf der Informationsaufnahme. Bei Requests sind beide Sequenzen mit je sieben Suchaktionen und rund 45 bis 46 Sekunden ähnlich. Bei FastAPI enthält pytest zusätzliche Dateilesungen. Bei Rich enthält Cubie mehr unterschiedliche Beobachtungen und die einzelne Ausgabe-Reparatur; seine Agentenzeit beträgt rund 531 Sekunden gegenüber rund 113 Sekunden unter pytest.

In Summe erfasst der Bericht für pytest 31 Modellaufrufe, 183.290 Eingabe- und 4.059 Ausgabetokens; für Cubie 35 Modellaufrufe, 239.222 Eingabe- und 12.690 Ausgabetokens. Allein die begrenzte ungültige Rich/Cubie-Antwort umfasst 8192 Ausgabetokens und prägt damit die aggregierte Ausgabemenge dieses Arms. Die Tokenzahlen sind aufsummierte Provider-Nutzungswerte über mehrere Aufrufe und keine Menge eindeutig verschiedener Kontextinhalte.

Da weder QA noch Dev oder die armspezifische Testarbeit erreicht wurden, dokumentiert dieses Archiv vor allem Verhalten in der vorgeschalteten Orientierung. Aus den übereinstimmenden Lösungsergebnissen lässt sich keine Gleichwertigkeit der Testansätze ableiten. Ebenso erlauben drei Aufgaben mit einem Seed keine allgemeine Aussage über die Agentengeneration oder die Ursache einzelner Suchentscheidungen.

## Quellenverzeichnis

Alle Pfade sind relativ zu diesem Dokument:

- [Startparameter](runs/20261112-002038/launch.json), [eingefrorene Konfiguration](runs/20261112-002038/frozen/study.toml) und [Ablaufplan](runs/20261112-002038/frozen/schedule.json).
- [Eingefrorenes Cubie-Design](runs/20261112-002038/frozen/designs/cubie.json) und [pytest-Design](runs/20261112-002038/frozen/designs/pytest.json).
- [Gesamtbericht](runs/20261112-002038/report.json) und [abschließender Monitorstand](runs/20261112-002038/monitor/state.json).
- Einzelarchive [0001](runs/20261112-002038/frozen/runs/0001/), [0002](runs/20261112-002038/frozen/runs/0002/), [0003](runs/20261112-002038/frozen/runs/0003/), [0004](runs/20261112-002038/frozen/runs/0004/), [0005](runs/20261112-002038/frozen/runs/0005/) und [0006](runs/20261112-002038/frozen/runs/0006/): jeweils `team.json`, `agent.json`, `messages.json`, `actions/*.json`, `result.json`, `full.patch` und `production.patch`.
- [Begrenzte Modellantwort Rich/Cubie](runs/20261112-002038/frozen/runs/0005/steps/0006-response.json).
- Ergänzend gelesener aktueller Implementierungsstand: [Teamcontroller](testguided_study/team.py) und [Suchwerkzeug](testguided_study/workspace.py). Diese Dateien dienen der Einordnung; die Ablaufbefunde stammen aus dem Archiv.
