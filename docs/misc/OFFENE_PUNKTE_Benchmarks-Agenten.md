# Offene Punkte: Benchmark- und Agentenkonzept

Stand: 10. November 2026. Abgleich von [Agentenkonzept](AGENTEN_KONZEPT.md)
und [Benchmark-Konzept](BENCHMARK_KONZEPT.md) mit Implementierung und Nachweisen.
„Offen“ unterscheidet fehlende Umsetzung, fehlende praktische Abnahme und
optionale Erweiterungen. Die folgenden Abschlusskriterien sind konkrete
Arbeitsvorschläge zur Erfüllung der jeweiligen Konzeptanforderung.

Bereits vorhanden sind Rollenadapter, Wheel-Export, Offline-Prüfungen,
Basisdatensatz, Messpakete, Gates und CI-Vorlage. Die
[echte explorative Messreihe](EXPERIMENT_Agenten-5-5.md) umfasst 6 Kalibrierungs-
und 15 Pilotepisoden auf öffentlichen Versandkostenaufgaben. Sie ersetzt
weder den Basisdatensatz-Pilot noch einen unabhängigen Goldstandard.

## Für die fachliche und methodische Abnahme

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Unabhängige Referenzaufnahme** | Agenten §5.5; Benchmark §4.2, §6, §10.1/10.4 | Zwei tatsächliche menschliche Prüfungen je offiziellem Fall dokumentieren. Anforderungen, konforme Varianten, Fehler, Gegenbeispiele und Mutanten prüfen; Widersprüche klären oder Fälle explorativ belassen. Erst danach `independently_checked` setzen. Die Prüfung synthetischer Belegdateien beweist keine menschliche Aufnahme. |
| **Semantische Reviewer-Bewertung** | Agenten §3.3, §5.2/5.5; Benchmark §4.2, §6.1, §7.4 | Freie Befunde ohne Kenntnis von Modell und Bedingung Referenzfehlern zuordnen. Ursache, betroffenen Code und Auswirkung bewerten, Dubletten zusammenführen und neue plausible Befunde prüfen. Entscheidungen versioniert archivieren; offene Zuordnungen als `pending_adjudication` führen. Referenzkorrekturen erfordern Neubewertung aller betroffenen Antworten. Ein automatischer semantischer Evaluator ist eine mögliche Alternative, keine Voraussetzung für das manuelle Verfahren. |
| **Pilot auf dem ausgewählten Basisdatensatz** | Agenten §5.5; Benchmark §10.4 | Nach Referenzaufnahme ein geeignetes Set aus den 24 Reviews und den Projektepisoden auswählen, Auswahl begründen und mit realen Agenten kalibrieren und messen. Der bisherige Zwei-/Fünf-Lauf deckt nur öffentliche Smokes ab. Wartbarkeit getrennt, Entwicklerqualität einschließlich Mutanten und Prozessbelegen berichten. Die vorgegebenen `NotImplementedError`-Startstände benötigen zuvor die unten genannte Runner-Erweiterung oder eine ausdrücklich begründete Set-Auswahl. |
| **Belastbare Stichprobe und Auswertung** | Benchmark §3.2, §9 | Zahl unabhängiger Projekte und Wiederholungen anhand der Pilotstreuung planen. Unsicherheit auf Projektebene berücksichtigen; Wiederholungen nicht als zusätzliche Projekte zählen. Fehler, Enthaltungen, offene Bewertungen, Ausnahmen und unbekannte Kosten offen ausweisen. Die bisherigen Zeiten stammen teilweise aus parallel laufenden CPU-Prüfungen; kontrollierte Laufbedingungen vor aussagekräftigen Aufwandvergleichen festlegen. |

Die offizielle §5.5-Abnahme bleibt vor allem durch Referenzaufnahme und
semantische Nachbewertung offen. Die Benchmark-Abnahme nach §10.4 benötigt
zusätzlich reale Messungen auf dem dafür ausgewählten Basisdatensatz.

