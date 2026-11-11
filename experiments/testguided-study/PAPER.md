# qb-cubie in einem testgeführten Programmieragenten: Methodik, Entwicklung und explorative Pilotbefunde

**Datenstand:** 11. November 2026, einschließlich des abgeschlossenen Archivs
`20261111-200641` (Ende 21:26:58 Uhr, Europe/Berlin).
**Status:** Entwicklungs- und Pilotstudie; eine qualifizierte Hauptmessung liegt
noch nicht vor.

## Zusammenfassung

Die Studie untersucht, ob der Zugang zu qb-cubie einschließlich einer
festgelegten Anleitung einem testgeführten Programmieragenten hilft, reale
Python-Änderungsaufgaben unter einem festen Arbeitsbudget zu lösen. Als Kontrolle
dient derselbe Agent mit regulären pytest-Tests. Beide Bedingungen arbeiten mit
demselben Modell, identischen Aufgabensnapshots und innerhalb eines Piloten mit
denselben Werkzeugen, Regeln und Ressourcenlimits. Ein unabhängiger Prüfer
bewertet ausschließlich den Produktionspatch anhand vorab festgelegter privater
Tests; die vom Agenten bearbeiteten Tests verändern diesen Maßstab nicht.

Unter `runs/` liegen sieben abgeschlossene Piloten mit jeweils sechs
Agentenversuchen sowie ein ausschließlich vorbereitetes Archiv. Die Piloten
verwenden immer dieselben drei Aufgaben und Seed 42. In drei verschiedenen
Piloten gelingt jeweils eine privat bestätigte Lösung: zweimal mit pytest und
einmal in der Cubie-Bedingung. Im jüngsten Pilot mit Agentenkern v5 und
`think=true` lösen beide Bedingungen 0 von 3 Aufgaben. Elf von 67 Modellaufrufen
enden am Ausgabelimit mit ausschließlich Thinking-Ausgabe und ohne ausführbare
JSON-Aktion; ein weiterer Aufruf endet mit einem Timeout. Kein Versuch dieses
Piloten verändert erfolgreich Produktionscode oder führt einen EBT-Vertrag aus.

Diese Befunde beschreiben vor allem Grenzen des gegenwärtigen Gesamtsystems aus
Modell, Anleitung und Agentensteuerung. Die kleine, wiederholt zur Entwicklung
verwendete Aufgabenmenge, wechselnde Designs und geringe Lösungsfähigkeit erlauben
keine belastbare allgemeine Einschätzung des zusätzlichen Nutzens von qb-cubie.
Insbesondere bedeutet 0:0 weder Gleichwertigkeit noch Wirkungslosigkeit. Zugleich
liefern die Archive konkrete Anhaltspunkte für weitere kontrollierte Iterationen.
Die persönliche Einschätzung des Projektverantwortlichen steht getrennt von den
empirischen Befunden im abschließenden Abschnitt.

## 1. Forschungsfrage und Gegenstand

Die im [Protokoll](PROTOKOLL.md) formulierte Frage lautet sinngemäß:

> Verbessert der Zugang zu qb-cubie und seiner festgelegten Anleitung die
> Lösungsquote eines testgeführten Agenten mit Ollama und Gemma4:12b bei einem
> festen Arbeitsbudget gegenüber demselben Agenten mit regulärem pytest?

qb-cubie stellt unter anderem **Example-Based Testing (EBT)** bereit. Ein
EBT-Vertrag beschreibt einen Aufruf des Produktionscodes mit konkreten Eingaben
und erwarteten Beobachtungen über `WorldState`. Er muss tatsächlich ausgeführt
und seine Bewertung wirksam geprüft werden. Ein Import oder die bloße
Konstruktion eines Vertrags genügt nicht. Die aktuellen Studienanleitungen
verwenden dafür `.run()` und bei `reporter=None` die explizite Prüfung
`assert result.evaluation is True`. Zusammengehörige Eingabe-/Ausgabepaare werden
in getrennten Verträgen ausgeführt. Die Erwartungen müssen aus der Aufgabe
stammen; auch ein formal korrekter Vertrag kann ein falsches Testorakel enthalten.
Die [Cubie-Anleitung](guides/cubie.md) und die
[pytest-Anleitung](guides/pytest.md) zeigen vergleichbare Beispiele für Werte,
Exceptions und Dateien.

Gemessen wird das **Angebot von Cubie einschließlich Anleitung** gegenüber pytest
einschließlich eigener Anleitung. Die Studie isoliert weder den Bibliothekseffekt
vom Anleitungseffekt noch den Effekt einzelner EBT-Funktionen. Unterbleibt die
Cubie-Nutzung, bleibt dies ein Ergebnis des untersuchten Agentenpakets. Daraus
lässt sich die Wirksamkeit tatsächlich ausgeführter EBT-Verträge jedoch kaum
beurteilen. Lesbarkeit, Reviewaufwand und Qualität synthetisch erzeugter Tests
sind plausible weitere Nutzenaspekte, bislang aber keine systematisch erhobenen
Endpunkte dieser Studie.

## 2. Datengrundlage und Untersuchungsumfang

### 2.1 Herkunft, Auswahl und Zulassung

Die Aufgaben stammen aus dem lokal vorhandenen Gemma-Developer-Agent-Pool, der
mit swegemma verwendet wird. Laut [Datendokumentation](DATEN.md) umfasst die
Quelldatei 129 Aufgaben: 67 aus FastAPI, 48 aus Rich, 13 aus Requests und eine aus
HTTPX. Die Herkunft ist keine automatische SWE-bench-Verified-Zulassung und die
Ergebnisse sind kein offizielles SWE-bench-Leaderboard-Ergebnis.

Der [Kandidatenkatalog](candidate-catalog.json) und die
[Einzelprüfungen](KANDIDATEN.md) dokumentieren 39 fachlich geprüfte Aufgaben:
26 Kandidaten, neun bedingte Fälle, drei zurückgestellte Fälle und einen
ausgeschlossenen Fall. 90 Aufgaben sind semantisch ungeprüft. Fachliche Eignung,
verfügbarer Snapshot und technische Zulassung sind verschiedene Voraussetzungen;
die 26 Kandidaten sind kein pauschal ausführbarer Messdatensatz.

Die Auswahl berücksichtigt primäre Aufgabentypen, Repositories und
Verwandtschaftsgruppen. Pro verwandter Gruppe wird höchstens eine Aufgabe
gezogen; Typen und Repositories werden reproduzierbar durchwechselt. Auswahlseed,
Anzahl und Filter werden vor der Inferenz festgehalten. Ein technischer Ausschluss
ist zu begründen; Aufgaben dürfen nicht danach ersetzt werden, ob ein Agent sie
löst. Die vorbereiteten Hauptprofile mit fünf bzw. zehn anderen Aufgaben sind
Planungen, keine bereits durchgeführten Messungen.

Vor einem Lauf werden die Ausgangssnapshots bereinigt: Git-Historie und private
Referenzdateien gelangen nicht in den Agentenarbeitsbereich; Symlinks werden
geprüft und gegebenenfalls materialisiert. Gemeinsame Abhängigkeiten sind
vorinstalliert. Der Agent kann weder Pakete nachinstallieren noch eine freie
Shell benutzen. Seine öffentliche Aufgabeninformation ist der jeweilige
`problem_statement`; Referenzpatch und private Prüftests bleiben verborgen.

### 2.2 Die drei tatsächlich untersuchten Aufgaben

