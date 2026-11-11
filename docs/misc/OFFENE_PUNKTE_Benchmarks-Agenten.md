# Offene Punkte: Benchmark- und Agentenkonzept

Stand: 11. November 2026. Abgleich von [Agentenkonzept](AGENTEN_KONZEPT.md)
und [Benchmark-Konzept](BENCHMARK_KONZEPT.md) mit Implementierung und Nachweisen.
„Offen“ unterscheidet fehlende Umsetzung, fehlende praktische Abnahme und
optionale Erweiterungen. Die folgenden Abschlusskriterien sind konkrete
Arbeitsvorschläge zur Erfüllung der jeweiligen Konzeptanforderung.

Bereits vorhanden sind Rollenadapter, Wheel-Export, Offline-Prüfungen,
Basisdatensatz, Messpakete, Gates und CI-Vorlage. Die
[echte explorative Messreihe](EXPERIMENT_Agenten-5-5.md) umfasst 6 Kalibrierungs-
und 15 Pilotepisoden auf öffentlichen Versandkostenaufgaben. Sie ersetzt
weder den Basisdatensatz-Pilot noch einen unabhängigen Goldstandard.

Menschliche Prüfungen je offiziellem Fall sind optional und keine Voraussetzung
für Vollständigkeit oder offizielle Pilotfreigabe. Erforderlich bleiben eine von
der Agentenantwort unabhängige, versionierte Referenz, die vorgesehenen
technischen Gegenproben und ein transparenter Bewertungsstand. `author_checked`
ist auch für offizielle Fälle zulässig. Nur tatsächlich belegte unabhängige
Prüfungen rechtfertigen `independently_checked`; fehlende Prüfungen werden nicht
als durchgeführt ausgewiesen. Ungeklärte Befunde bleiben offen und zählen nicht
als bestätigte Qualitätsnachweise.

## Bearbeitungsstand vom 11. November 2026

Umgesetzt sind präzise deklarierbares Stub-Rot im Basisdatensatz, ein
versionierter Import semantischer Finding-Zuordnungen mit abgeleiteten Archiven,
Neuberechnung von Bericht und Gates sowie zusätzliche Laufprovenienz.
Die neuen Gegenproben stehen in `test_stub_red.py`, `test_adjudication.py` und
`test_runtime_provenance.py`. CLI-Overrides sind aus dem zugesagten aktuellen
Umfang gestrichen; Konfigurationsdateien bleiben maßgeblich. Regeln für Abbruch,
Wiederholung und Aufbewahrung sind im
[Betriebsleitfaden](../GUIDE_Benchmark-Betrieb.md) festgelegt.

Noch offen sind Containerisolation, mehrere Inkremente/Testrevisionen,
nachgewiesene Installation gemäß Lock, echte Basisdatensatz-Pilotmessungen,
semantische Bewertungen der bereits vorhandenen realen Antworten, Ziel-CI,
externer Nutzertest und tatsächliche Sicherungs-/Wiederherstellungsnachweise.
Die zusätzlichen Messziele unten bleiben optionale Erweiterungen.

Die folgenden Tabellen bleiben als fachliche Kriterien erhalten; die hier
benannten erledigten Teilaufgaben sind keine offenen Pflichtlieferungen mehr.

