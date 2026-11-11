# Pilotanalyse und Konzept für den nächsten Agentenkern

Analysierter Lauf: `runs/20261111-163110`, gestartet am 11. November 2026 um
16:31 Uhr lokaler Zeit. Status: abgeschlossen, sechs von sechs Läufen verfügbar.
Dies ist der jüngste der drei vorhandenen Pilotarchive. Er verwendet bereits
`testguided-core-v2`; die Diagnose des ersten Piloten in
[AGENTENDESIGN.md](AGENTENDESIGN.md) beschreibt einen älteren Stand.

**Empfehlung:** Den gemeinsamen Kern um eine beleggestützte Ablaufsteuerung
erweitern. Arbeitsnotizen sollen Arbeit begleiten, Werkzeugfehler sollen konkrete
Reparaturen auslösen, und Testfortschritt soll an ausführbare Anforderungen
gebunden sein. Anschließend beide Frameworkspezialisierungen getrennt verbessern.
Eine bloße Erhöhung des Aufrufbudgets ist durch diese Daten nicht begründet.

Umsetzungsstand: Das unten entwickelte Konzept ist inzwischen im Kern v3 und
beiden Guides umgesetzt. Technische Regressionen und Container-Replays prüfen
es; neue fachliche Inferenzdaten liegen dadurch noch nicht vor. Die folgenden
Pilotbefunde bleiben die unveränderte Ausgangsanalyse.

## Datengrundlage und Aussagegrenzen

Ausgewertet wurden der [Bericht](runs/20261111-163110/report.json), der
[Laufplan](runs/20261111-163110/frozen/schedule.json), eingefrorene Designs,
sämtliche 110 Werkzeugaktionen, Fortschrittsdateien, Endpatches und unabhängige
Evaluationen. Die 668 in Freeze- und Laufmanifesten aufgeführten Eingabe- und
Laufartefakte wurden gegen ihre SHA-256-Werte geprüft; alle stimmen überein.
Auch die 53 aktuellen Laufzeitquellen stimmen mit der Quellenbindung des Freezes
überein. Die aggregierten Kennzahlen wurden gegen `report.json` abgeglichen.
Die archivierten Guides stimmen mit den aktuell ausgelieferten Guides überein.
Die Ursachenanalyse wurde mit `agent.py`, `iteration.py`, `workspace.py` und dem
Ollama-Client abgeglichen. Es wurde keine neue Modellinferenz gestartet.

Beide Bedingungen haben denselben Kern
`01a4400795d86ead0519c834f5c69ba78ae147e6741eb793be37001fdd4b918d`,
Gemma4:12b, Seed 42, Temperatur 0,2, `think=false`, 16.384 Kontexttokens,
4.096 Ausgabetokens sowie je 24 Modell-/Werkzeugaufrufe und 600 Sekunden Budget.
Das lokale Kontextlimit beträgt 40.000 Bytes.

Drei Aufgaben und ein Seed erlauben eine Fehleranalyse, aber keinen belastbaren
Frameworkvergleich. Der eine zusätzliche Erfolg gegenüber den beiden älteren
Null-Erfolg-Piloten ist ein Machbarkeitsbeleg für diesen konkreten Ablauf;
die Daten isolieren keine einzelne wirksame v2-Änderung. Modellgröße, Denkmodus
und Guidequalität wurden nicht unabhängig variiert.

## Ergebnisse nach Lauf

