# Changelog

Alle nennenswerten Änderungen an `qb-cubie` werden in dieser Datei dokumentiert.

## [Unreleased]

### Neu
- **Core-CLI `qb-cubie` mit `docframe update`:** Neuer CLI-Einstiegspunkt `qb-cubie` (`[project.scripts]` in [pyproject.toml](./pyproject.toml), implementiert in [cli.py](./src/qb_cubie/cli.py)) sowie Modul-Einstiegspunkte `python -m qb_cubie`, `python -m qb_cubie.services.docframe` und `python -m qb_cubie.services.doc_frame` zur direkten Ausführung von `DocFrame.update(...)` inklusive `--exclude` und `--format text|json`.

## [0.0.7] - 2026-11-16

### Neu
- **Service-Prototyp `DocFrame` (`qb_cubie.services.doc_frame` / `qb_cubie.services.docframe`) – Prototyp, noch zu evaluieren und zu härten:**
  - Zweistufige Synchronisations-, Routing- und Verifikations-Engine für Markdown-Dokumentrahmen (`<!-- qb:frame ... --> ... <!-- /qb:frame -->`) in [protocols.py](./src/qb_cubie/services/doc_frame/protocols.py), [\_catalog_scanner.py](./src/qb_cubie/services/doc_frame/_catalog_scanner.py), [frame_blocks.py](./src/qb_cubie/services/doc_frame/frame_blocks.py), [doc_frame_rules.py](./src/qb_cubie/services/doc_frame/doc_frame_rules.py), [doc_frame.py](./src/qb_cubie/services/doc_frame/doc_frame.py) sowie Kurz-Alias [docframe.py](./src/qb_cubie/services/docframe.py).
  - Standard-Presets (`CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`), Bausteine und dynamische Router (`HeaderContentSlot`, `DisclaimerSlot`, `ProvenanceBlock`, `FolderRouter`, `SiblingRouter`, `CatalogRouter`, `CompactNav` u. a.) sowie Dokument-Prüfregeln (`CUBIE_DOCFRAME_RULES`: `DOCFRAME-MISSING`, `DOCFRAME-OUTDATED`, `DOCFRAME-BROKEN-ROUTE`, `DOCFRAME-PROVENANCE-INCOMPLETE`).
  - Zugehörige Leitfäden ([GUIDE_DocFrame.md](./docs/services/GUIDE_DocFrame.md), [DEV-GUIDE_DocFrame.md](./docs/dev/services/DEV-GUIDE_DocFrame.md)) und Testsuite (`tests/tests_services/tests_doc_frame/`); `DocFrame` ist ausdrücklich als **Prototyp** markiert, der vor einer Stabilitätszusage noch systematisch evaluiert und gehärtet werden muss.
- **Dokumentations- & Entwicklerleitfäden ausgebaut:** Neuer Entwickler-Leitfaden [DEV-GUIDE_DocEnsurance.md](./docs/dev/services/DEV-GUIDE_DocEnsurance.md), Bereichs-Indizes [docs/README.md](./docs/README.md) und [docs/misc/README.md](./docs/misc/README.md), Statusdokument [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md) sowie [META_QUESTION.md](./META_QUESTION.md).

### Geändert
- **`DocEnsurance` in Subpaket strukturiert & um Dokument-Regeln (`check_document`) erweitert:** Service-Module nach `src/qb_cubie/services/doc_ensurance/` und zugehörige Tests nach `tests/tests_services/tests_doc_ensurance/` verschoben (Re-Exporte über `qb_cubie.services` bleiben erhalten); `DocEnsurance` unterstützt kombinierte `FramePattern`-/`CUBIE_DOCFRAME_RULES`-Prüfungen auf Dokumentebene.
- **Repository-Dokumentation & Styleguide-Prüfung aktualisiert:** Alle aktiven Markdown-Guides (`README.md`, `docs/`) mit `qb:frame`-Kopf- und Fußrahmen versehen; [GUIDE_Quality-Assurance.md](./docs/GUIDE_Quality-Assurance.md) und [GUIDE_Benchmarks.md](./docs/GUIDE_Benchmarks.md) überarbeitet; `test_docs_code_examples` in [tests/test_styleguide.py](./tests/test_styleguide.py) prüft im Standardlauf Codebeispiele und Dokumentrahmen gemeinsam.

## [0.0.6] - 2026-11-14