## Noch fehlende technische Umsetzung

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Isolation fremden Codes** | Agenten §2.1/4.2; Benchmark §7.3 | Begrenzten Container je Episode, getrennten Evaluator-Workspace und Ressourcenlimits umsetzen. Host-Workspace, Zugangsdaten und Container-Daemon ausschließen; Projektcode nach Provisionierung ohne Netzwerk ausführen. Abbruch der gesamten Umgebung prüfen. Temporäre Verzeichnisse und isoliertes Python sind bereits vorhanden, aber keine OS-Sicherheitsgrenze. |
| **Mehrere Inkremente und begründete Testrevisionen** | Agenten §4.1/4.2; Benchmark §5.2 | Das Protokoll über die einmalige Folge `test_design → red → green → refactor` hinaus erweitern. Je Inkrement Zwischenstände einfrieren; fachlich begründete Teständerungen dokumentieren und gegen den passenden vorherigen Produktionsstand erneut Rot/Grün prüfen. Bis dahin gilt ein Inkrement je Episode. |
| **`NotImplementedError` als fachliches Rot** | Agenten §4.2; Benchmark §5.2 | Erwartetes Stub-Verhalten gezielt anerkennen und gegen Import-, Installations- und sonstige Laufzeitfehler abgrenzen. Gegenproben müssen zeigen, dass beliebige Exceptions weiterhin kein gültiges Rot ergeben. `pytest.raises`-Rot funktioniert bereits. |
| **Nachbewertung zuverlässig übernehmen** | Agenten §3.3; Benchmark §6.1/9 | Zusätzlich zur vorhandenen Anzeige offener Fälle ein versioniertes Zusatzartefakt bzw. einen Importweg für menschliche Zuordnungen festlegen. Ursprungsantworten erhalten, neue Bewertungsstände binden und Berichte/Gates konsistent neu berechnen. Eine interaktive Oberfläche ist dafür optional. |
| **Vollständige Laufprovenienz** | Benchmark §7.2 | Die geforderten Angaben zu Repository-Commit und geändertem Arbeitsbaum getrennt erfassen; Abhängigkeitslock und später Container-Image-Digest automatisch binden. Wheel-, Quell-, Plan- und Artefakthashes sind vorhanden; der generische Freeze meldet den Lockhash derzeit als unbekannt. Beiliegende Lockdateien allein sind noch keine automatische Bindung an die verwendete Umgebung. |
| **CLI-Overrides für Laufkonfiguration** | Benchmark §6.2 | Die beschriebenen abschließenden CLI-Overrides anbieten und ihre Priorität gegenüber Set- und Szenariowerten prüfen. Aktuell werden Auswahl und Budgets über Konfigurationsdateien festgelegt. Alternativ den Konzeptumfang ausdrücklich auf diesen vorhandenen Weg begrenzen. |

## Praktische Nachweise und Betriebsregeln

| Offen | Bezug | Was fehlt zum Abschluss? |
| --- | --- | --- |
| **Tatsächlicher CI-Messbetrieb** | Benchmark §8, §10.5 | Die vorhandene Workflow-Vorlage mit einem echten geprüften Bundle und erreichbarem Provider in der Ziel-CI ausführen. Provisionierung, Laufzeitgrenzen, Gatefehler und Artefaktaufbewahrung dort praktisch nachweisen. Lokale Tests der Workflow-Schritte ersetzen diesen Betriebsnachweis nicht. |
| **Unverbrauchte Messaufgaben** | Benchmark §6, §9, §10.5 | Tatsächliche zurückgehaltene Aufgaben unabhängig aufnehmen und ihre Sichtbarkeit kontrollieren. Herkunft, Lizenz und Bekanntheit dokumentieren. Das vorhandene `held_out`-Schema und synthetische Testmetadaten stellen noch keinen unverbrauchten Datensatz bereit. |
| **Nutzbarkeit durch Außenstehende** | Benchmark §10.1/10.3 | Eine Person ohne Runner-Vorkenntnisse nach Anleitung Agent und Szenario anbinden und einen Bericht interpretieren lassen. Stolperstellen dokumentieren und beheben. Automatisierte Tutorial-/Wheel-Cases decken die Technik ab; ein solcher Nutzungsnachweis ist noch nicht dokumentiert. |
| **Abbruch und Wiederaufnahme** | Agenten §2.3/5.5; Benchmark §7.2 | Regeln für einen Abbruch vor dem Versiegeln des Runnerarchivs und für ausdrücklich gewünschte Wiederholungen festlegen. Fragmente erhalten, neue Versuche separat kennzeichnen und Vollständigkeit prüfen. Die Freigabe kann nicht deklarierte Läufe außerhalb der übergebenen Archive nicht entdecken. Nach HTTP-Abbruch vor einem neuen Versuch die serverseitige Inferenz prüfen; Verbindungsabbruch allein beweist deren Ende nicht. |
| **Dauerhafte Belegaufbewahrung** | Agenten §2.3/5.4/5.5; Benchmark §7.2/8 | Aufbewahrungsort, Sicherung, Zugriffsrechte und Fristen für Runner- und Adapterarchive festlegen. Das §5.5-Archiv ist lokal dauerhaft gesichert; frühere §5.4-Belege liegen laut Nachweis teils unter `/tmp`. Für weiter verwendete Ergebnisse deren Sicherung und Wiederherstellbarkeit prüfen. |

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

## Sinnvolle Reihenfolge

1. Referenzen unabhängig aufnehmen und semantische Nachbewertung abschließen.
2. Stub-Rot und die für das gewählte Set nötigen Prozessgrenzen klären;
   vor Ausführung fremden Codes die Containerisolation liefern.
3. Basisdatensatz-Set kalibrieren, einfrieren, real messen und auswerten.
4. Provenienz, Abbruchregeln, Sicherung und tatsächlichen CI-Betrieb abschließen.
5. Nur für entsprechende Aussagen: unbekannte Aufgaben, Produktvergleich und
   bestätigende Messung anschließen.
