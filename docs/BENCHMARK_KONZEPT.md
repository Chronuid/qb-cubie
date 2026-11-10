# Konzept: ReviewAgent und DeveloperAgent

**Stand:** 10. November 2026. **Status:** Phasen 1–3 und die Produktfunktionen für Phase 4 implementiert; unabhängige Referenzaufnahme und reale Pilotmessung ausstehend.

Die Benchmarks sollen Entwicklern ermöglichen, ihre eigenen Agentensysteme reproduzierbar zu prüfen, Schwächen zu lokalisieren und Änderungen zu vergleichen. ReviewAgent untersucht die Qualität nachvollziehbarer Reviews; DeveloperAgent untersucht die Entwicklung von Projekten mit Cubie und einem durch Tests geleiteten Vorgehen. Mitgelieferte Szenarien ermöglichen den Einstieg, eigene Szenarien und konfigurierbare Benchmark-Sets die Anwendung auf den jeweiligen Entwicklungsalltag.

Zusätzlich konkretisiert das Konzept [GUTACHTEN.md, Abschnitt 9.3](../GUTACHTEN.md#93-produktnutzen-anschließend-gezielt-nachweisen). Ein optionales Vergleichsprofil mit gewöhnlichem pytest dient der Untersuchung von Cubies Produktnutzen. Ein einzelnes Agentensystem mit eigenen Aufgaben zu prüfen, ist ein vollständiger, eigenständiger Anwendungsfall.

## 1. Fragestellungen und Reichweite

| Benchmark | Primäre Frage | Frage zum Produktnutzen |
| --- | --- | --- |
| ReviewAgent | Erkennt der Agent relevante Vertragsverletzungen und begründet er seine Entscheidung am richtigen Quellstand? | Verbessern explizite RBT-Kriterien und strukturierte Nachweise die Review-Arbeit gegenüber einem gewöhnlichen Review-Auftrag? |
| DeveloperAgent | Entwickelt der Agent ein fachlich korrektes, wartbares Projekt und leitet er Änderungen nachweisbar durch Tests? | Vereinfacht Cubie gegenüber pytest Einrichtung, Diagnose und spätere Anpassungen bei vergleichbarer Ergebnisqualität? |

Die Benchmarks messen jeweils ein Gesamtsystem aus Modell, Agentenprogramm, Werkzeugen, Prompt, Dokumentation und Budget. Ein Ergebnis darf nur für diese Konfiguration verallgemeinert werden. Die erste Version konzentriert sich auf kleine Python-Projekte und Datei-Workflows; sie ist kein allgemeiner Softwareentwicklungsbenchmark.

Die drei vorrangigen Designziele sind:

- **Nutzbarkeit:** Installation und Ausführung außerhalb des Cubie-Repositories; eigene lokale oder entfernte Agentensysteme über einen dokumentierten Adapter anbinden; einen ersten aussagekräftigen Bericht mit einem kleinen Smoke-Set erzeugen.
- **Erweiterbarkeit:** Eigene Szenarien als eigenständige Pakete hinzufügen, ohne Cubie zu forken oder interne Runner-Module zu ändern. Vorlagen, Validierung und Referenzläufe unterstützen die Entwicklung.
- **Konfigurierbarkeit:** Szenarien optional nach frei wählbaren Typen und Tags strukturieren; benannte Sets deklarativ zusammenstellen; vor der Ausführung den vollständigen Laufplan einschließlich Budgets prüfen.

Die Messungen adressieren insbesondere 9.3.3 und 9.3.4. Sie können Schwierigkeiten mit Eingabe-Erwartungs-Paaren, Zustandsrollen und Reporterpolitik sichtbar machen und damit 9.3.1/2 priorisieren. Sie implementieren diese API-Verbesserungen noch nicht. Neue Arenen gemäß 9.3.5 werden erst aus beobachteten Anforderungen abgeleitet.

## 2. Ausgangslage im Repository

- [EBT](../src/qb_cubie/ebt.py), `WorldState` und `TempFS` bilden den vorhandenen Prüfkern. Die [Nutzerexperimente](../tests/tests_user_workflows/TESTBERICHT.md) enthalten bereits direkte pytest-Gegenbeobachtungen sowie korrekte und fehlerhafte Datei-Workflows. Sie eignen sich als Vorlagen für die Infrastruktur, liefern aber noch keine Agentenmessung.
- [RBT](../src/qb_cubie/rbt.py) delegiert `target` und `check` an einen `Reviewer`. Es lädt keinen Quelltext und führt kein Target aus. Ein automatisierter Agentenadapter und die Bindung von Nachweisen an Quellstände müssen ergänzt werden.
- `ReviewData` hat `passed` und ein offenes `report`-Dictionary. `RBT.run()` gibt derzeit `None` zurück. Der Benchmark erhält Ergebnisse über einen eigenen aufzeichnenden Reporter; ein Zugriff auf private RBT-Felder ist unnötig.
- EBT-Verträge mit mehreren Eingängen teilen eine Zielmenge. Korrelierte Fälle werden deshalb einzeln parametrisiert. Ein `JsonReporter` erhebt keine fachliche Assertion: Der Benchmark prüft zusätzlich ausdrücklich `RunTrace.evaluation`.
- Die Root-[conftest.py](../tests/conftest.py) verändert Arbeitsverzeichnis und Importpfad. Die Prüfung erzeugter Projekte muss daher in separaten Prozessen außerhalb des Cubie-Checkouts laufen und ein gebautes Wheel verwenden.

Die Benchmark-Funktionalität erhält eine öffentlich dokumentierte Schnittstelle und wird zugleich in Cubies Testsuite verwendet. Sie wird als optional installierbarer Teil von `qb-cubie` mit dem Extra `benchmarks` und dem Kommando `cubie-bench` ausgeliefert. Die Installation benötigt keinen Repository-Checkout. Der Kern von EBT/RBT erhält dadurch keine Pflichtabhängigkeit auf Agentenanbieter; Änderungen am Reviewer-Protokoll sind für den ersten Durchstich nicht erforderlich.

## 3. Gemeinsames Versuchsdesign

### 3.1 Vergleichsbedingungen

Das Standardprofil `agent-evaluation` prüft eine oder mehrere eigene Agentenkonfigurationen auf dem gewählten Set. Es benötigt weder einen zweiten Agenten noch einen Cubie-/pytest-Vergleich. Beim DeveloperAgent ist die Cubie-Bedingung der Standard. Das zusätzliche Profil `cubie-vs-pytest` führt die unten beschriebenen gepaarten Bedingungen aus. Ein Vergleich zweier Versionen desselben Agentensystems ist unabhängig davon möglich.

| Bedingung | ReviewAgent | DeveloperAgent |
| --- | --- | --- |
| Cubie | Kriterien werden über RBT an den Agentenadapter übergeben; strukturierter Review-Nachweis | pytest als Treiber; EBT/WorldState/TempFS für geeignete Akzeptanzfälle, bei Bedarf RBT für ausdrücklich benannte Kriterien |
| pytest | Direkter Review-Auftrag über denselben Agentenadapter; pytest prüft das Ergebnis | pytest mit Assertions, Fixtures, Parametrisierung und `tmp_path`; eigene wiederverwendbare Hilfsfunktionen sind erlaubt |

Beide Bedingungen erhalten dieselben Anforderungen, Quelldaten, Werkzeuge und Ausgabeanforderungen. Dokumentation und Beispiele sind vorab festgelegte, zur jeweiligen Bedingung passende Pakete mit vergleichbarem Umfang. Die pytest-Bedingung wird fachlich geprüft, damit keine künstlich umständliche Baseline entsteht. Beim DeveloperAgent gilt derselbe durch Tests geleitete Prozess in beiden Bedingungen; sonst würden Framework und Vorgehensweise gleichzeitig verändert.

Beim ReviewAgent sind zwei Auswertungen zu unterscheiden:

1. **Integrationskontrolle:** Identischer Quellenkontext, identische Kriterien und identische Nutzlast erreichen den Adapter einmal über RBT und einmal direkt. Dieser Vergleich prüft die Integration; er begründet keinen erwartbaren Qualitätsgewinn allein durch den RBT-Aufruf.
2. **Arbeitsablaufvergleich:** RBT-Kriterien und dokumentierte Nachweisführung werden mit einem üblichen, fachlich gleichwertigen Review-Auftrag verglichen. Ein Unterschied gilt für das gesamte angebotene Verfahren einschließlich Prompt und Kontextaufbereitung. Bei gleichem Nachweisschema in beiden Bedingungen wird dessen Nutzen nicht separat identifiziert.

Die initiale Umsetzung beginnt mit der Integrationskontrolle und der absoluten Review-Qualität. Ein kausaler Anspruch zum Nutzen der Review-Struktur erfordert später eine gesonderte Ablation, etwa gleiche Inhalte mit und ohne explizite Kriteriengliederung. Sind Ergebnisse gleich, ist auch das ein verwertbares Ergebnis.

### 3.2 Vergleichbarkeit und Wiederholungen

Eine Versuchseinheit ist `Aufgabe × Bedingung × Agentenkonfiguration × Wiederholung`. Im Standardprofil kann jede dieser Dimensionen genau einen Wert haben. Jede Einheit startet mit frischem Workspace und frischer Unterhaltung ohne Zugriff auf frühere Lösungen. Gepaarte Aufgaben nutzen denselben Ausgangsstand. Reihenfolge und Varianten werden ausbalanciert; Seeds und Laufreihenfolge werden protokolliert. Seeds garantieren bei externen Modellen keine deterministischen Antworten.

Vorgeschlagener Start: zwei Wiederholungen je Bedingung für die Kalibrierung; anschließend fünf für den Pilot. Die endgültige Stichprobe wird nach beobachteter Streuung und verfügbarer Zahl unabhängiger Projekte geplant. Wiederholungen auf demselben Projekt ersetzen keine zusätzlichen Projekte.

Budgets werden vor dem Pilot festgelegt: maximale Laufzeit, Agentenschritte, Ein-/Ausgabetokens und tatsächliche Kosten, soweit verfügbar. Als vorläufige Obergrenzen dienen 5 Minuten und 20 Werkzeugaufrufe pro Review sowie 30 Minuten und 100 Werkzeugaufrufe pro Entwickler-Episode. Kalibrierung darf diese Grenzen ändern, die eingefrorene Messrunde nicht. Kontingente und Modellpreise werden im Laufmanifest festgehalten; bei unbekannten Kosten wird „nicht verfügbar“ berichtet.

Kein Best-of-n als Hauptergebnis: Jeder begonnene Versuch geht ein. Unzulässige Ausgaben, Agenten-Timeouts und Budgetüberschreitungen werden als Nichterfüllung ausgewiesen. Externe Infrastrukturfehler werden separat dokumentiert und nach einer vorher festgelegten Regel erneut versucht; die Erstversuche bleiben erhalten.

## 4. Benchmark 1: ReviewAgent

### 4.1 Aufgaben und Material

Eine Aufgabe enthält einen kleinen Projektstand oder einen Basisstand mit Diff, einen konkreten Review-Auftrag, verfügbare Anforderungen und ein festes Kontextpaket. Der Agent darf erlaubte Dateien lesen und sichtbare Tests ausführen, aber den eingereichten Quellstand nicht verändern. Ein abschließender Hashvergleich kontrolliert dies. Alle entscheidungsrelevanten Anforderungen müssen aus dem sichtbaren Material hervorgehen.

| Aufgabenfamilie | Beispiel | Erwartete Fähigkeit |
| --- | --- | --- |
| Fachliche Rückgaben | Summe bezahlt/unbezahlt, Centbeträge, `None` gegenüber `0` | Fachliche Abweichung statt bloßer Stilkommentare erkennen |
| Dateiinhalt und Topologie | Fehlende, zusätzliche oder überschriebene Datei | Rückgabe und gesamten geforderten Dateizustand berücksichtigen |
| Zustands- und Vertragsbindung | Erwartung wird nachträglich verändert, altes Ergebnis wiederverwendet | Lebenszyklus und Entscheidungskontext nachvollziehen |
| Fehler- und Prozesspolitik | Werkzeugabbruch wird als leere Diagnoseliste behandelt | Fehlerfreiheit von fehlender Beobachtung unterscheiden |
| Testqualität | Vertauschte Eingabe-Erwartungs-Paare, nur Happy Path, wirkungslose Assertions | Lücken im Testvertrag erklären und Gegenbeispiel nennen |
| Wartbarkeit und Anforderungen | Erweiterung erfordert mehrfach dieselbe Änderung | Konkrete Wartungsfolgen am Auftrag begründen |

Für Version 1 werden sechs Familien mit je vier kuratierten Fällen geplant: zwei fehlerhafte und zwei bezüglich der verlangten Kriterien konforme Fälle, insgesamt 24. Mindestens ein fehlerhafter Fall je Familie benötigt Kontext über mehrere Dateien. Ein Teil der konformen Fälle enthält auffälligen, aber zulässigen Code. So wird eine Strategie „immer ablehnen“ erkennbar. Mehrfachfehlerfälle folgen nach zuverlässiger Bewertung der Einzelfehler.

Historische Cubie-Fehler dienen als offen gekennzeichnete Kalibrierungsbeispiele. Der eigentliche Datensatz erhält neue Implementierungen und zusätzliche Domänen, damit Wiedererkennen bekannter Befunde nicht mit Review-Fähigkeit verwechselt wird. Subjektive Wartbarkeitsaufgaben werden separat ausgewertet, nicht mit eindeutig ausführbaren Fehlerfällen vermischt.

### 4.2 Referenzurteile und Antwortformat

Jeder Fall hat eine von der Agentenantwort unabhängige Referenz: Kriterium, betroffene Stelle bzw. Symbol, Fehlermechanismus, beobachtbare Folge, zulässige Alternativerklärungen und möglichst ein ausführbares Gegenbeispiel. Der Goldstandard benennt ausdrücklich, welche Kriterien erfüllt sind. Für den offiziellen Basisdatensatz sollen zwei menschliche Prüfungen die Aufnahme bestätigen; Uneinigkeit wird vor der Messung geklärt oder der Fall bleibt explorativ. Eigene lokale Szenarien können mit einer vom Autor gepflegten Referenz starten; ihr Validierungsstand wird ausdrücklich ausgewiesen. Ein LLM kann Vorschläge liefern, aber nicht allein den Goldstandard festlegen.

Der Agent liefert ein versioniertes JSON-Objekt mit:

- Entscheidung je `criterion_id`: `pass`, `fail` oder `abstain`;
- Befunden mit `criterion_id`, Pfad, Zeilenbereich oder Symbol, Erklärung, fachlicher Auswirkung und optionalem Gegenbeispiel;
- Verweisen auf tatsächlich gelesene Quellen und ausgeführte Prüfungen;
- einer Gesamtentscheidung und optional einer Konfidenz.

Der Runner ergänzt Quell-, Aufgaben- und Kontexthashes sowie die Agentenkonfiguration. Selbst gemeldete Hashes des Agenten reichen nicht. Für RBT wird nur eine vollständige Freigabe zu `ReviewData(passed=True)`; Ablehnung oder Enthaltung ergibt `False`, mit unterscheidbarem Status im Bericht. Parser- und Adapterfehler bleiben Infrastruktur- bzw. Protokollfehler und werden nicht in eine fachlich begründete Ablehnung umgedeutet.

Ein Finding zählt als Treffer, wenn Kriterium, Ursache, betroffener Code und Auswirkung zur Referenz passen. Exakte Wortwahl und exakte Zeilennummer sind keine Voraussetzung. Mehrere Formulierungen desselben Problems zählen nur einmal; zusätzliche unbegründete Behauptungen zählen als Fehlbefunde. Neue plausible Befunde werden ohne Kenntnis von Modell und Bedingung geprüft. Referenzkorrekturen führen zu einer neuen Datensatzversion und Neubewertung aller betroffenen Antworten.

### 4.3 Kennzahlen

Primär werden Präzision und Recall bestätigter Befunde gemeinsam berichtet. Ergänzend: F1, korrekte Freigaben konformer Fälle, Fehlfreigaben fehlerhafter Fälle, Enthaltungen und gültige Antwortformate. Ohne vorhergesagte Befunde ist Präzision „nicht definiert“; bei vorhandenen Referenzfehlern ist Recall dann null. Konforme Fälle gehen über Fehlbefunde und Freigaberaten ein, nicht über einen künstlichen Recall von eins.

Einzelfallzahlen werden zunächst pro Aufgabenfamilie aggregiert, dann gleichgewichtet über Familien. Kritische Fehlfreigaben erhalten eine eigene Liste. Fachlich korrekte Entscheidung und nachgewiesene Quellenbindung sind getrennte Dimensionen: Eine zufällig richtige Entscheidung ohne Begründung erfüllt die Nachweisanforderung nicht. Die Gültigkeit der vom Runner hinzugefügten Hashes misst dessen Integrität, keine eigenständige Agentenfähigkeit.

Zeit, Kosten, gelesene Dateien und Diagnoseaufwand ergänzen die Qualitätswerte. Ein Diagnoseauftrag kann etwa die Lokalisierung einer vorgegebenen fehlgeschlagenen Prüfung und die Nennung des minimalen Gegenbeispiels verlangen. Ein pauschaler LLM-Judge für „Review-Qualität“ ersetzt diese Auswertung nicht.

## 5. Benchmark 2: DeveloperAgent

### 5.1 Projekte und Episoden

Der mitgelieferte Basisdatensatz der ersten Version enthält drei voneinander unabhängig entworfene Datei-Projekte sowie eine einfache Funktionsaufgabe als Kontrollfall. Eigene Szenarien dürfen andere Domänen und Projektumfänge verwenden. Bestehende Nutzerexperimente liefern technische Vorlagen, werden aber nicht als neue unabhängige Projekte gezählt.

| Projekt | Erstentwicklung | Wartungsepisode | Diagnose-/Reparaturepisode |
| --- | --- | --- | --- |
| Abrechnungs-Export | CSV lesen, bezahlte Positionen filtern, exakte Centbeträge und Manifest schreiben | Stornierungen und zusätzliche Ausgabespalte | Fehler an Leerdatei oder Rundungsgrenze beheben |
| Konfigurationspaket | Gleichnamige Dateien aus Unterverzeichnissen zusammenführen | Prioritätsregel und optionales Schema ergänzen | Überschreibung oder Zusatzdatei lokalisieren |
| Dokumentindex | Verzeichnisbaum lesen, deterministischen Index und kopierte Dateien erzeugen | Rekursion und Ausschlussmuster ergänzen | Fehlende Datei oder instabile Sortierung beheben |
| Reine Berechnung | Kleine Funktion mit korrelierten Ein-/Ausgabepaaren | Zusätzlicher fachlicher Randfall | Vertauschte Zuordnung erkennen |

Jedes Basisprojekt besteht aus drei separat berichteten Episoden. Eigene Szenarien können eine einzelne Episode oder eine explizite Folge definieren. Erstentwicklung beginnt mit Paketgerüst und API-Signaturen, nicht mit einer fertigen Lösung. Für den primären Wartungsvergleich starten beide Bedingungen von demselben geprüften Referenzstand und funktional gleichwertigen Tests der jeweiligen Bedingung. Diagnoseaufgaben beginnen mit demselben eingebauten Fehler. Dadurch hängt Wartungsleistung nicht vom zufälligen Erfolg der Erstentwicklung ab. Zusätzlich kann eine fortlaufende Projektentwicklung als gesonderte Sekundärmessung laufen. Abhängige Episoden werden im Manifest angegeben; ihre Reihenfolge darf eine Set-Auswahl nicht aufbrechen.

Der Agent muss Produktionscode, ausführbare Tests und eine kurze Nutzungsbeschreibung liefern. Cubie soll geeignete Akzeptanzverträge tatsächlich ausführen; ein Import allein erfüllt diese Anforderung nicht. Fachlich darf das Anwendungsmodul ohne Cubie auskommen. Tests für reine Hilfsfunktionen dürfen auch in der Cubie-Bedingung direkte pytest-Assertions verwenden.

### 5.2 Operationalisierung von „Testguided-Design“

Für diesen Benchmark bedeutet der Begriff: Anforderungen in prüfbare Verträge übersetzen, vor der betreffenden Implementierungsänderung ein fachlich begründetes Scheitern beobachten und die Implementierung anschließend durch diese Prüfungen führen. Ein nachträglich geschriebenes Testpaket reicht dafür nicht aus.

Der Runner erzwingt und protokolliert für jedes geplante Inkrement:

1. **Testentwurf:** Der Agent reicht Anforderungszuordnung und Teständerung ein. Produktionscode bleibt auf dem bisherigen Stand. Ein Grundgerüst mit importierbaren Stubs ist vorhanden.
2. **Rot:** Der Runner führt die Tests selbst aus und friert Tests, Produktionsstand und Ergebnis per Hash ein. Mindestens ein neuer Test muss wegen der fehlenden fachlichen Eigenschaft scheitern. Syntax-, Import-, Installations- und Infrastrukturfehler erfüllen diese Bedingung nicht.
3. **Grün:** Der Agent implementiert die Eigenschaft. Die eingefrorenen Tests und bisherigen Regressionen müssen bestehen. Ein Wechsel von `NotImplementedError` zum geforderten Verhalten ist ein zulässiger Ausgangspunkt; eine bloße Behauptung im Protokoll ist es nicht.
4. **Überarbeitung:** Refactoring ist bei weiterhin bestandenen Tests erlaubt. Änderungen an eingefrorenen Tests brauchen eine aufgezeichnete fachliche Begründung und erneute Rot-/Grün-Prüfung gegen den passenden vorherigen Produktionsstand. Abschwächen oder Löschen eines Tests erfüllt das Inkrement nicht.

Die kontrollierten Zwischenstände sind die Prozessbelege. Git-Commitreihenfolge und Textausgaben des Agenten allein reichen nicht. Der Runner kann den beobachtbaren Ablauf belegen, aber nicht, wann der Agent intern eine Lösung erdacht hat. Dieser stärker strukturierte Ablauf ist Teil des Benchmarks; Aussagen zur völlig freien Entwicklung erfordern einen zusätzlichen Versuch.

### 5.3 Unabhängige Ergebnisprüfung

Ein separater Evaluator installiert das eingereichte Projekt und prüft dessen öffentliche API mit zurückgehaltenen pytest-Akzeptanztests, direkten Dateivergleichen und festgelegten Invarianten. Diese Prüfungen verwenden Cubies Auswertung nicht als Wahrheitsinstanz. Alle bewerteten Eigenschaften sind im sichtbaren Auftrag beschrieben; verborgen bleiben konkrete zusätzliche Testdaten.

Die Qualität der Agententests wird zusätzlich an kuratierten fehlerhaften Implementierungen untersucht. Beispiele sind falsche Filter, ausgelassene Datei, falscher Rückgabewert und falsche Priorität. Gezählt wird nur ein fachlicher Testfehlschlag nach erfolgreicher Ausführung; ein Importfehler ist keine erfolgreiche Fehlererkennung. Ausgewertet werden nur nachweislich nicht äquivalente, zur Aufgabe passende Mutanten. Eine vom Agenten abweichend strukturierte Lösung wird über API-kompatible Varianten geprüft; nicht anwendbare Mutanten werden offengelegt und nicht als überlebt gezählt. Die korrekte Referenz muss dieselben Tests bestehen, damit ein immer fehlschlagendes Testpaket keinen Vorteil erhält.

Verdeckte Tests, Sollausgaben und Mutanten befinden sich ausschließlich beim Evaluator. Dieser kopiert nur erlaubte Abgabedateien in eine neue Umgebung, prüft sie gegen die festgelegten Anforderungen und führt sie ohne Agentenzugriff aus. Ergebnisse verdeckter Tests werden erst nach Ende der Episode zurückgegeben.

### 5.4 Kennzahlen und Produktnutzen

| Dimension | Messung |
| --- | --- |
| Fachliche Qualität | Anteil erfüllter Anforderungskriterien; Anteil vollständig gelöster Episoden; Regressionen |
| Testguided-Design | Anteil vollständig belegter Rot-/Grün-Inkremente; vollständig prozesskonforme Episoden |
| Testqualität | Erkannte kuratierte Fehler und bestandene korrekte Referenz; Abdeckung expliziter Anforderungsklassen |
| Einrichtung | Zeit, Werkzeugaufrufe und fehlgeschlagene Integrationsversuche bis zum ersten aussagekräftigen Testlauf |
| Fehlersuche | Zeit und Schritte bis zur richtigen Lokalisierung und unabhängig geprüften Reparatur |
| Wartung | Zeit, Kosten, betroffene Dateien und fachlich notwendige Testanpassungen je Änderung |
| Verständlichkeit | Verblindete menschliche Verständnisaufgaben: richtige Antwort und Bearbeitungszeit |

„Gelöst mit Testguided-Design“ verlangt sowohl vollständige fachliche Abnahme als auch alle geforderten Prozessbelege und intakte Referenzprüfungen. Die Teilwerte bleiben sichtbar. Ein gutes Endprodukt ohne Prozessbelege wird als fachlich gelöst und nicht prozesskonform berichtet.

Weniger Codezeilen oder grüne selbst geschriebene Tests sind allein kein Produktivitätsnachweis. Zeilen- und Änderungszahlen bleiben beschreibende Hilfswerte. Verständlichkeit wird beispielsweise daran geprüft, ob eine außenstehende Person erlaubte Rückgaben, zusätzliche Dateien oder die Ursache einer Fehlermeldung korrekt erklären kann. Ohne diese zusätzliche Untersuchung wird nur die Agenteneffizienz behauptet, keine bessere Verständlichkeit für Menschen.

## 6. Referenzen, Datensatz und Kontamination

Jede Aufgabe besitzt ID, Version, sichtbaren Auftrag, Domäne, Schwierigkeitsmerkmale, Anforderungskriterien, Ausgangsprojekt, Referenzlösung und unabhängige Abnahmekriterien. Ein Vorabtest zeigt, dass die Referenz besteht und die vorgesehenen fehlerhaften Varianten gezielt scheitern. Widersprüchliche oder nicht entscheidbare Fälle werden vor der Messung ausgeschlossen.

Öffentliche Entwicklungsfälle dienen Adapterentwicklung und Promptabstimmung. Zurückgehaltene Messfälle werden getrennt verwaltet und erst nach Einfrieren der Konfiguration verwendet. Varianten desselben Projekts bleiben im selben Split. Ein anderer Dateiname oder neue Zahlenwerte machen aus einer bekannten Aufgabe keinen unabhängigen Testfall.

Beim Ausführen erhält der Agent ausschließlich sein exportiertes Projektpaket; das übergeordnete Cubie-Repository mit Referenzen ist nicht eingebunden. Auch Git-Historie und Artefaktverzeichnisse dürfen keine Lösungen offenlegen. Öffentlich veröffentlichte Messfälle werden danach als potenziell bekannt behandelt. Für spätere unverbrauchte Messungen braucht es neue zurückgehaltene Fälle. Herkunft, Lizenz und mögliche Bekanntheit werden im Datensatzmanifest dokumentiert.

### 6.1 Eigenes Szenariopaket

Ein **Szenario** beschreibt eine ausführbare Review-Aufgabe oder eine Entwicklungsepisode einschließlich Material, Anforderungen und Bewertung. Ein **Szenariopaket** bündelt solche Szenarien mit eigener Namenskennung und Version. Ein **Benchmark-Set** wählt Szenarien aus einem oder mehreren Paketen aus und legt deren Ausführung fest. Mitgelieferte und eigene Pakete verwenden dasselbe öffentliche Format.

```text
my-scenarios/
  package.json
  scenarios/
    invoice-review/
      scenario.json
      task.md
      visible/                  # ausschließlich dieses Material erhält der Agent
      evaluator/                # Referenzen und Prüfungen für die Bewertung
    invoice-development/
      scenario.json
      task.md
      visible/
      evaluator/
  sets/
    team-smoke.toml
```

JSON dient den versionierten Paket- und Szenariomanifesten; TOML den von Entwicklern gepflegten Sets und Agentenkonfigurationen. Beide Formate sollen ohne zusätzliche Parserabhängigkeit gelesen werden können. Das Paketmanifest enthält mindestens `schema_version`, `namespace`, `version`, eine explizite Szenarioliste und Lizenz-/Herkunftsangaben. IDs sind innerhalb des Pakets eindeutig; extern wird ein Szenario durch `namespace/id` und Paketversion bezeichnet. Versionsangaben werden durch Inhaltshashes ergänzt.

Beispiel eines Szenariomanifests; alle Felder und Kommandos in diesem Abschnitt sind ein vorgeschlagener Vertrag, noch keine implementierte API:

```json
{
  "schema_version": 1,
  "id": "invoice-review",
  "benchmark": "review_agent",
  "title": "Unbezahlte Rechnungen im Export erkennen",
  "types": ["correctness", "file_workflow"],
  "tags": ["csv", "billing"],
  "difficulty": "small",
  "group_id": "invoice-project",
  "split": "development",
  "task": "task.md",
  "visible": "visible",
  "criteria": ["paid_only", "exact_cents"],
  "evaluator": {
    "kind": "builtin.review_reference_v1",
    "reference": "evaluator/reference.json"
  }
}
```

`benchmark` ist verpflichtend und bestimmt den Ablauf: `review_agent` oder `developer_agent`. `types` und `tags` sind optional und standardmäßig leer. Typen beschreiben fachliche Aufgabenarten, Tags weitere Merkmale. Ein Szenario kann mehrere Typen haben; es gibt keine verpflichtende Klassenhierarchie. Vorgeschlagene mitgelieferte Typen sind etwa `correctness`, `file_workflow`, `state_lifecycle`, `error_handling`, `test_quality` und `maintainability`. Eigene Typen wie `myteam/payment_rules` sind ohne Registrierung im Cubie-Kern möglich. Entwickler-Episoden können zusätzlich `initial_development`, `maintenance` oder `diagnosis` führen.

Typen beeinflussen Auswahl und Berichtsgruppierung, aber ändern keine Bewertungslogik. Diese wird ausdrücklich über `evaluator.kind` festgelegt. Szenarien ohne Typ bleiben ohne Typfilter auswählbar. `group_id` bindet zusammengehörige Varianten und Episoden für Splits und statistische Auswertungen. Ein Szenario mit mehreren Typen wird einmal ausgeführt; in der Gesamtwertung zählt es einmal. Typauswertungen können sich überlappen und werden entsprechend gekennzeichnet.

### 6.2 Szenarien entwickeln und bewerten

Der vorgesehene Ablauf für Entwickler lautet:

1. Mit `cubie-bench init-scenario --benchmark review_agent ./my-case` oder `--benchmark developer_agent` eine Vorlage mit Material, Kriterien und Beispielreferenz erzeugen.
2. Fachlichen Auftrag, sichtbares Ausgangsprojekt und Referenz bzw. Abnahmetests ergänzen. Für Standardszenarien genügt die Konfiguration mitgelieferter Evaluatoren; eigener Runner-Code ist unnötig.
3. Mit `cubie-bench validate ./my-scenarios --check-references` Schema, Dateiverweise, Kriterienzuordnung und Referenz-/Negativfälle prüfen. Strukturprüfung allein führt keinen Szenariocode aus; Referenzprüfungen tun dies ausdrücklich in der Evaluatorumgebung.
4. Das Szenario über Paketpfad und ID oder über einen Set-Filter auswählen, zunächst mit einem Fake, anschließend mit dem eigenen Agenten ausführen und den Bericht prüfen.

Die Version 1 liefert mindestens einen Review-Referenzevaluator und einen Developer-Evaluator für pytest-Abnahmen und Testguided-Design. Für semantisch nicht automatisch entscheidbare Review-Befunde unterstützt der Referenzevaluator eine manuelle Nachbewertung. Ungeklärte Zuordnungen bleiben `pending_adjudication`; sie erhalten keinen erfundenen numerischen Qualitätswert. Ein wiederkehrender CI-Lauf kann solche Fälle gesondert melden. Eine rein automatische Review-Wertung muss ihren engeren, zuverlässig prüfbaren Geltungsbereich angeben.

Für besondere Domänen ist ein dokumentiertes Evaluatorprotokoll vorgesehen: Ein explizit konfiguriertes Kommando erhält eine versionierte JSON-Anfrage und schreibt ein strukturiertes Ergebnis mit Kriterienurteilen, Messwerten und Belegverweisen. Es läuft getrennt vom Agenten. Entdeckung und Auflistung eines Pakets importieren oder starten keinen fremden Python-Code. Eigene Metriken erhalten Namen, Einheit, Richtung und Aggregationsregel; sie ersetzen die gemeinsamen Pflichtfelder und Statuswerte nicht. Fehlende Fähigkeiten oder unverständliche Schemas führen vor Beginn eines kostenpflichtigen Laufs zu verständlichen Fehlern.

Lokale Verzeichnisse und separat installierte Szenariopakete sind in Version 1 ausreichend. Ein öffentliches Szenarioverzeichnis oder automatisches Herunterladen ist eine mögliche spätere Ergänzung. Externe Pakete können somit in eigenen Repositories gepflegt und geteilt werden, ohne Änderung am Cubie-Repository. Vorlagen, JSON-Schemas, ein Tutorial und ein Beispielpaket außerhalb des Cubie-Checkouts gehören zur Abnahme.

### 6.3 Benchmark-Sets konfigurieren

Ein Set ist eine eigenständige Datei, die Quellen, Auswahl, Wiederholungen, Agenten und Budgets benennt. Das folgende Beispiel kombiniert Basisfälle und eigene Szenarien:

```toml
schema_version = 1
name = "team-smoke"
profile = "agent-evaluation"
repetitions = 1
agents = ["../agents/current.toml"]
output = "../results/team-smoke"

[[sources]]
package = "builtin:base-v1"

[[sources]]
path = "../my-scenarios"

[select]
benchmarks = ["review_agent"]
types_any = ["correctness", "myteam/payment_rules"]
tags_none = ["slow"]
splits = ["development"]

[budgets]
wall_time_seconds = 300
tool_calls = 20

[limits]
max_runs = 12
max_total_wall_time_seconds = 3600
```

Alle relativen Pfade beziehen sich auf die jeweilige Konfigurationsdatei, nicht auf das aktuelle Arbeitsverzeichnis. Auswahlregeln sind fest definiert: innerhalb einer Liste gilt ODER; verschiedene Filterfelder werden mit UND verknüpft. `types_any` verlangt mindestens einen genannten Typ, `types_all` alle genannten Typen und `types_none` schließt jeden passenden Typ aus. Dasselbe Schema gilt für Tags. Zusätzlich sind explizite `ids`, `exclude_ids`, `benchmarks` und `splits` vorgesehen. Ausschlüsse haben Vorrang. Fehlende Filter schränken nicht ein; explizit leere Filterlisten sind ungültig, um unbeabsichtigte Leerauswahlen zu vermeiden.

Eine unbekannte explizite ID, eine leere Auswahl oder ein positiver Typ-/Tagfilter ohne Treffer erzeugt standardmäßig einen Konfigurationsfehler mit den verfügbaren Werten. Eigene Bezeichner bleiben zulässig, wenn sie im geladenen Paket vorkommen. Doppelte Namespaces mit verschiedenen Paketständen und doppelte Szenario-IDs werden abgelehnt. Fehlende Episodenvoraussetzungen werden gemeldet; sie werden nicht heimlich mit ausgeführt. Für ein bewusst zufälliges Teilset wird ein Seed gespeichert; abhängige Szenarien bleiben dabei zusammen. Der erste Umfang benötigt keine verschachtelte Set-Vererbung oder eigene Abfragesprache.

Vor dem Lauf erzeugt `cubie-bench plan --suite ./sets/team-smoke.toml` einen lesbaren Plan; `--format json` liefert dessen maschinenlesbare Form. Darin stehen aufgelöste IDs und Versionen, Typen, Evaluatoren, benötigte Adapterfähigkeiten, Bedingungen, Wiederholungen, Anzahl Versuche und Budgetobergrenzen. Eine harte Laufzahl- oder Budgetgrenze wird nicht durch stilles Abschneiden der Auswahl erfüllt: Der Plan muss passen oder die Konfiguration muss geändert werden. Eine Kostenobergrenze kann nur zugesichert werden, wenn der Adapter die erforderliche Kostenmessung und Begrenzung unterstützt.

`cubie-bench run --suite ./sets/team-smoke.toml` speichert den aufgelösten Plan samt Hashes als Laufmanifest. Budgetwerte sind global voreingestellt, können im Set und ausdrücklich pro Szenario überschrieben werden; globale harte Grenzen bleiben bindend. CLI-Overrides werden zuletzt angewendet und im Plan angezeigt. Ein späterer Vergleich prüft die tatsächlich aufgelösten Szenarien und Ausführungsbedingungen, nicht bloß den Set-Namen.

## 7. Runner, Adapter und Nachweise

### 7.1 Komponenten

Die gemeinsame Infrastruktur hat sechs Verantwortlichkeiten:

1. **ScenarioLoader:** prüft Paket- und Szenariomanifeste und exportiert ausschließlich sichtbare Aufgabenmaterialien.
2. **SuitePlanner:** löst Set-Filter, Agentenkonfigurationen, Voraussetzungen und Budgets in einen unveränderlichen Laufplan auf.
3. **AgentAdapter:** unterstützt explizit konfigurierte Agentensysteme; ein deterministischer Fake dient Infrastrukturtests. Anbieterzugriff liegt hinter dieser Grenze.
4. **EpisodeRunner:** verwaltet Workspace, Phasen, Budgets und tatsächlich ausgeführte Werkzeugaufrufe.
5. **IndependentEvaluator:** prüft Reviews gegen Referenzen und Projekte gegen unabhängige Abnahmen.
6. **ResultWriter:** schreibt Rohdaten, normalisierte JSON-Ergebnisse und einen lesbaren Markdown-Bericht.

Diese Namen beschreiben zunächst Verantwortlichkeiten, keine Verpflichtung zu sechs Klassen. Die wiederverwendbaren Implementierungen liegen im installierbaren Paket; Repository-Tests rufen dieselben öffentlichen Schnittstellen auf. CLI und optionale pytest-Integration verwenden denselben Planner und Runner, damit identische Sets dieselbe Bedeutung behalten.

Der öffentliche Agentenvertrag ist unabhängig von Modellanbieter und Agentenframework. Version 1 bietet einen Adapter für externe Prozesse mit versioniertem JSONL-Protokoll. SDK- oder HTTP-Anbindungen können diesen Vertrag ebenfalls implementieren. Eine Anfrage enthält Lauf-/Szenariokennung, Auftrag, erlaubten Workspace, aktuelle Prozessphase, Ausgabeformat und Budgets. Ereignisse enthalten Status, eingereichte Artefakte, Phasenabschluss und verfügbare Nutzungsdaten; der Runner verifiziert Artefakte und führt Bewertungsprüfungen selbst aus. Getrennte Phasen können innerhalb derselben Episode dieselbe Agentensitzung verwenden; zwischen Versuchseinheiten wird sie zurückgesetzt.

Ein Fähigkeitenaustausch vor der Ausführung meldet beispielsweise Review-Ausgabe, Workspace-Änderungen, schrittweise Test-/Implementierungsabgabe, Abbruch und Werkzeug-/Tokenmessung. Unterstützt ein Agent keine kontrollierte Phasenabgabe, kann er Review-Aufgaben bearbeiten, aber nicht als prozesskonform im DeveloperAgent-Profil gewertet werden. Eine unkontrollierte Endabgabe kann höchstens in einem gesondert bezeichneten explorativen Profil laufen. Unmessbare Werte werden als unbekannt ausgewiesen; verlangte harte Grenzen ohne Durchsetzungsmöglichkeit führen schon im Plan zum Fehler. Das Protokoll erhält Referenzadapter und Vertragstests, sodass Entwickler ihren Adapter ohne Modellaufrufe prüfen können.

### 7.2 Reproduzierbarer Beleg

Jeder Lauf enthält mindestens:

```text
schema_version, run_id, benchmark, task_id, task_version, split, condition
package_namespace, package_version, package_sha256, types, tags, group_id
suite_name, suite_sha256, resolved_plan_sha256, evaluator_id, evaluator_version
source_tree_sha256, submitted_tree_sha256, task_sha256, context_sha256
agent_id, agent_version, model_id, model_parameters, prompt_sha256
cubie_commit, wheel_sha256, python_version, dependency_lock_sha256, image_digest
budgets, repetition, seed, started_at, finished_at
status, criterion_results, metrics, artifact_hashes
```

Hinzu kommen die archivierten sichtbaren Quellen, Kriterien, Agentenantworten, Phasenstände, Patches und tatsächlichen Testergebnisse. Ein Hash allein ermöglicht ohne zugehörige Inhalte keine spätere Nachprüfung. Der Quellbaumhash basiert auf sortierten relativen Pfaden und Dateiinhalten; Modus und erlaubte Symlinks werden eindeutig behandelt. Repository-Commit und Arbeitsbaumhash werden getrennt erfasst, weil lokale Änderungen existieren können.

Bei Reviews werden Quellstand und Kontext vor und nach der Bearbeitung verglichen. Ändert sich eines davon, gilt die Entscheidung für den aufgezeichneten alten Stand; für den neuen Stand ist ein neuer Review nötig. Ein überholtes Urteil darf keine Freigabe für andere Quellen erzeugen. Das setzt 9.3.4 konkret um.

Statuswerte trennen mindestens `completed`, `agent_timeout`, `budget_exceeded`, `invalid_output`, `infrastructure_error` und `not_started`. Bewertungsvollständigkeit, einschließlich `pending_adjudication`, wird separat erfasst. Beim Erreichen eines globalen harten Limits werden offene Versuche ausdrücklich als `not_started` mit Ursache berichtet; es wird kein vollständiger Set-Lauf behauptet. Die fachliche Entscheidung liegt zusätzlich in `criterion_results`. Rohantworten werden archiviert; Providerzugangsdaten werden nicht in Arbeitsumgebung oder Artefakte übernommen.

### 7.3 Ausführungsumgebung

Generierter Code und Agentenwerkzeuge laufen in einer eigens begrenzten Benchmark-Umgebung, zunächst einem Container pro Episode mit festgelegten Ressourcen, ohne Host-Workspace, Container-Daemon-Socket oder Zugangsdaten. Der Agentenadapter außerhalb dieser Umgebung vermittelt notwendige Modellaufrufe; der ausgeführte Projektcode benötigt nach Provisionierung kein Netzwerk. Der Evaluator besitzt einen getrennten Workspace und beendet bei Timeout die gesamte Prozessgruppe bzw. den Container.

Dies ist Infrastruktur des Benchmarks, keine neue Cubie-Arena. `TempFS` und `PyVenv` bleiben Werkzeuge für temporäre Ausführung und bilden keine OS-Sicherheitsgrenze. Der Benchmark darf diese Rolle nicht stillschweigend auf sie übertragen.

## 8. Aufnahme in pytest und CI

Zielstruktur; implementierter Umfang siehe Phase 10.1 und 10.2:

```text
src/qb_cubie/benchmarks/
  cli.py                        # installiertes Kommando cubie-bench
  schemas/                      # öffentliche versionierte Datenverträge
  templates/                    # Vorlagen für eigene Szenarien und Sets
  adapters/                     # Prozessadapter und Fake-Adapter
  ...                           # Planner, Runner, Evaluatoren, Berichte
  datasets/base_v1/              # mitgelieferte Szenarien
tests/benchmarks/
  conftest.py                    # Optionen und explizite Freischaltung
  test_harness_contracts.py      # deterministische Infrastrukturprüfungen
  test_scenario_packages.py      # externe Pakete, Validierung und Auswahl
  test_review_agent.py           # echte Review-Episoden
  test_developer_agent.py        # echte Entwicklungs-Episoden
tests/wheel/                     # Installation und Nutzung ohne Checkout prüfen
benchmark-suites/                # smoke, Basisdatensatz und Produktvergleich
benchmark-results/              # generierte, nicht versionierte Rohartefakte
```

Zurückgehaltene Messfälle werden zur Laufzeit aus einem separat versionierten Evaluatorpaket bezogen und nicht im Agentenworkspace abgelegt. Innere Projekt- und Mutantentests dürfen von der äußeren Sammlung nicht als eigene Repository-Tests eingesammelt werden; ihre Vorlage wird etwa als Archiv exportiert.

Geplante Bedienung nach Implementierung, zuerst aus Sicht externer Entwickler:

```bash
# In der eigenen Umgebung installieren; die Version für Messläufe festhalten
python -m pip install 'qb-cubie[benchmarks]'

# Eigene Prozessanbindung konfigurieren und Vertrag prüfen
cubie-bench init-agent ./agents/current.toml
cubie-bench validate-agent ./agents/current.toml

# Mitgelieferte Szenarien und Typen entdecken; ein kleines Set erzeugen
cubie-bench list --package builtin:base-v1
cubie-bench init-suite ./sets/smoke.toml --preset smoke \
  --agent ./agents/current.toml
cubie-bench plan --suite ./sets/smoke.toml
cubie-bench run --suite ./sets/smoke.toml

# Eigene Szenarien validieren und das eigene Set ausführen
cubie-bench validate ./my-scenarios --check-references
cubie-bench run --suite ./sets/team-smoke.toml

# Zwei gespeicherte Läufe desselben Sets vergleichen
cubie-bench compare ./results/before ./results/after

# Bestehender Standardlauf im Cubie-Repository: offline, keine Modellaufrufe
.venv/bin/python -m pytest -q

# Bewusst freigeschalteter Agentenlauf
.venv/bin/python -m pytest tests/benchmarks -m agent_benchmark \
  --run-agent-benchmarks --suite=benchmark-suites/smoke.toml

# Optionaler Produktvergleich, beide Bedingungen stehen im Set
cubie-bench run --suite benchmark-suites/cubie-vs-pytest.toml
```

Das kleine Smoke-Set enthält mindestens je einen Review- und Developer-Fall und startet mit einer Wiederholung. Alle Einsteigerkommandos und Hilfetexte verweisen auf eine kurze Anleitung: installieren, Agent anbinden, Set planen, ausführen, Bericht lesen, eigenes Szenario ergänzen. Im Bericht sind Fehlschläge bis zum konkreten Kriterium und Beleg aufklappbar bzw. verlinkt. Ein JSON-Export ermöglicht eigene Dashboards. Der Aufruf benötigt keine manuelle menschliche Beteiligung, solange der gewählte Evaluator automatisch bewerten kann; offene Review-Zuordnungen werden gesammelt zur Nachbewertung angeboten.

Die Marker `agent_benchmark`, `review_agent` und `developer_agent` werden registriert. Echte Agententests sind ohne Freischaltung ausdrücklich übersprungen; ihre Sammlung darf weder Modellimporte noch Verbindungen auslösen. Ein Marker allein verhindert die Ausführung nicht. Bei ausdrücklicher Freischaltung führen fehlende Konfiguration oder ein nicht verfügbarer Adapter zum Konfigurationsfehler statt zu einem scheinbar erfolgreichen Lauf.

In Pull Requests laufen ausschließlich deterministische Infrastrukturprüfungen mit Fake-/Replay-Adaptern und kleinen Referenzprojekten. Ein manuell gestarteter oder geplanter, budgetierter CI-Job führt die echten Messungen aus und archiviert Berichte. Ein Fake- oder Replay-Erfolg belegt die Infrastruktur, keine neue Agentenleistung. Agentenresultate werden zunächst beobachtet; erst nach Kalibrierung und stabiler Messbasis kommen gesonderte Regressionsgrenzen infrage.

## 9. Auswertung und Entscheidungsregeln

Der Bericht zeigt für beide Benchmarks getrennt Qualität, Prozess, Aufwand und Fehlerarten. Modell und Toolversionen, Anzahl unabhängiger Projekte, Wiederholungen, Ausschlüsse und abgebrochene Läufe stehen bei den Ergebnissen. Ein künstlicher Gesamtscore über beide Benchmarks ist nicht vorgesehen.

Im Standardprofil stehen Agentenregressionen und Unterschiede zwischen eigenen Agentenkonfigurationen im Mittelpunkt. Berichte zeigen Einzelurteile und optionale Gruppen nach Typ, Tag, Paket und Projekt. Nicht bewertete oder noch offene Fälle haben sichtbare Nenner und werden nicht als bestandene Fälle gezählt. Offizielle und eigene Fälle bleiben nach Herkunft und Validierungsstand unterscheidbar. Eine veränderte Set-Zusammensetzung erzeugt eine Vergleichswarnung; eine Auswertung gemeinsamer Fälle ist möglich, wird aber als Teilvergleich bezeichnet. Metriken aus verschiedenen Evaluatorversionen werden nur bei dokumentierter Kompatibilität verglichen.

Cubie/pytest-Differenzen werden pro gepaarter Aufgabe berechnet. Unsicherheit wird nach Aufgabengruppe bzw. Projekt berücksichtigt, etwa durch Bootstrap ganzer Projekte; wiederholte Episoden werden nicht als unabhängige Projekte gezählt. Bei nur drei Datei-Projekten sind Intervalle und Signifikanzbehauptungen wenig belastbar: Der Pilot liefert Effektrichtung, Streuung und konkrete Probleme, keinen allgemeinen Produktnachweis.

Für eigene CI-Gates können Sets ausdrücklich Schwellen pro Metrik oder Typ festlegen. Ein Lauf unterscheidet „vollständig ausgeführt“ von „Qualitätsschwelle erreicht“; fehlende Pflichtmesswerte und offene Bewertungen erfüllen kein Gate. Nicht vorhandene Schwellen bedeuten reine Berichterstattung, keine automatische Qualitätsfreigabe. Lauf-/Konfigurationsfehler und verfehlte Qualitätsgrenzen erhalten dokumentierte, unterschiedliche Exitcodes.

Vor einer bestätigenden Produktnutzenmessung werden primäre Kennzahlen, Mindestverbesserung beim Aufwand und tolerierbare Qualitätsabweichung festgelegt. Die Werte folgen dem Pilot und dem beabsichtigten Einsatz, werden aber vor Sichtung der zurückgehaltenen Ergebnisse eingefroren. Ein positiver Nutzenbefund verlangt einen praktisch relevanten Vorteil bei vergleichbarer fachlicher Qualität; reine Zeitersparnis durch schlechtere Abnahme genügt nicht. Für kritische Fehlfreigaben werden absolute Fallzahlen und Einzelfälle berichtet.

Die mögliche Schlussfolgerung lautet beispielsweise: „Bei den untersuchten Datei-Workflows benötigte diese Agentenkonfiguration mit Cubie weniger Schritte zur Diagnose bei vergleichbarer Abnahmequote.“ Die Benchmarks dürfen ebenso ergeben, dass pytest einfacher ist oder dass Unterschiede unklar bleiben. Wiederholt falsche Erfolge würden zuerst eine Korrektur des Prüfkerns begründen; wiederholter Aufwand bei Vertragsaufbau würde konkrete API-Arbeit priorisieren.

## 10. Entwicklungsplan und Abnahme

| Phase | Konkrete Lieferung | Voraussetzung für den nächsten Schritt |
| --- | --- | --- |
| 1. Öffentliche Verträge und Referenzen | Paket-/Szenarioschema, Agenten-/Evaluatorprotokoll und Set-Semantik; zwei Review-Fälle; ein Datei-Projekt mit drei Episoden | Aufgaben sind eindeutig; Referenz und Negativfälle sind unabhängig geprüft; Typen und Ablauf sind sauber getrennt |
| 2. Installierbarer Durchstich ohne Modell | CLI, Fake-Adapter, Planner, Phasensteuerung, Evaluator, Ergebnisdateien und Vorlagen | Smoke-Set läuft aus installiertem Wheel ohne Checkout; korrekte Lösung besteht, falsche fällt durch; fehlende Belege und Timeouts werden erkannt |
| 3. Eigene Agenten und Szenarien | Prozessadapter, Tutorial, externes Beispielpaket, Typ-/Tagfilter und Laufvergleich | Entwickler können nach Anleitung einen eigenen Agenten und einen eigenen Fall ohne Core-Änderung anbinden; Ausführung benötigt keinen zweiten Agenten oder Produktvergleich |
| 4. Basisdatensatz und Pilot | 24 Reviews, drei Datei-Projekte und ein Kontrollprojekt; optionaler pytest-Vergleich; Wiederholungen | Referenzen und Mutanten validiert; reale Läufe nachprüfbar; Streuung, Kosten und Bewertungsstreitfälle dokumentiert |
| 5. Messbetrieb | Eigener CI-Job, konfigurierbare Gates, Berichte, eingefrorene Messkonfiguration und zurückgehaltene Aufgaben | Standardtests bleiben offline; Sets sind reproduzierbar; eigene CI-Nutzung sowie Produktmessung sind dokumentiert |

### 10.1 Öffentliche Verträge und Referenzen

Die deterministischen Abnahmecases liegen unter [tests/benchmarks](../tests/benchmarks).
Die [Kriterienzuordnung und der öffentliche Schnittstellenvertrag](../tests/BENCHMARK_CASES_10_1.md)
beschreiben Paket-/Szenariovalidierung, Agenten-/Evaluatornachrichten und
Set-Semantik. Zwei neue Review-Fälle sowie ein Dokumentindex mit drei Episoden,
Referenzlösungen und 17 Fehlervarianten liefern deterministische Gegenproben.
Die öffentliche API in `qb_cubie.benchmarks` implementiert diese Verträge;
[die Anleitung](GUIDE_Benchmark-Contracts.md) beschreibt ihre Verwendung.
Laden und Planen führen keinen Szenario- oder Agentencode aus. Die Referenzen
tragen weiterhin den Stand `author_checked`; eine unabhängige menschliche
Aufnahmeprüfung steht aus. Der ausführende Durchstich folgt in Phase 2.

Wesentliche Infrastrukturprüfungen sind: immer freigebender Reviewer wird an Fehlerfällen erkannt; immer ablehnender Reviewer an konformen Fällen; doppelte Findings erhöhen Recall nicht; Enthaltung ist keine Freigabe; veränderter Kontext entwertet alte Nachweise; grüne Tests ohne beobachtete Rotphase erfüllen den Prozess nicht; fachlicher Testfehlschlag und Importfehler bleiben unterscheidbar; fremde oder fehlende Ergebnisartefakte führen nie zum Erfolg. Diese Prüfungen sichern die Bewertungslogik und sind unabhängig von Modellantworten ausführbar.

Für Nutzbarkeit und Erweiterbarkeit kommen hinzu: Paket ohne Typangaben ist lauffähig; eigene Typen erfordern keine Registrierung; Mehrfachtypen vervielfachen keine Läufe; kombinierte Filter und Ausschlüsse haben die dokumentierte Bedeutung; unbekannte IDs und unvollständige Episodenfolgen scheitern vor Agentenstart; Pfade funktionieren aus einem anderen Arbeitsverzeichnis; Laden und Planen starten keinen Szenariocode; CLI und pytest erzeugen denselben Plan; bestehende und eigene Pakete können gemeinsam ausgewählt werden; Plan, globale Limits und Gates werden eingehalten. Eine Person ohne Kenntnis der Runner-Interna soll mit Tutorial und Vorlagen eine neue Aufgabe ergänzen und deren Bericht verstehen können.

Empfohlene Reihenfolge: zuerst ein kleiner vollständiger Durchstich beider Benchmarks, dann Datensatzausbau und mehrere Agentenkonfigurationen. Den Modellvergleich oder einen großen Aufgabenkatalog vorzuziehen, würde noch ungeprüfte Bewertungsmechanismen vervielfachen.

### 10.2 Installierbarer Durchstich ohne Modell

Der Durchstich ist implementiert: `qb-cubie[benchmarks]` installiert
`cubie-bench`; `init-suite --preset smoke --fake` erzeugt ein verschiebbares
Paket mit zwei Review-Fällen und einer Dokumentindex-Erstentwicklung.
Planner, Phasensteuerung, unabhängiger Evaluator und Ergebnisarchiv verwenden
öffentliche Schnittstellen. Die Cubie-Bedingung führt EBT und RBT tatsächlich aus.

Die [EBT-Cases und ihr Schnittstellenvertrag](../tests/BENCHMARK_CASES_10_2.md)
prüfen Referenzen, Mutanten, Rot-/Grün-Belege, fehlende Artefakte und Timeouts.
Der [Wheel-Harness](../scripts/check_wheel.py) führt die Installationscases ohne
Checkout aus. [Die Anleitung](GUIDE_Benchmark-Contracts.md) beschreibt Installation,
Planung, Ausführung und Berichte. Die ursprüngliche Rotphase bleibt dokumentiert.

Dieser Stand führt ausschließlich den deterministischen Fake mit
vertrauenswürdigen lokalen Materialien aus. Prozessadapter und Containerisolation
für fremden Agentencode sind noch nicht enthalten; ein Fake-Erfolg ist kein
Agentenleistungsnachweis. Referenzen bleiben `author_checked` bis zur
unabhängigen menschlichen Aufnahmeprüfung.

### 10.3 Eigene Agenten und Szenarien

Die dritte Phase ist implementiert: Öffentliche Python-API und CLI unterstützen
JSONL-Prozesse mit echtem Fähigkeitenaustausch, Agenten- und Szenariovorlagen,
explizite Referenzvalidierung, Typ-/Tagfilter und den Vergleich archivierter
Läufe. Der Runner kontrolliert Artefakte und beobachtet Entwicklerphasen selbst;
Sitzungen bleiben innerhalb einer Episode erhalten und beginnen je Versuch neu.

[Das Tutorial](GUIDE_Benchmark-Custom.md) und das mit `init-example` exportierbare
Versandkostenpaket ermöglichen den Einstieg aus einem installierten Wheel.
Das Paket enthält zwei Review-Varianten, eine Entwicklungsepisode und einen
deterministischen JSONL-Peer. `cubie-bench guide` zeigt die installierte Anleitung.
Die [EBT-Cases und ihr Schnittstellenvertrag](../tests/BENCHMARK_CASES_10_3.md)
prüfen den gesamten Ablauf mit einem einzigen Agenten und ohne Produktvergleich.

Die lokale Ausführung setzt vertrauenswürdige Agenten und Evaluatoren voraus;
die Containerisolation aus Abschnitt 7.3 ist noch nicht implementiert.
Werkzeugbudgets erfassen Runner-Aufrufe, keine internen Werkzeuge eines
externen Dienstes. Der Review-Evaluator vergleicht strukturierte Referenzfelder
und ist kein allgemeiner semantischer Reviewer. Das Beispiel liefert keinen
Agentenleistungsnachweis; Referenzen bleiben `author_checked`.

### 10.4 Basisdatensatz und Pilot

`init_base_package` und `cubie-bench init-base` exportieren das installierte
Paket `base-v1`: 24 Reviews aus sechs Familien sowie drei Datei-Projekte und
eine Funktionskontrolle mit je drei separat auswählbaren Episoden. Alle Fälle
haben neue Implementierungen, sichtbare Aufträge, Referenzen und Herkunftsangaben.
Die zwölf Entwicklungsepisoden enthalten insgesamt 52 kuratierte Mutanten und
fachlich entsprechende Cubie-/pytest-Testvorlagen. Objektive Review-Referenzen
werden ebenfalls ausführbar geprüft; Wartbarkeitsurteile bleiben manuell.

Sets unterstützen einen archivierten Seed und eine ausbalancierte Reihenfolge
unter Beachtung expliziter Episodenvorgänger. `summarize_pilot` und
`cubie-bench summarize-pilot` prüfen archivierte Inhalte und trennen Qualität,
Prozess, Familiengewichtung, unabhängige Projektgruppen, Streuung, unbekannte
Kosten und offene Nachbewertungen. Kopierte Versuche oder inkompatible Aufgaben-,
Evaluator- und Agentenstände werden nicht unbemerkt zusammengezählt.
Optionale Modell-/Providerdeklarationen werden mit dem Live-Handshake abgeglichen
und archiviert; sie bleiben Angaben des Adapters, kein unabhängiger Beweis eines
Provideraufrufs.

Die [EBT-Abnahmecases und der Schnittstellenvertrag](../tests/BENCHMARK_CASES_10_4.md)
sowie [das Tutorial](GUIDE_Benchmark-Custom.md#basisdatensatz-und-pilot)
beschreiben den implementierten Umfang. Referenzlösungen werden in allen zwölf
Entwicklungsepisoden und beiden Bedingungen einschließlich Rot-/Grün-Prozess
geprüft. Die deterministischen Prozess- und Fake-Agenten liefern ausschließlich
Infrastrukturbelege. Referenzen bleiben `author_checked`; die unabhängige
menschliche Aufnahme und reale Pilotmessung stehen weiterhin aus. Die
Produktfunktionen sind implementiert, die methodische Pilotabnahme ist offen.

## 11. Methodische Bezugspunkte

Die folgenden Quellen stützen technische Umsetzungsmuster; Aufgaben, Kennzahlen und Entscheidungsregeln dieses Dokuments sind eigene Designvorschläge:

- Der [SWE-bench Evaluation Harness](https://www.swebench.com/SWE-bench/reference/harness/) beschreibt eine Trennung von vorbereiteten Umgebungen, eingereichten Patches und Testauswertung. Das ist ein Bezugspunkt für die reproduzierbare externe Prüfung; eine Abhängigkeit von SWE-bench ist nicht vorgesehen.
- pytest dokumentiert [eigene Marker und deren Registrierung](https://docs.pytest.org/en/stable/how-to/mark.html) sowie [Marker mit eigenen Kommandozeilenoptionen](https://docs.pytest.org/en/stable/example/markers.html). Darauf kann die bewusste Freischaltung echter Agentenläufe aufbauen.
- Cubies [Vertragssemantik](GUIDE_Contract-Semantics.md), [RBT-Nutzungsmuster](GUIDE_RBT-Usage-Pattern.md) und [Qualitätsbegriffe](GUIDE_Quality-Assurance.md) definieren den lokalen Produktumfang und die Grenzen der Aussagen.
