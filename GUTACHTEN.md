<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="ChatGPT-Web (Deep Research)" model="unbekannt (kostenlose Version; ChatGPT-Web)" effort="unbekannt (kostenlose Version)" -->
# Gutachten: Technische Bestandsaufnahme von qb-cubie 0.1.1

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** ChatGPT-Web (Deep Research)
- **Modell:** unbekannt (kostenlose Version; ChatGPT-Web)
- **Reasoning-Effort:** unbekannt (kostenlose Version)
- **Analysedatum:** 25. November 2026 (Datum des bereitgestellten Berichts; genaue Uhrzeit nicht ausgewiesen)
- **Synthesebasis:** `docs/misc/lake/deep-research-report(1).md`; Abgleich mit `pyproject.toml`, `CHANGELOG.md`, `KNOWN_ISSUES.md`, `CI_PLATFORM_STATUS.md`, `docs/misc/lake/SOLVED_ISSUES.md`, `README.md` und den verlinkten QA-Handbüchern
- **Stand:** qb-cubie (`v0.1.1`, Branch und Arbeitsbaum-Commit nicht als sauberer Snapshot verifiziert)
- **Git-Log:** `5bb93d42` ("whoopsie :3", Arbeitsbaum-HEAD)

---

**Auftrag und Einordnung:** Der Deep-Research-Bericht wurde gemäß `docs/dev/DEV-GUIDE_Agent-Reports.md` in ein Gutachten mit `CUBIE_DOC_FRAME_2`-Provenance-Rahmen überführt und gegen ausgewählte aktuelle Repository-Dokumente abgeglichen. Dies ist kein vollständiges Code-, Test- oder CI-Audit. Wo Quellbericht und Repository-Stand voneinander abweichen, ist der Abgleich ausgewiesen; unverifizierte Bewertungen bleiben als Einschätzungen gekennzeichnet.
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

- **[BEFUND]** Der Repository-Stand weist Version `0.1.1` aus. Die in älteren Analysen als offen beschriebenen Fehler `BUG-002` (Assertions unter `python -O`), `BUG-003` (ungültige Linter-Ziele) und `BUG-007` (DocFrame-Erhalt des Erkenntnisgrenzen-Hinweises) sind im Changelog als behoben dokumentiert und in `docs/misc/lake/SOLVED_ISSUES.md` archiviert.
- **[BEFUND]** Linux und macOS sind laut `CI_PLATFORM_STATUS.md` für Python 3.13 und 3.14 Tier 1 und aktiv. Windows-CI ist vorübergehend eingefroren; `KNOWN_ISSUES.md` und der CI-Status nennen weiterhin plattformspezifische offene Befunde.
- **[BEFUND]** Die Core-Arenen `TempFS` und `PyVenv` bieten keine OS-Sicherheitsgrenze. Nicht vertrauenswürdiger Code darf daher nicht als sicher isoliert behandelt werden.
- **[EINSCHÄTZUNG]** Der aktuelle Dokumentations- und Changelog-Stand zeigt ein funktionsreiches, aktiv weiterentwickeltes Vorab-Release. Aussagen zur tatsächlichen Zuverlässigkeit, Testabdeckung und Produktionsreife erfordern reproduzierbare Tests und CI-Evidenz; dieses Gutachten liefert diese nicht.
- **[SCOPE]** Der Deep-Research-Quelltext ist qualitativ zusammengefasst, nicht wörtlich übernommen. Seine ursprünglichen Quellenmarker sind nicht auflösbar, da keine Quellenliste mitgeliefert wurde.

## 1. Umfang und Quellenlage

Der bereitgestellte Deep-Research-Bericht behandelt QA-Dokumentation, EBT/RBT, Arenen, statische Analyse, DocEnsurance und DocFrame, Reifegrad, CI sowie eine priorisierte Roadmap. Seine konkreten Aussagen wurden mit den oben genannten Projektdateien abgeglichen. Die Prüfung des Repositorys war dokumentationsbasiert und selektiv; Implementierung und Testläufe wurden nicht erneut untersucht.

Der Quelltext enthält pauschale Quellenhinweise auf das GitHub-Repository und im älteren Bericht nummerierte Marker, aber keine nachvollziehbare Quellenliste. Solche Marker werden hier nicht als Beleg verwendet. Aussagen aus dem Quellbericht, die sich im aktuellen Repository nicht bestätigen ließen, sind ausdrücklich als dortige Einschätzungen oder als ungeprüft gekennzeichnet.

## 2. Aktueller Repository-Stand

### 2.1 Metadaten und Lieferumfang

