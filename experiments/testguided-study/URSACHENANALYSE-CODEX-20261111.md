# Ursachenhypothese zu den bisherigen Testguided-Experimenten

**Verfasser dieses Dokuments:** KI-System Codex.  
**System: Codex, Modell: GPT-6.1-Sol, Reasoning-Effort: High**  
**Erstellt am:** 11. November 2026.  
**Datenstand:** alle acht Archive unter `runs/`, einschließlich des abgeschlossenen Piloten `20261111-200641`.  
**Status:** nachträgliche explorative Analyse und überprüfbare Arbeitshypothese; kein kausaler Wirksamkeitsnachweis.

Die Auswertung und die hier formulierten Hypothesen stammen von dem oben
genannten KI-System. Sie sind keine Stellungnahme des Projektverantwortlichen.
Die in [PAPER.md, Abschnitt 9](PAPER.md#9-persönliche-einschätzung-hypothesen-und-erfahrungen-des-projektverantwortlichen)
festgehaltenen persönlichen Erfahrungen wurden nicht als empirische Belege
dieser Analyse verwendet.

## 1. Zentrale Hypothese

**Die geringe Lösungsquote entsteht überwiegend durch einen Engpass im gemeinsamen
Arbeitsablauf aus Modell, Aktionsschnittstelle und Steuerung: Der Agent findet
relevanten Code, übersetzt seine Erkenntnisse aber zu selten in fachlich passende
Tests, gültige Änderungsaktionen und eine abgeschlossene Reparatur. Dadurch
erreicht er häufig nicht die Prozessphase, in der unterschiedliche Testmethoden
ihren möglichen Nutzen entfalten könnten.**

Im jüngsten Piloten kommt ein besonders sichtbarer Mechanismus hinzu:
Thinking verbraucht unter der konkreten Konfiguration oft das gesamte
Ausgabebudget, bevor eine ausführbare Aktion entsteht. In älteren Piloten
dominieren dagegen Such-/Testwiederholungen, fehlerhafte Testannahmen und
misslingende Dateiänderungen. Die Hypothese umfasst somit mehrere aufeinander
folgende Hürden; sie behauptet keine einzige Ursache für alle Misserfolge.

Diese Interpretation ist mit den Daten vereinbar und durch konkrete Abläufe
gestützt. Offen bleibt, ob vor allem das Modell, die Steuerung oder deren
Zusammenspiel den Engpass verursacht. Ebenso offen bleibt, ob Cubie bei einem
zuverlässig arbeitenden Agenten einen Vorteil, keinen Unterschied oder einen
Nachteil bewirken würde.

## 2. Datengrundlage und nachgerechnete Ergebnisse

Direkt ausgewertet wurden die sieben `report.json`, alle 42 individuellen
`result.json` sowie die zugehörigen finalen Produktionspatches unter
`evaluation/evaluated.patch`. Für den jüngsten Piloten wurden zusätzlich alle
67 Modellantworten und die Werkzeugaktionen untersucht. Frühere Prozessbefunde
wurden anhand ausgewählter Patches und der vorhandenen Pilotanalysen eingeordnet.
Es wurden keine neuen Modellversuche oder Containerläufe gestartet und keine
historischen Archive geändert.

Alle sieben abgeschlossenen Piloten verwenden `gemma4:12b`, dieselben drei
Aufgaben (`fastapi_9425`, `requests_6589`, `rich_3278`) und Seed 42. Das Archiv
`20261111-180104` enthält nur Vorbereitung und zählt nicht als gescheiterter
Agentenlauf. Konfiguration und Implementierung ändern sich zwischen Piloten;
maßgeblich sind die jeweiligen Freezes, nicht die heutige `study.toml`.

| Archiv am 11.11.2026 | Kern / Thinking | pytest privat gelöst | Cubie privat gelöst | Nichtleere finale Produktionspatches, beide Bedingungen |
| --- | --- | ---: | ---: | ---: |
| [132401](runs/20261111-132401/report.json) | früher Kern / aus | 0/3 | 0/3 | 0/6 |
| [160158](runs/20261111-160158/report.json) | früher Kern / aus | 0/3 | 0/3 | 0/6 |
| [163110](runs/20261111-163110/report.json) | v2 / aus | 1/3 | 0/3 | 2/6 |
| [171515](runs/20261111-171515/report.json) | v3 / aus | 0/3 | 0/3 | 0/6 |
| [180702](runs/20261111-180702/report.json) | v3, überarbeitet / aus | 0/3 | 1/3; eine Evaluation nicht verfügbar | 2/6 |
| [192412](runs/20261111-192412/report.json) | v4 / aus | 1/3 | 0/3 | 1/6 |
| [200641](runs/20261111-200641/report.json) | v5 / an | 0/3 | 0/3 | 0/6 |

Die Nenner der Lösungszahlen sind die jeweils drei geplanten Versuche.
Insgesamt liegen drei privat bestätigte Lösungen und fünf nichtleere finale
Produktionspatches aus 42 Versuchen vor. **37 Versuche hinterlassen keinen
Produktionspatch.** Das schließt zwischenzeitliche, später zurückgenommene
Änderungen nicht aus. Ein nichtleerer Patch ist außerdem noch kein Fortschritts-
oder Korrektheitsnachweis.

Die archivierten Endzustände verteilen sich wie folgt:

| Endzustand | Versuche |
| --- | ---: |
| `stalled` | 14 |
| `model_budget` | 13 |
| `invalid_output` | 10 |
| `submitted` | 2 |
| `context_budget` | 2 |
| `agent_timeout` | 1 |

Diese Zählungen beschreiben die Entwicklungshistorie. Sie sind keine 42
unabhängigen Messungen eines unveränderten Systems. Auch die Endzustände erklären
nicht automatisch die fachliche Ursache: Der erfolgreiche FastAPI/pytest-Patch
in v4 endet beispielsweise als `stalled`.

### Die drei Erfolge als Gegenprobe

- **Requests/pytest, v2:** Ein kleiner Produktionspatch zählt bei Strings
  UTF-8-Bytes; der sichtbare Test ergänzt `super_len("€") == 3`. Der Agent reicht
  ein und besteht privat. [Vollständiger Patch](runs/20261111-163110/frozen/runs/0003/full.patch).
- **FastAPI/Cubie, überarbeitetes v3:** Der Patch behandelt die stringifizierte
  Annotation `"None"` gezielt. Die ergänzten Tests führen EBT-Verträge aus und
  prüfen `result.evaluation is True`; private Evaluation und Einreichung sind
  erfolgreich. [Patch](runs/20261111-180702/frozen/runs/0001/full.patch),
  [Ergebnis](runs/20261111-180702/frozen/runs/0001/result.json).
- **FastAPI/pytest, v4:** Der Produktionspatch besteht privat, obwohl die selbst
  erzeugten Tests fachlich fehlerhaft bleiben und eine große Bestandsdatei
  überschreiben. Die private Evaluation entfernt diese Teständerung korrekt.
  Das ist eine erfolgreiche Zielfehlerreparatur, aber kein überzeugender
  testgeführter Abschluss. [Detailanalyse](PILOTANALYSE-20261111-192412.md).

Die ersten beiden Fälle zeigen, dass grundsätzlich beide Bedingungen eine
Lösung hervorbringen können. Sie widerlegen die starke Behauptung, Modell oder
Aufbau seien grundsätzlich unfähig. Sie belegen noch keine zuverlässige Fähigkeit.

## 3. Mögliche Ursachen und ihre Belege

### 3.1 Ausgabebudget wird vor der nächsten Aktion verbraucht

Für v5 wurden die Felder `raw.done_reason`, `raw.message.content`,
`raw.eval_count` und `raw.total_duration` aller archivierten Antworten sowie die
Provider-Usage und Agentenlaufzeiten nachgerechnet:

| Beobachtung im Piloten `200641` | Wert |
| --- | ---: |
| Modellaufrufe | 67 |
| Antworten mit `done_reason=length` | 11 |
| Davon mit leerem Aktionsinhalt und ausschließlich Thinking-Ausgabe | 11 |
| Ausgabetokens dieser elf Antworten | 90.112 = 11 × 8.192 |
| Anteil an allen bekannten Ausgabetokens | 87,3 % von 103.235 |
| Summe ihrer Providerlaufzeiten | 3.565,4 s = 59,4 min |
| Anteil an der summierten Agentenzeit von 4.476,4 s | 79,6 % |
| Erfolgreich angewandte Produktionsänderungen / ausgeführte EBTs | 0 / 0 |

Belege sind die [sechs Versuchsarchive](runs/20261111-200641/frozen/runs/), etwa
die [erste begrenzte FastAPI/Cubie-Antwort](runs/20261111-200641/frozen/runs/0001/steps/0006-response.json).
Die Providerlaufzeit enthält den gesamten jeweiligen Aufruf, nicht nur dessen
Thinking-Anteil. Die 79,6 % sind daher **Zeit in Aufrufen ohne ausführbare
Aktionsausgabe**, keine isolierte Messung reiner Denkzeit. Ein zusätzlicher
Timeout hat keine Tokenmessung; die Tokenzahlen sind bekannte Teilsummen.

**Ursachenhypothese:** Das Antwortverhalten mit `think=true`, das Ausgabelimit
von 8.192 Tokens und die Anforderung vollständiger JSON-Aktionen passen in diesem
Design schlecht zusammen. Eine aufwendigere Analyse erzeugt hier häufig keine
nutzbare nächste Aktion. Der einmalige Reparaturaufruf stellt den Ablauf nicht
dauerhaft wieder her.

**Grenze:** v5 führt zugleich verpflichtende Analysephasen ein. Die Beobachtung
isoliert daher keinen allgemeinen Thinking-Effekt. Schon v4 ohne Thinking
erzeugte abgeschnittene Dateiaktionen. Einfach mehr Ausgabetokens zu erlauben
könnte längere Antworten ermöglichen, unter gleichem Zeitbudget aber auch noch
weniger Handlungsspielraum übrig lassen.

### 3.2 Richtige Problemidee, misslingende Übersetzung in Werkzeugaktionen

In v5/Requests/pytest erzeugt der Agent passende rote Tests für `"€"` und
`"Test€"`. Er benennt den Unterschied zwischen Zeichen- und Bytelänge und
versucht eine Produktionsänderung. Der Ersetzungsanker entspricht jedoch nicht
dem vorhandenen Code; das Werkzeug weist ihn mit `anchor_missing` ab.
Danach endet der letzte Modellaufruf am Ausgabelimit.
[Testbeleg](runs/20261111-200641/frozen/runs/0003/steps/0012-tool.json),
[Editkonflikt](runs/20261111-200641/frozen/runs/0003/steps/0015-tool.json).

Auch Navigation verursacht vermeidbare Umwege: Im selben Versuch liefern
`find_paths("test_utils.py")` und `find_paths("test_*.py")` keine Treffer,
`find_paths("tests/*")` dagegen schon. Die Schnittstelle gleicht Muster gegen
relative Pfade ab. Diese Semantik wird vom Modell nicht durchgehend passend
angewandt. [Werkzeugfolge](runs/20261111-200641/frozen/runs/0003/steps/).

In v4 wiederholt der Agent nach einem Ankerkonflikt mehrfach Änderungen ohne
die verlangte erneute Leseaktion. Einmalige Rückkehr zu einem gültigen Leseaufruf
verhindert zudem keine erneute überlange Schreibantwort.
[Rekonstruktion der v4-Versuche](PILOTANALYSE-20261111-192412.md).

**Ursachenhypothese:** Ein Teil der geringen Leistung entsteht zwischen
inhaltlicher Diagnose und präziser Werkzeugbedienung. Allgemeine Hinweise und
Fehlermeldungen reichen nicht zuverlässig, um die Aktionsstrategie zu ändern.
Kleine, auf gelesene Ausschnitte bezogene Änderungen und eine zustandsabhängige
Wiederherstellung könnten diesen Engpass reduzieren.

**Gegenbefund und Grenze:** Die Werkzeuge ermöglichen nachweislich erfolgreiche
Änderungen. Schutzprüfungen verhindern außerdem reale Beschädigungen. Ein
abgewiesener Edit belegt keinen Werkzeugdefekt; die Hypothese betrifft die
Passung zwischen Agent und Schnittstelle. Der Erfolg einer vereinfachten
Steuerung muss erst gemessen werden.

### 3.3 Testorakel und Repräsentation des Beispiels sind nicht stabil

Der v4/pytest-Erfolg auf FastAPI geht mit falschen eigenen Testannahmen einher:
Unter anderem werden `{}` als Antwort und URLs erwartet, die nicht zu den
registrierten Routen passen. Wiederholtes Rot führt trotzdem zu Änderungen an
der Produktion. Der private Erfolg kann die Qualität dieser Tests nicht retten.

Im v5/Cubie-Versuch auf Requests wird ein vermeintliches Raketenzeichen als
Python-Literal `'\ud83d\ude80'` geschrieben. Die Prüfung des archivierten
Ersetzungstextes mit dem Python-AST ergibt zwei Surrogat-Codepunkte, U+D83D und
U+DE80, statt eines Zeichens U+1F680. Der Test erwartet vier Bytes, beobachtet am
Ausgangscode aber die Länge zwei. Er verwendet eine gewöhnliche Assertion und
führt keinen EBT-Vertrag aus.
[Patch](runs/20261111-200641/frozen/runs/0004/full.patch),
[Testausgabe](runs/20261111-200641/frozen/runs/0004/steps/0015-tool.json).

**Ursachenhypothese:** Die Kette „Anforderung → konkretes Beispiel → ausführbarer
Test → Interpretation des Fehlers“ ist selbst fehleranfällig. Formal korrektes
JSON, syntaktisch gültiger Python-Code und Assertion-Rot genügen nicht, um eine
fachlich passende Reproduktion nachzuweisen. Die v5-Analyseaktionen erzwingen
eine Dokumentation, prüfen aber deren inhaltliche Wahrheit nicht.

**Gegenbefund:** Der passende Euro-Test im anderen v5-Arm und der v2-Erfolg
zeigen, dass diese Fähigkeit vorhanden ist. Ein Defizit tritt fallweise auf;
eine generelle Unfähigkeit zur Testformulierung wäre zu stark behauptet.

### 3.4 Vorbelastete sichtbare Tests erschweren die Diagnose

Im jüngsten Freeze hat FastAPI bereits acht Collection-Fehler, Requests fünf
fehlgeschlagene Tests bei 577 bestandenen und Rich 65 fehlgeschlagene Tests bei
746 bestandenen. Die [sichtbaren Ausgangsprüfungen](runs/20261111-200641/frozen/preflight/visible/)
und die [Technikanalyse](TECHNIKANALYSE-20261111-171515.md) dokumentieren unter
anderem fehlende optionale Abhängigkeiten und Snapshot-/Umgebungsprobleme.

**Ursachenhypothese:** Bereits roter Ausgangszustand erhöht die Anforderungen an
Fehlerzuordnung und Testauswahl. Ein Agent, der diese Unterscheidung ohnehin
unsicher beherrscht, kann Zeit auf irrelevante Probleme verwenden.

**Grenze:** Die gezielten privaten Ausgangs-/Referenzprüfungen funktionieren.
Zudem scheitern viele Versuche bereits vor einem Testlauf. Die Umgebung ist ein
plausibler Verstärker, keine ausreichende Erklärung aller Ergebnisse.

### 3.5 Die Cubie-Behandlung wird häufig nicht praktisch umgesetzt

In v4 und v5 führt keiner der sechs Cubie-Versuche einen EBT aus. Im
überarbeiteten v3 findet beobachtete EBT-Nutzung nur in zwei Cubie-Versuchen
statt: FastAPI mit sechs und Requests mit drei Ausführungen über mehrere
Testläufe. Das sind Ausführungszählungen, keine neun unabhängigen Testfälle.
[v3-FastAPI-Ergebnis](runs/20261111-180702/frozen/runs/0001/result.json),
[v3-Requests-Ergebnis](runs/20261111-180702/frozen/runs/0004/result.json).

**Folgerung für die zentrale Hypothese:** Der Vergleich misst bislang häufig,
ob das Paket aus Anleitung, Modell und Steuerung überhaupt zur Anwendung kommt.
Ein Effekt tatsächlich ausgeführter EBT-Verträge kann dann kaum sichtbar werden.
Die Nichtnutzung gehört trotzdem zum Ergebnis des untersuchten Cubie-Angebots.

Als konkurrierende Hypothese bleibt offen, dass zusätzliche API-Regeln und
Anleitung den Agenten belasten. Die geringe Nutzung ist damit weder ein Beweis
für einen verborgenen Cubie-Vorteil noch eine Entlastung des untersuchten
Pakets. Nur erfolgreiche EBT-Nutzer nachträglich herauszugreifen würde die
Bedingungen anhand eines bereits beeinflussten Verhaltens selektieren.

## 4. Welche Aussagen die Daten nicht tragen

Sieben Iterationen auf drei Aufgaben sind keine ausreichend breite Stichprobe
für einen allgemeinen Frameworkvergleich. Dieselben Aufgaben und derselbe Seed
wurden wiederholt zur Entwicklung verwendet. Die zwei pytest-Erfolge und der
eine Cubie-Erfolg dürfen deshalb nicht als belastbarer Gesamtvorteil von pytest
interpretiert werden. Auch 0:0 im jüngsten Piloten belegt keine Gleichwertigkeit.
Das dortige Bootstrapintervall [0; 0] entsteht, weil alle beobachteten
Paardifferenzen null sind; es liefert keine enge Unsicherheitsaussage für neue
Aufgaben.

Im Archiv `180702` wird der vom Cubie-Agenten verursachte Requests-Importfehler
historisch als nicht verfügbare Evaluation behandelt. Damit bleiben im Bericht
nur zwei vollständige Paare. Zählt man diesen beschädigten Produktionspatch
transparent als Misserfolg, verändert sich die gepaarte Differenz von +50 auf
+33,3 Prozentpunkte. Diese Sensitivität unterstreicht die Bedeutung korrekter
Ausfallklassifikation; sie begründet keinen zuverlässigen Vorteil.
[Historischer Evaluationsbeleg](runs/20261111-180702/frozen/runs/0004/evaluation/result.json).

Ein stärkeres Modell könnte die beschriebenen Hürden besser bewältigen. Die
bisherigen Versuche vergleichen aber kein zweites Modell. Eine Modellgrenze ist
deshalb eine plausible Alternativerklärung, kein isoliert nachgewiesener Befund.
Ebenso wenig lässt sich aus den Daten ableiten, dass weitere Promptregeln oder
höhere Budgets allein genügen würden.

## 5. Kontrollierte Prüfung der Hypothese

Die folgenden Untersuchungen sind Vorschläge; sie wurden für dieses Dokument
nicht durchgeführt. Das Ziel ist, die beschriebenen Mechanismen einzeln zu
prüfen, bevor ein allgemeiner Nutzenvergleich interpretiert wird.

| Untersuchung | Gezielt variieren | Konstant halten | Vorhersage / mögliche Widerlegung |
| --- | --- | --- | --- |
| A: Steuerung und Thinking trennen | Vier Kombinationen aus v4/v5 und `think=false/true` | Modell, Aufgaben, Seeds, Guides soweit für beide Designs kompatibel, Zeit-/Tokenlimits, Umgebung, Evaluator | Wenn Thinking den Ausgabestau verursacht, steigt bei aktivem Thinking die Rate begrenzter Antworten ohne Aktion innerhalb desselben Designs. Tritt das nur bei v5 auf, spricht das für eine Wechselwirkung. |
| B: Änderungen zuverlässig anwenden | Eine vereinfachte Edit-/Wiederherstellungsstrategie gegenüber dem eingefrorenen Ausgangsdesign | Modell, Thinking und übriger Arbeitsauftrag | Weniger Anker-/Lese-Konflikte und mehr erfolgreiche kleine Produktionsänderungen. Bleibt bei passenden Reproduktionen die Änderung ebenso oft aus, wird diese Teilhypothese geschwächt. |
| C: Modellgrenze prüfen | Ein leistungsfähigeres Vergleichsmodell | Möglichst dasselbe qualifizierte Design, Aufgaben und Evaluator; gleiche äußere Budgets | Häufigere passende Reproduktionen und private Lösungen würden eine Modellgrenze stützen. Bei weiterem Aktionsstau bleibt die Schnittstelle als Ursache relevant. |
| D: Umgebungsbeitrag isolieren | Originalumgebung gegenüber dokumentiert bereinigter sichtbarer Testumgebung | Modell, Design, Aufgaben und private Bewertung | Weniger irrelevante Fehlerdiagnosen und mehr abgeschlossene Reparaturen würden den Verstärkereffekt stützen. |

Für A müssen die beiden Frameworkbedingungen in jeder der vier Kombinationen
vertreten sein. Varianten sollten über Aufgaben-/Seed-Blöcke in wechselnder
Reihenfolge laufen; alle Änderungen gehören in einen neuen Freeze. Mehrere Seeds
prüfen die Stabilität, ersetzen aber keine zusätzlichen Aufgaben. Ein größeres
Ausgabelimit wäre ein eigener Faktor und sollte nicht gleichzeitig mit einem
Designwechsel eingeführt werden. Ein Modellvergleich unter derselben Zeitgrenze
vergleicht die praktischen Modellpakete einschließlich ihres Durchsatzes;
abweichende Budgets erlauben nur Aussagen über das jeweilige Modell-Budget-Paket.

Die Messung sollte neben privatem Erfolg einen **pro Versuch nachvollziehbaren
Prozesspfad** erfassen: relevante Quelle gelesen, fachlich passende Reproduktion,
Änderung angewandt, dieselbe finale Testversion gegen Ausgangs- und Reparaturcode
geprüft, Regressionen und private Evaluation. Diese Merkmale sind getrennt zu
bewerten; der FastAPI/v4-Erfolg zeigt, dass ein privater Erfolg auch ohne einen
solchen vollständigen Pfad vorkommt. Fachliche Passung erfordert eine Prüfung der
Testinhalte, nicht nur Runnerzähler oder Modellnotizen.

**Die zentrale Hypothese wäre deutlich geschwächt**, wenn ein eingefrorener
Agent in beiden Bedingungen regelmäßig passende Reproduktionen erstellt,
korrekte kleine Änderungen ausführt und sinnvoll verifiziert, die geringe
private Lösungsquote aber unverändert bleibt. Dann wären verbleibende fachliche
Modellfehler, Aufgabenschwierigkeit, Teststrategie und mögliche Frameworkeffekte
stärker zu untersuchen. Verbessert sich dagegen zunächst die Aktionsfähigkeit
und anschließend der Reparaturerfolg, stützt das den postulierten Ablaufengpass.

Erst nach dieser Qualifikation sollte der eigentliche Cubie/pytest-Vergleich auf
**neuen, vorab eingefrorenen Aufgaben** erfolgen. Primär bleibt die private
Lösungsquote je geplantem Versuch; agentenbedingte Syntaxfehler zählen als
Misserfolg, echte Infrastrukturausfälle werden separat ausgewiesen.
EBT-Nutzung, Testqualität und Aufwand sind zusätzliche Endpunkte. Eine allgemeine
Wirkungsaussage benötigt mehr unabhängige Aufgaben und eine vorab definierte
praktisch relevante Effektgröße.

## 6. Bewertung des bisherigen Stands

Am stärksten belegt sind der jüngste Verlust von Ausgabe und Zeit vor einer
Aktionsausgabe sowie die Seltenheit finaler Produktionsänderungen über alle
Piloten. Fehlerhafte Orakel, Editkonflikte, Wiederholungen und vorbelastete
Tests liefern konkrete ergänzende Mechanismen. Die Daten sprechen damit für
eine gezielte Untersuchung der gemeinsamen Handlungsfähigkeit des Agenten.

Welche Änderung diese Handlungsfähigkeit zuverlässig verbessert und welchen
zusätzlichen Nutzen Cubie anschließend bietet, bleibt eine offene empirische
Frage. Die hier entwickelte Hypothese macht diese beiden Fragen getrennt
prüfbar und setzt einen belastbaren Frameworkvergleich nicht bereits voraus.