## Für die fachliche und methodische Abnahme

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Nachvollziehbare Referenzvalidierung** | Agenten §5.5; Benchmark §4.2, §6, §10.1/10.4 | Anforderungen, konforme Varianten, Fehler, Gegenbeispiele und Mutanten anhand versionierter Referenzen und technischer Gegenproben prüfen. `author_checked` genügt auch für offizielle Fälle. Zwei dokumentierte menschliche Prüfungen je Fall sind eine optionale zusätzliche Absicherung; nur dann `independently_checked` setzen. Ungeklärte Widersprüche transparent ausweisen und vor bestätigenden Aussagen klären. |
| **Semantische Reviewer-Bewertung** | Agenten §3.3, §5.2/5.5; Benchmark §4.2, §6.1, §7.4 | Freie Befunde ohne Kenntnis von Modell und Bedingung Referenzfehlern zuordnen. Ursache, betroffenen Code und Auswirkung bewerten, Dubletten zusammenführen und neue plausible Befunde prüfen. Entscheidungen versioniert archivieren; offene Zuordnungen als `pending_adjudication` führen. Referenzkorrekturen erfordern Neubewertung aller betroffenen Antworten. Eine dokumentierte automatische semantische Bewertung ist ebenso zulässig; menschliche Zuordnung ist optional. Offene Zuordnungen verhindern bestätigte Aussagen zu diesen Befunden, nicht die Vollständigkeit des archivierten Laufs. |
| **Pilot auf dem ausgewählten Basisdatensatz** | Agenten §5.5; Benchmark §10.4 | Nach dokumentierter Referenzvalidierung ein geeignetes Set aus den 24 Reviews und den Projektepisoden auswählen, Auswahl begründen und mit realen Agenten kalibrieren und messen. Der bisherige Zwei-/Fünf-Lauf deckt nur öffentliche Smokes ab. Wartbarkeit getrennt, Entwicklerqualität einschließlich Mutanten und Prozessbelegen berichten. Die vorgegebenen `NotImplementedError`-Startstände benötigen zuvor die unten genannte Runner-Erweiterung oder eine ausdrücklich begründete Set-Auswahl. |
| **Belastbare Stichprobe und Auswertung** | Benchmark §3.2, §9 | Zahl unabhängiger Projekte und Wiederholungen anhand der Pilotstreuung planen. Unsicherheit auf Projektebene berücksichtigen; Wiederholungen nicht als zusätzliche Projekte zählen. Fehler, Enthaltungen, offene Bewertungen, Ausnahmen und unbekannte Kosten offen ausweisen. Die bisherigen Zeiten stammen teilweise aus parallel laufenden CPU-Prüfungen; kontrollierte Laufbedingungen vor aussagekräftigen Aufwandvergleichen festlegen. |

Die offizielle §5.5-Abnahme benötigt nachvollziehbare Referenzvalidierung und
eine dokumentierte semantische Bewertung, soweit die ausgewiesenen Kennzahlen
sie erfordern. Fehlende menschliche Prüfungen je Fall sind kein Abschlussblocker. Die Benchmark-Abnahme nach §10.4 benötigt
zusätzlich reale Messungen auf dem dafür ausgewählten Basisdatensatz.

## Noch fehlende technische Umsetzung

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Isolation fremden Codes** | Agenten §2.1/4.2; Benchmark §7.3 | Begrenzten Container je Episode, getrennten Evaluator-Workspace und Ressourcenlimits umsetzen. Host-Workspace, Zugangsdaten und Container-Daemon ausschließen; Projektcode nach Provisionierung ohne Netzwerk ausführen. Abbruch der gesamten Umgebung prüfen. Temporäre Verzeichnisse und isoliertes Python sind bereits vorhanden, aber keine OS-Sicherheitsgrenze. |
| **Mehrere Inkremente und begründete Testrevisionen** | Agenten §4.1/4.2; Benchmark §5.2 | Das Protokoll über die einmalige Folge `test_design → red → green → refactor` hinaus erweitern. Je Inkrement Zwischenstände einfrieren; fachlich begründete Teständerungen dokumentieren und gegen den passenden vorherigen Produktionsstand erneut Rot/Grün prüfen. Bis dahin gilt ein Inkrement je Episode. |
| **`NotImplementedError` als fachliches Rot — umgesetzt** | Agenten §4.2; Benchmark §5.2 | `expected_red_exception` bindet Modul und exakte Meldung; nur der erwartete Produktionsstub in Rot zählt fachlich. Import-, Setup-, andere Laufzeitfehler und Stubfehler in Grün bleiben ungültig. Die vier initialen Basisaufgaben deklarieren ihre Stubs. Reale pytest-Gegenproben: `tests/benchmarks/phase3/test_stub_red.py`. |
| **Nachbewertung zuverlässig übernehmen — Import umgesetzt** | Agenten §3.3; Benchmark §6.1/9 | `apply_adjudication` importiert versionierte Finding-Zuordnungen mit Begründung und Hashbindung. Neue Archive erhalten Originalantworten und ursprüngliche Ergebnisse; Bericht, Kennzahlen und Gates werden neu berechnet. Das Bewertungsverfahren muss die Zuordnungen weiterhin fachlich liefern; vorhandene reale Antworten sind noch nachzubewerten. |
| **Vollständige Laufprovenienz — teilweise umgesetzt** | Benchmark §7.2 | Commit, Dirty-Status, Git-Diffhash, gefundener Lockhash und Fingerprint installierter Distributionsversionen werden automatisch erfasst. Eine gefundene Lockdatei beweist keine lockkonforme Installation; dies bleibt ausdrücklich unbestätigt. Container-Image-Digest fehlt bis zur Containerimplementierung. |
| **CLI-Overrides für Laufkonfiguration — Umfang geklärt** | Benchmark §6.2 | Das Konzept ist ausdrücklich auf vorhandene Konfigurationsdateien begrenzt. Auswahl und Budgets werden vor dem Lauf geplant und eingefroren; zusätzliche CLI-Overrides sind keine offene Pflichtlieferung. |