| Lauf | Aufgabe | Bedingung | Aufrufe Modell / Werkzeug | Agentenzeit | Ergebnis und entscheidender Verlauf |
| --- | --- | --- | ---: | ---: | --- |
| 0001 | FastAPI 9425 | Cubie | 10 / 10 | 42,8 s | `stalled`; neun Inhaltssuchen, keine Datei gelesen oder geändert |
| 0002 | FastAPI 9425 | pytest | 15 / 15 | 118,7 s | `stalled`; falscher Pfad wiederholt gelesen, danach identische breite Suchen |
| 0003 | Requests 6589 | pytest | 14 / 13 | 85,1 s | `submitted`, privat gelöst; gezielter Rot–Änderung–Grün-Zyklus |
| 0004 | Requests 6589 | Cubie | 24 / 24 | 244,0 s | `model_budget`; zwölf Arbeitsnotizen und zwölf Leseversuche desselben falschen Pfads |
| 0005 | Rich 3278 | Cubie | 24 / 24 | 229,1 s | `model_budget`; neuer Test wird grün, prüft aber ein anderes Verhalten; keine Produktionsänderung |
| 0006 | Rich 3278 | pytest | 24 / 24 | 242,8 s | `model_budget`; Testdatei unter falschem Namen geschrieben, fünf Änderungen scheitern an der Textverankerung |

Pytest löst 1/3 Aufgaben, Cubie 0/3. Alle drei Paare sind verfügbar; kein Lauf
endet wegen Wandzeit, Kontextbudget oder ungültigem JSON. Zwei enden mit
`stalled`, drei am Modellbudget, einer mit Abgabe. Nur 0003 ändert erfolgreich
Produktionscode. Die vorhandene verankerte Ersetzung schützt in 0006 korrekt
vor einer Änderung auf Basis nicht passenden Ausgangstexts.

Die sichtbaren Testbeobachtungen umfassen insgesamt vier ungültige Testläufe,
drei sonstige Testfehlschläge, ein Assertion-Rot und zweimal Grün. Das zweite
Grün gehört zum fachlich unpassenden Rich-Test. Ein grüner Testlauf allein
belegt somit keinen Fortschritt an der eigentlichen Anforderung.

Ressourcen: 111 Modellaufrufe, 110 Werkzeugaktionen, davon **39 Arbeitsnotizen
(35,5 %)**. 969.809 von 979.599 gemeldeten Tokens sind Eingabetokens (99,0 %),
über alle Anfragen aufsummiert. Das sind Providerzähler, keine Zahl einzigartiger
Kontexttokens oder unmittelbar bezahlter Rechenoperationen. Die mediane
Agentenzeit beträgt 118,7 Sekunden für pytest und 229,1 Sekunden für Cubie;
unterschiedliche Abbruchpunkte begrenzen die Interpretation dieser Differenz.

## Befunde und Mechanismen

### 1. Die Arbeitsnotiz verdrängt Arbeit und verdeckt Stillstand

In [0004](runs/20261111-163110/frozen/runs/0004/agent.json) alternieren
`update_ledger` und `read_file("requests/utils.py")` bis zum Budgetende.
Der tatsächliche Pfad ist `src/requests/utils.py`, wie der gepaarte Lauf 0003
durch Suche feststellt. Die letzte Fortschrittsmeldung von 0004 lautet dennoch
`continue`.

Das ist durch die Implementierung erklärbar: Jede Notiz braucht einen eigenen
Modell- und Werkzeugaufruf. `progress()` vergleicht aufeinanderfolgende Ereignisse;
auch die Abbruchzählung in `develop()` wird durch eine dazwischenliegende Notiz
zurückgesetzt. Unterschiedlicher Notiztext kann selbst Notizserien unsichtbar
machen. Dass ein Ledger vorhanden ist, bedeutet außerdem nicht, dass sein Inhalt
auf überprüften Dateien beruht: Beide FastAPI-Hypothesen verwischen die im Issue
explizite Unterscheidung zwischen `None` und der Zeichenkette `"None"`.

### 2. Werkzeuge sind verfügbar, aber nicht als verständlicher Arbeitsablauf verankert

Kein Lauf nutzt `list_files` oder `search_files`. Alle 26 Suchen verwenden das
alte globale `search_text`. In 0001 wird ein Dateipfad als Suchinhalt verwendet;
in 0002 werden trotz bekanntem Treffer nicht vorhandene Dateipfade konstruiert.
Das Werkzeugangebot allein korrigiert das mentale Modell des Agenten nicht.

