# Vergleichsstudie: Cubie in einem testgeführten lokalen Agenten

## Forschungsfrage – unabhängig von der bisherigen Implementierung

Verbessert der Zugang zu qb-cubie und seiner festgelegten Anleitung die
Lösungsquote eines testgeführten Agenten mit Ollama und Gemma4:12b bei einem
festen Arbeitsbudget gegenüber demselben Agenten mit regulärem pytest?

Das Ergebnis darf positiv, unentschieden oder negativ ausfallen. Der Vergleich
soll eine Nutzenbehauptung prüfen, nicht ihren Erfolg voraussetzen. Gemessen
wird zunächst **Cubie einschließlich Anleitung**. Zwei Gruppen können den Effekt
der Bibliothek nicht vom Effekt der zusätzlichen Anleitung isolieren. Dafür
wäre später eine eigene Ablationsstudie notwendig.

## Gemeinsames Testguided-Agenten-Design

1. Aufgabe, vorhandenen Code und Tests untersuchen; relevanten Ausgangslauf beobachten.
2. Bei fehlendem Verhalten einen fachlich begründeten Test ergänzen oder überarbeiten.
3. Eine fachliche Rotbeobachtung anstreben; Sammel-, Syntax- und Importfehler beheben.
4. Implementierung ändern und relevante Tests wiederholen.
5. Bei Bedarf Code **und Tests** überarbeiten; vor Abgabe erneut prüfen.

Beide Agenten erhalten dieselben Werkzeuge, denselben Basisprompt, dieselben
Kontextregeln und Budgets. Der Unterschied besteht in Bibliothek und Anleitung:

| Bedingung | Pytest-Agent | Cubie-Agent |
| --- | --- | --- |
| Testausführung | pytest | pytest, darin Cubie-Tests möglich |
| Bibliotheken | Aufgabe und pytest | zusätzlich qb-cubie |
| Anleitung | festgehaltene pytest-Kurzanleitung | festgehaltene Cubie-Kurzanleitung |
| Produktionscode und sichtbare Tests | bearbeitbar | bearbeitbar |
| Neue, geänderte und gelöschte Tests nach Rot/Grün | erlaubt | erlaubt |
| Private Prüftests, Referenzfix, fremde Läufe | unsichtbar | unsichtbar |

Eine bereits geeignete Testsuite muss nicht künstlich verändert werden. Ein
begründet falsches Testorakel darf korrigiert werden. Die Arbeitsschritte sind
eine gemeinsame Handlungsanweisung, keine starre Einbahnstraße mit anschließend
gesperrten Tests. Die tatsächliche TDD-Nutzung wird separat anhand der Belege
geprüft. Selbst gemeldete Phasen und grüne eigene Tests beweisen keine Qualität.

## Kleine, vorab festgelegte Stichprobe

Für den Einstieg sind drei Pilotaufgaben mit je einem Seed, also sechs Läufe,
sinnvoll. Der synthetische Smoke zählt dabei nicht als fachlicher Pilot.
Auf dem Piloten dürfen Prompts, Werkzeugergonomie, Kontext- und Zeitgrenzen
angepasst werden. Änderungen danach erfordern einen neuen Freeze.

Die Aufgabenzahl ist konfigurierbar. Für wenige Stunden gibt es zwei Hauptprofile:
fünf **andere** Aufgaben mit einem Seed und beiden Agenten ergeben zehn Läufe;
zehn Aufgaben ergeben zwanzig Läufe. Mit jeweils 600 Sekunden Agentenzeit,
120 Sekunden pro privater Prüfung und 60 Sekunden angenommener Rüstzeit pro
Container ergeben sich einschließlich Ausgangs-/Referenzprüfung etwa 2:40 bzw.
5:20 Stunden. Drei bzw. sechs Stunden sind Planungsziele mit Reserve, keine
garantierten Gesamtlaufzeiten. Erst den Piloten messen und anschließend das für
beide Agenten gleiche Budget festschreiben. Builds und Datenzulassung extra rechnen.

`selection.task_count`, `selection.seed`, `selection.task_types` und `seeds`
bestimmen Anzahl, Auswahl und Wiederholungen. Die Auswahl wechselt rundenweise
Aufgabentypen und Repositories; verwandte Fixes werden zusammengefasst. Bei
gleichem Pool und Seed ist eine kleinere Auswahl ein Präfix der größeren.
Die Datengrundlage bleibt eine kleine explorative Stichprobe; mehr Seeds sind
keine zusätzlichen unabhängigen Aufgaben. Größere Umfänge, etwa zwölf Aufgaben
mit zwei Seeds, sind möglich und werden vorab mit `study.py plan` kalkuliert.
Bei unveränderter 1800-Sekunden-Vorlage ergeben schon die 48 Agentenläufe bis
zu 24 Stunden ohne Vorbereitung und Evaluation.