| Aufgabe | Repository und Typ | Geforderte Änderung | Privates FAIL_TO_PASS / PASS_TO_PASS im jüngsten Freeze |
| --- | --- | --- | ---: |
| `fastapi_9425` | FastAPI; API/Schema; Kompatibilität; Integration im selben Prozess | Die stringifizierte Rückgabeannotation `"None"` als fehlendes Rückgabemodell behandeln, sodass insbesondere HTTP 204 möglich ist | 1 / 8 |
| `requests_6589` | Requests; Parsing/Encoding; Bugfix; lokale HTTP-Fixture | Bei Stringdaten kodierte Bytes für die Längenbestimmung berücksichtigen; der private Zielfall prüft den `Content-Length`-Pfad | 1 / 11 |
| `rich_3278` | Rich; Parsing/Encoding; Bugfix; Darstellungssnapshot | Private Escape-Sequenzen von `ESC 0` bis `ESC ?` entfernen, damit sie die Ausgabe nicht beschädigen | 16 / 7 |

Die Counts beziehen sich auf gesammelte pytest-Fälle, einschließlich
Parametrisierungen. Sie entsprechen weder der Zahl unabhängiger Aufgaben noch
dem Umfang der gesamten Projektsuiten. Aufgabenbeschreibungen, Ausgangscommits
und konkrete Node-IDs sind in den
[eingefrorenen Records](runs/20261111-200641/frozen/inputs/) archiviert;
die Typzuordnung steht im
[Aufgabenmanifest](runs/20261111-200641/frozen/tasks.json).

Die Aufgaben decken zwei primäre Typen und drei Repositories ab, mit zwei
Bugfixes und einer Kompatibilitätsänderung. Daraus lassen sich keine zuverlässigen
Unterschiede nach Aufgabentyp, Repository oder Änderungsart schätzen.
Lebenszyklus- und Terminierungsfälle sind hier nicht vertreten. Das verlangt auch
eine Einschränkung auf Python-Bibliotheks- und Webentwicklungsaufgaben und
überwiegend EBT-bezogene Cubie-Nutzung.

### 2.3 Welche Archive in die Ergebnisdarstellung eingehen

Die quantitative Entwicklungstabelle in Abschnitt 5 umfasst sämtliche sieben
abgeschlossenen Archive unter `runs/`: insgesamt 42 Agentenversuche auf **drei
verschiedenen Aufgaben**, jeweils mit zwei Bedingungen und Seed 42. Ein achtes
Archiv (`20261111-180104`) endet nach der Vorbereitung und enthält keine
Agentenergebnisse. Es wird als Vorbereitung ausgewiesen, nicht als gescheiterter
Pilot gezählt.

Zusätzlich enthält `local/live-pilot-validation` einen echten technischen Kurzlauf
auf FastAPI mit zwei Versuchen, 60 Sekunden und höchstens drei Modellaufrufen je
Versuch. Beide Versuche enden am Aufrufbudget ohne Lösung. Dieser explizit
begrenzte Start-/Monitorcheck wird separat als Technikbeleg geführt und nicht in
die Serie vollständiger Drei-Aufgaben-Piloten aufgenommen
([Startparameter](local/live-pilot-validation/launch.json),
[Bericht](local/live-pilot-validation/report.json)). Synthetische Smokes und
Containerprüfungen mit wiedergegebenen Modellantworten belegen ebenfalls
Infrastrukturfunktionen, keine selbstständige Modellleistung.

## 3. Forschungsmethodik

### 3.1 Gepaarter Vergleich und gemeinsame Arbeitsweise

Für jede Kombination aus Aufgabe und Seed bearbeiten beide Bedingungen denselben
unveränderten Snapshot in einem frischen Container mit leerem Dialog. Die
Aufgabenpaare werden mit festem Seed gemischt; der zuerst ausgeführte Arm
wechselt zwischen Cubie und pytest. Bei drei Paaren ist ein zahlenmäßig exakt
gleiches Verhältnis nicht möglich. Im jüngsten
[Laufplan](runs/20261111-200641/frozen/schedule.json) beginnt Cubie bei FastAPI
und Rich, pytest bei Requests. Die Läufe erfolgen seriell, ohne Übernahme von
Patches, Dialogen oder privaten Evaluationsergebnissen aus anderen Versuchen.

Innerhalb eines Piloten sind Modell, gemeinsamer Agentenkern, Werkzeuge,
Kontextregeln und Budgets gleich. Unterschiede sind das installierte Cubie samt
seinen Abhängigkeiten und die jeweilige Frameworkanleitung. Die Anleitungen
müssen fachlich brauchbar sein und werden nicht künstlich auf dieselbe Länge
gekürzt; ihr Kontextverbrauch gehört zur jeweiligen Bedingung.

Der gemeinsame Arbeitsauftrag ist testgeführt: vorhandenen Code und Tests
untersuchen, das Problem möglichst gezielt reproduzieren, einen fachlich
begründeten Test ergänzen oder verbessern, Produktionscode ändern und relevante
Tests erneut ausführen. Produktionscode **und sichtbare Tests bleiben jederzeit
bearbeitbar**, auch nach Rot oder Grün. Eine geeignete vorhandene Testsuite muss
nicht künstlich verändert werden. Falsche Testannahmen dürfen begründet
korrigiert werden; gültige Anforderungen dürfen nicht nur zum Erreichen von Grün
abgeschwächt werden.

Der Runner bietet strukturierte JSON-Aktionen für Navigation, Lesen, Schreiben,
lokale Ersetzung, Testsammlung, Testausführung und weitere Diagnose an. In v5
kommen verpflichtende kurze Analyseaktionen hinzu. Das frei gesetzte
`stage`-Label und die Erklärungen des Modells dokumentieren Absichten, beweisen
aber weder Reproduktion noch Fortschritt. Solche Bewertungen werden getrennt
von beobachteten Datei- und Testbelegen gehalten.

### 3.2 Unabhängiger Bewertungsmaßstab

Vor Inferenz müssen für jede Aufgabe zwei nichtleere Gruppen konkreter Tests
feststehen:

- **FAIL_TO_PASS:** Der private Test scheitert am Ausgangscode fachlich an einer
  Assertion und besteht mit dem Referenzfix.
- **PASS_TO_PASS:** Der private Kontrolltest besteht bereits vorher und muss
  nach der Änderung weiterhin bestehen.

Die Pipeline leitet die Fälle aus tatsächlicher Testsammlung und Ausgangs- und
Referenzläufen ab. Sie berücksichtigt geänderte Testfunktionen sowie
standardmäßig bis zu acht zusätzliche unveränderte Kontrollfälle; vorhandene
unveränderte Fälle aus dem ausgewählten Testumfang können zu größeren
Kontrollgruppen führen. Die konkreten Node-IDs werden eingefroren. Reine
Collection-/Importfehler oder eine Endlosschleife erfüllen das geforderte
Assertion-Rot nicht; dies begrenzt bereits die Zulassung bestimmter Fehlerarten.

Nach der Agentenarbeit werden der gesamte Patch und sämtliche Teständerungen
archiviert. Für die private Evaluation entsteht ein **neuer gemeinsamer
Evaluator-Container ohne Cubie**. swegemmas Produktionsfilter entfernt Änderungen
an sichtbaren Tests und geschützter Runnerkonfiguration aus dem bewerteten Patch.
Angewandt wird nur der Produktionspatch. Danach werden die eingefrorenen privaten
Reparatur- und Kontrolltests ausgeführt. Sie geben dem Agenten kein Feedback.