Fehler liefern lange Python-Tracebacks statt kurzer, typisierter Rückmeldungen.
In 0006 gibt es fünf erfolglose `replace_text`-Aufrufe; ein erneutes Lesen folgt
erst am letzten Schritt. Die Exaktheitsbedingung ist sinnvoll, die anschließende
Fehlerbehandlung unzureichend.

### 3. Schemaerfüllung garantiert weder eine brauchbare Aktion noch einen Test

[0006, Schritt 0007](runs/20261111-163110/frozen/runs/0006/steps/0007-tool.json)
schreibt erfolgreich eine Datei namens `", "`. Sie enthält Imports und viele
Kommentare, aber keine Verhaltensassertion. Das nachfolgende Testziel ist eine
andere, nicht vorhandene Datei. Die Antwort hat gültiges JSON und den Stopgrund
`stop`; die bestehende Reparatur für `invalid_output` wird deshalb nicht aktiv.

Beide Rich-Agenten führen zunächst `run_tests(["rich/ansi.py"])` aus; pytest
sammelt dort keine Tests. Der Runner bestätigt zwar die Ausführung und meldet
`invalid_test_run`, stellt aber keine Verbindung zwischen angelegter Datei,
gesammeltem Test und dem nächsten sinnvollen Schritt her.

### 4. Der Testoracle weicht vom Issue ab

Das sichtbare Rich-Issue nennt ausdrücklich zweistellige Sequenzen wie
`\x1b7` und `\x1b8` sowie den Bereich `\x1b0` bis `\x1b?`. 0005 prüft stattdessen
`\x1b[8;mHello\x1b[0m`. Nach Reparaturen von `.render()` über `.text` zu `.plain`
wird dieser Test grün, ohne Produktionsänderung. Er reproduziert den gemeldeten
Fehler nicht. 0006 argumentiert ebenfalls über CSI-/SGR-Parameter und versucht
eine fachlich anders gerichtete Regexänderung.

Der erfolgreiche Requests-Lauf zeigt das Gegenbild:
[Teständerung](runs/20261111-163110/frozen/runs/0003/steps/0007-tool.json),
[Assertion-Rot](runs/20261111-163110/frozen/runs/0003/steps/0008-tool.json),
[Implementierungsänderung](runs/20261111-163110/frozen/runs/0003/steps/0010-tool.json)
und [Grün](runs/20261111-163110/frozen/runs/0003/steps/0011-tool.json).
`super_len("€") == 3` scheitert zunächst mit Istwert 1; nach der Änderung bestehen
203 sichtbare Tests bei zwölf Skips. Alle zwölf ausgewählten privaten
Prüffälle bestehen ebenfalls. Das belegt die Lösung innerhalb des eingefrorenen
Evaluationsumfangs, keine universelle Korrektheit über andere Umgebungen.

### 5. Cubie wird im letzten Pilot nicht verhaltensprüfend verwendet

0001 und 0004 gelangen nicht zum Testschreiben. 0005 importiert `EBT` und
`WorldState`, ruft sie aber nie auf; der finale Test ist eine gewöhnliche
pytest-Assertion. **Kein Cubie-Lauf führt einen EBT-Vertrag aus.** Die Quote 0/3
misst damit vorwiegend Navigation, Ablauf und Aufgabenverständnis in der
Cubie-Bedingung; sie belegt keinen Nachteil der EBT-Ausführung.

Der Cubie-Guide enthält mehrere ausführliche Beispiele und zwei zulässige
Auswertungsstile: explizites Prüfen von `result.evaluation` bei `reporter=None`
und Ausführung mit Standardreporter. Letzteres ist laut Implementierung korrekt:
`PytestReporter` erzeugt bei Vertragsverletzung eine Assertion. Ein fehlendes
explizites `assert` in diesen Beispielen ist daher kein nachgewiesener Bug.
Für ein kleines Modell ist ein einziger klarer Standardstil dennoch eine
prüfbare Vereinfachungshypothese.

