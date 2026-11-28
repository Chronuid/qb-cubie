# Gutachten: TGD und seine Umsetzung in qb-cubie

**Prüfdatum:** 28. November 2026
**Repository:** Branch `main`, HEAD `2086ea156fbdb25048eebf64db8956f886bcfb01` (`Tried to prepare RUN-006`), Version `0.1.3` laut `pyproject.toml`. `main` ist laut lokalem Git-Status `origin/main` um einen Commit voraus. Arbeitsbaum bei Beginn sauber. Das Tag `v0.1.3` zeigt auf Release-Commit `20c4b42b`; `v0.1.2` bis `v0.1.3` umfassen 10 Commits, nicht 12. Der zusätzliche HEAD-Commit fügt nur `RUN-6.md` und den Deep-Research-Bericht hinzu. Remote-Erreichbarkeit wurde nicht geprüft.

**Auftrag und Provenance:** Dieses Gutachten aktualisiert die frühere Fassung in `GUTACHTEN.md`. Erkenntnisebene A ist `docs/misc/lake/deep-research-report(2).md` (ChatGPT-Web, kostenloses Deep Research, Modell/Effort unbekannt; dort angegebene Quellenmarker `[18]`, `[26]` sind ohne Quellenverzeichnis nicht auflösbar). Ebene B ist die hier dokumentierte erneute Prüfung von Git, Projektdateien, ausgewählten TGD-Dokumenten, Implementierung und Tests. Ebene C sind die daraus abgeleiteten Bewertungen und Empfehlungen. Die frühere Fassung bezog sich auf 0.1.1 und ist als historische Provenance, nicht als aktueller Befund zu lesen.

## Management Summary

Die frühere Einschätzung, der v0.1.3-Code sei nicht eingesehen worden, ist durch diese Prüfung überholt. Das Release enthält konkret implementierte Regelprofile, DocFrame- und DocEnsurance-Regelcontainer, Service-Core-Anpassungen und gezielte Tests. Die Dokumentation beschreibt einen modularen, situativ skalierbaren TGD-Prozess; insbesondere sind `ANALYSIS`, `HYPOTHESIS` und `GREEN_AUDIT` keine stets erforderlichen Phasen. Agent-Reports und ihre Formatregeln sind Konventionen bzw. Hilfsmittel, kein universelles Prozess-Gate. DocFrame ist laut Routing weiterhin ein Prototyp.

Stärken sind die expliziten Schreibgrenzen der Kernknoten, die begründete Audit-Rückführung und konkrete Tests für konfigurierte Regelprofile und deren Fehlersignale. Einschränkungen: Dokumentierte Gates belegen zunächst nur die ausgeführten, kodifizierten Prüfungen; ihre fachliche Vollständigkeit folgt daraus nicht. Git-Commit-Reihenfolge oder Testnamen beweisen keine gelebte Freeze-Disziplin. Für diesen Auftrag wurden keine Tests ausgeführt. Der Stand `0.1.3` gilt für Paketcode; der lokale HEAD enthält spätere, nur dokumentarische Run-Dateien.

**Gesamturteil:** Für ein experimentelles Projekt ist TGD nachvollziehbar und in Teilen operativ konkretisiert. Das Material rechtfertigt weder eine pauschale Produktionsreifeaussage noch die Deep-Research-Empfehlung, alle Möglichkeiten zu formalisieren. Sinnvoll sind kleine Klarstellungen zu Gate-Nachweisen und Abschlussstatus; zusätzliche CI-Gates, Mutationstestpflichten oder verpflichtende Berichte sind anhand der vorliegenden Belege nicht verhältnismäßig begründet.

## Prüfstand und Untersuchungsumfang

Geprüft wurden `docs/README.md`, `docs/tgd/README.md` und die sechs verlinkten `NODE_*.md`, `docs/GUIDE_TGD.md`, `docs/dev/DEV-GUIDE_TGD-Workflow.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/misc/runs/README.md`, `RUN-5.md`, `RUN-6.md`, der Deep-Research-Bericht, `CHANGELOG.md`, `pyproject.toml` sowie frühere Fassung dieses Gutachtens. Git-Log und Diff `v0.1.2..v0.1.3` wurden untersucht; besonders `rule_profiles.py`, `doc_frame_rules.py`, `doc_rules.py`, Service-Core `guards.py`, `rules.py`, `workspace.py` und die einschlägigen Tests.