### Neu
- **Erweiterbares Regel-System (`DocRuleProtocol` & `CUBIE_DOC_RULES`) für `DocEnsurance`:**
  - Neue konfigurierbare Standardregeln in [doc_rules.py](./src/qb_cubie/services/doc_rules.py): `NoOutput`/`NoOutputRule` (`DOC-NO-OUTPUT`), `HighComplexity`/`HighComplexityRule` (`DOC-HIGH-COMPLEXITY`), `LargeOutput`/`LargeOutputRule` (`DOC-LARGE-OUTPUT`) und `RawTraceback`/`RawTracebackRule` (`DOC-RAW-TRACEBACK`) sowie das gebündelte Preset `CUBIE_DOC_RULES`.
  - Modulare Regel- und Pattern-Bausteine in [doc_patterns.py](./src/qb_cubie/services/doc_patterns.py): `ExplanationRule`, `CodeRule`, `DocLinterRule` (Adapter für `AstLinter`, `CstLinter`, `Pylint` und `MyPy`), `OutputRule`, `MissingOutputRule` (`DOC-OUT-MISSING`), `OutputMatchRule` (`DOC-OUT`) sowie `DEFAULT_DOC_RULES`.
  - `DocEnsurance` unterstützt den Parameter `rules` sowie `register_rule(*rules)` zur deterministischen Registrierung und Überschreibung anhand von `rule_id`; `DocDiagnostic` unterstützt `severity` (`"error"` oder `"warning"`, validiert via `validate_severity`/`VALID_SEVERITIES`).
- **Neues Qualitätssicherungs-Handbuch & Release-Leitfaden:** Neues Handbuch [GUIDE_Quality-Assurance.md](./docs/GUIDE_Quality-Assurance.md) (inklusive `expect=False`-Vertragsinversion) sowie verbindlicher Release-Ablauf in [DEV-GUIDE_Release-Preparation.md](./docs/dev/DEV-GUIDE_Release-Preparation.md).
- **Erweiterte Service-Testsuiten:** Neue Testmodule [test_doc_ensurance_arenas.py](./tests/tests_services/test_doc_ensurance_arenas.py), [test_doc_ensurance_rules.py](./tests/tests_services/test_doc_ensurance_rules.py), [test_doc_linter_feedback.py](./tests/tests_services/test_doc_linter_feedback.py), [test_doc_rule_edge_cases.py](./tests/tests_services/test_doc_rule_edge_cases.py) und [test_doc_rules.py](./tests/tests_services/test_doc_rules.py).

### Geändert
- **Core von Basis-Umgebungs-Provisionierung bereinigt:** `src/qb_cubie/arenas/arena_envs` entfernt; `PyVenv` und `ArenaBuilder` nutzen ohne expliziten Pfad nun `default_arena_path()` im Benutzer-Cache (`QB_CUBIE_DEFAULT_ARENA` bzw. `~/.cache/qb-cubie/arenas/py<major>.<minor>-empty`). `MANIFEST.in`, `pyproject.toml`, `scripts/provision_test_arenas.py`, `tests/conftest.py` und [GUIDE_Arena-Management.md](./docs/GUIDE_Arena-Management.md) entsprechend aktualisiert.
- **`DocEnsurance` modularisiert & Warnungs-Handling ergänzt:** Markdown-Scanning nach [\_markdown_scanner.py](./src/qb_cubie/services/_markdown_scanner.py) und Pattern-/Regelbausteine nach [doc_patterns.py](./src/qb_cubie/services/doc_patterns.py) ausgelagert; `PytestReporter` emittiert `"warning"`-Diagnosen als `UserWarning` ohne Testabbruch und schlägt nur bei `"error"`-Diagnosen fehl.
- **Core-Robustheitsfixes:** Gemeinsamer `normalize_fs`-Helper in [\_hydration.py](./src/qb_cubie/arenas/_hydration.py) für `EBT` und Arena-Hydratisierung mit `STATE-GUARD` gegen mehrdeutige Zielnamen; `AstLinter` ergänzt um `name` und `register_excludes(...)`; `MultiprocessManager` nutzt nach `PickleProcessor`-Fehlern oder bei nicht-pickelbaren Callables gezielt `LokyProcessor` als Fallback.
- **Dokumentations- & Styleguide-Prüfung verschärft:** `test_docs_code_examples` in [test_styleguide.py](./tests/test_styleguide.py) prüft alle Markdown-Guides zusätzlich mit `rules=CUBIE_DOC_RULES`; [GUIDE_DocEnsurance.md](./docs/services/GUIDE_DocEnsurance.md) und weitere Guides auf den neuen Regel- und Warnungsstand aktualisiert.

## [0.0.5] - 2026-11-14

### Neu
- **Konfigurierbares TTL-Timeout für `DocEnsurance`:** Neuer Keyword-Parameter `timeout: float | None = 10.0` inklusive `STATE-GUARD`-Validierung (`TypeError`/`ValueError` für `bool`, nicht-numerische Typen, `<= 0`, `inf` und `NaN`) und automatischer Übertragung auf unkonfigurierte Arenen unter Vorrang expliziter Arena-Timeouts.
- **Erweiterte `DocEnsurance`-Vertrags- & Isomorphie-Tests:** Neue EBT-Testsuiten [test_doc_ensurance_edge_cases.py](./tests/tests_services/test_doc_ensurance_edge_cases.py) (10 Äquivalenzklassen von Fence-Varianten über `SystemExit` bis `PyVenv`/`CloudpickleCodec`) und [test_doc_ensurance_isomorphism.py](./tests/tests_services/test_doc_ensurance_isomorphism.py) (kommutativer Isomorphie-Abgleich zwischen Markdown-Fences und Python-Docstring-Modulen) sowie TTL-Timeout-Tests in [test_doc_ensurance_configs.py](./tests/tests_services/test_doc_ensurance_configs.py).