## Praktische Nachweise und Betriebsregeln

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Tatsächlicher CI-Messbetrieb** | Benchmark §8, §10.5 | Die vorhandene Workflow-Vorlage mit einem echten geprüften Bundle und erreichbarem Provider in der Ziel-CI ausführen. Provisionierung, Laufzeitgrenzen, Gatefehler und Artefaktaufbewahrung dort praktisch nachweisen. Lokale Tests der Workflow-Schritte ersetzen diesen Betriebsnachweis nicht. |
| **Unverbrauchte Messaufgaben** | Benchmark §6, §9, §10.5 | Tatsächliche zurückgehaltene Aufgaben unabhängig aufnehmen und ihre Sichtbarkeit kontrollieren. Herkunft, Lizenz und Bekanntheit dokumentieren. Das vorhandene `held_out`-Schema und synthetische Testmetadaten stellen noch keinen unverbrauchten Datensatz bereit. |
| **Nutzbarkeit durch Außenstehende** | Benchmark §10.1/10.3 | Eine Person ohne Runner-Vorkenntnisse nach Anleitung Agent und Szenario anbinden und einen Bericht interpretieren lassen. Stolperstellen dokumentieren und beheben. Automatisierte Tutorial-/Wheel-Cases decken die Technik ab; ein solcher Nutzungsnachweis ist noch nicht dokumentiert. |
| **Abbruch und Wiederaufnahme — Regeln festgelegt** | Agenten §2.3/5.5; Benchmark §7.2 | Der Betriebsleitfaden legt Studienjournal, Erhalt unversiegelter Fragmente, neue Versuchskennungen und explizite Wiederholungsgründe fest. Nach HTTP-Abbruch ist vor einem neuen Versuch das Ende der serverseitigen Inferenz nachzuweisen. Journalabgleich und Providerprüfung bleiben betriebliche Schritte; unversiegelte Fragmente erfüllen die Pilotfreigabe nicht. |
| **Dauerhafte Belegaufbewahrung — Regeln festgelegt, Nachweise offen** | Agenten §2.3/5.4/5.5; Benchmark §7.2/8 | Primärablage, getrennte Sicherung, Zugriffsrollen, mindestens zwölf Monate Aufbewahrung und Wiederherstellungsprüfung sind im Betriebsleitfaden festgelegt. Für vorhandene Archive sind Sicherungsziel und erfolgreiche Wiederherstellung noch tatsächlich zu dokumentieren; alte `/tmp`-Belege gelten ohne Prüfung nicht als gesichert. |

## Nur bei erweitertem Messziel erforderlich

Diese Punkte blockieren den einzelnen lokalen Cubie-Agententest nicht.

