# Anforderungen: automatisierter SWE-bench-Datensatzimport

Stand: 11. November 2026. **Produktimplementierung für Import, Referenzprüfung
und Developer-Agent-Reparaturepisoden vorhanden; reale Download-/Container-
Integrationsnachweise stehen noch aus.** Nutzung und Laufzeitvoraussetzungen:
[SWE-bench-Leitfaden](../GUIDE_Benchmark-SWEbench.md).
Dies konkretisiert den Datensatzausbau aus dem
[Benchmark-Konzept §6](BENCHMARK_KONZEPT.md#6-referenzen-datensatz-und-kontamination)
und den [offenen Punkten](OFFENE_PUNKTE_Benchmarks-Agenten.md).
Die [Abnahmematrix](../../tests/docs_tmp/BENCHMARK_CASES_SWE_BENCH.md) ordnet
Anforderungen den ausführbaren Cases zu.

## Ziel und fachlicher Umfang

Ein Loader soll ausgewählte reale Reparaturaufgaben ohne manuelles Kopieren
aus SWE-bench beziehen, ihren Ausgangsstand reproduzierbar bereitstellen und
verschiebbare Cubie-Szenariopakete erzeugen. Das bestehende `base-v1` bleibt
ein eigener Datensatz. Import, Referenzprüfung und Agentenmessung sind getrennte
Operationen mit getrennten Nachweisen.

Die erste Ausbaustufe unterstützt die Python-Aufgaben der offiziellen Quellen
`SWE-bench/SWE-bench`, `SWE-bench/SWE-bench_Lite` und
`SWE-bench/SWE-bench_Verified`. Multimodal-, Multilingual-, Retrieval- und
Drittanbieterderivate benötigen eigene Adapter und werden zunächst abgelehnt.
Lite ist ein geeigneter technischer Einstieg; eine konkrete Stichprobe wird
vor einer Messung begründet und eingefroren. Fallzahlen werden aus der gepinnten
Quelle gelesen und nicht im Loader fest verdrahtet.

Aus einem Datensatzfall entsteht genau eine unabhängige Reparaturepisode mit
`benchmark="developer_agent"`, `process_profile="issue_resolution"` und
`requires=[]`. Der Ausgangsstand ist ein defektes Projekt, kein künstlicher
Entwicklungsstub. Importierte Aufgaben liefern weder Review-Findings noch einen
beobachteten TDD-Prozess. Review-Szenarien benötigen gesonderte Kriterien und
Referenzen; sie werden nicht automatisch aus dem Gold-Patch abgeleitet.

## Quellenbasis und daraus abgeleitete Entscheidungen

Die offiziellen Datensatzkarten beschreiben unter anderem Issue-Text,
Ausgangscommit sowie getrennte Lösungs- und Test-Patches. Diese Daten lassen
sich für Cubie als Auftrag, Projektstart und private Abnahme abbilden.
Quellen: [Full-Datensatzkarte](https://huggingface.co/datasets/SWE-bench/SWE-bench/blob/main/README.md),
[Lite-Datensatzkarte](https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite/blob/main/README.md),
[Verified-Datensatzkarte](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/blob/main/README.md).

Der offizielle Harness verwendet Container und unterstützt Gold-Patch-Prüfungen.
Sein dokumentierter Ergebniscache berücksichtigt `run_id` und `instance_id`,
jedoch keinen geänderten Patchinhalt. Deshalb verlangt dieser Entwurf neue
Versuchskennungen und eine zusätzliche Inhaltsbindung.
Quelle: [Harness-Referenz](https://www.swebench.com/SWE-bench/reference/harness/).

Alle folgenden Muss-Regeln sind Cubie-Designentscheidungen. Der Loader darf
Upstream-Metadaten weder als eigenen Prüfbeleg noch als Nachweis unverbrauchter
Aufgaben behandeln. Schemaabweichungen zwischen Revisionen müssen sichtbar bleiben.

## Öffentliche Schnittstellen

Die Funktionen werden aus `qb_cubie.benchmarks` exportiert:

```python
plan_swebench_import(config: dict, *, source=None) -> dict
import_swebench(config: dict, destination, *, source=None) -> dict
validate_swebench_references(package, *, executor=None) -> dict
```

`source` und `executor` sind synchrone Callables als austauschbare Integrationsgrenzen.
Ohne Übergabe werden die produktiven Download- bzw. Containeradapter verwendet.
Die EBT-Cases ersetzen diese Adapter durch explizit synthetische lokale Gegenstellen;
sie implementieren den Loader nicht selbst. Ein Loaderaufruf erhält eine Kopie
der Konfiguration und verändert die übergebene Struktur nicht.

### Konfiguration

| Feld | Muss-Regel |
| --- | --- |
| `schema_version` | Exakt `1`; unbekannte Konfigurationsfelder werden als Tippfehler abgelehnt. |
| `dataset_name` | Eine der drei oben genannten offiziellen Quellen. |
| `revision` | Vollständige unveränderliche 40-stellige hexadezimale Quellrevision; keine Branches, Tags oder `latest`. |
| `split` | Nichtleerer, im Quellsnapshot vorhandener Upstream-Split; niemals still auf `test` ausweichen. |
| `snapshot` | Optionaler Pfad zu einem vollständigen lokalen Snapshot gemäß untenstehendem Format. |
| `cache_dir` | Lokaler Beschaffungscache; kein Inhalt dieses absoluten Pfads gelangt in das exportierte Paket. |
| `offline` | Boolescher Wert, Standard `true`; fehlende lokale Daten führen dann ohne Netzwerkversuch zum Fehler. |
| `namespace`, `version` | Eigene Cubie-Paketidentität; Namespace gemäß bestehender ID-Regeln, Version nichtleer. Andere Inhalte unter derselben Identität müssen beim gemeinsamen Planen abgelehnt werden. |
| `instance_ids` | Eindeutige explizite IDs; fehlend oder `[]` bedeutet alle. Jede unbekannte explizite ID ist ein Fehler. |
| `repositories` | Optionale eindeutige Liste `owner/name`; fehlend oder `[]` bedeutet alle. Mit IDs durch UND verknüpft. |
| `limit`, `seed` | Optionales positives ganzzahliges Limit und ganzzahliger Seed, Standard `0`; boolesche Werte sind keine Zahlen. |
| `include_hints` | Boolescher Wert, Standard `false`; Änderung erzeugt eine andere Import-/Messidentität. |
| `on_error` | `fail` als Standard oder ausdrücklich `skip`; keine stillen Auslassungen. |
| `process_profile` | In dieser Stufe ausschließlich `issue_resolution`. |
| `harness_revision` | Vollständige 40-stellige hexadezimale Revision des unterstützten SWE-bench-Harness. |

Beispiel für einen Python-Aufruf:

```python
config = {
    "schema_version": 1,
    "dataset_name": "SWE-bench/SWE-bench_Lite",
    "revision": dataset_commit,           # geprüfte vollständige Quellrevision
    "split": "test",
    "cache_dir": "/data/swebench-cache",
    "offline": False,                    # Beschaffung ausdrücklich aktivieren
    "namespace": "swebench-lite-study",
    "version": "1.0.0",
    "instance_ids": selected_instance_ids,
    "seed": 17,
    "include_hints": False,
    "on_error": "fail",
    "process_profile": "issue_resolution",
    "harness_revision": harness_commit,
}
plan = plan_swebench_import(config)
result = import_swebench(config, "/data/scenarios/swebench-lite-study")
```

Ein CLI-Wrapper kann später TOML in dieselbe Konfiguration übersetzen; ein
neuer CLI-Befehl ist mit dieser Spezifikation noch nicht zugesagt.

## Anforderungen und deterministische Regeln

### SBL-01: Beschaffung und Offlinebetrieb

Der Standardquelladapter bezieht den Datensatz aus Hugging Face an der exakten
Revision, liest den verlangten Split und beschafft die dazugehörigen Git-Objekte
der ausgewählten Repositories. Repositories dürfen ausschließlich aus geprüften
`owner/name`-Kennungen unter der konfigurierten offiziellen GitHub-Basisadresse
abgeleitet werden. Eingabefelder sind niemals Shellkommandos.

`source(request)` erhält `dataset_name`, `revision`, `split`, `cache_dir` und
`offline` und liefert den Pfad eines vollständigen lokalen Snapshots zurück.
Es wird höchstens einmal je öffentlichem Plan-/Importaufruf verwendet. Ein
angegebener lokaler Snapshot wird direkt geprüft. Bei `offline=true` darf ein
fehlender/unvollständiger Snapshot ausschließlich aus bereits lokal geprüften
Cacheeinträgen ergänzt werden; ein übergebenes entferntes `source` wird nicht
aufgerufen. Ein vollständiger Snapshot benötigt weder Hugging-Face-Paket noch
Containerlaufzeit. Optionale Downloadabhängigkeiten werden erst bei Bedarf geladen.

Beschaffung hat endliche Verbindungs-/Transferzeitlimits und höchstens zwei
Wiederholungen für vorübergehende Transportfehler. Revisions-, Schema-, Lizenz-
und Prüfsummenfehler werden nicht wiederholt. Cacheeinträge werden erst nach
vollständiger Prüfung atomar veröffentlicht, getrennt nach Quelle, Revision und
Split. Abgebrochene Downloads dürfen keinen gültigen Cacheeintrag vortäuschen.
Fehler nennen Operation und Quelle; Zugangsdaten werden nicht protokolliert.

### SBL-02: Lokaler Snapshot und Schemanormalisierung

```text
snapshot/
  source.json
  records.jsonl
  repos/                       # lokale Git-Objektspeicher; kein Agentenmaterial
```

`source.json` enthält `schema_version=1`, `dataset_name`, `revision`, `split`,
`records_sha256`, `dataset_license`, `repository_licenses` (Repo → Lizenz) und
`repositories` (Repo → relativer Git-Speicherpfad). Quelle, Revision und Split
müssen der Konfiguration entsprechen. SHA-256 wird vor dem Parsen der JSONL-Zeilen
gegen die tatsächlich gespeicherten Bytes geprüft. Relative Repositorypfade
dürfen auch nach Symlinkauflösung den Snapshot nicht verlassen.

Jeder Datensatz benötigt nichtleere Strings für `instance_id`, `repo`,
`base_commit`, `version`, `problem_statement`, `patch` und `test_patch`.
`instance_id` ist eine sichere einzelne Cubie-ID; `repo` hat genau die Form
`owner/name`; Commits sind vollständige 40-stellige Hexwerte.
`environment_setup_commit` ist optional; wenn vorhanden und nichtleer, gelten
dieselben Commitregeln. Fehlend/leer wird als `null` normalisiert und der
Harness verwendet seine gepinnte Standardprovisionierung, niemals Repository-HEAD.
Ein nichtleerer Setupcommit ist zusätzlich zum Basiscommit bereitzustellen.

`FAIL_TO_PASS` und `PASS_TO_PASS` werden aus nativen Listen oder JSON-kodierten
Listen in Listen eindeutiger nichtleerer Strings normalisiert. Ihre Mengen
dürfen sich nicht überschneiden; `FAIL_TO_PASS` darf nicht leer sein.
`PASS_TO_PASS=[]` bleibt zulässig und wird als fehlende Regressionsabdeckung
ausgewiesen. Fehlende Pflichtfelder, ungültiges JSON und doppelte Instanz-IDs
sind Fehler, auch bei inhaltsgleichen Dubletten. Doppelte Test-IDs werden nicht
stillschweigend entfernt. Unicode im Auftrag bleibt erhalten.

Zusätzliche Felder wie `difficulty`, `image`, `eval_script`, `eval_type` oder
`log_parser` werden im privaten Rohdatensatz erhalten und gehasht. Der Import
führt sie nicht aus. Eine unterstützte Harness-/Datensatzkombination muss diese
Felder interpretieren können; andernfalls scheitert die ausführende Validierung
mit einer verständlichen Kompatibilitätsdiagnose. Unbekannte Felder gelangen
niemals automatisch in Prompt oder sichtbare Projektdateien.

### SBL-03: Auswahl und Importidentität

Zuerst werden Quellintegrität, Schema, Lizenzen und explizite IDs geprüft.
Danach werden IDs und Repositoryfilter geschnitten. Eine leere Ergebnismenge
ist ein Fehler. Kandidaten werden nach `instance_id` sortiert. Ohne Limit
bleibt diese Ordnung erhalten. Mit Limit werden Kandidaten nach
`SHA256(UTF8(str(seed) + "\n" + instance_id))` und bei Gleichstand nach ID
geordnet, die ersten `limit` ausgewählt und abschließend nach ID ausgegeben.
Ein Limit oberhalb der Kandidatenzahl kürzt nichts und ist kein Fehler.

Der Plan enthält `schema_version=1`, `source`, `selection`, `excluded` und
`plan_sha256`. `source` enthält mindestens Quellkennung, Revision, Split und
Rohdatenhash. Jeder ausgewählte Eintrag enthält den vollständig normalisierten
Datensatz einschließlich privater Evaluationsdaten. `excluded` nennt für jeden
nicht ausgewählten gültigen Datensatz ID und Grund `id_filter`, `repository_filter`
oder `limit`; in dieser Reihenfolge hat der erste zutreffende Grund Vorrang.

Der Planhash bindet Quellrevision, Rohdatenhash, normalisierte Datensätze,
vollständige Auswahl-/Promptregeln, Harnessrevision, Paketidentität und
Format-/Loadervertragsversion. Er wird als SHA-256 über UTF-8-JSON mit sortierten
Schlüsseln, `ensure_ascii=false` und Trennzeichen `,`/`:` gebildet. Absolute lokale
Pfade und Zielpfad gehören nicht hinein. Reine Zeilenumordnung verändert den
Rohdatenhash und darf damit den Planhash ändern, aber nicht die ausgewählten IDs.
Gleichwertige Listen-/JSON-Darstellungen ergeben gleiche normalisierte Einträge.
Neue Quellbytes werden nie unter der alten Importidentität ausgegeben.

### SBL-04: Projektstart und Schutz der Referenzen

Der Import liest den exakten Git-Baum von `base_commit` in einen neuen sichtbaren
Projektbaum; der Checkout des Cache-Repositorys bleibt unverändert. Weder dessen
HEAD noch `environment_setup_commit` ersetzen den Basiscommit. Nur versionierte
Dateien werden exportiert. `.git`, Hooks, spätere Commits, Cache-/Buildartefakte
und Lösungsdateien aus der Evaluatorablage werden nicht übernommen. Submodule
werden in der ersten Stufe ausdrücklich abgelehnt. Dateimodi bleiben erhalten;
aus dem sichtbaren Baum herausweisende Symlinks sind Fehler.

`task.md` enthält den Issue-Text und feste Hinweise zum Abgabeformat. Hints werden
nur bei `include_hints=true` ergänzt. Gold-Patch, Test-Patch, private Rohzeilen,
Testlisten und Evaluationsskripte liegen außerhalb von `visible/`. Bestehende
Tests des Basiscommits bleiben sichtbar; nachträgliche Tests des `test_patch`
werden nur im getrennten Evaluator-Workspace angewendet. Der Loader entfernt
keine Hinweise, die bereits im öffentlichen Issue-Text stehen; dies ist eine
verbleibende Kontaminationsgrenze.

### SBL-05: Cubie-Paket, Herkunft und Kontamination

Das Ergebnis enthält `package.json`, `dataset.json`, `swebench-import.json`
und je Instanz `scenario.json`, `task.md`, `visible/`, `evaluator/reference.json`,
private Patchdateien und die private Rohzeile. Alle Paketpfade sind relativ;
lokale Quellpfade und volatile Importzeitstempel gehören nicht hinein. Gleiche
Eingaben produzieren an verschiedenen Zielen identische Paketbytes.

Szenario-ID ist die unveränderte Instanz-ID. `group_id` und `design_id` werden
deterministisch aus derselben Repositorykennung abgeleitet (`/` → `__`);
mehrere Issues desselben Repositorys erhöhen nicht die Zahl unabhängiger
Projekte. Überlappende Full-/Lite-/Verified-Instanzen werden bei einer gemeinsamen
Studienplanung über `repo + instance_id + base_commit` erkannt und vor dem Lauf
als Mehrfachauswahl abgelehnt, auch bei verschiedenen Paketnamespaces.

Der Katalog trägt `publication_status="public"`, `potentially_known=true` und
Cubie-`split="development"`. Der Upstream-Split bleibt separat unter
`source.split` erhalten. Öffentliches `test` wird nicht als Cubie-`held_out`
ausgegeben. `origin`, `license`, `domain`, `assessment="executable"` und die
Herkunftsangaben sind vollständig. `source` nennt `dataset_name`, `revision`,
`split`, `instance_id`, `repo`, `base_commit`, `environment_setup_commit`,
`dataset_license`, `repository_license` und Rohzeilenhash. Paket-/Szenariolizenzen
dürfen nicht pauschal durch die Cubie-Lizenz ersetzt werden. Fehlende oder
ungeklärte Lizenzangaben blockieren die Aufnahme.

`swebench-import.json` bindet Plan, Loadervertragsversion, Quellhashes,
Harnessrevision, importierte/übersprungene IDs und ein Inventar sämtlicher
sonstiger Paketdateien samt relativen Pfaden, Modi, Symlinkzielen und SHA-256.
Es hasht sich nicht selbst; der bestehende Paket-/Freezehash bindet anschließend
auch dieses Manifest. `load_package` prüft das Inventar und lehnt beschädigte
Referenzen ab. Verschieben verändert die Gültigkeit nicht. Exportierte Referenzen
beginnen mit `validation_status="unvalidated"` und `human_reviews=[]`.

### SBL-06: Transaktionen und Fehlerpolitik

Ein vorhandenes Ziel wird nie überschrieben, auch nicht beim wiederholten
Aufruf. Die gesamte Erstellung und Strukturprüfung erfolgt in einer temporären
Geschwisterablage; erst das vollständige Paket wird atomar veröffentlicht.
Bei `on_error="fail"` bleibt nach einem Fehler kein Zielpaket zurück.
Der Quellcache und manuell erstellte Zieldateien bleiben unbeschädigt.

`skip` erlaubt ausschließlich datensatzbezogene Materialisierungsfehler nach
erfolgreicher Planung, beispielsweise einen fehlenden Git-Commit. Konfigurations-,
Quellintegritäts-, Schema-, Lizenz- und Pfadschutzfehler bleiben fatal. Jede
Auslassung erhält `instance_id`, `stage` und einen konkreten `reason`; keine
Auslassung gilt als fachlich gelöste Aufgabe. Kein erfolgreich importierter Fall
bedeutet Fehler statt Veröffentlichung eines leeren Pakets.

`import_swebench` liefert `package` als absoluten Zielpfad, `plan_sha256`,
`imported` als sortierte ID-Liste, `skipped` und `status="complete"` bzw.
`"partial"`. Das private Paketmanifest bewahrt dieselbe Bilanz ohne absolute Pfade.

### SBL-07: Ausführende Referenzvalidierung

Der neue Evaluatortyp `external.swebench_v1` hat eigene Referenzregeln. Er darf
mehrere Projektdateien reparieren und benötigt keine erfundenen Review-Findings,
Funktionslösungen oder künstlich erzeugten Mutanten. `reference.json` enthält
`gold_patch`, `test_patch` als private relative Dateipfade, normalisierte
`FAIL_TO_PASS`/`PASS_TO_PASS`, Herkunft und anfangs `unvalidated`. Bestehende
Evaluatorverträge behalten ihre strengeren eigenen Pflichtfelder.

`load_package` und `validate_package(..., check_references=False)` prüfen nur
Struktur und Hashes. Sie starten weder Projektinstallation noch Tests und
werten `unvalidated` nicht als ausführend geprüft. Eine allgemeine Validierung
mit `check_references=True` muss an den neuen Evaluator delegieren oder eine
fehlende Laufzeit ausdrücklich melden; eine stille Strukturprüfung genügt nicht.

`validate_swebench_references` führt je Instanz zwei frische getrennte Umgebungen
aus: Basisstand plus Test-Patch und Basisstand plus Gold-Patch plus Test-Patch.
Auf dem Basisstand müssen alle `FAIL_TO_PASS` fachlich scheitern und alle
`PASS_TO_PASS` bestehen. Auf Gold müssen beide Mengen vollständig bestehen.
Fehlende, übersprungene oder unbekannte Testresultate, Patch-/Installationsfehler,
Import-/Collectionfehler und Timeouts ergeben keine gültige Referenz.

Der Standardexecutor verwendet die gepinnte offizielle Harnessrevision in
begrenzten Containern mit separaten Projekt-/Evaluatorworkspaces. Er erfasst
den tatsächlich ausgeführten Image-Digest; ein veränderliches Tag genügt nicht.
Provisionierung darf benötigte Abhängigkeiten gezielt beziehen; Projekttests
laufen danach ohne Netzwerk. Host-Checkout, Zugangsdaten und Container-Daemon
werden nicht in Projektcontainer eingebunden. Zeit-, Speicher-, CPU- und
Prozessgrenzen sowie Beendigung aller Kindprozesse sind Voraussetzung. Ohne
diese Laufzeit erfolgt ein klarer Fehler vor Ausführung von Repositorycode;
ein Host-pytest-Fallback ist unzulässig. Der Import selbst braucht keine Container.

`executor(request)` erhält mindestens `instance_id`, `stage` (`base`/`gold`),
`base_commit`, `environment_setup_commit`, `patch` (Basis: leer), `test_patch`
(jeweils Inhalt), `FAIL_TO_PASS`, `PASS_TO_PASS`, `harness_revision`,
`network=false`, `run_id`, `request_sha256` und einen getrennten `output_dir`.
Die Ausführungsgrenzen werden durch den Executor vor dem Start ergänzt und
im Request-/Belegmanifest gebunden. Der Requesthash bindet fachliche Eingaben,
Stage und Harness-/Umgebungskonfiguration, aber keinen temporären Ausgabeort.

Die Antwort enthält identische `instance_id`, `run_id`, `request_sha256`,
`status`, `tests` (Test-ID → `pass`/`fail`/Fehlerstatus), tatsächlichen
`image_digest` und `artifacts` als Liste relativer Pfade mit `sha256`.
Belege müssen im Ausgabebaum liegen, vorhanden und unverändert sein. Für jeden
Versuch, jede Stage und jede erneute Validierung wird eine neue `run_id`
erzeugt. Antworten ohne passende Inhaltsbindung werden verworfen.

Die Rückgabe enthält `valid` und `scenarios`. Jede Ergebniszeile nennt
Szenario-/Instanz-ID, `reference_passed`, `validation_status`, `human_reviews`,
`evidence` mit Stage-/Requestbindung und bei Fehlschlag `reason` und Fehlerklasse.
Nach beiden erfolgreichen Stages ist der Ergebnisstatus `author_checked`,
sonst `unvalidated`. Die Paketdateien werden nicht verändert. Der Prüfbericht
und seine Belege werden separat dauerhaft archiviert; eine Messfreigabe muss
ihre Bindung an Paket- und Harnesshash prüfen. Menschliche Prüfungen bleiben
optional. Der Upstream-Name `Verified` erzeugt kein `independently_checked`.

### SBL-08: Übergang in Planung und Messbetrieb

`load_package`, `validate_package`, `plan_suite`, Freeze/Archive und Reporting
müssen den neuen Evaluatortyp und das Reparaturprofil bewusst unterstützen.
Strukturell gültige importierte Pakete sind ladbar. Eine Messung benötigt
jedoch einen erfolgreichen gebundenen Referenzbericht und einen Adapter, der
vollständige Projektänderungen als Patch abgeben kann. Die bestehenden
Einmodul-/Phasenannahmen dürfen nicht still auf diese Aufgaben angewendet werden.

Die fachliche Erfolgsregel für Agentenpatches ist dieselbe vollständige
FAIL-/PASS-TO-PASS-Abnahme. Private Tests werden nach Abgabe im Evaluatorbaum
angewendet; Teständerungen des Agenten dürfen sie weder ersetzen noch die
Sammlung unterdrücken. Der Agentenexport und sämtliche Requests enthalten nur
Auftrag und sichtbaren Basisstand. Der Evaluator darf Referenzmaterial lesen,
der Agent weder Evaluatorablage noch deren Git-Objekte.

Ergebnisse tragen `process_profile="issue_resolution"`, `process_passed=null`
und getrennte fachliche bzw. Infrastrukturstatus. Sie fließen nicht in TDD-
Prozessquoten, Review-Metriken oder einen gemeinsamen Gesamtscore ein.
Repositorygruppen, Ausschlüsse, fehlende Regressionsabdeckung, Herkunft und
potenzielle Bekanntheit bleiben in Planung, eingefrorenem Bundle und Bericht
sichtbar. Der Import öffentlicher SWE-bench-Daten erfüllt nicht den offenen
Punkt „Unverbrauchte Messaufgaben“.

## Abnahme und noch benötigte Nachweise

Die automatisierten EBTs prüfen zunächst die öffentlichen Loaderverträge und
die Auswertung synthetischer Executorantworten. Ein positiver Offline-Case
belegt weder echten Hugging-Face-Download noch Containerisolation oder
SWE-bench-Leistung. Die vollständige Lieferabnahme benötigt zusätzlich:

1. Die Offline-Cases aus der [Abnahmematrix](../../tests/docs_tmp/BENCHMARK_CASES_SWE_BENCH.md)
   bestehen mit der echten Implementierung; Standardtests bleiben netzwerkfrei.
2. Eine ausdrücklich gestartete Integration bezieht eine eingefrorene kleine
   Auswahl aus jeder unterstützten Quelle; Revisionen, Rohdaten und Lizenzen
   werden archiviert. Wiederholung im Offlinebetrieb ergibt identische Pakete.
3. Ein echter Containerlauf zeigt Basis-Rot/Gold-Grün, einen falschen Patch,
   fehlende Tests, Netzwerk-/Dateisystemgrenzen, Ressourcenabbruch und neue
   Versuchskennungen nach einer Wiederholung. Kein Erfolg aus altem Harnesscache.
4. Ein installierter Wheel-Durchstich exportiert, verschiebt, lädt, friert ein
   und misst ein importiertes Mehrdateienprojekt mit einem lokalen Agenten.
   Requests/Agentenworkspace werden auf Referenzlecks geprüft. Fehlender
   Referenzbericht und doppelt ausgewählte Instanzen werden vor Agentenstart abgelehnt.
5. Reporting weist Reparaturqualität ohne TDD-Prozessgutschrift aus und bewahrt
   die Repositorygruppen und sämtliche ausgelassenen/fehlgeschlagenen Versuche.

Diese Integrationsnachweise sind definiert, aber noch nicht durchgeführt.
Die Offline-Abnahme und ergänzende Produktprüfungen sind implementiert. Der
Standardexecutor benötigt einen separat installierten gepinnten Harness und
provisionierte Instanzimages; der Reparaturagent ein eigenes Digest-Image.
Eine reale Modellmessung ist für die technische Loaderabnahme nicht erforderlich.