### Geändert
- **`DocEnsurance`-Scanner & -Ausführung gehärtet:** Unterstützung von 4+-Backtick-, Tilde- (`~~~`) und eingerückten Fences ohne Beschädigung mehrzeiliger Strings, saubere Abgrenzung von Listen/Tabellen/Blockquotes gegen `Explanation`-Absätze, isolierte Behandlung ungeschlossener `<details>`-Blöcke, Wortgrenzen-Tag-Parsing (`session=`/`raises=`), MRO-Exception-Prüfung inklusive `SystemExit` und leerer Fehlermeldungen, Erhalt geteilter `TaggedScope`-Sessions bei nicht-fatalen Diagnosen (`DOC-POST`, `DOC-OUT`, `DOC-RAISE`), Filterung defekter Schritte in `IsolatedScope`, präzisierte Pfad-vs.-In-Memory-Heuristik, normalisierte `excludes`-Pfade und vollständiger Zustandsreset bei Instanz-Wiederverwendung.
- **Service-Dokumentation aktualisiert:** [GUIDE_DocEnsurance.md](./docs/services/GUIDE_DocEnsurance.md) um API-Quick-Lookup, Konfigurationsdetails (Pfad-Guards, Timeout-Vorrang, `PyVenv` mit `CloudpickleCodec`, `DocReport`) und das `timeout`-Beispiel erweitert.
- **Styleguide-Modulprüfung reaktiviert:** `test_module_size` in [test_styleguide.py](./tests/test_styleguide.py) wieder aktiviert (`MODULE_LIMIT = 777`).
- **Release-Workflow automatisiert:** `.github/workflows/release.yml` erstellt GitHub-Releases automatisiert aus den passenden `CHANGELOG.md`-Abschnitten und veröffentlicht die verifizierten Distributionen über Trusted Publishing auf PyPI.

## [0.0.4] - 2026-11-14

### Neu
- **Neues Paket `qb_cubie.services` mit `DocEnsurance`:** Strukturelle und ausführbare Verifikation von Markdown-Codebeispielen gegen definierte Patterns (`CUBIE_DOC_STYLE`, `ExamplePattern`, `Explanation`, `CodeSnippet`, `CollapsibleResult`, `TaggedScope`, `IsolatedScope`) inklusive geteilter Sessions (`session=<id>`) und erwarteter Exceptions (`raises=<Exception>`).
- **Service-Dokumentation:** Neuer Leitfaden [GUIDE_DocEnsurance.md](./docs/services/GUIDE_DocEnsurance.md) mit API-Referenz, Diagnosecodes (`DOC-PRE`, `DOC-POST`, `DOC-EXEC`, `DOC-RAISE`, `DOC-OUT`) und Erweiterungsprotokollen (`DocBlockProtocol`, `DocPatternProtocol`, `DocScopeProtocol`).
- **Testsuite-Profile & `Makefile`:** Schneller Dev-Standard (`-m 'not slow'`), Subsystem- und Geschwindigkeitsmarker in `pyproject.toml` und `tests/conftest.py`, lokales/CI-Hypothesis-Profil (`dev` vs. `ci`) sowie `Makefile`-Ziele und [tests/README.md](./tests/README.md).
- **Entwicklungs-Roadmap:** Neuer Planungsleitfaden [DEV-GUIDE_Next-Steps.md](./docs/dev/DEV-GUIDE_Next-Steps.md).

### Geändert
- **Benchmark-Paket ausgelagert:** `qb_cubie.benchmarks` wurde aus dem Core nach `experiments/benchmarks/cubie_benchmarks` (Importname `cubie_benchmarks`) verschoben; der CLI-Einstiegspunkt `cubie-bench` und das Extra `qb-cubie[benchmarks]` bleiben erhalten.
- **Dokumentationsprüfung vereinheitlicht:** `tests/test_readme_examples.py` wurde durch `DocEnsurance` in `tests/test_styleguide.py::test_docs_code_examples` abgelöst; historische `tests/docs_tmp/`-Matrizen wurden entfernt.
- **Arenen, Codecs & Reporter gehärtet:** Verbesserte Anforderungsprüfung und `PyVenv`-Provisionierung (`scripts/provision_test_arenas.py`), Codec-Robustheit (`CloudpickleCodec`, `MSGspecCodec`, `PickleCodec`) sowie sauberere `PytestReporter`-Ausgaben.
- **CI-Workflow:** Vollständiger Testlauf mit `pytest -m "" -q` (inklusive `slow` und `ci`-Hypothesis-Profil) sowie Dokumentation des Plattformstatus ([CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md)); Python 3.14-Classifier ergänzt.

## [0.0.3] - 2026-11-12

- Erste PyPI-Veröffentlichung von `qb-cubie` (EBT-Foundation, `WorldState`, RBT-Pipeline mit `HeadlessReviewer`, `TempFS`/`PyVenv`-Arenen, `AstLinter`/`CstLinter`, Audit-Fixes zu Abschnitt 9.1/9.2, Trusted Publishing und Testguided-Study-Artefakte).