Die Release-Historie enthält Commit `8ff3d79e` zum DocFrame-Regelumbau, weitere TGD-/Dokumentationsänderungen und `20c4b42b` als Release-Vorbereitung. Changelog dokumentiert die neuen `FrameRuleProfile`, `DocFrameRuleSet`, `DocRuleSet`, `DocFrameFootLinks`, konfigurierbare `foot`-Schweregrade sowie Service-Core-Refactoring und Fehlerbehebungen. Die Versionsangabe 0.1.3 stimmt mit Tag und pyproject überein; spätere Codeentwicklung nach dem Tag wurde nicht behauptet.

## Prozessmodell, Rollen und Übergaben

`docs/tgd/README.md` und `GUIDE_TGD.md` stellen sechs Knoten vor: `ANALYSIS`, `HYPOTHESIS`, `PHASE_RED`, `PHASE_GREEN`, `GREEN_AUDIT`, `LIVING_DOCS`. Die ersten beiden sind situative Stützräder; der reguläre schlanke Kern kann Red → Green → Living Docs sein. Die Handbücher enthalten Eintritts-/Austrittsbedingungen und Schreibgrenzen. Das Projektprofil konkretisiert diese für qb-cubie. Das ist eine Kombination aus expliziten Invarianten und projektspezifischen Konventionen, nicht der Nachweis, dass jeder mögliche Lauf alle Dokumente oder Artefakte erzeugen muss.

`PHASE_GREEN` friert Prüfsystem und produktive Doku ein und bearbeitet das Arbeitsergebnis. Bei reproduzierbarem Widerspruch wird ein Audit-Artefakt übergeben. `GREEN_AUDIT` sieht Reproduktion, Urteil (`RESOLVED`/`REFUTED`) und begrenzte Korrektur vor. `REFUTED` führt zurück zu Green; `RESOLVED` zum Abschluss. Die operative Tabelle im Workflow-Profil beschreibt erlaubte Änderungen und Prüfungen. Das Audit ist damit ein begründeter Eskalationspfad, keine Pflichtphase. Die Dokumentation kann nicht technisch verhindern, dass Erwartungen informell geändert oder Freeze-Regeln missachtet werden; Git-Diff und Prüfprotokolle liefern dafür prüfbare Indizien, keinen Beweis über Absichten.

RUN-Dateien halten laufbezogenen Kontext fest; Format und Provenance-Frame sind optional. `RUN-6.md` ist ein umfangreicher, auf diesen Auftrag zugeschnittener Arbeitsauftrag, kein Beleg für die generische Minimalform und kein abgeschlossenes Testprotokoll. `RUN-5.md` enthält Release-Vorbereitung und expliziten Stopp vor Veröffentlichung; der Auftrag verweist auf einen Quota-Abbruch-Run, der in den hier zugänglichen Beispielen nicht eindeutig identifiziert werden konnte. Ein unterbrochener Run behält dokumentarischen Wert, belegt aber keinen abgeschlossenen Gate-Durchlauf. Der Status sollte jeweils im konkreten Run erkennbar sein.

## Implementierung und Testbasis

`rule_profiles.py` bindet `FramePattern`-Profile an Regelsequenzen; `DocFrameRuleSet` prüft Profiltypen und eindeutige Pattern-IDs, dispatcht Regeln passend zu den gefundenen Frame-IDs und nutzt einen Fallback auf das erste Profil bei ungeframten Dateien. Die Presets unterscheiden unter anderem `DOCFRAME-FOOT-LINKS`: Frame 1 als Fehler, Frames 2/3 als Warnung. `DocRuleSet` bündelt DocEnsurance-Regeln. Dies ist konkrete Abstraktion, nicht bloß eine aus Commitnamen abgeleitete SRP-Absicht. Ob die Aufteilung langfristig die beste ist, bleibt eine Designbewertung.

Die Tests in `test_rules_and_docframe.py`, `test_doc_frame.py` und `test_doc_ensurance.py` decken unter anderem unterschiedliche Schweregrade, defekte Routen, leere/ungültige Regelsets und Guards ab. Sie prüfen damit ausgewählte Verträge und Mutanten-artige Gegenbeispiele; sie sind keine allgemeine Mutationstestquote und decken nicht automatisch alle Integrationskombinationen ab. Service-Core-Änderungen umfassen gemeinsame Attribut-Token-Validierung, Report-Aufbau und Workspace-Regeln; der Diff und Release-Changelog belegen Anpassungen, aber für dieses Gutachten wurden keine Laufzeitergebnisse erzeugt.