Ein Versuch gilt als gelöst, wenn diese unabhängige Prüfung erfolgreich ist und
alle benannten Fälle bestehen. Dies gilt auch für einen brauchbaren Zwischenstand
bei Stillstand, ungültiger letzter Ausgabe oder ausgeschöpftem Budget; `submit`
ist keine zusätzliche Erfolgsbedingung. Umgekehrt genügt eine Einreichung oder
eine grüne eigene Testsuite nicht. Der Maßstab prüft die konkrete Zieländerung
und eine begrenzte Regressionsauswahl, nicht die vollständige Korrektheit des
Projekts.

Ein vom Modell verursachter Syntax-/Importfehler soll als fehlgeschlagene Lösung
zählen. Infrastrukturfehler und nicht auswertbare Prüfungen bleiben separat
`unavailable`. Die historische Umsetzung trennte dies nicht in jedem Fall
korrekt; Abschnitt 5.2 benennt die konkrete Abweichung. Archive werden deshalb
nicht nachträglich umgeschrieben.

### 3.3 Modell, Ressourcen und Reproduzierbarkeit

Die verbindlichen Einstellungen sind jeweils die im Archiv eingefrorenen Werte.
Die gegenwärtige Vorlage `study.toml` und historische Textbeschreibungen können
davon abweichen. Für den jüngsten Pilot gelten:

| Merkmal | Eingefrorener Stand `20261111-200641` |
| --- | --- |
| Modell / Bereitstellung | `gemma4:12b`, lokal über Ollama 0.40.2 |
| Modellidentität | 11.9B, GGUF, `Q4_K_M`; Digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Sampling | Seed 42, Temperatur 0,2, `think=true` |
| Kontext / Ausgabe | `num_ctx=32768`, `num_predict=8192` |
| Agentenzeit | 900 Sekunden je Versuch |
| Modell-/Werkzeugaufrufe | kein festes Zahlenlimit; das Zeitbudget bleibt wirksam |
| Einzelkommando / private Verifikation | 90 / 120 Sekunden |
| Konfiguriertes Kontext-/Werkzeugausgabelimit | 80.000 Bytes / 12.000 Zeichen |
| Tatsächliche Kontextkapazität laut Runner | 40.090 Bytes nach Reserveberechnung |
| Agentenkern / Anleitungen | `testguided-core-v5`, `pytest-guide-v5`, `cubie-guide-v5` |
| Containerumgebung | Python 3.13.18, pytest 9.2.0; Cubie-Image mit qb-cubie 0.0.3 |
| Prüfbrücke | swegemma 0.2.11 mit gemeinsamem, getrenntem Evaluator |

Quellen sind die [eingefrorene Konfiguration](runs/20261111-200641/frozen/study.toml),
die [Umgebungsidentität](runs/20261111-200641/frozen/preflight/identity.json)
und die individuellen `result.json`. Die Byteschätzung ist keine exakte
Tokenzählung. Die Verbrauchsmetriken stammen aus den Providerzählern
`prompt_eval_count` und `eval_count`; unbekannte Werte bleiben unbekannt.
Wiederholt übertragener Kontext zählt mehrfach. Provider-Ausgabetokens sind
insbesondere bei aktivem Thinking nicht mit der Länge der sichtbaren JSON-Aktion
gleichzusetzen.

Agentenzeit beginnt an der Agentenschleife; Containeraufbau, Vorbereitung und
private Prüfung werden getrennt behandelt. Modellladezeit innerhalb eines
Aufrufs zählt dazu. Das Gesamtzeitlimit wird an Aktionsgrenzen geprüft und
begrenzt ausstehende Aufrufe, ist aber keine harte Betriebssystemfrist.
Deshalb sind geringe Überschreitungen möglich. Hardware, Treiber und sonstige
Last sollten für weitergehende Zeitvergleiche zusätzlich dokumentiert werden;
die geprüfte Identitätsdatei enthält keine vollständige GPU-/Lastbeschreibung.
Gleiche Seeds garantieren über unterschiedliche Ausführungsumgebungen hinweg
keine bitgleichen Antworten und machen unterschiedliche Prompts nicht identisch.

### 3.4 Belegsicherung und Vorgehen dieser Auswertung

Ein Freeze bindet Aufgaben, Guides, Designs, Laufplan und Laufzeitcode an Hashes.
Die Vorprüfung hält Modell- und Imageidentität sowie Ausgangs- und
Referenzprüfungen fest. Jeder Versuch archiviert Anfragen, Rohantworten,
validierte und tatsächlich ausgeführte Aktionen, Werkzeugergebnisse, Testbelege,
Zwischenpatches, Endpatch und private Evaluation. Der Monitor beobachtet den
Ablauf; er bietet keine Eingabe zur Korrektur laufender Agenten.

Für dieses Dokument wurden alle sieben Berichte und die 42 Einzelergebnisse
abgeglichen sowie die jüngsten sechs Aktionsfolgen, Rohantworten und Patches
rekonstruiert. Die bestehenden Pilot- und Technikanalysen dienen zusätzlich
als Quellen für frühere Prozessbefunde. Über alle acht Archive unter `runs/`
wurden **5.563 Hashreferenzen** aus den Eingabemanifesten, den in `ready.json`
verzeichneten Vorprüfungsdateien und den Laufmanifesten geprüft; alle stimmen.
Mehrfach referenzierte Dateien sind dabei mehrfach gezählt. Dies belegt
Archivkonsistenz, nicht Testvollständigkeit oder fachliche Richtigkeit.
Die Auswertung startete keine neue Modellinferenz und veränderte keine
historischen Laufartefakte.

### 3.5 Zielgrößen und statistische Interpretation

Primäre Zielgröße ist die **unabhängig bestätigte Lösungsquote** unter gleichem
Budget. Berichtet werden Erfolge je geplantem und je auswertbarem Versuch,
fehlende Ergebnisse sowie vollständige und diskordante Aufgabenpaare.
„Diskordant“ bedeutet, dass nur eine Bedingung die Aufgabe löst.

Der gepaarte Effekt ist `Cubie minus pytest` in der Lösungsquote. Bei mehreren
Seeds wird zuerst innerhalb einer Aufgabe gemittelt und dann gleichgewichtet
über Aufgaben. Das implementierte explorative 95-%-Bootstrapintervall resampelt
Aufgaben mit Zurücklegen (10.000 Ziehungen, fester Zufallsseed), nicht einzelne
Versuche. Unter zwei auswertbaren Aufgaben wird kein Intervall berechnet
([Berichtsimplementation](testguided_study/report.py)). Bei größeren Stichproben
wären Abhängigkeiten innerhalb von Repositories zusätzlich zu berücksichtigen.

Sekundäre Größen sind Zeit, gemessene Eingabe-/Ausgabetokens, Modell- und
Werkzeugaufrufe, Testbeobachtungen, Werkzeugfehler und Abbrucharten. Kürzere Zeit
oder weniger Tokens sind bei überwiegend erfolglosen Versuchen kein Nachweis
höherer Effizienz. Häufiges Grün kann lediglich wiederholte Bestandstests bedeuten;
viele Tests oder Assertion-Fehler belegen weder Abdeckung noch ein richtiges
Orakel. EBT-Zähler messen beobachtete Ausführungen über Testläufe hinweg und
keine Anzahl verschiedener hochwertiger Testfälle.

Zur Prozessbewertung gehört deshalb die manuelle Prüfung: Passt der Test zur
Anforderung? Tritt fachliches Rot vor der zugehörigen Änderung auf? Besteht
dieselbe finale Testversion anschließend? Bleibt gültige Bestandsabdeckung
erhalten? Wurden Testkorrekturen begründet und Cubie-Verträge tatsächlich
ausgeführt und geprüft? Das Protokoll sieht dafür ein gemeinsames Raster und
eine Prüfung ohne Kenntnis des Erfolgs der Gegenseite vor. Die vorliegende
nachträgliche Analyse ist keine verblindete, unabhängige Mehrfachbegutachtung;
eine Reviewerübereinstimmung wurde nicht erhoben.