Vor den Messläufen schriftlich festlegen:

- Datenquelle und Revision, Auswahlseed, Kandidatenliste, Ein-/Ausschlüsse und endgültige IDs.
- Python-Kompatibilität, vollständig lokal verfügbare Abhängigkeiten und klare Issue-Beschreibung.
- Mehrere fachliche Schwerpunkte: reine Logik, Datenstrukturen, Fehlerfälle, Dateiverarbeitung.
- Höchstens wenige Aufgaben pro Repository; offensichtliche Duplikate und verwandte Issues vermeiden.
- Pilot und Messung ohne überlappende Aufgaben; Referenzzulassung vor der Inferenz.
- Keine Auswahl danach, bei welchen Aufgaben Cubie oder das Modell gewinnt.

Für öffentliche SWE-bench-Aufgaben bleiben Trainingskontamination und bekannte
Lösungen möglich. Datenquelle und Bekanntheit angeben; dies ist kein Nachweis
für unbekannte Aufgaben. Die jetzige Studie betrachtet Python-Änderungsaufgaben und
vor allem Cubies EBT-Nutzung. Sie bewertet damit weder alle Cubie-Funktionen noch
die allgemeine Leistungsfähigkeit lokaler Agenten.

## Aufgabentypen als Bestandteil des Protokolls

Die IDs sind konkrete Tasks aus dem lokalen Gemma-Developer-Agent-Aufgabenpool,
der mit swegemma ausgeführt wird. Ihre Herkunft ist nicht automatisch eine
SWE-bench-Verified-Zulassung. Unsere Annotation entsteht vor Modellläufen aus
lokalem Issue, Referenzpatch und Testpatch und wird getrennt von technischer
Zulassung geführt. [Alle Einzelprüfungen](KANDIDATEN.md) sind dokumentiert;
der [Katalog](candidate-catalog.json) bindet sie an Quellhashes.

| Primärer Aufgabentyp | Fachliche Beobachtungen |
| --- | --- |
| Parsing und Encoding | korrelierte Wertepaare, Grenzfälle, Headerwerte, Byte-/Zeichenlängen |
| API und Schema | HTTP-Status/Body, JSON-/Schema-Diffs, Aliasverhalten |
| Python-Protokolle | Proxyobjekte, Deskriptoren, Attribute, Hashbarkeit |
| Terminaldarstellung | Text-/ANSI-Snapshots, Styles, Spans, Promptantworten |
| Exceptions und Diagnostik | Typ/Meldung, Notizen, Serialisierungs-Roundtrips |
| Dateisystem und Konfiguration | temporäre Dateien, Environment und Optionspriorität |
| Lebenszyklen und Zustände | Close/Reset, Zustandsübergänge, Exitcodes und Prozessbelege |
| Unicode-Algorithmen | Zellbreiten, Graphemspans, Schnittpositionen, Terminierung |

Jede Messaufgabe trägt `task_type`, `change_kind`, `test_scope`, `repo` und
`related_group`. Änderungsart und Testaufbau sind eigene Achsen: Ein Feature ist
kein Bugfix, eine lokale HTTP-Fixture kein reiner Unit-Test. Der Typ ist die
primäre Arbeitsanforderung, kein Maß für Schwierigkeit oder vermuteten Cubie-Nutzen.
Aufgaben können Nebenanforderungen haben; die Begründungen bleiben im Katalog.

Die Metadaten werden im Freeze, Laufplan und Ergebnis gespeichert. Berichte
zeigen pro Typ und Änderungsart Fallzahlen, Erfolge und Ausfälle, gepaarte
Differenzen, gemessene Tokens, Zeit, Modell-/Werkzeugaufrufe und Testbeobachtungen.
Die fachlichen Artefakte selbst bleiben im JUnit-, Aktions- und Patcharchiv.
So lassen sich Unterschiede auf konkrete Aufgaben und Belegarten zurückführen.
Private Referenzbegründungen gelangen nicht in den Agentenprompt.