| Ziel / Erweiterung | Bezug | Nötige zusätzliche Arbeit |
| --- | --- | --- |
| **Cubie gegenüber pytest vergleichen** | Agenten §4.3; Benchmark §3.1/9 | Separate Agenten-IDs und Prompt-Hashes für beide Bedingungen exportieren, Dokumentationsumfang und Ausgangsstände fachlich angleichen, echte gepaarte Messungen ausführen. Vorlagen und Developer-Modi sind vorhanden; der aktuelle Live-Ablauf misst ausschließlich Cubie. |
| **Bestätigenden Produktnutzen behaupten** | Benchmark §9 | Vor Sichtung zurückgehaltener Ergebnisse primäre Kennzahlen, praktisch relevante Aufwandsverbesserung und tolerierbare Qualitätsabweichung einfrieren; dann auf ausreichend unabhängigen Projekten messen. Dafür liegt noch kein Nachweis vor. |
| **Nutzen der Review-Struktur kausal bestimmen** | Benchmark §3.1 | Eine gesonderte Ablation mit gleichen Inhalten und unterschiedlich strukturierter Kriterienführung planen und messen. Der bisherige Reviewer-Erfolg isoliert diesen Effekt nicht. |
| **Große Reviewer-Kontexte** | Agenten §3.2 | Nachweisbares Verfahren für Teilkontexte entwickeln: Auswahl, tatsächlich gelesene Inhalte, Auslassungen und Quellenbindung dokumentieren. Bisher werden kleine vollständige Kontexte verwendet. |
| **Harte Token-/Kostenlimits** | Agenten §2.4; Benchmark §3.2/7.1/10.5 | Providerfähige Messung und Durchsetzung einschließlich Reparaturaufrufen ergänzen. Bis dahin harte Limits ablehnen und unbekannte Kosten als unbekannt belassen. Dies ist ausdrücklich außerhalb des aktuellen lokalen Runnerumfangs. |
| **Developer und Reviewer zusammenarbeiten lassen** | Agenten §5 | Eigener Versuchsarm: Developer-Abgabe einfrieren, Review darauf binden, Reparatur in neuer Episode prüfen. Die unabhängige Abnahme muss ausschlaggebend bleiben. |
| **Beliebige Adapter automatisch provisionieren** | Benchmark §10.5 | Bei Bedarf deklarierte Adapterabhängigkeiten reproduzierbar installieren und archivieren. Der aktuelle Runner setzt eine vorbereitete Umgebung voraus; automatische Provisionierung ist derzeit nicht zugesagt. |

Weitere ausdrücklich spätere Optionen sind Mehrfachfehler-Reviews,
fortlaufende Projektentwicklung, freie Entwicklung ohne kontrollierte Phasen
und ein öffentliches Szenarioverzeichnis mit automatischem Download
(Benchmark §4.1, §5.1/5.2, §6.1). Sie sind keine offenen Pflichtlieferungen
des bestehenden lokalen Durchstichs.

## Datensätze verbessern: automatisierter SWE-bench-Import

Die [Loader-Anforderungen](SWE_BENCH_LOADER_ANFORDERUNGEN.md) konkretisieren
den Datensatzausbau mit gepinnten Full-/Lite-/Verified-Quellen, automatischer
Beschaffung, reproduzierbarer Auswahl, Herkunft und Lizenzen, geschützten
Referenzen sowie getrennter Basis-/Gold-Prüfung. Die
[neuen EBT-Cases](../../tests/docs_tmp/BENCHMARK_CASES_SWE_BENCH.md) definieren
die ausführbare Abnahme. Import, externer Evaluator, gebundene Referenzfreigabe,
Suite/Freeze und Reparaturmodus des Developer-Agenten sind im Produktcode
implementiert; siehe [Nutzungsleitfaden](../GUIDE_Benchmark-SWEbench.md).

Damit ist die Anforderungsklärung dieses Erweiterungspunkts erledigt. Offen
bleiben echte Download-/Containerprüfung und der vollständige installierte
Messdurchstich gemäß SBL-01 bis SBL-08. Öffentliche SWE-bench-Fälle gelten als
potenziell bekannt und ersetzen weder unverbrauchte Messaufgaben noch einen
beobachteten TDD-Prozess. Der vorhandene lokale Durchstich erhält dadurch keine
zusätzliche Pflichtabhängigkeit von SWE-bench.

## Sinnvolle Reihenfolge

1. Referenzen nachvollziehbar validieren und erforderliche semantische
   Bewertungen abschließen; menschliche Prüfungen je Fall bleiben optional.
2. Stub-Rot und die für das gewählte Set nötigen Prozessgrenzen klären;
   vor Ausführung fremden Codes die Containerisolation liefern.
3. Basisdatensatz-Set kalibrieren, einfrieren, real messen und auswerten.
4. Provenienz, Abbruchregeln, Sicherung und tatsächlichen CI-Betrieb abschließen.
5. Nur für entsprechende Aussagen: unbekannte Aufgaben, Produktvergleich und
   bestätigende Messung anschließen.