**Prüfstatus:** keine Test-, Lint-, CI- oder DocFrame-Läufe ausgeführt. Vorhandene Tests wurden statisch gelesen; Testergebnisse werden daher nicht als bestanden behauptet. Kein Netzwerk-/Remote-Abgleich. Keine Prüfung sämtlicher sechs Knoten bis in jede Randregel; der Fokus lag auf Übergang, Freeze, Routing und den im Bericht behaupteten Codeänderungen.

## Deep-Research-Befunde: erneute Einordnung

| Aussage des Berichts | Einordnung nach Repository-Prüfung |
|---|---|
| TGD habe Gates und getrennte Rollen; Kriterien müssten überprüfbar sein | **Präzisiert:** Handbücher enthalten Rollen, Schreibgrenzen und Abnahmekriterien. Nicht jede Gate-Aussage ist ein automatisch verifiziertes Gate; Testausführung und fachliche Vollständigkeit müssen separat belegt werden. |
| `rule_profiles.py`/DocRuleSet seien vermutlich SRP-Abstraktionen, Code nicht geprüft | **Bestätigt und präzisiert:** Implementierung und gezielte Tests existieren; konkrete Profilbindung und Delegation nachvollzogen. „SRP-konform“ bleibt eine wertende, nicht binär beweisbare Designaussage. |
| Test-Freeze solle per Commit- und CI-Regel erzwungen werden | **Eingeschränkt:** Freeze ist als Prozessinvariante dokumentiert. Commit-Reihenfolge ist kein hinreichender Beleg. Eine CI-Regel für „Tests im vorletzten Commit“ ist aus dem Projektbedarf nicht begründet. |
| Living Docs müsse automatisch Testergebnisse veröffentlichen | **Nicht gestützt / Empfehlung nicht übernommen:** Dokumentation synchronisiert Handbücher und Beispiele; kein Beleg, dass Stakeholder-Reports Teil des Projektziels sind. |
| Lücken bei Artefakten, Übergaben und Synchronität | **Teilweise widerlegt:** Konkrete Handoffs und Routing-Indizes sind vorhanden; GUIDE, Knoten und Workflow-Profil verweisen aufeinander. Vollständige Driftfreiheit ist nicht durch statische Sichtung aller Randfälle bewiesen. |
| Plattformneutralität und Minimalität der RUN-Dateien unklar | **Präzisiert:** Workflow-Profil definiert werkzeugneutrales Minimalformat und optionale Frames. `RUN-6.md` ist absichtlich ausführlich, weil es einen komplexen Gutachtenauftrag trägt. |
| Mutationstests seien erforderlich | **Eingeschränkt:** Es gibt mutanten-artige Testfälle und Prozess-Mutanten-Mappings. Eine allgemeine Mutationstestpflicht ist weder aus Dokumentation noch Prüfziel abzuleiten. |
| Prozess könne unnötig aufwändig sein | **Offen als Praxiseffekt:** Dokumentation erlaubt situative Skalierung. Tatsächlicher Zeit-/Nutzenaufwand wurde nicht gemessen. |
| Commit-Messages seien zu wenig erklärend | **Offen/teilweise präzisiert:** Changelog beschreibt v0.1.3 substantiell; einzelne Commit-Nachrichten sind knapp. Ob ein Issue-Link nötig wäre, lässt sich ohne konkreten Nachvollziehbarkeitsfehler nicht behaupten. |
| Quellen [18], [26] stützen Best Practices | **Offen:** Quellenverzeichnis und genaue Referenzen fehlen; Aussagen können nicht unabhängig attribuiert werden. |

Der Bericht korrigiert sich selbst als codearme Vorprüfung. Seine Unsicherheiten waren daher sachgerecht, aber aus diesen Vermutungen dürfen keine aktuellen Mängel fortgeschrieben werden.

## Kritische Bewertung und Empfehlungen

**Stärken:** modulare, ausdrücklich skalierbare Rollen; dokumentierte Schreibgrenzen; definierter Audit-Rückweg; konkrete, konfigurierbare DocFrame-Regeln; Tests für ausgewählte Fehlersignale; zentrale Routing-Indizes. Die Trennung zwischen Produktdokumentation, Run-Artefakten und optionalen Berichten reduziert Verwechslungen.

