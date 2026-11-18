<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="High" -->
# Meta-QA-Hypothese

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Hydrogen
- **Reasoning-Effort:** High
- **Analysedatum:** 18. November 2026, ~22:50 (CET)
- **Synthesebasis:** `tests/tests_ebt/GEMINI.md`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `META_QUESTION.md`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `src/qb_cubie/reporter.py`, `src/qb_cubie/multiprocessors.py`, `tests/conftest.py`, `tests/tests_meta/test_gate_1.py`, `tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `tests/tests_ebt/test_ebt_state_validation.py`, `tests/tests_ebt/test_ebt_return_reporting.py`, `tests/tests_ebt/test_ebt_quantors.py`, `docs/GUIDE_Contract-Semantics.md`, `pyproject.toml`
- **Stand**: qb-cubie (v0.0.7)
- **Git-Log**: `253da1ed745faa05e42ebebc14f222a420edbdeb`

```text
commit 253da1ed745faa05e42ebebc14f222a420edbdeb (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Wed Nov 18 22:18:38 2026 +0100

    build the new test-module for the quantor-declarations.
```

---

---

<!-- /qb:frame -->

# Meta-QA-Hypothese zur Qualität von `tests/tests_ebt/test_ebt_quantor_declaration.py`

## Ausgangslage & empirischer Befund

Das Modul [`tests/tests_ebt/test_ebt_quantor_declaration.py`](./test_ebt_quantor_declaration.py) (491 Zeilen, 15 Testfunktionen, 33 parametrisierte Testfälle in den Gruppen A–E) befindet sich auf `HEAD` (`253da1ed`) im **TGD-Red-Zustand**:

- In [`src/qb_cubie/protocols.py`](../../src/qb_cubie/protocols.py#L125) sind `Quantor = Literal["all", "exists"]` sowie `RunTrace.pre_quantor = "all"` und `RunTrace.post_quantor = "exists"` bereits angelegt, und [`JsonReporter._document`](../../src/qb_cubie/reporter.py#L258-L265) serialisiert beide Felder.
- In [`src/qb_cubie/ebt.py`](../../src/qb_cubie/ebt.py) ist das Quantor-Wrapper-Feature jedoch noch nicht umgesetzt: `_ensure_list` / `_validate_states` (Z. 524–546) weisen jedes `dict` mit `TypeError("STATE-GUARD: ... must be a WorldState, a list of WorldStates or None; received dict.")` ab, `_evaluate_run` (Z. 302) verdrahtet `all(successes)` fest und `_evaluate_step_logic` (Z. 648) verdrahtet `any(t.evaluation for t in positives)` fest.
- Entsprechend schlagen bei `pytest tests/tests_ebt/test_ebt_quantor_declaration.py -v` **alle 33 Fälle** fehl (`33 failed in 0.34s`), während das übrige `tests/tests_ebt/`-Paket ohne diese Datei mit `430 passed, 1 deselected` grün läuft.

---

## Haupthypothese

> **Haupthypothese:** Obwohl [`tests/tests_ebt/test_ebt_quantor_declaration.py`](./test_ebt_quantor_declaration.py) alle fünf Spezifikationsgruppen (Baseline-Parität, `pre`-Quantoren, `post`-Quantoren, Kreuzkombinationen, `STATE-GUARD`s) formal adressiert, **erreicht das Modul im Sinne der Meta-QA-Kriterien aus [`META_QUESTION.md`](../../META_QUESTION.md) noch nicht die nötige logische Trennschärfe und Verifikationsdichte**: Mehrere Verträge sind gegen naheliegende Implementierungs-Mutanten immun (bis hin zum Rückfall auf die alte Standard-Semantik), ein behaupteter Ausführungsabbruch wird gar nicht gemessen, zentrale Laufzeitpfade (`PytestReporter`, `JsonReporter`, `multiprocessing=True`, Revalidierung nach Mutation) bleiben ungeprüft, das `EBT-in-EBT`-Adapter-Muster maskiert Fehlerdiagnosen und das neue Dict-Wrapper-Format unterläuft die statische Prüfung der bestehenden Meta-Gates 2 und 3.

---

## Überprüfbare Teil-Hypothesen

### H1 — Mutanten-Immunität bei `pre="exists" × post="all"` (`test_inverted_quantors_pre_exists_post_all`)

- **Befund:** In [`test_inverted_quantors_pre_exists_post_all`](./test_ebt_quantor_declaration.py#L322-L350) enthält `pre_cfg` die Eingänge `"  other "` (`pre[0]`) und `"  Cubie  "` (`pre[1]`), während `post_cfg` die drei Prädikate `[str, val == "cubie", len(val) == 5]` fordert. Für `"other"` sind bereits `post[0]` (`str`) und `post[2]` (`len("other") == 5`) wahr; für `"cubie"` sind alle drei wahr.
- **Konsequenz:** Würde eine fehlerhafte `EBT`-Implementierung die Quantoren-Auswertung komplett ignorieren (also weiterhin `pre="all"` mit `post="exists"` berechnen) und lediglich die Metadaten `pre_quantor="exists"` sowie `post_quantor="all"` in `RunTrace` eintragen, bestünde der Test **trotzdem grün**, weil `"other"` `post="exists"` erfüllt und damit auch `all(pre)` wahr wäre. Zudem fehlt ein **negativer Gegen-Test** für $\exists p \forall q$ mit verteilter Erfüllung (*Split Satisfaction*: `pre[0]` erfüllt nur `post[0]`, `pre[1]` erfüllt nur `post[1]`), bei dem $\exists p \forall q$ scheitern muss, $\forall p \exists q$ jedoch fälschlich bestehen würde.
- **Überprüfbares Kriterium:** Gegen einen Stub-Mutanten in `EBT`, der `pre_quantor`/`post_quantor` im `RunTrace` speichert, aber die Auswertung unverändert auf `all(successes)` und `any(positives)` belässt, liefert `test_inverted_quantors_pre_exists_post_all` ein **False Positive (`PASSED`)**.

---

### H2 — Unverifizierte Abbruch- und Schritt-Exaktheits-Behauptung in `test_pre_quantor_all_aborts_on_first_failure`

- **Befund:** Der Docstring von [`test_pre_quantor_all_aborts_on_first_failure`](./test_ebt_quantor_declaration.py#L158-L186) behauptet: *„`pre` mit `quantor='all'` bricht beim ersten Fehlschlag ab und meldet exakt diesen Schritt.“* Tatsächlich prüft [`_eval_failure_step_adapter`](./test_ebt_quantor_declaration.py#L64-L89) in der Assertion (Z. 169–175) ausschließlich `res["expected_step_id"] in res["failed_step_ids"]` und `f"for step '{trace.run_id}_1':" in report_msg`.
- **Konsequenz:**
  1. Es wird **weder** geprüft, ob `pre[2]` (`/health`) nach dem Fehlschlag von `pre[1]` (`/broken`) tatsächlich nicht mehr ausgeführt wird (weder über einen Aufrufzähler auf dem Target noch über `trace_count == 2`), **noch** wird `failed_step_ids == [expected_step_id]` (genau ein fehlgeschlagener Schritt) geprüft.
  2. Ein Abgleich mit [`EBT._validate_singleprocess`](../../src/qb_cubie/ebt.py#L216-L224) zeigt zudem, dass `EBT` aktuell **alle** `pre`-Zustände ausführt, bevor `_evaluate_run()` oder [`PytestReporter._generate_report`](../../src/qb_cubie/reporter.py#L91) läuft (`next((sid for sid, tr in steps.items() if not ...))` wählt lediglich den ersten fehlgeschlagenen Schritt für den Bericht). Ein echtes Short-Circuiting steht außerdem im Spannungsfeld zu `multiprocessing=True`.
- **Überprüfbares Kriterium:** Ein Mutant ohne vorzeitigen Abbruch (alle 3 Schritte ausgeführt, `trace_count == 3`) – und sogar ein Mutant, bei dem zusätzlich `pre[2]` fehlschlägt (`len(failed_step_ids) == 2`) – besteht `test_pre_quantor_all_aborts_on_first_failure` ohne Beanstandung.

---

### H3 — Fehlende Trennschärfe bei `post="all"` + `expect=False`, Positions-Blindheit und Redundanz

- **Befund A (Fehlende Unterscheidungskraft in `test_post_quantor_all_with_negative_worldstate_expect_false`):** In [`test_post_quantor_all_with_negative_worldstate_expect_false`](./test_ebt_quantor_declaration.py#L353-L381) enthält `post_cfg` genau **einen** positiven Zustand (`WorldState(returns=int)`) und genau **einen** negativen Zustand (`WorldState(returns=-1, expect=False)`). Bei jeweils einem Element fallen `all` und `any` sowohl auf `positives` als auch auf `negatives` zusammen. Der Test erkennt daher weder einen Rückfall von `post="all"` auf `any(positives)` (bei vorhandenem Negativ-Filter) noch den umgekehrten Implementierungsfehler, `post="all"` versehentlich auch auf `negatives` anzuwenden (`all(t.evaluation for t in negatives)` statt `any(...)`, wodurch mehrere disjunkte Verbote wie `-1` und `-2` wirkungslos würden).
- **Befund B (Positions-Blindheit & Duplikation bei Fehlschlägen in `post="all"`):** [`test_post_quantor_all_fails_if_single_predicate_violated`](./test_ebt_quantor_declaration.py#L288-L316) (Prüfung an Index `2`, letztes Element scheitert) und [`test_double_negation_guard_with_explicit_quantor`](./test_ebt_quantor_declaration.py#L384-L404) (Prüfung an Index `1`, letztes Element scheitert) prüfen strukturell denselben Grenzfall (letztes Prädikat verletzt bei `EBT(..., expect=False)`). Ein Fall, in dem `post[0]` oder ein mittleres Prädikat scheitert, fehlt komplett – ein Mutant, der nur `traces[-1]` auswertet, bleibt unerkannt.
- **Befund C (Zu weiche Kardinalitäts-Schranke in `test_post_quantor_exists_passes_on_partial_match`):** Zeile 250 prüft `1 <= res["trace_count"] <= 3`, obwohl der passende Zustand (`returns=10`) an Index `1` steht; damit bliebe selbst ein Bug unbemerkt, der `post[0]` unterschlägt und nur `1` Trace erzeugt.
- **Überprüfbares Kriterium:** Ein Mutant, der bei `post="all"` nur `traces[-1]` prüft oder `all(negatives)` statt `any(negatives)` verwendet, besteht alle Tests der Gruppen C und D. Erst ≥2 positive und ≥2 negative `WorldState`-Einträge sowie Fehlschläge an Index `0` und `-1` schließen diese Lücke.

---

### H4 — Lücken bei `STATE-GUARD`s, Reporter-Diagnosen, Multiprocessing und Revalidierung

- **Befund A (`STATE-GUARD`-Lücken in Gruppe E):**
  - [`test_guard_rejects_empty_states_collection`](./test_ebt_quantor_declaration.py#L453-L470) deckt nur `("pre", "exists")` und `("post", "all")` ab, nicht aber `("pre", "all")` und `("post", "exists")`.
  - Ungetestet bleiben: fehlender `"quantor"`-Schlüssel (`{"states": [WorldState()]}`), leeres Dict `{}`, unbekannte Zusatz-Schlüssel im Wrapper, ungültige `states`-Typen im Wrapper (`None`, `int`, `(WorldState(),)`, `[None]`), Case-/Whitespace-Varianten (`"ALL"`, `" exists "`), Default-Reporter-Propagation (`reporter=PytestReporter()`) sowie die Revalidierung nach Mutation von `case.pre`/`case.post` zwischen zwei `.run()`-Aufrufen (analog zu [`test_ebt_state_validation.py`](../tests_ebt/test_ebt_state_validation.py#L84-L107)).
  - Minor-Benennungsfehler in Zeile 475: `test_guard_rejects_non_bool_or_invalid_quantor_type` lehnt `[None, True, 1]` ab (gemeint ist `non_str_or_bool_quantor_type`, da `bool` gerade abgewiesen wird).
- **Befund B (Fehlende Abdeckung von `PytestReporter`, `JsonReporter` und `multiprocessing=True`):**
  - Außer einem einzelnen Substring-Check in `_eval_failure_step_adapter` (Z. 77) gibt es **keinen** Reporter-Test für fehlgeschlagenes `pre="exists"` (alle Schritte gescheitert -> welche Meldung erzeugt `PytestReporter._generate_report`?) oder fehlgeschlagenes `post="all"` (welcher `Q-State` ist `Mismatch`?).
  - Ebenso existieren weder Tests mit `JsonReporter` (Persistierung von `pre_quantor` / `post_quantor`) noch Tests mit `multiprocessing=True` (Transport und Aggregation über `MultiprocessManager`).
- **Überprüfbares Kriterium:** Eine Teil-Implementierung, die Quantoren nur in `_configure_states` (ohne Revalidierung in `_arrange`), nur in `_validate_singleprocess` (ohne `_validate_multiprocess`) oder ohne angepasste `PytestReporter`-Fehlerausgabe für `pre="exists"` umsetzt, bleibt gegen dieses Test-Modul grün.

---

### H5 — Blinde Flecken der Meta-Gates 2 und 3 gegenüber dem neuen Dict-Wrapper-Format

- **Befund:** Die statischen CST-Regeln der Repository-Gates in [`tests/tests_meta/test_gate_2.py`](../tests_meta/test_gate_2.py#L91-L104) (`EbtCrossProductRule`) und [`tests/tests_meta/test_gate_3.py`](../tests_meta/test_gate_3.py#L77-L94) (`EbtLonelyNegationRule`) inspizieren ausschließlich `cst.List`, `cst.Tuple` und direkte `WorldState(...)`-Aufrufe:
  - In Gate 2 liefert `_count_pre_states` und `_count_positive_post_states` für jedes `cst.Dict` pauschal `1`.
  - In Gate 3 liefert `_extract_post_worldstates` für ein `cst.Dict` pauschal `None`.
- **Konsequenz:**
  1. Ein echtes unkommentiertes Kreuzprodukt im neuen Format (`pre={"quantor": "all", "states": [p1, p2]}`, `post={"quantor": "exists", "states": [q1, q2]}`) sowie eine einsame Negation im Wrapper (`post={"quantor": "all", "states": [WorldState(returns=99, expect=False)]}`) **unterlaufen beide Meta-Gates spurlos**.
  2. Umgekehrt setzt [`test_inverted_quantors_pre_exists_post_all`](./test_ebt_quantor_declaration.py#L340) einen `meta:cross-product-reason`-Tag, obwohl bei `pre="exists" × post="all"` logisch keine disjunktive Kreuzprodukt-Abschwächung vorliegt.
- **Überprüfbares Kriterium:** `pytest tests/tests_meta/ -v` läuft aktuell mit `78 passed` durch, meldet aber bei synthetischen CST-Sonden mit Dict-Wrapper-Kreuzprodukten oder Dict-Wrapper-Lonely-Negations fälschlich `0` Diagnostics.

---

### H6 — Diagnosemaskierung durch `EBT-in-EBT`-Adapter sowie offene Linter- & Collection-Hygiene

- **Befund A (Verlust von Stacktrace und Diff-Lesbarkeit durch `_eval_contract_adapter`):** Nahezu alle Tests kapseln den eigentlichen `EBT`-Aufruf in `_eval_contract_adapter` (Z. 44–61) und prüfen das Ergebnis über `outer = EBT(..., post=WorldState(returns=lambda res: ...), reporter=None)` + `assert outer is not None and outer.evaluation is True`. Im Fehlerfall fängt `_eval_contract_adapter` `(ValueError, TypeError)` ab (wodurch der ursprüngliche Traceback verloren geht), während das äußere `EBT` wegen `reporter=None` und anonymer `lambda res:`-Prädikate lediglich eine einzeilige `RunTrace`-Dump-Meldung mit `'<function ...<lambda> at 0x...>'` erzeugt.
- **Befund B (Collection-Vertrag & Linter-Befunde):**
  - Gemäß [`tests/conftest.py`](../conftest.py#L15-L83) erben alle Tests unter `tests/tests_ebt/` automatisch `ebt` und ohne expliziten Marker den Speed-Marker `fast`. Da `test_ebt_quantor_declaration.py` ohne `xfail` auf `main` eingecheckt wurde, bricht der Standard-Dev-Lauf (`addopts = "--strict-markers -m 'not slow'"` in [`pyproject.toml`](../../pyproject.toml#L71)) derzeit mit **33 Fehlern**.
  - `.venv/bin/ruff check tests/tests_ebt/test_ebt_quantor_declaration.py` scheitert mit **1 Fehler** (`I001`: überflüssige Leerzeile im Import-Block vor Zeile 12).
  - `.venv/bin/pylint tests/tests_ebt/test_ebt_quantor_declaration.py` bewertet das Modul mit **`8.86/10`** wegen **13× `C0301`** (Zeilenlänge `> 100`, u. a. Z. 13, 41, 49, 101, 130, 155, 162, 181, 213, 236, 319, 340, 407).
  - `MYPYPATH=src .venv/bin/mypy tests/tests_ebt/test_ebt_quantor_declaration.py` besteht fehlerfrei (`Success: no issues found in 1 source file`).
- **Überprüfbares Kriterium:** Reproduzierbar über `pytest`, `ruff check` und `pylint` auf `HEAD` (`253da1ed`); das Beheben der Import-Leerzeile und der 13 überlangen Zeilen hebt `ruff` auf `0 errors` und `pylint` auf `10.00/10`.

---

## Priorisierte Empfehlungen vor/mit der Core-Implementierung

1. **Testschärfe vor Implementierung härten (gegen H1–H3):**
   - In `test_inverted_quantors_pre_exists_post_all` einen Negativ-Test für Split-Satisfaction (`pre[0]` erfüllt nur `post[0]`, `pre[1]` nur `post[1]`) ergänzen und den Positiv-Test so bauen, dass `pre[0]` *keinen* `post`-Zustand erfüllt (so fällt `all(pre) / any(post)` sofort durch).
   - In `test_pre_quantor_all_aborts_on_first_failure` klären und explizit asserten, ob `EBT` tatsächlich nach Fehlschlag abbricht (Aufrufzähler / `trace_count == 2`) oder lediglich den ersten Fehler meldet (`failed_step_ids == [expected_step_id]`).
   - Für `post="all"` mit `expect=False` mindestens 2 positive + 2 negative Zustände testen sowie Fehlschläge an Index `0` und `-1` abdecken; `test_double_negation_guard_with_explicit_quantor` mit letzterem zusammenführen oder auf einen anderen Fehlerpfad (z. B. `raises`) fokussieren.
2. **Guard-, Reporter- und Multiprocessing-Matrix vervollständigen (gegen H4, H6-A):**
   - Gruppe E um `("pre", "all")` / `("post", "exists")` mit `states=[]`, fehlenden `"quantor"`-Key, leeres `{}`, Zusatz-Keys, ungültige `states`-Container, Case/Whitespace, Mutation + Re-Run sowie direkte `pytest.raises(...)`-Prüfungen mit Default-Reporter ergänzen; mindestens einen `PytestReporter`-, `JsonReporter`- und `multiprocessing=True`-Test aufnehmen.
3. **Meta-Gates & Hygiene nachziehen (gegen H5, H6-B):**
   - `EbtCrossProductRule` (`test_gate_2.py`) und `EbtLonelyNegationRule` (`test_gate_3.py`) auf Dict-Wrapper `{"quantor": ..., "states": ...}` erweitern (wobei bei `post={"quantor": "all", ...}` die positive Konjunktion semantisch kein disjunktives Kreuzprodukt bildet, sofern `pre` ebenfalls eingeordnet wird).
   - `I001` und die 13× `C0301`-Zeilen bereinigen und den Red-Phase-Status bis zur Core-Implementierung sauber markieren (z. B. `pytest.mark.xfail(..., strict=True)`), damit die Default-Suite auf `main` nicht dauerrot bleibt.
