# EBT-Abnahmecases: Kalibrierung und Pilot (§5, Schritt 5)

> Aktualisierung vom 11. November 2026: Menschliche Prüfungen je offiziellem
> Fall sind optional und kein Vollständigkeitskriterium. Offizielle Piloten
> erlauben `author_checked`; nur der beanspruchte Status `independently_checked`
> verlangt weiterhin zwei belegte unabhängige Zustimmungen. Frühere Aussagen
> zu einer verpflichtenden menschlichen Aufnahme unten sind historisch.
> Maßgeblich sind die [aktuellen Abschlusskriterien](../../docs/GUIDE_Benchmarks.md#noch-benötigte-praktische-nachweise).

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. **Pilotfreigabe implementiert und offline geprüft;
explorative Modellmessung separat dokumentiert.** Die [65 ursprünglichen Cases](../ollama_agents/pilot) konkretisieren die Pilotfreigabe der
[Rollen- und Ablaufbeschreibung](../../experiments/ollama-agents/README.md).
Die ursprüngliche Testentwurfsphase und ihre Rotphase bleiben unten dokumentiert.
Die anschließende Umsetzung ergänzt Produktcode und Messablauf; Rollenprompts
bleiben unverändert. Offizielle menschliche Referenzen wurden nicht aufgenommen.

## Kriterienmatrix

| Kriterium | Ausführbarer Nachweis |
| --- | --- |
| Zwei Kalibrierungs-, anschließend fünf Messwiederholungen pro Aufgabe, Agent und Bedingung | `test_design.py` plant Reviewer und Developer im Standardprofil sowie im optionalen Cubie-/pytest-Vergleich. Jede Zelle enthält genau die Wiederholungen 1–2 beziehungsweise 1–5. `test_calibration_gate.py` verlangt die passende Kalibrierung vor der Pilotfreigabe und weist andere Wiederholungszahlen zurück. |
| Dasselbe ausgewählte Set | Nicht kalibrierte Bedingungen oder Szenarien sowie veränderte Quellen, Aufträge und Paketversionen verhindern die Freigabe. Eine neue Aufgabe benötigt eine neue Kalibrierung. |
| Kalibrierung darf Parameter verändern | `test_tuning_budget_after_calibration_is_allowed_until_freeze` ändert das Laufzeitbudget vor dem Einfrieren. Die Kalibrierungsbelege bleiben dabei im Originalzustand erhalten. |
| Parameter vor dem Messstart eingefroren | `test_freeze_binds_calibration_and_admissions_before_measurement_starts` verlangt eine gehashte Bindung der Kalibrierungsarchive an das portable Messpaket und einen UTC-Zeitpunkt zwischen Kalibrierungsende und Pilotstart. Änderungen an Budget, Seed, Agent, Quelle, Referenz, Aufnahmebeleg oder Kalibrierungsarchiv verhindern den Messstart. |
| Modellidentität, Prompt und interne Grenzen gehören zur Konfiguration | Acht Gegenproben in `test_existing_infrastructure.py` prüfen unterschiedliche Messidentitäten bei geändertem Digest, Prompt-Hash, Temperatur, Modellseed, Kontextgröße, Ausgabelimit, `think` oder interner Modellaufrufgrenze. Der echte Freeze archiviert die vollständige synthetische Modellkonfiguration und startet den Prozess dabei nicht. |
| Alle begonnenen Versuche enthalten | Reale Runnerläufe erzeugen Timeouts, Infrastrukturfehler und ungültige Ausgaben. Auch erfolglose Kalibrierungen bleiben vollständig im eingefrorenen Belegpaket. Zusätzliche Kalibrierungsrunden, doppelte oder kopierte Archive, fehlende Versuche und beschädigte Belege verhindern eine stille Auswahl. Nicht gestartete Zellen erfüllen die Kalibrierungszahl nicht. |
| Kein Best-of-n und kein Vermischen von Kalibrierung und Messung | Die Pilotstatistik enthält ausschließlich die fünf eingefrorenen Messwiederholungen. Zehn fehlgeschlagene Reviewer-Versuche bleiben zehn gestartete Versuche im Nenner. Ein veröffentlichtes Messpaket darf nicht überschrieben werden. Zusätzliche Kalibrierungsrunden erfordern eine explizit geänderte Studie; die Freigabe dieses Zwei-/Fünf-Protokolls verweigert sie. |
| Offizielle Referenzen unabhängig aufgenommen | Jede ausgewählte Referenz benötigt `independently_checked` und zwei verschiedene, zustimmende Prüferkennungen mit privaten Belegdateien. Autorreferenz, doppelte Identität, Widerspruch und fehlende oder sichtbare Belege verhindern die Freigabe. Nicht ausgewählte Fälle dürfen gültige Autorreferenzen behalten. |
| Kalibrierungsnachweise bleiben historisch korrekt | Die Kalibrierung verwendet `author_checked`. Später ergänzte Aufnahmebelege ändern die alten Archive nicht. Der Pilot bindet den neuen Referenzstand einschließlich Aufnahmebelegen. |
| Frische Workspaces und private Evaluatorbelege | Tatsächliche eingefrorene Runnerläufe nach Verschieben des Messpakets und Löschen der ursprünglichen Eingaben. Jede Messung erhält einen eigenen Workspace. Referenzen und Aufnahmebelege erscheinen nicht im sichtbaren Quellenexport. |
| Wiederholungen sind keine unabhängigen Projekte | Pro Bedingung zehn Reviews: zwei Varianten desselben Projekts mit je fünf Wiederholungen. Die Zusammenfassung meldet ein unabhängiges Projekt und zwei Szenarien. Kosten bleiben unbekannt; Offline-Fakes bleiben `infrastructure_only`. |

## Implementierter Schnittstellenvertrag

Die Funktion gehört zum Agentenbeispiel und ist **keine neue öffentliche
Cubie-API**. Der Einstieg wird erst im Testkörper aufgelöst:

```python
# examples/ollama-agents/pilot.py
freeze_pilot(
    calibration_archives=[Path("calibration/results/<archive-id>")],
    suite_path=Path("sets/pilot.toml"),
    destination=Path("frozen-pilot"),
)
# -> {"schema_version": 1, "path": "<absolute destination>",
#     "measurement_sha256": "<SHA-256 of measurement.json>"}
```

Die Funktion prüft die übergebenen Archive mit der vorhandenen Archivvalidierung,
gleicht die Kalibrierungszellen mit dem gewählten Pilotset ab und verlangt die
unabhängige Referenzaufnahme für alle ausgewählten Szenarien. Fehlgeschlagene,
aber tatsächlich gestartete Kalibrierungsversuche zählen; ein erfolgreiches
Qualitätsurteil ist keine Voraussetzung zum Einfrieren. Die Funktion startet
weder Agenten noch Inferenz und schreibt bei Ablehnung kein Zielverzeichnis.

Das Ergebnis erweitert das vorhandene portable `freeze_suite`-Messformat.
`measurement.json` bindet weiterhin Plan, Eingaben, Dateihashes und Laufzeit.
Zusätzlich enthält es:

```json
{
  "pilot": {
    "calibration_repetitions": 2,
    "measurement_repetitions": 5,
    "reference_admission": "independently_checked",
    "frozen_at": "<ISO-8601 timestamp with UTC offset>",
    "calibration_archives": [
      {"path": "inputs/calibration/0", "manifest_sha256": "<SHA-256>"}
    ]
  }
}
```

Die Archive werden vollständig unter relativen Pfaden mitkopiert; ihre Dateien
und Aufnahmebelege gehören zum gehashten Messpaket. Die Tests schreiben den
konkreten Archiv-Unterpfad nicht vor. Der bestehende `run_frozen_suite` führt
das Paket aus, `read_archive` prüft die Ergebnisbindung und `summarize_pilot`
wertet ausschließlich das neue Ergebnisarchiv aus. Ein weiteres Laufprotokoll,
eine zusätzliche Phasensteuerung oder ein neuer Evaluator sind nicht nötig.

## Testdaten, Unabhängigkeit und Grenzen

Alle Tests stehen unter der vorhandenen automatischen Netzsperre für
`../ollama_agents`. Sie verwenden echte EBT-Ausführungen mit Prüfung von
`evaluation` sowohl am Ergebnis als auch am einzelnen Trace. Erwartete
Ablehnungen durchlaufen `ExceptionExpectation(ValueError, ...)`; fehlender
Produktcode scheitert an einer ausdrücklichen Assertion im Testkörper, ohne
Sammlungsfehler, Setupfehler, `skip` oder `xfail`.

Die öffentlichen Smoke-Aufgaben dienen ausschließlich als Entwicklungsdaten.
Der eingebaute Fake liefert deterministische Eingaben; Planung, Dateisystem,
Archivierung, Hashprüfung, Auswertung und eingefrorene Ausführung sind real.
Die Modellkonfiguration ist ausdrücklich synthetisch. Ihr Prozess würde bei
einem versehentlichen Start sofort fehlschlagen. Damit prüfen die Cases den
Messablauf, nicht Modellleistung oder die Eignung des öffentlichen Smoke-Sets
als unverbrauchter Pilotdatensatz.

Aufnahmebelege sind ausdrücklich mit `SYNTHETIC TEST RECEIPT` gekennzeichnet.
Sie belegen nur die strukturelle Prüfung des Freigabevertrags. Sie ersetzen
keine zwei menschlichen Prüfungen, keinen unabhängigen fachlichen Goldstandard
und keine blinde semantische Finding-Nachbewertung. Letztere bleibt gemäß §3.3
des Agentenkonzepts separat erforderlich; ein exakter Finding-Abgleich wird
durch diese Cases nicht zu einer semantischen Leistungsbewertung.

Vollständigkeit wird für die **angegebenen** Kalibrierungsarchive und den
eingefrorenen Runnerplan geprüft. Nicht deklarierte Läufe außerhalb dieser
Archive lassen sich daraus nicht entdecken. Ein Prozessabbruch vor dem
Versiegeln eines Runnerarchivs benötigt gesonderte Wiederherstellungsregeln;
ein solches Fragment darf keine vollständige Kalibrierung vortäuschen.
Eine automatische Retry-Policy und adaptive Wahl der besten Wiederholung
sind nicht Bestandteil dieses Vertrags.

Echte lokale Messungen, Hardware-/GPU-Belegung, Laden und Vorwärmen,
Provider-Rohbelege, dauerhafte Aufbewahrung, unabhängige menschliche Aufnahme
und der abschließende Pilotbericht bleiben anschließende Arbeit. Die bisherigen
Rollen- und Wheel-Cases aus §5.1–5.4 gelten weiterhin. Der Offline-Erfolg
dieser Cases allein kann §5.5 nicht abschließen.

## Ursprüngliche Ausführung und Rotphase

```bash
.venv/bin/python -m pytest tests/ollama_agents/pilot --collect-only -q
.venv/bin/python -m pytest tests/ollama_agents/pilot -q --tb=short \
  --junitxml=/tmp/cubie-agent-5-5-red.xml
.venv/bin/python -m pytest tests/ollama_agents --ignore=tests/ollama_agents/pilot -q
.venv/bin/python -m ruff check tests/ollama_agents/pilot
git diff --check
```

Die erste Testergänzung umfasst **65 Cases: 22 bestanden und 43 gezielt rot**
am fehlenden `examples/ollama-agents/pilot.py`. Es gibt keine Sammlungs-/Setupfehler
und keine Skips. Die 22 grünen Gegenproben prüfen die tatsächlichen Grundlagen
des neuen Vertrags unabhängig vom fehlenden Einstieg.

Alle **253 bisherigen Offline-Agentencases** bestehen unverändert. Ruff und
`git diff --check` bestehen. Der JUnit-Bericht der Rotphase liegt temporär unter
`/tmp/cubie-agent-5-5-red.xml`. Ein vollständiger Repository-, Wheel- oder
Live-Modelllauf gehört nicht zu dieser Testentwurfsphase.

## Produktumsetzung und zusätzliche Gegenproben

Die ursprünglichen **65 Cases bestehen**. Die Implementierung liegt unter
[`examples/ollama-agents/ollama_agents/pilot`](../../examples/ollama-agents/ollama_agents/pilot).
Der Checkout-Einstieg `examples/ollama-agents/pilot.py` und der installierte
Aufruf `python -m ollama_agents.pilot` verwenden dieselbe Funktion.

`freeze.py` veröffentlicht das Messpaket erst nach Prüfung der temporären Kopie.
`validation.py` gleicht Aufgaben, Paketversionen, Bedingungen, Wiederholungen,
Quellenbytes und Dateimodi, Referenzurteile und private Abnahmetests ab. Nur
Aufnahmebelege und ihre Metadaten sowie explizite Budgetanpassungen dürfen sich
zwischen Kalibrierung und Einfrieren ändern. Alle kopierten Archive werden erneut
mit dem tatsächlichen Runner-Archivprüfer geprüft. Zeitpunkt und Hashbelege
beziehen sich auf den veröffentlichten Snapshot.

Die offizielle Variante bleibt der Standard und verlangt unabhängige Aufnahme.
Die zusätzliche Option `exploratory=True` beziehungsweise `--exploratory` schreibt
`study_kind=exploratory` und `reference_admission=author_checked` in das Manifest.
Sie verändert weder Referenzstatus noch Prüfbelege. Ihr Nachweis darf daher
keine offizielle Aufnahme behaupten.

Zwölf weitere Cases in
[`test_implementation_boundaries.py`](../ollama_agents/pilot/test_implementation_boundaries.py)
prüfen explizite Exploration, unveränderte Autorreferenzen, geänderte private
Abnahmen und Referenzentscheidungen, zukünftige/umgekehrte/zeitzonenlose
Zeitstempel, die JSON-CLI, verweigerten Modellzugriff ohne Opt-in, offizielle
Kennzeichnung sowie unbekannte Statuswerte und veränderte Dateirechte.
Damit umfasst §5.5 **77 Offline-Cases**, zusammen mit den bisherigen Fällen
**330 Agentencases**.

Zwei ursprüngliche Gegenproben wurden bei der Umsetzung in ihrer Testvorbereitung
korrigiert: Der vorhandene TOML-Serializer schreibt Schlüsselnamen in
Anführungszeichen. Budget und Seed werden jetzt geparst, ihre ursprünglichen
Werte geprüft und die geänderten Werte serialisiert. Beide Cases verlangen
weiterhin unverändert die Zurückweisung vor Messstart. Die Kriterien wurden
nicht abgeschwächt.

Der installierte Ablauf `python -m ollama_agents.pilot.live ZIEL --exploratory`
führt das öffentliche Set seriell aus: zwei separat archivierte unbewertete
Vorprüfungen, vier Reviewer- und zwei Developer-Kalibrierungen, danach zehn
Reviewer- und fünf Developer-Messungen. Beide Kalibrierungen werden vor dem
Einfrieren beider Pilotsets abgeschlossen. `study.json` wird vor jedem Stapel
geschrieben. Fehlerstatus, fehlende Belege und Abbruchfragmente bleiben sichtbar;
es gibt keine automatische Wiederholung gescheiterter Episoden.

Der Ollama-Export deklariert seine Modulbibliothek jetzt als `adapter_files`.
Dadurch werden Rollenprozesse, Prompts, Werkzeuge und Pilothelfer beim Einfrieren
vollständig mitgenommen. Die Belegziele des Live-Ablaufs zeigen ausdrücklich auf
dauerhafte Verzeichnisse außerhalb der temporären Ausführungskopien.
`observations.py` prüft die Bindung der externen Manifeste über archiviertes
stderr und hasht deren Einzelschritte nach. Digest und Provider-Version werden
an Stapelgrenzen erneut geprüft; GPU- und Ladezustand werden dort festgehalten.

Ein zusätzlicher installierter Wheel-Case durchläuft mit lokalem HTTP-Replay
den vollständigen Zwei-/Fünf-Ablauf einschließlich aller **21 Episoden** und
zweier Vorprüfungen. Planung, Rollenprozesse, EBT/pytest, unabhängige Auswertung,
Rohantwortarchive und Hashprüfungen sind real; ausschließlich Ollama wird
ersetzt. Das ist ein Infrastrukturbeleg. Die tatsächliche lokale Modellmessung
steht getrennt unter [Messung und Ergebnisgrenzen](../../experiments/ollama-agents/README.md#explorative-messung-vom-10-november-2026).

## Abschließende Prüfung und echte Messreihe

Der abschließende Lauf gegen den fertigen Stand:

```bash
.venv/bin/python -m pytest tests/ollama_agents tests/benchmarks \
  tests/test_styleguide.py tests/test_lint.py -q --tb=short
```

Ergebnis: **893 bestanden, 3 bestehende Skips**. Darin sind alle **330
Agentencases** einschließlich der **77 §5.5-Cases** und alle **541 bestandenen
Benchmark-Cases** enthalten. Ruff, MyPy für die Beispielbibliothek sowie
`git diff --check` bestehen. Die bestehenden Größen-/Docstring- und
Importauflösungsprobleme im Export und den betroffenen CLI-Funktionen wurden
durch Aufteilen der Verantwortlichkeiten und dynamisches Laden der installierten
Rollenmodule behoben.

Der aus der Quelldistribution gebaute abschließende Wheel-Stand besteht
**68 installierte Cases** außerhalb des Checkouts: 22 Kern-, 22 Linter-,
8 Benchmark-, 5 Erweiterungs-, 3 Basisdatensatz-, 4 Messpaket- und 4
Ollama-Agenten-Cases. Letztere enthalten den vollständigen Zwei-/Fünf-Ablauf.
Wheel-SHA-256:
`caab3d7de8d6b98331ce6fc7ff6acb6c15f8db695f8b98207ceb9169f3d959b9`.

Die tatsächliche explorative Modellmessung enthält **21 Episoden**: 6
Kalibrierungen und 15 Pilotmessungen. Alle sind `completed`; die fünf
Developer-Pilotepisoden bestehen Fach- und Prozessabnahme. Alle zehn
Reviewer-Pilotkriterien entsprechen der Autorreferenz; fünf fehlerhafte
Stände bestehen den exakten Finding-Abgleich nicht. Diese bekannte Grenze
wird getrennt berichtet und nicht als semantisches Fehlurteil ausgegeben.
Es wurden keine Versuche ersetzt oder ausgeschlossen. Die detaillierten
Zeiten, Tokens, Konfigurationen und Grenzen stehen unter
[Messung und Ergebnisgrenzen](../../experiments/ollama-agents/README.md#explorative-messung-vom-10-november-2026).

Gemeinsames dauerhaftes Belegarchiv:
`/home/symphonie/.local/share/cubie/agent-5-5-evidence-20261110.tar.gz`,
SHA-256
`4028ab93d49d83b1c64f4afffa6242816ccc5c5b8a165d84cb1882d76cb19036`.
Es enthält Rohdaten, alle Runner- und Adapterarchive, Provider-/Hardwarebeobachtungen,
getrennte Zusammenfassungen, Modellkonfigurationen, das gemessene und das
abschließende Wheel mit zugehörigen Quelldistributionen sowie Prüflogs und
die erfassten Laufzeitabhängigkeiten. Beide Wheels unterscheiden sich in der
abschließenden Härtung und Exportaufteilung; die Reviewer- und Developer-Module
wurden zusätzlich byteweise verglichen und sind identisch.

Produktimplementierung und explorative reale Messung sind damit nachgewiesen.
Die **offizielle methodische §5.5-Abnahme bleibt offen**, bis menschliche
Referenzaufnahme und blinde semantische Nachbewertung tatsächlich vorliegen.