**Risiken/Grenzen:** Dokumentation allein erzwingt keine Prozessdisziplin. Ein grüner Testlauf besagt nur, dass die ausgeführten Tests unter den jeweiligen Bedingungen bestanden haben. Er belegt weder vollständige Anforderungen noch fehlerfreie Implementierung. Prototypisches DocFrame sollte nicht als unabhängige Qualitätsgarantie verstanden werden. Agenten, die alte Berichte lesen, sind nur insoweit unabhängig, wie sie den aktuellen Stand selbst prüfen und frühere Aussagen als Hypothesen behandeln.

Empfehlungen, ausdrücklich als Vorschläge und nicht als bestehende Pflichten:

1. **Abschlussstatus im jeweiligen RUN klar markieren (niedrig, optional):** begonnen, teilweise geprüft, abgeschlossen oder abgebrochen; dazu tatsächliche Befehle/Ergebnisse. Nutzen: Teilergebnisse bleiben verwertbar, ohne abgeschlossene Gates vorzutäuschen. `RUN-6.md` enthält bereits umfangreiche Prüfkriterien; Status folgt erst im Abschluss.
2. **Gate-Aussagen an konkrete Evidenz binden (niedrig, optional):** Bei einem als bestanden bezeichneten Gate Prüfkommando, Zielumfang und Ergebnis nennen. Nutzen: Leser unterscheiden dokumentierte Kriterien von tatsächlich ausgeführten Prüfungen.
3. **Keine pauschale CI-/Mutationstestpflicht einführen:** erst bei konkretem wiederkehrendem Fehlermuster prüfen, ob Automatisierung mehr Nutzen als Wartungsaufwand bringt.

## Threads of Validity / Gültigkeitsgrenzen

- **Belastbar:** Branch/HEAD/Version/Tagstatus lokal; Diff zwischen Release-Tags; Existenz und Struktur der untersuchten Implementierung und Tests; dokumentierte Prozessbeschreibung und Run-Konventionen.
- **Eingeschränkt:** Designqualität und Synchronität beruhen auf gezielter, nicht erschöpfender Code-/Dokumentensichtung. Die Tests wurden nicht ausgeführt. Aussagen über erfolgreiche Laufzeit, vollständige Regelabdeckung oder reale Agentendisziplin sind damit nicht belegt.
- **Offen:** Remote-Referenzen außerhalb des lokalen Clone-Zustands; tatsächliche CI-Läufe; praktische Prozesskosten; die nicht auflösbaren Deep-Research-Quellenmarker; genaue Zuordnung des im Auftrag erwähnten Quota-Abbruch-Beispiels.
- **Für höhere Sicherheit erforderlich:** gezielte Testläufe für die betroffenen Regelprofile und unabhängiger Review eines konkreten TGD-Laufprotokolls. Eine vollständige Suite oder Mutationstestkampagne war für die dokumentarische Synthese nicht erforderlich und wurde nicht ausgeführt.

## Quellen und Provenance

**A – Extern übernommener Bericht:** `docs/misc/lake/deep-research-report(2).md`, datiert 28.11.2026. Er verweist auf GUIDE_TGD, DEV-Guide, Commits und nicht auflösbare externe Marker; seine genannten externen Fachquellen sind mangels Bibliographie nicht nachvollziehbar.

**B – Eigenständige Repository-Prüfung:** `docs/README.md`; `docs/tgd/README.md` und `NODE_ANALYSIS.md`, `NODE_HYPOTHESIS.md`, `NODE_PHASE_RED.md`, `NODE_PHASE_GREEN.md`, `NODE_GREEN_AUDIT.md`, `NODE_LIVING_DOCS.md`; `docs/GUIDE_TGD.md`; `docs/dev/DEV-GUIDE_TGD-Workflow.md`; `docs/dev/DEV-GUIDE_Agent-Reports.md`; `docs/misc/runs/README.md`, `RUN-5.md`, `RUN-6.md`; `pyproject.toml`; `CHANGELOG.md`; Quellmodule und Tests aus dem Abschnitt „Implementierung und Testbasis“; Git `v0.1.2..v0.1.3` und aktueller HEAD.

**C – Synthese:** Bewertungen und Empfehlungen in diesem Dokument. Sie sind gutachterliche Einschätzungen, keine Projektinvarianten. Es wurden keine externen Quellen zusätzlich recherchiert.