## 4. Bisherige Entwicklung

Die Entwicklung begann mit einer isolierten Studienbrücke aus lokalen
Ollama-Aufrufen und swegemmas Container-, Snapshot- und Prüffunktionen. Sie ist
vom Produktbenchmark `qb_cubie.benchmarks` getrennt. Frühe Docker-Replays
belegten frei bearbeitbare Tests und den Schutz der privaten Bewertung vor
vereinfachten sichtbaren Tests. Diese Techniknachweise sind im
[Validierungsbericht](VALIDIERUNG.md) dokumentiert; dessen ältere Aussagen über
noch nicht gestartete Piloten beschreiben den damaligen Stand.

Die ersten Agentenläufe zeigten Such- und Testwiederholungen, unpassende
Testorakel und abgeschnittene Antworten. Darauf folgten versionierte,
eingefrorene Designs:

| Entwicklungsstand | Wesentliche Änderung und Anlass |
| --- | --- |
| Früher, noch nicht separat versionierter Kern | Gemeinsamer Prompt, strukturierte Werkzeuge, begrenzte Dialoghistorie; frühe Piloten verbrauchen oft das Aufrufbudget ohne Änderung |
| v2 | Gemeinsamer Kern plus Frameworkspezialisierung, expliziter Arbeitsledger, verankerte Ersetzungen, Stillstandsbehandlung und begrenzte Reparatur ungültiger Antworten |
| v3 | Notizen an echte Aktionen koppeln; belegbasierter Kontext, getrennte Pfad-/Inhaltssuche, Collection, Baseline-Gegenprobe, Testversionen und EBT-Laufzeitbelege; danach weitere Korrekturen an Kontext und Werkzeugfeedback |
| v4 | Datei-Hashes vom Runner statt vom Modell binden, kleine Änderungen anleiten, das Testorakel expliziter prüfen, Feedback nach Grün ohne Produktionsänderung sowie eingeschränkter Leseaufruf nach ungültiger Ausgabe |
| v5 | Reproduktionsanalyse vor Dateiänderungen, Diagnose nach fehlgeschlagenen Tests und Review vor Abgabe als verbindliche Entscheidungspunkte; im jüngsten Pilot zusätzlich Thinking aktivieren |

Die [Designhistorie](AGENTENDESIGN.md), die
[v4-Dokumentation](AGENTENDESIGN-V4.md) und die
[v5-Dokumentation](AGENTENDESIGN-V5.md) erläutern Umsetzung und technische
Abnahmen. Ein formal korrektes Entscheidungsprotokoll ist weiterhin eine
Modellbewertung, keine automatisch geprüfte fachliche Wahrheit.

Design v3 wurde unter verschiedenen Budget- und Implementierungsständen
ausgeführt. Ein Versionslabel allein identifiziert daher keinen identischen
Versuch; verbindlich bleiben Codehashes und Freeze. Der Wechsel von v4 zu v5
ändert zugleich die Steuerung und `think=false` zu `think=true`. Die folgenden
Ergebnisse sind deshalb eine Entwicklungshistorie, keine kontrollierte
Wirksamkeitsrangliste der Versionen.

## 5. Ergebnisse der bisherigen Piloten

### 5.1 Vollständige Übersicht

Alle Archive in der folgenden Tabelle stammen vom 11.11.2026. Ergebnisse beziehen
sich auf private Evaluationen. „0/3“ bedeutet null Erfolge unter drei geplanten
Versuchen des jeweiligen Arms, nicht null bestandene Einzeltests.

| Archiv | Kern / Thinking | Agentenzeit / Aufrufgrenze; Kontext / Ausgabe in Tokens | pytest gelöst | Cubie gelöst | Vollständige / nicht verfügbare Paare |
| --- | --- | --- | ---: | ---: | ---: |
| [132401](runs/20261111-132401/report.json) | früh / aus | 600 s / 24; 16.384 / 4.096 | 0/3 | 0/3 | 3 / 0 |
| [160158](runs/20261111-160158/report.json) | früh / aus | 600 s / 24; 16.384 / 4.096 | 0/3 | 0/3 | 3 / 0 |
| [163110](runs/20261111-163110/report.json) | v2 / aus | 600 s / 24; 16.384 / 4.096 | 1/3 | 0/3 | 3 / 0 |
| [171515](runs/20261111-171515/report.json) | v3 / aus | 600 s / 24; 16.384 / 4.096 | 0/3 | 0/3 | 3 / 0 |
| [180104](runs/20261111-180104/monitor/state.json) | v3 / aus | nur vorbereitet; keine Agentenläufe | — | — | — |
| [180702](runs/20261111-180702/report.json) | v3, überarbeitet / aus | 900 s / unbegrenzt; 32.768 / 8.192 | 0/3 | 1/3; ein weiterer Versuch nicht verfügbar | 2 / 1 |
| [192412](runs/20261111-192412/report.json) | v4 / aus | 900 s / unbegrenzt; 32.768 / 8.192 | 1/3 | 0/3 | 3 / 0 |
| [200641](runs/20261111-200641/report.json) | v5 / an | 900 s / unbegrenzt; 32.768 / 8.192 | 0/3 | 0/3 | 3 / 0 |

Die sieben abgeschlossenen Piloten enthalten 41 als verfügbar klassifizierte
Ergebnisse und ein historisch nicht verfügbares Ergebnis. Nur drei der
42 Versuche sind privat erfolgreich. Diese Zählung beschreibt die vorhandenen
Entwicklungsartefakte; eine darüber gepoolte Framework-Lösungsquote wäre wegen
wechselnder Designs und wiederholter Aufgaben methodisch irreführend.

### 5.2 Einzelne Erfolge und eine historische Auswertungsabweichung

**v2: Requests mit pytest.** Im Archiv `163110` löst der pytest-Agent
`requests_6589`, reicht ein und zeigt einen gezielten Rot–Änderung–Grün-Zyklus.
Die anderen fünf Versuche lösen ihre Aufgaben nicht. Dieser Erfolg belegt eine
grundsätzliche Lösungsfähigkeit auf einer konkreten Aufgabe, keine stabile
Erfolgsquote ([Pilotanalyse](PILOTANALYSE-20261111.md)).

**Überarbeitetes v3: FastAPI mit Cubie.** Im Archiv `180702` ändert der
Cubie-Agent die Behandlung von `"None"` in `get_typed_return_annotation`,
ergänzt tatsächlich ausgeführte EBT-Tests und reicht eine privat erfolgreiche
Lösung ein. Für diesen Versuch werden sechs EBT-Ausführungen und -Bewertungen,
davon fünf erfolgreich, über mehrere Testläufe gezählt. Dies zeigt, dass eine
produktive Cubie-Nutzung in diesem Aufbau prinzipiell möglich ist
([vollständiger Patch](runs/20261111-180702/frozen/runs/0001/full.patch),
[Ergebnis](runs/20261111-180702/frozen/runs/0001/result.json)).

Im selben Archiv erzeugt der Cubie-Agent auf Requests einen Produktionspatch
mit einem Einrückungsfehler. Der private Prüfer scheitert schon beim Import mit
pytest-Exitcode 4. Historisch wird dieser Versuch als `resolved=null` und
`available=false` gespeichert, obwohl die Ursache eine vom Agenten verursachte
Beschädigung ist und gemäß Protokoll als Misserfolg zählen sollte
([Evaluationsbeleg](runs/20261111-180702/frozen/runs/0004/evaluation/result.json)).