Kleine Typgruppen werden deskriptiv ausgewertet. Bei einer Aufgabe pro Typ
erlaubt das Ergebnis keine belastbare Typ-Rangfolge. Fehlende Typen und
Testabdeckung ausdrücklich ausweisen: Im aktuellen Hauptprofil sind Lifecycle-
und Terminierungsfälle noch nicht vertreten. Eine Endlosschleife als Ausgangsfehler
und bestimmte Missing-API-Fehler erfüllen das aktuelle Assertion-Rot-Gate nicht;
diese Einschränkung darf nicht nach einem Modellergebnis umgedeutet werden.

Kurze und lange Pläne sind Varianten vor Studienbeginn. Einen nach erfolgreichen
Zwischenergebnissen verlängerten Lauf nicht als unabhängig vorregistrierte zweite
Studie ausgeben. Änderungen an Auswahl und Typfiltern benötigen einen neuen Freeze.

## Gepaarter Ablauf und faire Ressourcen

Für jede Kombination aus Aufgabe und Seed bearbeiten beide Agenten denselben
unveränderten Snapshot. Die Reihenfolge der Aufgabenpaare wird reproduzierbar
gemischt; Pytest/Cubie als erster Lauf wechseln sich balanciert ab. Alle Läufe
erfolgen seriell. Jeder erhält einen neuen Container und einen leeren Dialog.
Es gibt keinen Wissenstransfer und keine übernommenen Lösungsversuche.

Festgehalten werden Modellname **und Digest**, Quantisierung, Ollama-Version,
Samplingparameter, Thinking-Einstellung, Kontextgröße, Ausgabelimit, Prompts,
Guidebytes, Werkzeug- und Runnercode, swegemma-Code und Abhängigkeiten sowie
Container-IDs. Ein Seed garantiert nicht über unterschiedliche Hardware und
Software hinweg bitgleiche Inferenz. Auch bei gleichem Seed sind die beiden
Prompts verschieden; die Paarung kontrolliert Aufgabe und Laufbedingungen.

Gleich sind Zeit-, Modellaufruf-, Werkzeug-, Kontext- und Ausgabelimits. Die
Anleitungen müssen brauchbar sein, nicht künstlich gleich lang. Ihre Tokens
zählen zum jeweiligen Kontext und tatsächlichen Verbrauch. Die Kontextgrenze
in Bytes ist keine Tokenzählung; im Piloten die archivierten Ollama-Zählwerte
prüfen und genügend Platz für die Antwort lassen. Ältere vollständige Dialogpaare
können nach derselben Regel aus dem Kontext fallen; sie bleiben im Archiv.

Zeit wird ab Beginn der Agentenschleife gemessen; Setup und private Evaluation
werden getrennt protokolliert. Modellladezeit innerhalb eines Aufrufs zählt zur
Agentenzeit. Deshalb Reihenfolge ausbalancieren und für Zeitvergleiche keine
anderen Inferenzjobs parallel ausführen. Hardware, GPU-Treiber und sonstige Last
zusätzlich im Versuchsprotokoll festhalten. Es gibt keine automatische Wiederholung
ungültiger Antworten oder stillen Modellwechsel.

Auch bei ausgeschöpftem Budget oder ungültiger letzter Modellausgabe wird der
bis dahin gespeicherte Arbeitsstand unabhängig geprüft; eine explizite Abgabe ist
kein zusätzliches Erfolgskriterium. Der Status bleibt sichtbar. Die Agentenuhr
wird an den Aktionsgrenzen geprüft, und die verbleibende Zeit begrenzt HTTP- und
Werkzeugaufrufe. Das ist keine vom Betriebssystem erzwungene Gesamtlaufzeitgrenze:
Socketoperationen und abschließende Belegsicherung können darüber hinausgehen.

## Beobachtung während der Ausführung

Der Starter `./study --mode pilot|short|long|smoke` erstellt ein neues Archiv und
führt Vorbereitung, Zulassung, Freeze, Vorprüfung und Agentenläufe aus.
`--prepare-only` beendet den Ablauf vor Inferenz. Alle Flagüberschreibungen werden
vor dem Freeze angewandt und als Startkonfiguration dokumentiert.