### 6. Kontext und allgemeine Testfehler benötigen bessere Aufbereitung

Die Bytegrenze wird in den archivierten Nachrichten eingehalten (Maximum
39.993 Bytes). Trotzdem meldet FastAPI/pytest bis zu 16.327 Eingabetokens bei
16.384 konfigurierten Kontexttokens. Schema, Chatformat und Ausgabereserve werden
durch eine reine Byteprüfung nicht zuverlässig abgedeckt. Ein tatsächlicher
Verlust bestimmter Instruktionen beim Provider ist damit **nicht bewiesen**;
Kontextdruck ist eine zu untersuchende Hypothese.

Der breite Rich-Testlauf 0006/0013 hat 835 Testfälle, 65 Fehler und 24 Skips;
51 Fehler enden mit TypeError, 14 mit AssertionError. Zu diesem Zeitpunkt wurde
Produktionscode nicht erfolgreich geändert. Diese Suitefehler wurden somit nicht
durch einen erfolgreichen Agentenpatch an Produktionscode verursacht. Ihre
genaue Herkunft ist gesondert zu prüfen. Die gemischte Suite wird nur als
`test_failure` zusammengefasst; der Modellkontext enthält den abgeschnittenen
Beginn der Ausgabe. Einzelne relevante Fehler können darin untergehen.

## Zielentwurf: gemeinsamer Kern v3

Freeze, getrennte Workspaces, private Evaluation, Modellidentitäten und gepaarte
Ausführung bleiben Grundlage. Die beiden Bedingungen bleiben Spezialisierungen
eines gemeinsamen Kerns. Ein zweiter Modellagent oder ein größeres Modell ist
für die hier belegten Steuerungsprobleme zunächst nicht erforderlich.

### A. Arbeitsnotiz als Metadatum einer Aktion

Die Modellantwort enthält eine konkrete Aktion und optional eine kurze
Aktualisierung von Hypothese, Anforderung und nächstem Schritt. Der Runner
übernimmt sie atomar mit der Aktion; dafür entsteht kein zusätzlicher
Werkzeugaufruf. Modellaufrufe, Tokens und Zeit bleiben vollständig budgetiert.
`update_ledger` entfällt im neuen Schema als eigenständige Standardaktion.

Der Runner führt belegte Fakten separat: existierende Pfade, gelesene Bereiche,
Dateihashes, gesammelte Test-IDs und letzte Ergebnisse. Eine Modellhypothese darf
diese Fakten nicht überschreiben. Zu jeder Anforderung werden erwartetes
Verhalten, konkretes Beispiel und die zugehörige Issue-Stelle notiert. Lange
Selbstgespräche ersetzen keine Aktion.

### B. Ablauf aus Belegen ableiten und Schleifen gezielt unterbrechen

Der Controller verwaltet `orientieren → reproduzieren → ändern → verifizieren →
abgeben`, ergänzt um Reparaturpfade. Das sind beobachtete Arbeitszustände;
das frei gesetzte `stage` bleibt lediglich Auditinformation.

Wiederholungen werden über ein Fenster fachlicher Werkzeugaktionen erkannt,
unabhängig von Notizen und `stage`. Die Signatur enthält Aktion, wesentliche
Argumente, Ergebnis und relevante Dateiversion. Eine beliebige Änderung an einer
unbeteiligten Datei zählt nicht automatisch als Fortschritt. Zusätzlich wird
gezählt, wie lange keine neue relevante Datei, kein neuer Befund oder keine
erfolgreiche Änderung hinzugekommen ist. Unterschiedliche Suchbegriffe allein
setzen diese Zählung nicht zurück.