Der historische Bericht weist daher Cubie mit 1/3 je geplantem, aber 1/2 je
auswertbarem Versuch aus. Der gepaarte Effekt auf den nur zwei vollständigen
Paaren beträgt **+50 Prozentpunkte**, mit Bootstrapintervall [0; +100]. Zählt
man den syntaktisch beschädigten Requests-Patch transparent als Misserfolg,
liegen drei Paare vor und die deskriptive Differenz beträgt **+33,3
Prozentpunkte**. Das ist eine Sensitivitätsbetrachtung, kein nachträglich
geänderter Originalreport. Der historische Vorteil hängt somit auch am
Ausschluss eines vom Agenten verursachten Fehlers. Die aktuelle
[Prüferimplementation](testguided_study/backend.py) enthält eine gesonderte
Behandlung patchbedingter Importfehler mit Exitcode 4; die alten Artefakte
bleiben unverändert.

**v4: FastAPI mit pytest.** Im Archiv `192412` besteht ein pytest-Produktionspatch
die neun privaten Fälle. Der Agent überschreibt jedoch eine sichtbare
1.114-Zeilen-Testdatei durch 45 Zeilen mit fachlich fehlerhaften Tests. Die eigene
Suite bleibt rot; der Versuch endet als `stalled`, ohne Abgabe. Für die
unabhängige Evaluation wird die Teständerung korrekt entfernt. Der
Produktionspatch ist somit nach dem festgelegten Maßstab erfolgreich, der
Arbeitsprozess aber kein schlüssiger testgeführter Abschluss
([detaillierte Analyse](PILOTANALYSE-20261111-192412.md)).

Im v4-Pilot stehen 1/3 pytest-Erfolge 0/3 Cubie-Erfolgen gegenüber. Die gepaarte
Differenz beträgt −33,3 Prozentpunkte, das explorative Bootstrapintervall
[−100; 0]. In keinem der drei Cubie-Versuche wird ein EBT ausgeführt. Der
Erfolg auf nur einem Paar und die fehlende EBT-Nutzung erlauben keine allgemeine
Aussage zugunsten regulärer Assertions oder gegen EBT.

### 5.3 Vorbelastung der sichtbaren Ausgangstests

Die Vorprüfung des jüngsten Freezes zeigt bereits **vor jeder Agentenänderung**:

| Projekt | Beobachteter sichtbarer Ausgangszustand |
| --- | --- |
| FastAPI | Acht Collection-Fehler; unter anderem fehlen optionale Abhängigkeiten wie `pydantic_settings` |
| Requests | 577 bestanden, fünf fehlgeschlagen, 15 übersprungen |
| Rich | 746 bestanden, 65 fehlgeschlagen, 24 übersprungen |

Diese Belege stehen unter
[preflight/visible](runs/20261111-200641/frozen/preflight/visible/).
Die [Technikanalyse](TECHNIKANALYSE-20261111-171515.md) führt Rich-Fehler unter
anderem auf eine schon im Snapshot vorhandene Inkonsistenz bei
`Column(highlight=...)` zurück. Ein Teil der Requests-Fehler betrifft
Verbindungsversuche aus der Containerumgebung. Solche Ausgangsfehler dürfen
nicht als neue Agentenregressionen ausgelegt werden, erschweren aber die
Orientierung und die sinnvolle Auswahl von Regressionstests.

Die gezielten privaten Prüfungen sind davon zu unterscheiden: Im jüngsten
Freeze scheitert jede unveränderte Basis fachlich an den privaten Tests und
jeder Referenzpatch besteht sie
([Referenzprüfungen](runs/20261111-200641/frozen/preflight/references.json)).
Der Prüfer kann also die Basis von der Referenzlösung unterscheiden. Das
belegt die Funktionsfähigkeit dieses begrenzten Maßstabs und beseitigt die
Probleme der sichtbaren Gesamtsuiten nicht.

## 6. Vertiefte Auswertung des jüngsten Piloten v5

### 6.1 Ergebnis und Ressourcen

Das Archiv `20261111-200641` ist vollständig abgeschlossen. Alle sechs privaten
Evaluationen sind verfügbar und negativ: pytest **0/3**, Cubie **0/3**, keine
diskordanten Paare, gepaarte Differenz **0 Prozentpunkte**. Der Bericht erzeugt
ein Bootstrapintervall von [0; 0]. Da alle drei beobachteten Aufgabendifferenzen
null sind, kann Resampling daraus keine andere Differenz erzeugen. Dieses
degenerierte Intervall ist **kein Nachweis für Gleichwertigkeit und kein
verlässlich enger Unsicherheitsbereich für neue Aufgaben**.

| Versuch | Aufgabe / Bedingung | Agentenzeit | Modell- / Werkzeugaufrufe | Abbruch | Endpatch |
| --- | --- | ---: | ---: | --- | --- |
| 0001 | FastAPI / Cubie | 727,4 s | 8 / 6 | `invalid_output` | leer |
| 0002 | FastAPI / pytest | 681,4 s | 6 / 4 | `invalid_output` | leer |
| 0003 | Requests / pytest | 829,3 s | 17 / 15 | `invalid_output` | nur zusätzliche Tests |
| 0004 | Requests / Cubie | 900,1 s | 19 / 17 | `agent_timeout` | nur Teständerung |
| 0005 | Rich / Cubie | 653,5 s | 8 / 6 | `invalid_output` | leer |
| 0006 | Rich / pytest | 684,7 s | 9 / 7 | `invalid_output` | leer |

Die individuellen Belege liegen unter
[frozen/runs](runs/20261111-200641/frozen/runs/); aggregiert ergibt sich:

| Kennzahl | pytest | Cubie |
| --- | ---: | ---: |
| Gelöst / geplant / auswertbar | 0 / 3 / 3 | 0 / 3 / 3 |
| Median der Agentenzeit | 684,7 s | 727,4 s |
| Modellaufrufe gesamt | 32 | 35 |
| Werkzeugaufrufe gesamt | 26 | 29 |
| Werkzeugfehler | 1 | 4 |
| Abgewiesene Wiederholungen | 0 | 0 |
| Sichtbare Testlaufbeobachtungen | einmal Grün, einmal Assertion-Rot | einmal Assertion-Rot |
| EBT ausgeführt / bewertet / bestanden | 0 / 0 / 0 | 0 / 0 / 0 |
| Gemessene Eingabetokens | 198.821 | keine vollständige Summe; Teilmessungen vorhanden |
| Gemessene Ausgabetokens | 53.542 | keine vollständige Summe; Teilmessungen vorhanden |
| Gemessene Gesamttokens | 252.363 | keine vollständige Summe |

Quelle: [Gesamtreport](runs/20261111-200641/report.json). Beim letzten Aufruf des
Requests/Cubie-Versuchs fehlen aufgrund des Provider-Timeouts die Tokenzähler.
Deshalb setzt der Bericht die aggregierten Cubie-Tokenwerte korrekt auf `null`.
Die **bekannte Teilsumme** beträgt 254.210 Tokens; für beide Bedingungen zusammen
sind 506.573 Tokens dokumentiert, davon 403.338 Eingabe und 103.235 Ausgabe.
Dies sind unvollständige Verbrauchswerte, keine vollständigen Gesamtkosten.

Die summierte Agentenzeit beträgt 4.476,4 Sekunden beziehungsweise 74,6 Minuten.
Zwischen Studienstart und abgeschlossenem Monitorzustand liegen 80,3 Minuten;
die Differenz umfasst weitere Ablaufschritte. Keiner der sechs Versuche erreicht
`submit`. Erfolgreiche Produktionsänderungen gibt es nicht; vier Endpatches sind
leer und zwei betreffen ausschließlich Tests.