Die lokale Live-Anzeige ist rein beobachtend: tatsächlicher Modellkontext,
validierte Aktion, sichtbares Werkzeugergebnis, abgeschlossene Antwort und
Studienfortschritt. Der Modellaufruf bleibt nichtstreamend; Wartezeiten werden als
solche angezeigt. Eine Ansichtenpause oder die Betrachtung älterer Schritte
verändert weder Agentenablauf noch Kontext oder Budget. Es gibt keine Eingabe-
oder Korrekturfunktion im Monitor. Beide Bedingungen werden unter denselben
Beobachtungseinstellungen ausgeführt; die Belegsicherung zählt zur Agentenzeit.

Ereignisse und Zustand liegen getrennt von eingefrorenen Eingaben unter
`monitor/`. Die Browser-API liefert keine privaten Referenzdateien und keine
beliebigen Dateipfade. Das Ereignisjournal ergänzt die bereits gespeicherten
Anfragen, Rohantworten und Test-/Patchbelege. Nach einem Abbruch werden vorhandene
Versuche erhalten und als unterbrochen bzw. nicht verfügbar ausgewiesen.

## Unabhängige Bewertung bei bearbeitbaren Tests

Der sichtbare Arbeitsstand und die Bewertungsumgebung haben verschiedene Zwecke:

1. Der Agent arbeitet mit der gesamten sichtbaren Suite und darf sie verändern.
2. Jeder Testlauf und jede Schreibaktion erhält einen Beleg; Zwischenpatches
   erlauben es, Änderungen an Tests später nachzuvollziehen.
3. Der vollständige Abgabepatch einschließlich aller Teständerungen wird archiviert.
4. In einem **neuen gemeinsamen Evaluator-Container ohne Cubie** wird aus dem
   Ausgangssnapshot nur der von swegemma gefilterte Produktionspatch angewandt.
   Sichtbare Test- und Runnerkonfiguration-Änderungen werden dafür ausgelassen.
5. Private, vorab eingefrorene Prüftests bewerten Reparatur und Regressionen.

Die Teständerungen werden also nicht aus dem Experiment entfernt. Sie bleiben
Teil der Agentenarbeit und ihrer Bewertung; sie ändern lediglich nicht den
unabhängigen Maßstab. Ein grüner manipuliert verkleinerter Testbestand kann eine
falsche Lösung dadurch nicht erfolgreich machen. Wenn ein Issue gerade eine
Produktänderung in einer von swegemma geschützten Konfigurations-/Testdatei
verlangt, ist es für diesen Studienpfad ungeeignet und vorab auszuschließen.

Eine Aufgabe wird nur zugelassen, wenn der Ausgangscode mit den privaten Tests
wegen Assertions scheitert und der Referenzfix damit vollständig besteht.
Explizite FAIL_TO_PASS- und PASS_TO_PASS-IDs sind Pflicht. Modellfehler wie
Syntax-/Importfehler in einer zugelassenen Aufgabe zählen als fehlgeschlagene
Lösungen; ausgefallene Infrastruktur und nicht auswertbare Läufe bleiben separat
sichtbar. Prüfzeitüberschreitungen werden als nicht verfügbar ausgewiesen;
insbesondere bei ungleichen Ausfallraten ist eine reine Complete-Pair-Aussage
nicht belastbar. Keine Versuche still ersetzen oder nur erfolgreiche Wiederholungen wählen.

Die Startpipeline leitet diese IDs **vor Inferenz** durch tatsächliche Sammlung
und Referenzläufe ab: geänderte Testfunktionen aus dem privaten Testpatch sowie
standardmäßig bis zu acht zusätzliche unveränderte Kontrollfälle. Gibt es nur
neue Testdateien ohne bestehende Kontrollfälle, wird deterministisch eine nach
Dateinamen verwandte vorhandene Testdatei ergänzt. Offensichtlich gesperrte
Skip-Fälle werden nicht als Kontrollfälle gewählt. Rot→Grün wird zur
Reparaturgruppe, Grün→Grün zur Regressionsgruppe; beide müssen nichtleer sein.
Die Auswahl und die vollständigen beobachteten Node-IDs werden archiviert.

Private Bewertung und erneute Vorprüfung führen anschließend genau diese
benannten Fälle aus. Das ist eine begrenzte, explizit dokumentierte
Regressionsabdeckung und kein Nachweis einer grünen gesamten Projektsuite.
`--regression-tests` verändert die Zahl zusätzlicher Kontrollfälle und muss
für beide Bedingungen vorab festgelegt werden. Fehlgeschlagene Zulassung
stoppt vor Modellaufrufen; es erfolgt kein automatischer Kandidatenaustausch.

## Zielgrößen und Auswertung

