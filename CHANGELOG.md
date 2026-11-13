# Changelog

Alle nennenswerten Änderungen an `qb-cubie` werden in dieser Datei dokumentiert.

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