### 6.2 Thinking und Aktionsausgabe als unmittelbarer Engpass

Die 67 Modellaufrufe erzeugen 55 Werkzeugaufrufe, elf mit `done_reason=length`
beendete Antworten und einen Timeout ohne Tokenmessung. **Alle elf am Limit
beendeten Antworten enthalten leeres `message.content` und ausschließlich
Thinking-Ausgabe.** Jede verbraucht 8.192 Ausgabetokens, zusammen 90.112 Tokens.
Das sind 87,3 % der bekannten 103.235 Ausgabetokens dieses Piloten.

Der Runner verwirft diese Antworten, weil keine vollständige Aktion vorliegt.
Jeder Versuch nutzt den einen erlaubten Reparaturaufruf; eine dauerhafte
Wiederherstellung des Arbeitsflusses gelingt dadurch nicht. FastAPI und Rich
scheitern in beiden Bedingungen nach dem Lesen relevanter Implementierung,
bevor eine Reproduktionsanalyse oder Dateiänderung erfolgreich ausgeführt wird
(zum Beispiel [FastAPI/Cubie, Antwort 0006](runs/20261111-200641/frozen/runs/0001/steps/0006-response.json)).

Damit lässt sich ein konkreter Mechanismus benennen: Unter dieser Konfiguration
verbraucht das Modell häufig das gesamte Ausgabelimit, bevor es die nächste
gültige Aktion ausgibt. Das belegt eine praktische Unverträglichkeit des
beobachteten Antwortverhaltens mit dem gewählten Aktions- und Budgetrahmen.
Es beweist weder, dass Thinking allgemein schadet, noch, dass allein ein höheres
Limit das Problem behebt. Steuerung und Thinking wurden gemeinsam geändert;
ein isolierter Vergleich fehlt.

### 6.3 Requests/pytest: passende Reproduktion, keine angewandte Reparatur

Der Agent liest `super_len`, dokumentiert eine Reproduktionsanalyse und führt
zunächst die bestehende Utility-Testdatei aus: 203 Fälle bestehen, zwölf werden
übersprungen. Anschließend schreibt er eine neue Testdatei mit zwei sinnvollen
UTF-8-Beispielen: `super_len("€") == 3` und `super_len("Test€") == 7`.
Beide scheitern am unveränderten Produktionscode mit den beobachteten Werten
1 und 5. Diese Beispiele treffen die fachliche Differenz zwischen Zeichen-
und Bytelänge.

Nach der vorgeschriebenen Diagnose versucht der Agent eine größere Ersetzung
von Produktionscode. Der alte Anker stimmt jedoch nicht mit der Datei überein;
die Änderung wird als `edit_conflict/anchor_missing` abgewiesen. Der letzte
Modellaufruf endet erneut im Ausgabelimit. Es bleiben passende rote Tests ohne
angewandte Implementierung und ohne nachgewiesenes Grün
([Testlauf](runs/20261111-200641/frozen/runs/0003/steps/0012-tool.json),
[abgewiesener Edit](runs/20261111-200641/frozen/runs/0003/steps/0015-tool.json)).

### 6.4 Requests/Cubie: Assertion-Rot mit verfälschtem Unicode-Beispiel

Der Cubie-Agent formuliert zunächst ein passendes Beispiel mit dem Zeichen
`🚀`, dessen UTF-8-Darstellung vier Bytes benötigt. Zwei Versuche, eine
eingerückte Testmethode als vollständigen Dateiinhalt zu schreiben, werden wegen
Syntaxfehlern abgewiesen. Es folgen ein Ankerkonflikt und eine Ablehnung wegen
notwendigen Neulesens. Schließlich gelingt eine lokale Ergänzung in der
vorhandenen Testdatei.

Der tatsächlich gespeicherte Python-Test enthält allerdings den Stringliteral
`'\ud83d\ude80'`. In dieser Schreibweise besteht der Python-String aus zwei
Surrogat-Codepunkten und ist nicht dasselbe wie das einzelne Zeichen `🚀`.
Die Assertion beobachtet folgerichtig `2 == 4`; eine normale UTF-8-Kodierung
dieses Surrogatstrings würde zudem scheitern. Das automatische
`assertion_failure`-Label belegt hier ein rotes Ergebnis, aber keine saubere
Reproduktion des ursprünglich gewählten Beispiels. Eine fachlich passende
Reproduktion müsste das echte Zeichen oder `"\U0001F680"` verwenden.

Der ergänzte Test ist eine gewöhnliche Assertion; es wird kein EBT-Vertrag
ausgeführt. Nach dem roten Test kommt keine erfolgreiche Diagnose oder
Produktionsänderung mehr zustande: Eine Antwort endet im Ausgabelimit und der
anschließende Reparaturaufruf überschreitet die verbleibende Zeit
([finaler Patch](runs/20261111-200641/frozen/runs/0004/full.patch),
[Testbeleg](runs/20261111-200641/frozen/runs/0004/steps/0015-tool.json)).

### 6.5 Was v5 bislang tatsächlich zeigt

Die verpflichtenden Analysepunkte funktionieren in den Requests-Versuchen
formal: Beide protokollieren Reproduktion, pytest zusätzlich die Diagnose nach
Rot. Vier andere Versuche erreichen den ersten Analysepunkt nicht. Keine
Abschlussanalyse und kein selbstständig verifizierter Abschluss werden erreicht.

Gegenüber v4 gibt es weniger gemeldete Werkzeugfehler und keine abgewiesenen
Wiederholungen. Da wesentlich mehr Zeit in nicht ausführbare Antworten fließt
und die Zahl der Werkzeugaktionen sinkt, ist dies kein hinreichender Beleg für
eine bessere Steuerung. Die geringere private Erfolgszahl gegenüber dem einzelnen
v4-Erfolg lässt umgekehrt ebenfalls keinen kausalen Schluss über v5 zu.

## 7. Aussagekraft und Grenzen

**Zu wenig unabhängige Aufgaben.** Sieben Piloten erzeugen keine 21 neuen
Aufgaben. Alle wiederholen dieselben drei Probleme mit demselben Seed. Die
Aufgaben wurden außerdem zur Designentwicklung verwendet; weitere Erfolge auf
ihnen wären zunächst Entwicklungsfortschritt und kein Generalisierungsnachweis.
Eine Hauptmessung auf neuen Aufgaben fehlt.

**Geringe Lösungsfähigkeit und Bodeneffekt.** Meist scheitern die Agenten, bevor
sie sinnvoll zwischen Testmethodiken wählen oder eine Reparatur abschließen.
Wenn beide Bedingungen nahezu immer erfolglos sind, kann eine Differenz schwer
sichtbar werden. Dieser Bodeneffekt ist eine plausible Interpretation der
geringen Trennschärfe, kein Beweis für einen verborgenen Cubie-Vorteil. Die
einzelnen Erfolge zeigen zugleich, dass der Aufbau nicht grundsätzlich jede
Lösung verhindert.

**Intervention oft nicht umgesetzt.** Im v4- und v5-Pilot wird kein EBT
ausgeführt; im überarbeiteten v3 ist die Nutzung auf zwei Versuche begrenzt.
Der Angebotseffekt des Gesamtpakets bleibt untersuchbar, ein Mechanismusvorteil
der EBT-Ausführung hingegen weitgehend offen. Nur die erfolgreichen Nutzer
nachträglich zu vergleichen würde Auswahlverzerrungen schaffen.