Als zunächst zu prüfende Politik: Nach zwei gleichen erfolglosen Aktionen
konkrete Reparatur anbieten; vor einem dritten unveränderten Versuch diesen mit
einer strukturierten Rückmeldung abweisen. Bleibt eine begrenzte Umplanung ohne
neue Evidenz, mit `stalled` enden. Ablehnungen zählen weiter gegen das Budget.
Ein erneuter Versuch nach relevantem Dateiwandel oder korrigierten Argumenten
bleibt möglich. Die Parameter werden vor Entwicklungsversuchen festgelegt.

Tests bleiben jederzeit bearbeitbar. Ein zunächst grüner neuer Test führt zur
Prüfung seiner Reproduktionswirkung; er erzwingt weder einen künstlich roten
Test noch automatisch eine Implementierungsänderung. Ein bereits hinreichender
Bestandstest kann die Anforderung abdecken. Eine Abgabe ohne Reproduktion bleibt
möglich, muss die fehlende Evidenz jedoch ausdrücklich ausweisen.

### C. Navigation und Änderungen reparierbar gestalten

- Eine kleine anfängliche Repositoryübersicht aus dem sichtbaren Workspace
  liefern: Wurzel, Quell-/Testverzeichnisse und Projektkonfiguration. Große Bäume
  paginieren; keine privaten Aufgabennamen oder Referenzinformationen einspeisen.
- Dateinamen über `find_paths(pattern, start)` und Inhalte über
  `search_content(path, query, start)` suchen. Ein klarer Standard pro Zweck;
  das globale alte Werkzeug im neuen Standarddesign entfernen. Das erfordert
  eine neue Schema-/Designrevision, nicht nur einen anderen Prompt.
- Bei `not_found` kurze Fehlercodes und vorhandene ähnliche Pfade liefern.
  Vorschläge sind Suchhilfe und werden nicht ungeprüft als Änderungsziel benutzt.
- `replace_text` behält eindeutige Verankerung, ergänzt Ausgangshash und
  `match_count`. Bei Konflikt einen kleinen aktuellen Ausschnitt liefern und vor
  unverändertem Retry ein erneutes Lesen verlangen.
- Mutationen bestätigen tatsächlichen Pfad und neuen Hash. Auffällige neue
  Dateinamen und abweichende nachfolgende Testziele gezielt validieren;
  nicht pauschal alle ungewöhnlichen Repositorypfade verbieten.

### D. Testbelege strukturieren und an Dateiversionen binden

`run_tests` liefert zusätzlich zu Rohbelegen gesammelte Test-IDs, Counts und
begrenzte Diagnosen je Fehler: Phase, Exceptiontyp, Ort, kurze Meldung. Eine
gezielte Collection-Funktion kann fehlende Ziele früh erkennen. Fehlende Ziele,
Test-API-Fehler und vermutete Verhaltensfehler benötigen unterschiedliche
Reparaturvorschläge; TypeError oder AttributeError dürfen nicht pauschal als
Testfehler gelten, weil sie auch den eigentlichen Produktbug darstellen können.

Der Controller verknüpft Testversion, Produktionsversion und Ergebnisse.
Gleiche Dateinamen vor Rot und Grün reichen nicht: Nach einer Teständerung muss
die Reproduktionswirkung neu beurteilt werden. Bei Bedarf den finalen Test in
einem separaten sichtbaren Basisworkspace gegen den Ausgangscode ausführen.
Das verbraucht dasselbe transparente Werkzeug-/Zeitbudget in beiden Bedingungen
und erhält keinen Zugang zu privaten Evaluatortests.

Vor breiten Regressionen zuerst betroffene Tests ausführen. Allgemeine
Suitefehler gegen eine sichtbare Baseline abgleichen und als bestehend, neu oder
ungeklärt ausweisen. Die Hauptmessung benötigt weiterhin nur die eingefrorenen
Prüfungen als Erfolgsmaß; bestehende Suitefehler dürfen weder verborgen noch
nachträglich einem Agentenpatch zugeschrieben werden.

### E. Kontext nach Arbeitsbedarf zusammenstellen

