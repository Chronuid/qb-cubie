# EBT-Abnahmecases: Basisdatensatz und Pilot (Phase 10.4)

> Aktualisierung vom 11. November 2026: Menschliche Prüfungen je offiziellem
> Fall sind optional und kein Vollständigkeitskriterium. Offizielle Piloten
> erlauben `author_checked`; nur der beanspruchte Status `independently_checked`
> verlangt weiterhin zwei belegte unabhängige Zustimmungen. Frühere Aussagen
> zu einer verpflichtenden menschlichen Aufnahme unten sind historisch.
> Maßgeblich sind die [aktuellen Abschlusskriterien](../../docs/misc/OFFENE_PUNKTE_Benchmarks-Agenten.md).

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. **Produktfunktionen implementiert; Referenzen bleiben
`author_checked`. Unabhängige menschliche Aufnahme und reale Modellmessung sind offen.**

Die ursprünglich 55 Cases unter [benchmarks/phase4](../benchmarks/phase4) konkretisieren die
vierte Phase aus [Entwicklungsplan und Abnahme](../../docs/misc/BENCHMARK_KONZEPT.md#10-entwicklungsplan-und-abnahme).
Sie verwenden die vorhandenen EBT-Hüllen `accepted` und `rejected` mit
`WorldState` und gegebenenfalls `ExceptionExpectation`. Die Hüllen prüfen
`RunTrace.evaluation` und das Urteil der einzelnen Spur ausdrücklich.
Fehlende öffentliche Funktionen führen zu normalen Assertion-Fehlschlägen.
Es gibt keine `xfail`-Marker, Skips oder Modell-/Netzwerkaufrufe.

## Kriterienzuordnung

| Kriterium aus dem Konzept | Cases und Gegenproben |
| --- | --- |
| 24 Reviews aus sechs Familien mit je zwei konformen und zwei fehlerhaften Fällen (§4.1) | [test_base_dataset.py](../benchmarks/phase4/test_base_dataset.py): vollständiger Export, eindeutige IDs, genau eine primäre Familie je Review und korrekte Verteilung je Familie. Mindestens ein fehlerhafter Mehrdateienfall je Familie benennt vorhandene Kontextdateien und begründet die Kontextanforderung. |
| Drei unabhängige Datei-Projekte plus Funktionskontrolle mit jeweils drei Episoden (§5.1) | Vier Projektgruppen mit Erstentwicklung, Wartung und Diagnose. Die Kontrolle zählt nicht als Datei-Projekt. Primäre Episoden sind unabhängig auswählbar und besitzen Referenzen, Mutanten sowie Testvorlagen für beide Bedingungen. |
| Validierte Referenzen und Mutanten (§4.2, §5.3, §6.2) | Objektive Fälle müssen ausführbar geprüft sein; Wartbarkeitsurteile bleiben als manuell zu prüfen sichtbar. Beschädigte Lösung, überlebender Mutant und Importfehler im Evaluator verhindern die Validierung. |
| Zwei menschliche Aufnahmeprüfungen (§4.2) | [test_reference_admission.py](../benchmarks/phase4/test_reference_admission.py): zwei verschiedene belegte Zustimmungen. Ablehnung gleicher Identitäten, bloßer Strings, ungeklärter Einwände und fehlender oder aus dem Szenario hinausweisender Belege. Lokale Autorreferenzen bleiben zulässig. |
| Herkunft, Lizenz, Bekanntheit und unabhängige Entwürfe (§6) | Vollständiges `dataset.json` mit Herkunft, Lizenz, Domäne und Entwurfskennung. Öffentliche Fälle sind Entwicklungsfälle und potenziell bekannt. Projektvarianten teilen ihre Entwurfskennung; die vier Projekte haben verschiedene Kennungen. Alte Review-Quelldateien dürfen nicht unverändert als neue Fälle erscheinen. |
| Ein Agent genügt; pytest-Vergleich bleibt optional (§3.1) | [test_pilot_design.py](../benchmarks/phase4/test_pilot_design.py): zwei Kalibrierungs- und fünf Pilotwiederholungen mit einem Agenten, Standardprofil nur Cubie, Vergleichsprofil vollständig gepaart. Keine stille Kürzung bei überschrittenem Laufzahllimit. |
| Seed und ausbalancierte Laufreihenfolge (§3.2) | Derselbe Seed ergibt denselben vollständigen Plan; die zuerst ausgeführte Bedingung ist je Aufgabe über Wiederholungen ausbalanciert, bei fünf Wiederholungen mit Differenz höchstens eins. |
| Qualität, Prozess und Projektzahl getrennt (§5.2, §9) | [test_developer_pilot.py](../benchmarks/phase4/test_developer_pilot.py): fachlich korrekte Abgaben mit und ohne gültigen Prozess. Getrennte Gruppen nach Agent und Bedingung, mit Episodenzahlen und unabhängigen Projektgruppen. Kein Gesamtscore über Benchmarks. |
| Familiengewichtung und Streuung (§4.3, §9) | [test_pilot_summary.py](../benchmarks/phase4/test_pilot_summary.py): ungleich große Familien ergeben Macro-Recall 0,5 statt gepooltem Recall 0,25. Konforme Fälle erhalten keinen künstlichen Recall; undefinierte Präzision bleibt sichtbar. Manuelle Familien gehen nicht in objektive Macro-Metriken ein. Stichprobenstandardabweichung mit `n-1`; bei einer Beobachtung bleibt sie undefiniert. |
| Kosten und Aufwand (§3.2, §7.2) | Archivierte Laufzeiten; bekannte und unbekannte Kosten getrennt. Eine bekannte Teilsumme ersetzt keine vollständige Gesamtsumme. Fehlende Kosten sind niemals null. |
| Jeder begonnene Versuch bleibt sichtbar (§3.2) | Timeout, Budgetüberschreitung, ungültige Ausgabe und Infrastrukturfehler bleiben im Nenner begonnener Versuche und erhalten separate Statuszahlen. `not_started` bleibt geplant, zählt aber nicht als begonnen. |
| Bewertungsstreitfälle und nachprüfbare Läufe (§6.2, §7.2) | Offene Nachbewertungen erhalten keine Qualitätsgutschrift und behalten Lauf-ID, Szenario und Belege. Veränderte Ergebnisse/Pläne, fehlende Belege und doppelt eingereichte Archive werden abgelehnt. Die Auswertung verändert Archive nicht und akzeptiert verschobene Archive. |

## Öffentlicher Vertrag

Die folgenden Schnittstellen sind implementiert. Die erste Rotphase bleibt
unten dokumentiert. Der exportierte Datensatz ist öffentliches Entwicklungsmaterial;
eine unabhängige menschliche Aufnahme wird nicht behauptet.

### Basisdatensatz

```python
init_base_package(path) -> {"package": "/absolute/path"}
```

Das verschiebbare Paket hat den Namespace `base-v1` und genau 36 Szenarien.
`load_package`, `validate_package` und `init_suite` verwenden es anschließend
wie ein eigenes Paket. Vorhandene Inhalte werden nicht überschrieben.

Die primären Review-Familien stehen in `types`: `correctness`, `file_workflow`,
`state_lifecycle`, `error_handling`, `test_quality`, `maintainability`.
Weitere Typen bleiben möglich. Die Developer-Projektgruppen heißen
`billing-export`, `configuration-package`, `document-index`, `pure-calculation`.
Ihre Episoden tragen die Typen `initial_development`, `maintenance`, `diagnosis`.
Die primären Episoden haben `requires=[]`; fortlaufende Entwicklung bleibt eine
gesonderte Sekundärmessung.

`dataset.json` enthält `schema_version=1`, `publication_status="public"` und
`cases`, indiziert nach Szenario-ID. Jeder Eintrag hat nichtleere Angaben
`origin`, `license`, `design_id`, `domain` sowie `potentially_known=true` und
`assessment`. Letzteres ist bei Wartbarkeitsreviews `manual`, sonst `executable`.
Alle exportierten Fälle haben `split="development"`.

Mehrdateienreferenzen ergänzen `required_context` als Pfadliste relativ zu
`visible` und `context_reason` als Begründung. Die Existenz dieser Felder beweist
noch keine fachliche Mehrdateienabhängigkeit; das bleibt menschlich zu prüfen.

`validate_package(path, check_references=True)` soll objektive Reviews ebenso
wie Developer-Referenzen tatsächlich prüfen und je Szenario
`reference_check="executed"` sowie `reference_passed=True` liefern.
Manuelle Referenzen erhalten stattdessen `reference_check="manual_required"`
und `reference_passed=None`. Programmausführung ersetzt keine menschliche
Aufnahme: Der erste Export bleibt `author_checked` mit leerem `human_reviews`.

Zur strukturellen Aufnahme als `independently_checked` sind mindestens zwei
verschiedene `reviewer_id` mit `decision="approve"` und vorhandenen `evidence`
erforderlich. Belegpfade sind relativ zum Szenario und liegen außerhalb des
sichtbaren Agentenmaterials. Ein ungeklärter `dispute` verhindert die Aufnahme.
Die Testbelege sind ausdrücklich synthetisch. Die Software kann die tatsächliche
Identität oder Unabhängigkeit der Menschen nicht aus diesen Feldern beweisen.

### Pilotplanung und Auswertung

Sets nutzen weiterhin `plan_suite` und `run_suite`. Zusätzlich soll ihr
ganzzahliger `seed` im aufgelösten Plan erhalten bleiben und die ausbalancierte
Reihenfolge reproduzierbar bestimmen. Externe Antworten werden dadurch nicht
deterministisch.

```python
summarize_pilot([archive_path, ...]) -> dict
```

Die CLI unterstützt den Export mit `cubie-bench init-base PATH`. Der Aufruf zur
Pilotzusammenfassung lautet:

```text
cubie-bench summarize-pilot ARCHIVE --format json
```

Die Funktion liest ausschließlich Archive, prüft deren Bindung an Manifest und
Plan und verändert keine Dateien. Kopierte Versuche werden nicht doppelt gezählt.
Die Ausgabe enthält:

- `schema_version=1`, `measurement_kind`, `warnings`, `groups`,
  `pending_adjudications`;
- eine Gruppe je `benchmark × agent_id × condition` mit `scenario_count`,
  `independent_groups` (eindeutige Paketnamespace-/Projektgruppen),
  `repetitions`, `statuses`, `quality_pass_rate`;
- `counts`: `planned`, `started`, `completed`, `evaluated`, `pending`,
  `not_started`, `quality_passed`, `process_passed`. Bei Reviews ist die Anzahl
  erfüllter Developer-Prozesse null; dies ist keine Prozessbewertung des Reviews;
- bei Reviews `families` mit `assessment` und je Metrik `defined_count`, `mean`,
  `stddev`; `macro_metrics` enthält die gleichgewichteten Mittel der definierten
  objektiven Familienmittel. Fehlen definierte Werte, steht dort `None`;
- bei Developer-Läufen `episodes` mit getrennten Episodenzahlen;
- `usage.cost` mit `known_count`, `unknown_count`, `known_total`, `total`,
  `mean`, `stddev`. Mittelwert und Streuung beziehen sich auf bekannte Werte;
  `total` ist nur bei vollständigen Beobachtungen definiert;
- `usage.wall_time_seconds` mit Anzahl bekannter/unbekannter Beobachtungen,
  Mittelwert und Stichprobenstandardabweichung aus den Zeitstempeln;
- offene Nachbewertungen mit `archive`, `run_id`, `scenario_id`, `evidence`.

`evaluated` zählt ausschließlich abgeschlossene Bewertungen. Offene oder
abgebrochene Versuche erhöhen `quality_passed` nicht. Der Nenner der deskriptiven
Erfolgsquote ist `started`; Infrastrukturfehler werden zusätzlich ausgewiesen.
Die Quote beschreibt diese Versuche, nicht ausschließlich die Agentenfähigkeit.
Ein Retry darf seinen Erstversuch nicht überschreiben; eine automatische
Retry-Policy ist durch diese Cases noch nicht spezifiziert.

Ein externer Prozess ohne Modellnachweis bleibt
`measurement_kind="infrastructure_only"` und erhält eine Warnung. Ein
Prozess-Handshake allein belegt keine Modellnutzung.

## Belegmaterial und Grenzen

Die [Pilot-Fixture](../benchmarks/phase4/conftest.py) erweitert das bestehende externe
Versandkostenpaket ausschließlich im temporären Verzeichnis. Der echte Runner
startet einen deterministischen JSONL-Peer und archiviert zehn Reviews: fünf
Szenarien aus zwei Projektgruppen mit je zwei Wiederholungen. Die größere Familie
enthält absichtlich übersehene, die kleinere erkannte Befunde. Die Varianten
beanspruchen keine zusätzlichen unabhängigen Projekte. Der Peer meldet festgelegte
Kosten als Testdaten; die Cases prüfen keine tatsächlichen Providerpreise.

Ein zweites echtes Runnerarchiv enthält acht Developer-Versuche mit zwei
Fake-Agenten, zwei Bedingungen und zwei Wiederholungen. Beide Agenten liefern
fachlich korrekte Lösungen; nur einer erfüllt den beobachteten Rot-/Grün-Prozess.
Zwei Kontrollcases prüfen die unmodifizierten Archive über die vorhandene
öffentliche Vergleichsfunktion sowie ihre Befunde und Prozessurteile.

Unterbrechungen und offene Bewertungen werden anschließend als ausdrücklich
simulierte Archivzustände erzeugt und neu gehasht. Diese Gegenproben testen die
Auswertung, keine tatsächlich beobachteten Ausfälle oder menschlichen Streitfälle.
Der Wartbarkeitsfall prüft separat, dass ein numerischer Matcherwert allein keine
Aufnahme in objektive Macro-Metriken rechtfertigt.

Die Cases ersetzen die menschliche Prüfung der 36 Aufgabenmaterialien nicht.
Verschiedene Entwurfskennungen und Hashes sind
Strukturkontrollen, kein Beweis unabhängiger Entwürfe. Auffällige konforme Fälle,
fachliche Mehrdateienabhängigkeit und gleichwertige Cubie-/pytest-Tests bleiben
Teil der Aufnahmeprüfung. Reale Agentenläufe, Nachbewertung neuer plausibler Findings,
Retry-Regeln und zurückgehaltene Aufgaben bleiben Folgearbeit. Die optionale
Archivierung deklarierter Modell-/Providerdaten ist inzwischen implementiert;
die methodische Pilotabnahme steht weiter aus.

## Erste Ausführung

```bash
.venv/bin/python -m pytest tests/benchmarks/phase4 -q --tb=short
```

Am 10. November 2026: **9 bestanden, 46 fehlgeschlagen**, keine Sammlungs- oder
Setupfehler. Die Fehlschläge verteilen sich auf:

- 18 Cases: fehlender Basisdatensatzexport `init_base_package`;
- 20 Cases: fehlende Pilotzusammenfassung `summarize_pilot`;
- 2 Cases: fehlende Seedsicherung und Ausbalancierung der Bedingungen;
- 6 Cases: unzureichende Validierung menschlicher Aufnahmeprüfungen.

Die neun bestandenen Gegenproben bestätigen gültige Referenzstrukturen, lokale
Autorreferenzen, echte Runnerarchive, Wiederholungen, optionale Bedingungen und
harte Laufzahlgrenzen. Produktcode wurde für diese Rotphase nicht verändert.

Die bisherigen Benchmark- und Styleguide-Prüfungen bleiben unverändert grün:

```bash
.venv/bin/python -m pytest tests/benchmarks tests/test_styleguide.py --ignore=tests/benchmarks/phase4 -q
```

Ergebnis: **390 bestanden, ein bestehender Skip** (ausgesetzte Modulgrößenregel).
Ruff für die neuen Python-Dateien und `git diff --check` sind ohne Befund.
Für diese erste Testergänzung wurde kein vollständiger Repository- oder
Wheel-Regressionslauf ausgeführt. Die Prüfung nach Produktumsetzung folgt unten.

## Produktumsetzung und ergänzende Gegenproben

Die ursprünglichen Anforderungen sind im Produktcode implementiert. Beim
Offenstellen einer Bewertung wählt die Gegenprobe jetzt ausdrücklich einen
erfolgreichen Versuch aus: Der lexikografisch erste Versuch hatte bereits ein
negatives Qualitätsurteil. Die weiterhin geforderte Abnahme einer sinkenden
Erfolgszahl wurde durch diese Fixture-Korrektur nicht abgeschwächt.

Der mitgelieferte Basisdatensatz liegt unter
[`src/qb_cubie/benchmarks/data/base`](../../src/qb_cubie/benchmarks/data/base).
Er enthält alle 36 Aufgabenmaterialien, 20 ausführbare objektive Review-Referenzen,
vier manuelle Wartbarkeitsreferenzen und zwölf Projektabnahmen mit insgesamt
52 Mutanten. Die Abnahmen verwenden konkrete, von der Implementierung unabhängige
Ausgaben und mehrere Datensätze einschließlich Leerfällen, Binärdaten und
Centbeträgen jenseits der Float-Präzision. Die Startstände sind importierbare
Stubs, frühere Referenzstände oder gezielt fehlerhafte Diagnosevarianten.
Die Abrechnungsabnahme enthält zusätzlich mehrzeilige zitierte CSV-Felder und
50-stellige Beträge mit Rundungsgrenze. Die Referenz liest CSV mit `StringIO`
und setzt die Decimal-Präzision entsprechend der Eingabelänge. Das
Konfigurationspaket benennt die Unicode-Escapierung seiner JSON-Ausgabe im
sichtbaren Auftrag ausdrücklich.

Die sieben zusätzlichen Cases in
[test_base_execution.py](../benchmarks/phase4/test_base_execution.py) prüfen alle
zwölf Projektepisoden in beiden Bedingungen, einschließlich fachlichem Rot,
eingefrorenen Tests und anschließendem Grün. Hinzu kommen ein falsch deklariertes
Review-Referenzurteil, ein Laufzeitfehler statt eines fachlichen Gegenbeispiels
und die Bindung des Herkunftskatalogs an die Paketidentität.

Drei Cases in [test_model_provenance.py](../benchmarks/phase4/test_model_provenance.py)
prüfen vollständige Modellangaben, abweichende Live-Deklarationen und unvollständige
Konfigurationen. Sie verwenden ausschließlich einen synthetischen Offline-Peer.
Der Runner bindet optionale `[model]`-Angaben an den Handshake und archiviert
Modellkennung, Revision, Provider-/Adapterversion, Parameter und Prompt-Hash.
Die Zusammenfassung kennzeichnet diese Angaben ausdrücklich als Adapterdeklaration;
sie kann daraus keinen tatsächlich erfolgten Provideraufruf beweisen.

Drei weitere [Integritätsfälle](../benchmarks/phase4/test_pilot_integrity.py) verhindern
die gemeinsame Auswertung verschiedener Evaluatorversionen unter derselben
Aufgabenkennung, unbelegte Belegverweise und erfundene Quell-/Kontexthashes.
Vergleich und Pilotzusammenfassung verwenden dieselbe Archivprüfung. Diese prüft
auch die Eingabedateien, den Suite-Hash und die tatsächlichen archivierten Quellen.
Die reine Zusammenfassung startet keinen Szenariocode.

Damit umfasst Phase 10.4 **68 Repository-Cases und drei Wheel-Cases**.
[Die Wheel-Cases](../wheel/benchmark_base_installed.py) prüfen Export und Verschieben,
Referenzvalidierung sowie einen gepaarten wiederholten Lauf mit Pilotzusammenfassung
und gehashtem Herkunftskatalog. Der Wheel-Harness führt sie außerhalb des Checkouts
mit dem installierten Paket und der installierten CLI aus.

Die Seed-Reihenfolge verändert die bisherige Ordnung nur bei ausdrücklich
gesetztem Seed. Projektabhängigkeiten bleiben erhalten. Die Pilotzusammenfassung
verweigert stille Mischungen verschiedener Szenario-/Evaluatorstände oder
Agentenkonfigurationen unter denselben Kennungen; neue Agentenversionen erhalten
unterschiedliche IDs. Kein Best-of-n und kein Gesamtscore werden eingeführt.

Die [installierte Anleitung](../../docs/GUIDE_Benchmark-Custom.md#basisdatensatz-und-pilot)
beschreibt Export, Planung, Ausführung, Auswertung und Modelldeklaration.
Der lokale Runner bleibt eine Umgebung für vertrauenswürdige Agenten und
Evaluatoren. Containerisolation, harte Token-/Kostenlimits, semantisches
Review-Matching und eine interaktive Nachbewertungsverwaltung bleiben außerhalb
dieses Umfangs. Alle menschlichen Referenzaufnahmen und tatsächlichen
Modellleistungsnachweise stehen weiterhin aus.

## Prüfung nach Implementierung

Der abschließende gezielte Lauf gegen den fertigen Produktcode umfasst alle
Benchmark-Cases, den Styleguide und Ruff/Mypy/Pylint:

```bash
.venv/bin/python -m pytest tests/benchmarks tests/test_styleguide.py tests/test_lint.py -q
```

Ergebnis: **467 bestanden, ein bestehender Skip** (ausgesetzte Modulgrößenregel).
Enthalten sind alle **445 Benchmark-Cases**, darunter sämtliche **68 Cases aus
Phase 10.4**. Die ursprünglichen fachlichen und methodischen Anforderungen
wurden nicht abgeschwächt. Ruff für den Produktcode und alle neuen Python-Dateien
sowie `git diff --check` sind ohne Befund.

`uv build --offline` erzeugt Source-Archiv und Wheel. Der vollständige
`scripts/check_wheel.py`-Lauf gegen das abschließende Wheel besteht:

| Installiertes Profil | Bestanden |
| --- | ---: |
| Core | 22 |
| Linters | 22 |
| Bisheriger Benchmark-Durchstich | 8 |
| Eigene Agenten und Szenarien | 5 |
| Basisdatensatz und Pilot | 3 |

Alle **60 Wheel-Prüfungen** bestehen außerhalb des Checkouts. Der dokumentierte
Wheel-Hash stammt aus dem installierten Artefakt; die neuen Prüfungen vergleichen
ihn mit dem tatsächlich installierten Wheel. Das Wheel enthält die vollständigen
Basisressourcen und die erweiterte Anleitung.

Der parallel gestartete vollständige Repositorylauf ergab **1766 bestanden,
einen Styleguide-Fehlschlag, zwölf bestehende Skips und sechs bestehende Warnungen**
in 459,24 Sekunden. Er hatte vor dem abschließenden Aufteilen der Archivprüfung
begonnen und beanstandete deren damalige Funktion mit 13 statt höchstens zwölf
Codezeilen. Dieser Verstoß ist behoben; der abschließende Lauf mit 467 bestandenen
Tests enthält die bestandene Größenprüfung. Die später ergänzten drei
Integritätsfälle sind ebenfalls in diesem abschließenden Lauf enthalten.
Weitere Fehlschläge traten im vollständigen Repositorylauf nicht auf.

Nach den abschließenden CSV-Randdaten und der präzisierten JSON-Ausgabevorgabe
wurden sämtliche Phase-10.4-Cases einschließlich Styleguide und aller drei
Quellcode-Linter erneut ausgeführt: **90 bestanden, ein bestehender Skip**.
Das danach neu gebaute Wheel besteht erneut alle **60 Wheel-Prüfungen**.