**Mehrere Änderungen gleichzeitig.** Designs, Kontextaufbereitung, Budgets und
Thinking ändern sich im Entwicklungsverlauf. Unterschiede zwischen Piloten
können keinem einzelnen Faktor zugeschrieben werden. Ein stärkeres Modell
wurde noch nicht verglichen; die Hypothese einer Modellgrenze bleibt offen.

**Begrenzte und teilweise problematische Umgebung.** Die privaten Zieltests sind
zugelassen, sichtbare Gesamtsuiten aber bereits fehlerhaft. Die unabhängige
Regressionsabdeckung ist begrenzt. Historische Fehlklassifikation, unvollständige
Tokenmessung und fehlende vollständige Hardware-/Lastdokumentation begrenzen
insbesondere Ausfall- und Ressourcenvergleiche.

**Keine Aussage über sämtliche Nutzendimensionen.** Die Studie misst bislang
weder die menschliche Lesbarkeit der Verträge noch Reviewzeit, Präzision,
Fehlerfindungsvermögen oder Arbeitsgeschwindigkeit in den eigenen Projekten des
Projektverantwortlichen. Auch Trainingskontamination durch öffentliche Issues
und bekannte Referenzlösungen lässt sich mit den vorliegenden Daten nicht
ausschließen.

Die Kennzahlen sind damit als Beschreibung der beobachteten Piloten und als
Diagnosehilfe brauchbar. Für eine belastbare allgemeine Einschätzung von
qb-cubie gegenüber regulärem pytest reichen sie derzeit nicht aus. Ein
degeneriertes Nullintervall oder ein einzelnes gewonnenes Paar ändern daran
nichts.

## 8. Folgerungen für die Fortführung

Aus den Befunden ergibt sich zunächst eine Machbarkeitsaufgabe: Der gemeinsame
Agent muss zuverlässig gültige Aktionen liefern, ein fachlich passendes Problem
reproduzieren, kleine Änderungen anwenden und den Abschluss prüfen können.
Der bestehende
[Qualifikationsmechanismus](testguided_study/campaign.py) verlangt vor einer
Hauptmessung pro Bedingung mindestens zwei unabhängige reale Aufgabengruppen mit
privatem Erfolg und beobachtetem Rot-Grün-Zyklus bei passender Umgebung und
konkretem Design. Eine solche Qualifikation für das aktuelle v5-Design liegt
nicht vor; dessen
[eingefrorener Kampagnenstand](runs/20261111-200641/frozen/campaign.json)
weist beide Bedingungen als unqualifiziert aus.

Für die nächste Untersuchung bieten sich folgende voneinander trennbare Schritte
an. Sie sind Vorschläge aus dieser Analyse und keine bereits gemessenen Effekte:

1. **Aktionsfähigkeit stabilisieren.** Die am Ausgabelimit endenden Antworten und
   die Editkonflikte als gesonderte Fehlermuster bearbeiten. Replays prüfen die
   technischen Verträge; echte Modellläufe müssen zeigen, ob daraus häufiger
   sinnvolle Aktionen und Lösungen entstehen.
2. **Modell- und Designeffekte getrennt prüfen.** Bei gleichem Modell und Budget
   zunächst Steuerung bzw. Thinking einzeln variieren; ein leistungsfähigeres
   Modell anschließend mit festgehaltenem Design vergleichen. Wird dafür ein
   anderes Budget benötigt, ist die Aussage ausdrücklich auf das jeweilige
   Modell-Budget-Paket zu beziehen. Die Hypothese „stärkeres Modell und/oder
   besseres Design“ wäre gestützt, wenn Reproduktion, gültige Aktionen und
   private Lösungen auf weiteren Entwicklungsaufgaben verlässlich zunehmen.
3. **Neue Messaufgaben vorab einfrieren.** Die drei bekannten Aufgaben bleiben
   Entwicklungsfälle. Für den Nutzenvergleich neue, technisch zugelassene und
   hinreichend vielfältige Aufgaben verwenden; relevante Verwandtschaftsgruppen
   ausschließen. Mehrere Seeds ergänzen die Stabilitätsprüfung, ersetzen aber
   keine zusätzlichen Aufgaben.
4. **Auswertung und Ausfälle verbindlich festlegen.** Modellbedingte Syntaxfehler
   als Misserfolg, Infrastrukturfehler separat zählen; geplante Nenner,
   vollständige Paare und Tokenlücken offen berichten. Eine praktisch relevante
   Mindestverbesserung vorab festlegen und die Stichprobe daran ausrichten.
   Die im Protokoll genannten zehn Prozentpunkte sind ein Beispiel, kein mit
   diesen drei Aufgaben sinnvoll geprüfter Schwellenwert.
5. **Zusätzlichen Nutzen gezielt messen.** Testpräzision durch fachliche
   Oracleprüfung und geeignete fehlerhafte Varianten untersuchen; Lesbarkeit
   und Reviewzeit mit einem vorher definierten menschlichen Bewertungsraster
   erfassen. Dafür getrennte Endpunkte und ein eigenes Erhebungsdesign verwenden,
   damit persönliche Erfahrung und gemessener Effekt vergleichbar werden.

Die Studie liefert gegenwärtig eine dokumentierte Methodik und konkrete
Fehlerdiagnosen. Ob mehr Modellfähigkeit, eine ausgereiftere Steuerung oder ihre
Kombination den Cubie-Vergleich aussagekräftiger macht, ist der nächste empirisch
zu prüfende Schritt.

## 9. Persönliche Einschätzung, Hypothesen und Erfahrungen des Projektverantwortlichen

*Dieser Abschnitt gibt die persönliche Einschätzung des
Projektverantwortlichen wieder. Die folgenden Erfahrungen wurden in der
vorliegenden Studie nicht systematisch erhoben und sind von ihren quantitativen
Ergebnissen zu unterscheiden.*

**Meine Einschätzung des bisherigen Stands:** Ich halte die bisherigen Metriken
noch nicht für ausreichend, um eine aussagekräftige Einschätzung des Nutzens von
qb-cubie in diesem Vergleich abzugeben. Dafür liegen bislang zu wenige Daten
vor, insbesondere zu wenige unabhängige Aufgaben. Außerdem waren die Agenten
bisher kaum dazu fähig, die Aufgaben zuverlässig zu lösen. Die Kennzahlen
beschreiben damit vor allem einen frühen Entwicklungsstand des Studienaufbaus.

**Meine Hypothese:** Die Studie benötigt ein stärkeres Modell und/oder ein
besser ausgefeiltes Agentendesign, um aussagekräftige Vergleichsmetriken zu
erzeugen. Erst wenn die Agenten Aufgaben regelmäßig verstehen, geeignete Tests
formulieren und Reparaturen abschließen können, erwarte ich einen hinreichend
informativen Vergleich der beiden Testansätze. Dies ist eine zu prüfende
Hypothese, kein bereits belegtes Ergebnis.

**Meine subjektiven Erfahrungen und meine Motivation zur Fortführung:**

- Das Projekt qb-cubie hat sich bereits für meine eigenen Projekte als nützlich
  erwiesen.
- Ich habe die Erfahrung gemacht, dass auch Agenten mit qb-cubie bessere und
  präzisere Tests aufsetzen können und dabei sogar schneller sein können als
  ohne qb-cubie.
- Die EBT-Cases von qb-cubie kann ich wesentlich besser lesen und nachvollziehen.
  Das hilft mir, synthetisch generierte Testfälle zu reviewen und fachlich zu
  bewerten.
- Deshalb halte ich es für sinnvoll, weitere Energie zu investieren, die Studie
  mit dieser Methodik fortzuführen und darauf aufbauende Iterationen der Agenten
  weiterzuentwickeln.