Aufgabe, kompakter Guide, überprüfte Fakten, aktueller Plan und jüngste
Beobachtung bilden den Pflichtkontext. Dazu kommen gezielte Codeausschnitte.
Wiederholte Tracebacks und überholte Volltexttreffer werden zusammengefasst;
Rohbelege bleiben im Archiv zugänglich. Meldungen enthalten getestete IDs und
Dateiversionen, damit Kontextverdichtung keine erfundenen Belege erzeugt.

Ein Tokenbudget muss Schema/Chatformat und Ausgabereserve berücksichtigen.
Falls kein verlässlicher lokaler Tokenizer verfügbar ist, konservative
kalibrierte Grenzen verwenden und Schätzung, tatsächlich gemeldete Tokens und
vermutete Providertrunkierung getrennt protokollieren. Ein größeres `num_ctx`
ersetzt diese Kontextauswahl nicht. Die konkrete Reserve ist zu kalibrieren.

## Spezialisierungen beider Agenten

| Aspekt | pytest | Cubie |
| --- | --- | --- |
| Standard | Bestehenden nahen Test erweitern; direkter Ist-/Sollvergleich | Relevantes Verhalten durch ausführbaren EBT-Vertrag prüfen |
| Werte | Korrelierte Paare parametrisieren | Ein korreliertes Paar pro EBT-Ausführung |
| Objekte/Generatoren | Bestehende öffentliche Beobachtungs-API lesen | Kleinen Adapter nur zur Beobachtung verwenden; er delegiert an Produktionscode |
| Exceptions | `pytest.raises` mit passendem Typ und begründeter Meldung | Ein klarer Standard mit `ExceptionExpectation`; beide Beispiele testen denselben Vertrag |
| Dateisystem | `tmp_path` und konkrete Inhaltsassertionen | Zunächst einfacher `tmp_path`-Fall; TempFS nur bei benötigter Semantik erklären |
| Nachweis | Test wird gesammelt und prüft die Issue-Anforderung | Zusätzlich EBT tatsächlich ausgeführt und Evaluation wirksam geprüft |

Beide Guides werden auf wenige gleichwertige Muster verkürzt: Werte,
Exceptions und beobachtbares Objekt-/Dateiverhalten. Der Cubie-Guide verwendet
zunächst durchgehend `reporter=None` mit expliziter Prüfung von
`result.evaluation is True`. Das ist eine Designentscheidung zur Konsistenz;
die Alternative mit Standardreporter ist nicht grundsätzlich falsch.
Generische Beispiele rufen Produktionsfunktionen auf und führen deren
Berechnung nicht als Testlambda erneut aus.

Für Rich wäre aus dem sichtbaren Issue beispielsweise die Unterscheidung
`ESC + "7"` gegenüber `ESC + "[7m"` herzuleiten; für FastAPI die Zeichenkette
`"None"` gegenüber `None`. Diese Beispiele erklären den Diagnosebefund.
Sie gehören nicht als aufgabenspezifische Lösungstipps in einen allgemeinen
Guide für spätere Messaufgaben.

Cubie-Nutzung wird getrennt ausgewiesen: kein Test entstanden, nur importiert,
Vertrag konstruiert, Vertrag ausgeführt, Ergebnis wirksam geprüft. Statische
Erkennung ist ein Indiz; Laufzeitbelege sind stärker und müssen für beide
Bedingungen mit gleicher Transparenz erhoben werden. Gewöhnliche Assertions
bleiben für ergänzende Prüfungen erlaubt. Eine nachträgliche Pflicht zur
EBT-Nutzung verändert die Intervention und braucht eine eigene Designrevision.
Lösungsquote und tatsächliche Framework-Nutzung sind getrennte Messgrößen.

## Umsetzung und empirische Abnahme

Die Reihenfolge adressiert zuerst die am klarsten belegten gemeinsamen Ursachen.
Jeder Schritt erhält eine Hypothese, Elternrevision, neuen Freeze und vorab
festgelegte Kriterien. Die bestehenden Archive werden nicht verändert.