- **[BEFUND]** `pyproject.toml` weist `qb-cubie` Version `0.1.1` und Python `>=3.13` aus. Die Classifier führen Python 3.13 und 3.14 sowie „Operating System :: OS Independent“ auf. Letzteres ist Paket-Metadatum und kein Nachweis gleichwertiger CI-Unterstützung auf allen Betriebssystemen.
- **[BEFUND]** Optionale Abhängigkeitsgruppen sind `linters`, `benchmarks` und `swebench`. Das README grenzt Benchmark-Infrastruktur und die Testguided-Vergleichsstudie ausdrücklich vom Core ab.
- **[BEFUND]** Das Changelog datiert `0.1.1` auf den 24.11.2026. Der bereitgestellte Research-Text nennt den 25.11.2026 als aktuellen Stand, nicht als Changelog-Veröffentlichungsdatum.

### 2.2 Dokumentation und QA-Methodik

- **[BEFUND]** Die Dokumentation gliedert Nutzer- und Entwicklerwissen in Guides zu Vertragsdesign, Expect-Flags, Quantoren, TGD, EBT/RBT, Arenen, Linter, DocEnsurance und DocFrame. Die semantische Referenz ist `docs/core/GUIDE_Contract-Semantics.md`.
- **[BEFUND]** Die Repository-Konfiguration (`pyproject.toml`) definiert pytest-Marker für unter anderem `fast`, `slow`, `ebt`, `arena`, `linter`, `services`, `workflows`, `reviewer`, `meta` und `lint`. `addopts` schließt standardmäßig mit `-m 'not slow'` langsame Tests aus.
- **[BEFUND]** Der Entwicklerleitfaden für Berichte verlangt eine kurze Zusammenfassung, belegbare Aussagen, die Trennung von Ist/Hypothese/Soll, Scope-Angaben und die Dokumentation tatsächlich ausgeführter Prüfungen. Dieses Gutachten übernimmt diese Struktur.
- **[EINSCHÄTZUNG DES QUELLBERICHTS]** Die modulare Gliederung und Beispiele seien didaktisch nützlich. Ob die Lernprogression und Verständlichkeit für Zielgruppen im praktischen Einsatz genügen, wurde hier nicht evaluiert.

### 2.3 Semantik und Prüfwerkzeuge

- **[BEFUND LAUT QUELLBERICHT]** EBT verwendet pro angegebenem Eingang ein Zielaufruf; als Standard werden `pre`-All-Quantifizierung und `post`-Existenz-Quantifizierung beschrieben. Der Quellbericht weist zudem auf die Einschränkung für `expect=False` im `post`-Zustand hin. Die vollständige Semantik ist in `docs/core/GUIDE_Contract-Semantics.md` beschrieben; in dieser Transformation wurden die Laufzeitregeln nicht durch Tests verifiziert.
- **[BEFUND]** `pyproject.toml` stellt LibCST, MyPy und Pylint über das Extra `linters` bereit. Die Konfiguration belegt Verfügbarkeit als optionale Entwicklungswerkzeuge, nicht die Qualität oder Vollständigkeit konkreter Diagnosen.
- **[BEFUND LAUT QUELLBERICHT]** DocEnsurance führt Dokumentationsbeispiele aus und vergleicht erwartete Ausgaben. Der Bericht weist auf das allgemeine Risiko hin, dass Soll-Ausgaben unpassend gepflegt sein könnten. Eine unabhängige Bewertung der konkreten Regeln und Testabdeckung fand nicht statt.

### 2.4 Fehlerstatus: Änderungen seit älterer Bestandsaufnahme

Der Quellbericht ist zeitlich nicht einheitlich: Die Datei `deep-research-report(1).md` beschreibt den Stand `0.1.1`, während die ältere `GUTACHTEN.md`-Fassung und `deep-research-report.md` noch `0.1.0` behandeln. Für den aktuellen Abgleich gilt der Repository-Stand `0.1.1`.