Diese Erfahrungen begründen für mich die weitere Untersuchung. Sie ersetzen
keinen kontrollierten Wirksamkeitsnachweis und sollten in künftigen Iterationen
durch geeignete Messungen überprüfbar werden.

## 10. Synthese der Ursachenanalysen und formalisierte Hypothesensysteme (Antigravity & Codex)

Im Anschluss an den Abschluss der Pilotserie führten zwei unabhängige KI-Systeme
detaillierte post-hoc Ursachenanalysen der gesamten empirischen Datenbasis aller
sieben Piloten (42 Läufe) durch:
1. **Antigravity** (Gemini-3.8-Flash, Reasoning: High; Dokument: [`HYPOTHESEN-URSACHENANALYSE-20261111.md`](HYPOTHESEN-URSACHENANALYSE-20261111.md))
2. **Codex** (GPT-6.1-Sol, Reasoning: High; Dokument: [`URSACHENANALYSE-CODEX-20261111.md`](URSACHENANALYSE-CODEX-20261111.md))

Beide Analysen stimmen in der Diagnose überein, dass die beobachtete niedrige
Erfolgsquote (7,1 %, 3 von 42 Läufen) und das Nullergebnis in v5 (0:0) einen
massiven **Bodeneffekt** darstellen: Die Agenten scheitern an vorgelagerten
Ablauf- und Inferenzbarrieren, bevor die testmethodische Ebene von `qb-cubie`
überhaupt wirksam werden kann (in 19 von 21 Cubie-Läufen wurde kein einziger
EBT-Vertrag ausgeführt). Zur gezielten empirischen Überprüfung formulieren beide
Analysen komplementäre, operationalisierte Hypothesensysteme.

### 10.1 Das Kaskaden-Hypothesensystem (Antigravity)

Antigravity dekonstruiert das Scheitern als eine hierarchische Kaskade auf fünf
Systemebenen (Inferenz/Tokens → Modellkapazität → Agentensteuerung →
Test-Baseline → Prior-Bias).

- **Haupthypothese ($H_{\text{Kaskade}}$ – Kaskade der Systemengpässe):**  
  Die niedrige Erfolgsquote und das Fehlen eines messbaren Cubie-Vorteils spiegeln
  weder Gleichwertigkeit noch Wirkungslosigkeit der Testmethoden wider, sondern
  einen Bodeneffekt: Vorhergelagerte Engpässe bei Inferenz und Steuerung
  verhindern in über 90 % der Fälle das Erreichen der methodischen Testebene.
- **Teilhypothese H1 (Token Starvation / Reasoning-Verdrängung):**  
  Das Totalversagen in v5 beruht auf dem ungeteilten Token-Budget
  (`num_predict = 8192`), in dem ausuferndes Thinking die JSON-Aktionsausgabe
  vollständig verdrängte.  
  *Falsifizierbare Vorhersage:* Eine Deckelung des Reasonings (z. B. max. 2.048
  Tokens) oder Anhebung des Limits auf $\ge 16.384$ Tokens senkt die Quote von
  `invalid_output` mit `done_reason: length` von 73,3 % auf unter 10 %.
- **Teilhypothese H2 (Prior Dominance / Pre-Training-Bias):**  
  Ein 12B-Modell substituiert die unbekannte EBT-Syntax unter kognitiver Last
  deterministisch durch sein dominantes Pre-Training-Muster (`pytest`), solange
  freie Dateierstellung erlaubt ist.  
  *Falsifizierbare Vorhersage:* Die strukturelle Einengung des Aktionsraums (z. B.
  über ein dediziertes Werkzeug `create_ebt_contract` statt freiem `write_file`)
  steigert die EBT-Ausführungsquote von 9,5 % auf über 75 %.
- **Teilhypothese H3 (Baseline Pollution / Rausch-Attraktor):**  
  Das vollständige Scheitern auf `rich_3278` (0/14) ist primär durch die 65
  vorbestehenden Testfehler bedingt, die als kognitiver Attraktor die
  Selbstkorrektur sabotieren.  
  *Falsifizierbare Vorhersage:* Wird `run_tests` vor dem ersten Patch auf den
  aufgabenspezifischen Testpfad isoliert, sinkt die Stalling-Rate auf Rich um
  mindestens 50 %.
- **Teilhypothese H4 (Capability Threshold / Modellgrenze):**  
  Die fehlerfreie Synthese aus Problemverstehen, exaktem Editieren und
  Testabnahme erfordert eine Modellkapazität oberhalb von 12B-Q4_K_M.  
  *Falsifizierbare Vorhersage:* Ein Wechsel auf ein 30B+- oder spezialisiertes
  Coding-Modell unter gleichem Freeze steigert die Lösungsquote auf denselben
  drei Aufgaben von 7,1 % auf über 30 %.

### 10.2 Das Workflow-Engpass- und Prüfprogramm (Codex)

Codex fokussiert auf die Bruchstelle zwischen inhaltlicher Problemidee und
präziser Schnittstellenbedienung sowie eine strikte methodische Auditierung der
Metriken.

- **Zentrale Arbeitshypothese (Workflow & Interface Bottleneck):**  
  Der Engpass entsteht im gemeinsamen Arbeitsablauf aus Modell,
  Aktionsschnittstelle und Steuerung: Der Agent lokalisiert zwar relevanten Code,
  scheitert aber an der Übersetzung in fachlich passende Tests, syntaktisch
  gültige Anker-Edits (`anchor_missing`) und verifizierte Reparaturen. In v5
  verbrauchten elf am Limit beendete Thinking-Antworten ohne Aktion 87,3 % der
  Ausgabetokens und 79,6 % der gesamten Agentenlaufzeit.
- **Vierstufiges faktorielles Prüfprogramm:**
  - *Untersuchung A (Steuerung vs. Thinking trennen):* 2×2-Design (v4 vs. v5 ×
    `think=false/true`), um festzustellen, ob Thinking isoliert oder erst im
    Zusammenspiel mit den v5-Analysephasen den Aktionsstau erzeugt.
  - *Untersuchung B (Änderungszuverlässigkeit):* Vereinfachte
    Edit-/Wiederherstellungsstrategie zur Senkung von Anker- und Lesekonflikten.
  - *Untersuchung C (Modellgrenze prüfen):* Leistungsfähigeres Vergleichsmodell
    unter identischem Budget und Evaluator.
  - *Untersuchung D (Umgebungsbeitrag isolieren):* Bereinigte sichtbare Suite
    gegenüber Originalumgebung zur Messung des Rauscheffekts.
- **Falsifizierungskriterium der Workflow-Hypothese:**  
  Die Hypothese wäre substanziell geschwächt, wenn der Agent bei verbesserter
  Schnittstelle regelmäßig passende Reproduktionen und gültige Edits liefert, die
  private Lösungsquote aber dennoch auf dem Bodenniveau verharrt (in diesem Fall
  wären primär Aufgabenkomplexität, Orakel-Fehler oder Frameworkeffekte
  ausschlaggebend).

### 10.3 Methodische Konsequenz für die Hauptstudie

Beide Analysen konvergieren in der wissenschaftlichen Schlussfolgerung: Ein
valider statistischer Vergleich zwischen `qb-cubie` und `pytest` setzt zwingend
voraus, dass die Agentenbasisfähigkeit über den kognitiven und infrastrukturellen
Bodeneffekt gehoben wird. Künftige Hauptläufe dürfen erst nach erfolgter
Agentenqualifikation und ausschließlich auf vorab eingefrorenen, ungesehenen
Aufgaben durchgeführt werden.