**Primär:** Anteil unabhängig gelöster Aufgaben pro Agent unter gleichem Budget.
Erfolg verlangt die fachliche Zieländerung plus die festgelegten Regressionstests; die private
Evaluation liefert kein Feedback an den Agenten.

**Sekundär:** Agentenlaufzeit, gemessene Eingabe-/Ausgabetokens, Modell- und
Werkzeugaufrufe, Abbrucharten und beobachtete Testläufe. Die Zahl erzeugter Tests
ist keine Qualitätsmetrik. Geringerer Ressourcenverbrauch bei deutlich schlechterer
Lösungsquote gilt nicht allein als Nutzen.

**Manuelle Prozessprüfung:** Pro Aufgabe und Agent, mit demselben Raster:

- Welche Anforderungen deckt der sichtbare Testbestand ab?
- Gibt es eine fachliche Rotbeobachtung vor der zugehörigen Implementierung?
- Bezieht sich das Rot auf den behobenen Fehler oder einen anderen Defekt?
- Wurden valide Anforderungen entfernt, abgeschwächt oder übersprungen?
- Wurden Testkorrekturen fachlich begründet und nach Änderungen erneut geprüft?
- Hat der Cubie-Agent Cubie tatsächlich verhaltensprüfend genutzt?

Die automatische Kennzeichnung `assertion_failure` unterstützt diese Prüfung,
beweist aber nicht, dass das Orakel richtig ist. Bei kleinem Budget alle
diskordanten Paare und eine vorab gezogene gleich große Stichprobe der übrigen
prüfen. Reviewer beurteilen die Lösung ohne Kenntnis des Erfolgs der Gegenseite;
eine vollständige Verblindung gegenüber der Bibliothek ist im Code nicht möglich.

Der Bericht zeigt alle geplanten Läufe, fehlende Ergebnisse und Erfolge je
geplantem sowie je auswertbarem Lauf. Für den gepaarten Vergleich wird zunächst
pro Aufgabe über Seeds gemittelt, dann die Differenz Cubie minus Pytest über
Aufgaben gemittelt. Ein exploratives 95%-Bootstrapintervall resampelt **Aufgaben**,
nicht einzelne Seeds. Bei weniger als zwei auswertbaren Aufgaben gibt es kein
Intervall. Abhängigkeiten innerhalb eines Repositorys bleiben eine Einschränkung;
bei einer größeren Studie nach Repository clustern. Bei fehlenden Paaren den
gepaarten Effekt nur zusammen mit den Ausfallraten berichten.

Vor der Messung eine praktisch relevante Verbesserung festlegen, beispielsweise
zehn Prozentpunkte Lösungsquote ohne erheblichen zusätzlichen Aufwand. Die kleine
Studie muss diese Schwelle nicht eindeutig unterscheiden können. Nullresultate,
negative Effekte, breite Intervalle und Nichtnutzung von Cubie sind Ergebnisse.
Keine allgemeine Überlegenheit aus dem Smoke oder aus einzelnen Erfolgen ableiten.

## Abgrenzung zur bestehenden Technik

| Vorhandener Baustein | Entscheidung für diese Studie |
| --- | --- |
| `qb_cubie.benchmarks` mit Produkt-CLI, kuratierten Szenarien und Berichten | nicht als Studiensteuerung verwendet; bleibt Produktfunktion |
| Bisheriger Developer mit Testentwurf → eingefrorenen Tests → Implementierung | nicht verwendet; widerspricht frei überarbeitbarer Suite |
| `ollama_agents`-HTTP-Client und JSON-Validator | wiederverwendet; Standardbibliothek, Messwerte und Rohantworten |
| swegemma 0.2.11 Container, Snapshots, Setup und unabhängiger Prüfer | verwendet und mit Codehashes festgehalten |
| swegemma-ADK-Agentenschleife und deren gefilterter Abgabeweg | durch gemeinsamen lokalen Ollama-Studienagenten ersetzt |
| Bisherige Experimentbelege | historische Technikbelege, keine Daten dieser Studie |

Die Bridge liegt bewusst unter `experiments/testguided-study`, gehört nicht zur
öffentlichen Cubie-API und importiert keinen Cubie-Benchmarkcode. swegemmas
installierter Quellcode wird nicht verändert. Seine Testfilterung wird erst
am getrennten Bewertungsübergang eingesetzt. Dadurch sind Produktbenchmark und
vergleichende Studie organisatorisch wie technisch getrennt.