- **[BEFUND] BUG-002 behoben:** `CHANGELOG.md` beschreibt die Ersetzung optimierungsabhängiger `assert`-Anweisungen im `PytestReporter` durch explizite Fehlerauslösung und nennt Subprozess-Verträge für `-O`/`-OO`. Der Eintrag ist außerdem in `SOLVED_ISSUES.md` archiviert.
- **[BEFUND] BUG-003 behoben:** Das Changelog dokumentiert explizite Validierung nicht existierender oder ungeeigneter `Path`-Ziele im `CstLinter` sowie zugehörige Verträge; der Fehler ist archiviert.
- **[BEFUND] BUG-007 behoben:** Das Changelog dokumentiert den zentralen DocFrame-Erkenntnisgrenzen-Hinweis, verlustfreie Erhaltung dokumenteigener Segmente und wieder aktivierte Dokumentations-Frame-Prüfungen; der Fehler ist archiviert.
- **[BEFUND] Noch offene Punkte:** `KNOWN_ISSUES.md` führt weiterhin `BUG-004` (verstreute relative Links bei Doku-Umbauten), `BUG-005` (redundante `foot`-Zone bei Routing-Dokumenten) und `BUG-006` (fehlende begründete `# noqa`-Ausnahmen in `test_function_size`) als offen. Der Quellbericht, der eine mögliche DocFrame-Gate-Scheinsicherheit anspricht, ist eine Einschätzung; der aktuelle Projektstand dokumentiert ein aktives Gate, beweist aber nicht dessen vollständige Wirksamkeit.

## 3. Plattformstatus und Sicherheitsgrenzen

### 3.1 CI-Abdeckung

`CI_PLATFORM_STATUS.md` ist die maßgebliche Statusquelle für die hier vorgenommene Einordnung:

| Plattform | Python | Dokumentierter Status | Einordnung |
| --- | --- | --- | --- |
| Linux (`ubuntu-24.04`) | 3.13, 3.14 | Tier 1, aktiv; Wheel- und Repository-Suite laut Status bestanden | Dokumentierter Status, keine erneute CI-Ausführung für dieses Gutachten |
| macOS (`macos-15`) | 3.13, 3.14 | Tier 1, aktiv; Wheel- und Repository-Suite laut Status bestanden | Dokumentierter Status, keine erneute CI-Ausführung für dieses Gutachten |
| Windows (`windows-2022`) | 3.13, 3.14 | Vorübergehend eingefroren | Offene Befunde und deaktivierte Matrix laut Statusdokument |

Der Statusbericht führt unter anderem einen unvollständigen Study-Run im Wheel-Job sowie Windows-spezifische Probleme bei Pfad-/Diagnose-Sortierung, Shebang-Verarbeitung und Callable-Pickling auf. Umfang und Aktualität dieser Einzelfehler wurden nicht separat verifiziert. Eine OS-unabhängige PyPI-Klassifizierung ersetzt keine Windows-CI.

### 3.2 Isolation

- **[BEFUND]** `KNOWN_ISSUES.md` dokumentiert, dass `TempFS` und `PyVenv` mit den Benutzerrechten des Hosts laufen und keine OS-Sicherheitsgrenze bereitstellen. Sie sind damit für vertrauenswürdigen Code vorgesehen.
- **[EINSCHÄTZUNG]** Diese Einschränkung ist eine Einsatzgrenze, kein Beleg für einen neu entdeckten Fehler. Soll nicht vertrauenswürdiger Code ausgeführt werden, ist eine externe Sicherheitsgrenze erforderlich. Die Entwürfe in den Virtualisierungs-Feature-Drafts sind nicht als verfügbare öffentliche Core-Schnittstelle zu behandeln.

## 4. Einschätzung von Reifegrad und Risiken

### Stärken

- **[EINSCHÄTZUNG]** Die klare Trennung aus Semantikreferenz, Nutzungsguides und Entwicklerdokumentation unterstützt nachvollziehbares Arbeiten.
- **[BEFUND]** Das Changelog dokumentiert konkrete Fehlerkorrekturen für Reporter-Verhalten, Linter-Pfade und DocFrame. Das Bug-Archiv macht deren Lebenszyklus sichtbar.
- **[BEFUND]** Plattformstatus und bekannte Einschränkungen werden explizit dokumentiert, einschließlich eingefrorener Windows-CI und fehlender OS-Sandbox.

### Risiken und Grenzen

- **[RISIKO] Windows-Abdeckung:** Windows ist laut aktuellem Status nicht Teil der aktiven CI-Matrix. Nutzer, die Windows benötigen, sollten die dokumentierten Einschränkungen berücksichtigen und eigene Validierung durchführen.
- **[RISIKO] Keine Sandbox:** Die Core-Arenen schützen den Host nicht vor nicht vertrauenswürdigem Zielcode.
- **[RISIKO] Offene Dokumentations-/Style-Themen:** `BUG-004` bis `BUG-006` sind in `KNOWN_ISSUES.md` offen. Ihre Auswirkung hängt vom betroffenen Workflow ab.
- **[HINWEIS] Grenzen formaler Gates:** Tests, DocEnsurance und DocFrame prüfen kodifizierte Erwartungen. Sie belegen nicht, dass Erwartungen vollständig oder fachlich richtig sind.
- **[UNGEPRÜFT] Produktionsreife:** Weder Fehlerquote noch praktische Wirksamkeit der QA-Methodik wurden im Rahmen dieser Transformation gemessen. Eine pauschale Aussage, das Paket sei produktionsreif oder nicht produktionsreif, wäre durch die hier erhobene Evidenz nicht gedeckt.