| Priorität | Änderung und betroffene Komponenten | Verbindliche technische Gegenprobe |
| --- | --- | --- |
| P0 | Notiz als Aktionsmetadatum; Controller in `agent.py` / `iteration.py`; Schema in `design.py` | Alternierende Notiz-/Fehlerfolgen werden erkannt; Notizen kosten keine separate Aktion; erfolgreicher Requests-Zyklus bleibt möglich |
| P0 | Pfadsuche, Fehlercodes, Änderungsbelege in `workspace.py` | Fehlender Pfad führt zur belegten Navigation; falscher Anker verändert nichts und erzeugt verwertbare Reparaturdaten |
| P1 | Testdiagnosen und versionierte Belegkette; `workspace.py`, `agent.py`, `campaign.py` | Falscher Testpfad und Null-Collection werden erkannt; Grün durch Teständerung allein gilt nicht als implementierter Fix |
| P1 | Kontextauswahl und kompakte Guides | Pflichtbelege bleiben trotz langer Such-/Fehlerausgabe erhalten; Frameworkbeispiele sind ausführbar und bei Vertragsbruch rot |
| P2 | Bericht mit Prozess- und Nutzungsmetriken | Ausfälle, falsche Lösungen, Stillstand und fehlende Framework-Nutzung bleiben getrennt |

Zunächst deterministische Replays der hier beobachteten Fehlfolgen verwenden,
danach echte Workspace-/Containerprüfungen mit beiden Frameworks. Diese Tests
belegen Eigenschaften der Implementierung, keine höhere Modellleistung.

Für die empirische Prüfung zuerst nur den gemeinsamen Kern bei unveränderten
Guides verbessern; danach bei festem Kern die Guides überarbeiten. Replays oder
einzelne Guideauszüge können nicht belegen, dass ein neues Design mit echter
Inferenz besser arbeitet. Dasselbe Modell und dieselben Gesamtbudgets zunächst
beibehalten. Modellwechsel, `think` und Budgeterhöhung wären separate spätere
Ablationen, wenn nach der Kernverbesserung noch entsprechende Fehler dominieren.

Die drei Pilotaufgaben sind bekannte Entwicklungsregressionen. Ihr erneutes
Lösen prüft Wiederauftreten bekannter Fehler; Generalisierung muss auf vorab
gewählten weiteren Entwicklungsgruppen gezeigt werden. Mehrere Seeds messen
Stabilität innerhalb einer Aufgabe, ersetzen aber keine unabhängigen Gruppen.
Keine Aufgabe aufgrund des Ergebnisses stillschweigend austauschen.

Vor der Hauptmessung gelten weiterhin mindestens zwei unabhängige reale gelöste
Gruppen je Bedingung mit beobachtetem Rot–Grün und identischer eingefrorener
Umgebung. Bei Einführung der versionierten Belegkette sollte die Qualifikation
zusätzlich sicherstellen, dass die finale Testversion den Defekt am Ausgangscode
nachweist. Die finale Designrevision muss die Qualifikation selbst bestehen;
Erfolge ihrer Vorläufer qualifizieren sie nicht automatisch. Entwicklungsaufgaben
und verwandte Gruppen bleiben für die Hauptmessung gesperrt.

Zusätzliche Entwicklungsmetriken: Zeit/Aufrufe bis zur ersten relevanten
Dateilesung, bis zur ausführbaren Reproduktion und bis zur ersten erfolgreichen
Produktionsänderung; Anteil Notizaktionen; wiederholte Fehler trotz Feedback;
Anzahl getesteter Anforderungen; nachweisbare EBT-Nutzung; Kontexttokens und
Abbruchgrund. Primäres Nutzenergebnis bleibt die private Lösungsquote auf einem
unberührten gepaarten Aufgabenpool. Die vorliegenden Daten begründen diese
Optimierungsschritte; ihre Wirksamkeit ist anschließend empirisch nachzuweisen.