## 5. Empfehlungen

1. **Windows-Support gezielt wiederherstellen oder klar begrenzen.** Die dokumentierten CI-Befunde als reproduzierbare Verträge behandeln und die aktive Matrix erst nach verifizierten grünen Läufen erweitern.
2. **Sicherheitsgrenze deutlich im Nutzungskontext halten.** Beispiele und API-Dokumentation zu Arenen sollen unmissverständlich vermitteln, dass Host-Rechte gelten und nicht vertrauenswürdiger Code eine externe Isolation benötigt.
3. **Offene Dokumentationsprobleme nach Nutzerwirkung priorisieren.** `BUG-004` betrifft Linkpflege bei Umbauten; `BUG-005` die Frame-Konvention; `BUG-006` Style-Ausnahmen. Je Fix sollen Akzeptanzkriterien und gezielte Regressionstests dokumentiert werden.
4. **Gutachten mit reproduzierbaren Nachweisen ergänzen, wenn eine Reifegradentscheidung ansteht.** Dazu gehören konkrete CI-Run-IDs, Testprofile und Ergebnisse sowie eine Prüfung der Semantik und Dokumentationsbeispiele gegen Implementierung und Tests.
5. **Versionierte externe Bestandsaufnahmen zeitlich trennen.** Berichte für `0.1.0` und `0.1.1` nicht vermischen; Quellenmarker nur dann als Belege führen, wenn eine zugängliche Referenzliste und Abrufdaten vorliegen.

Diese Empfehlungen sind gutachterliche Vorschläge und keine bereits ausgeführten Maßnahmen.

## 6. Gesamturteil

**[GESAMTEINSCHÄTZUNG]** qb-cubie `0.1.1` weist eine umfangreiche, modular aufgebaute QA-Dokumentation und mehrere klar dokumentierte Test- und Analysebausteine auf. Gegenüber der älteren `0.1.0`-Bestandsaufnahme sind mindestens drei dort priorisierte Bugs laut Changelog behoben. Gleichzeitig ist die Plattformabdeckung nicht vollständig: Windows-CI ist eingefroren, und die Arenen bilden keine Sicherheitsgrenze gegen nicht vertrauenswürdigen Code. Offene Dokumentations- und Style-Themen sind nachvollziehbar gelistet.

Auf Basis der hier geprüften Dokumente lässt sich der Stand als aktiv entwickeltes Vorab-Release mit dokumentierten Einsatzgrenzen einordnen. Eine belastbare Aussage über Fehlerfreiheit oder allgemeine Produktionsreife lässt sich ohne unabhängige Ausführung der Tests, Prüfung des Codes und aktuelle CI-Belege nicht treffen.

## 7. Verifikation und Grenzen

| Prüfschritt | Kommando / Quelle | Ergebnis |
| --- | --- | --- |
| Berichtsvorgaben gelesen | Manuelle Sichtung `docs/dev/DEV-GUIDE_Agent-Reports.md` | Provenance-Header, Kurzfassung, Belegtrennung und Prüfprotokoll berücksichtigt |
| Quellbericht gesichtet | Manuelle Sichtung `docs/misc/lake/deep-research-report(1).md` | Themen und Empfehlungen extrahiert; keine Quellenliste vorhanden |
| Versionsstand geprüft | `pyproject.toml`, `CHANGELOG.md` | Version `0.1.1`; Changelog-Eintrag datiert auf 24.11.2026 |
| Bugstatus abgeglichen | `KNOWN_ISSUES.md`, `docs/misc/lake/SOLVED_ISSUES.md`, `CHANGELOG.md` | `BUG-002`, `BUG-003`, `BUG-007` als behoben dokumentiert; `BUG-004` bis `BUG-006` als offen gelistet |
| CI-Status abgeglichen | `CI_PLATFORM_STATUS.md` | Linux/macOS aktiv laut Status; Windows eingefroren |
| Laufzeittests / CI erneut ausgeführt | Keine | Nicht Teil des Auftrags; Befunde wurden nicht dynamisch reproduziert |
| DocFrame synchronisiert | Nicht ausgeführt | Rahmenzonen wurden manuell in Anlehnung an den Leitfaden strukturiert; kein `docframe update`-Lauf erfolgt |

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
