<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Argon" effort="High" -->
# Analysis: Reperatur vom Cubie-Core

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 21:25 (CET)
- **Synthesebasis:** `tests/ANALYSIS.md`, `tests/HYPOTHESIS.md`, `tests/GEMINI-2.md`, `tests/GEMINI-1.md`, `META_QUESTION.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_Contract-Semantics.md`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `tests/conftest.py`, `tests/test_lint.py`, `tests/test_styleguide.py`, `tests/test_offline_core.py`, `tests/tests_arena/test_ebt_arena_mutation.py`, `tests/tests_meta/test_gate_1.py`, `tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `tests/tests_ebt/test_ebt_quantors.py`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `tests/tests_ebt/test_ebt_args_normalization.py`, `tests/tests_ebt/test_ebt_returns.py`, `tests/tests_ebt/test_ebt_return_reporting.py`, `tests/tests_ebt/test_ebt_exception_contracts.py`, `tests/tests_ebt/test_ebt_run_isolation.py`, `tests/tests_ebt/test_ebt_contract_mutation.py`, `tests/tests_ebt/test_ebt_persistent_reports.py`
- **Stand**: qb-cubie (v0.0.8)
- **Git-Log**:

```text
commit db96ea4b404c7b462e350f9e0bc5b8335c4f4d82 (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 19 20:33:16 2026 +0100

    Found a critical bug. Analysed it. Gotta think about it.
```

---

---

<!-- /qb:frame -->

# Operationsfähiges Arbeitspaket: Reparatur & Härtung der Test-Suite (`qb-cubie`, TGD Red-Phase)

## 1. Auftrag, Architektur-Grundsatz & TGD-Phasengrenze

### 1.1 Verbindliches Architektur-Ziel (Option A aus `ANALYSIS.md` & `HYPOTHESIS.md`)

Die Test-Suite von `qb-cubie` wird so umgebaut und gehärtet, dass `WorldState(..., expect=False)` niemals mehr heimlich das Standard-Existenzquantor-Verhalten (`post="exists"`) überschreibt:

1. **Reine Standard-Quantoren:**
   - `EBT.pre` arbeitet standardmäßig als **reiner Allquantor (`"all"`, logisches UND)**.
   - `EBT.post` arbeitet standardmäßig als **reiner Existenzquantor (`"exists"`, logisches ODER)**.
2. **Explizite Konjunktion statt verdecktem `AND`-Veto:**
   - Lokale Ausschlüsse über `WorldState(..., expect=False)` sind prädikatenlogisch einschränkende Bedingungen ($\neg m(q, y)$) und dürfen ausschließlich unter einem **explizit deklarierten Allquantor** (`post={"quantor": "all", "states": [...]}`) verwendet werden.
   - Unter `post="exists"` (`OR`) führt ein `WorldState(..., expect=False)` zu prädikatenlogischen Tautologien (z. B. $(y \in \mathbb{Z}) \lor (y \neq 99) \equiv \top$ für alle $y$) oder zum Verschlucken des Positiv-Ziels (z. B. $(y = 3) \lor (y \neq 99) \equiv (y \neq 99)$) und muss daher durch einen **`STATE-GUARD`** (`ValueError`) vor der Ausführung abgewiesen werden.
3. **Weitere Core-Invarianten, die durch neue Tests erzwungen werden:**
   - `WorldState(..., expect=False)` in `pre` ist unzulässig und wird vor der Ausführung mit `ValueError("STATE-GUARD: ...")` abgewiesen.
   - `WorldState.expect` und `EBT.expect` akzeptieren strikt nur `bool` (`True`/`False`); jeder Nicht-`bool`-Wert (inklusive `None`, `1`, `0`, `"true"`, `[]`) wird mit `TypeError("STATE-GUARD: ...")` abgewiesen.
   - `evaluate_step_logic(traces, post_quantor)` in `src/qb_cubie/protocols.py` wertet den deklarierten `post_quantor` einheitlich ohne $Q^+/Q^-$-Partitionierung und ohne Vacuous-True (`if not positives: satisfies_pos = True`) aus.
   - **Sticky-Quantor-Invariante:** Ein wiederverwendetes `EBT`-Objekt behält seinen explizit deklarierten Quantor (`pre="exists"` bzw. `post="all"`) über wiederholte `.run()`-Aufrufe ohne Neuzuweisung sowie bei In-Place-Listenmutationen bei, setzt ihn jedoch bei jeder Attribut-Neuzuweisung ohne Dict-Wrapper (`case.pre = ...` bzw. `case.post = ...` mit Liste, Einzel-`WorldState` oder `None`) deterministisch auf den jeweiligen Standard-Quantor (`pre_quantor="all"`, `post_quantor="exists"`) zurück.

### 1.2 Strikte Scope-Abgrenzung (TGD Red-Phase)

- **Ausschließlich `tests/` bearbeiten:** In diesem Arbeitspaket werden exakt **12 Dateien unter `tests/`** modifiziert.
- **`src/qb_cubie/` und `docs/` bleiben in diesem Schritt unverändert:**
  - Alle **migrierten Bestands-Tests (AP 1)** und **aktualisierten Meta-Gates (AP 2)** müssen bereits gegen den aktuellen Core (`v0.0.8`) zu **100 % grün (`PASSED`)** laufen.
  - Die **5 neuen Guard- und Lifecycle-Tests in `tests/tests_ebt/test_ebt_quantor_declaration.py` (AP 3)** müssen gegen den noch ungehärteten Core (`v0.0.8`) deterministisch **rot fehlschlagen (`FAILED`)** (= kontrollierter TGD Red-Phase-Nachweis) und in der anschließenden Core-Reparatur (TGD Green-Phase) ohne weitere Änderung am Testcode auf **grün (`PASSED`)** springen.

### 1.3 Übersicht aller 12 zu bearbeitenden Dateien

| Arbeitspaket | Zieldatei | Art der Änderung | Erwarteter Status in TGD Red-Phase (`v0.0.8`) |
| :---: | :--- | :--- | :---: |
| **AP 1.1** | `tests/tests_ebt/test_ebt_quantors.py` | Migration von 7 Tests (7 `EBT`-Aufrufe) auf `post={"quantor": "all", ...}` + Beseitigung der Subsumtion in Z. 113–158 & Harmonisierung Z. 214 + Import-Sortierung (`I001`) | **100 % PASSED** |
| **AP 1.2** | `tests/tests_ebt/test_ebt_returns.py` | Migration von 2 Tests (**3 `EBT`-Aufrufe**, inkl. `inverted`) in Z. 87–123 auf `post={"quantor": "all", ...}` | **100 % PASSED** |
| **AP 1.3** | `tests/tests_ebt/test_ebt_exception_contracts.py` | Migration von 2 Tests (**3 `EBT`-Aufrufe**, inkl. `inverted`) in Z. 76–111 auf `post={"quantor": "all", ...}` | **100 % PASSED** |
| **AP 1.4** | `tests/tests_ebt/test_ebt_return_reporting.py` | Migration von 4 Tests (4 `EBT`-Aufrufe) in Z. 76–126 auf `post={"quantor": "all", ...}` | **100 % PASSED** |
| **AP 1.5** | `tests/tests_ebt/test_ebt_run_isolation.py` | Migration von 2 Tests (2 `EBT`-Aufrufe) in Z. 41–57 auf `post={"quantor": "all", ...}` | **100 % PASSED** |
| **AP 1.6** | `tests/tests_ebt/test_ebt_contract_mutation.py` | Migration von 1 parametrisiertem Test (1 `EBT`-Aufruf) in Z. 14–45 auf `post={"quantor": "all", "states": post}` | **100 % PASSED** |
| **AP 1.7** | `tests/tests_ebt/test_ebt_persistent_reports.py` | Migration von 1 Test (1 `EBT`-Aufruf) in Z. 136–150 auf `post={"quantor": "all", ...}` | **100 % PASSED** |
| **AP 1.8** | `tests/test_offline_core.py` | Migration des `feature == "ebt"`-Smoke-Tests (1 `EBT`-Aufruf) in Z. 160–166 auf `post={"quantor": "all", ...}` unter Erhalt der $2 \times 2$-Trace-Matrix | **100 % PASSED** |
| **AP 1.9** | `tests/tests_arena/test_ebt_arena_mutation.py` | Migration von 1 Test (1 `EBT`-Aufruf) in Z. 99–112 auf `post={"quantor": "all", ...}` + Import-Sortierung (`I001`) | **100 % PASSED** |
| **AP 2.1** | `tests/tests_meta/test_gate_2.py` | Dict-Wrapper-Unterstützung in `_count_pre_states` / `_count_positive_post_states` + Update der Clean-Probes (Z. 167–168) + neue Kalibrierungs-Probes | **100 % PASSED** |
| **AP 2.2** | `tests/tests_meta/test_gate_3.py` | Dict-Wrapper-Unterstützung in `_extract_post_worldstates` + Umstellung aller 10 Clean-Probes mit statischem `expect=False` + neue Dict-Fault-Probes | **100 % PASSED** |
| **AP 3** | `tests/tests_ebt/test_ebt_quantor_declaration.py` | Ergänzung von **5 neuen Red-Phase-Testfunktionen** in Gruppe E (`STATE-GUARD`s, `evaluate_step_logic`-Reinheit, Sticky-Quantor-Lebenszyklus) | Bestehende Tests **PASSED**, 5 neue Tests **FAILED (Red)** |

*(Hinweis: `tests/tests_ebt/test_ebt_args_normalization.py:338-381` und die bestehenden Tests in `tests/tests_ebt/test_ebt_quantor_declaration.py:387-434` nutzen bereits `post={"quantor": "all", ...}` und bleiben unverändert.)*

---

## 2. Arbeitspaket 1 (AP 1): Migration der 9 bestehenden Testdateien (21 Testfunktionen, 23 `EBT`-Aufrufe)

> [!IMPORTANT]
> **Verbindliche Meta-QA-Regeln für AP 1 (aus `HYPOTHESIS.md`):**
> 1. **Keine Abschwächung von Assertions:** Alle bestehenden `assert`-Anweisungen auf `result.evaluation`, `trace.evaluation`, `len(trace.traces)`, `diffs` und Report-Inhalte bleiben unangetastet.
> 2. **Keine fehlerhaften Kurz-Alternativen:** Verwende ausschließlich die unten spezifizierten `post={"quantor": "all", "states": ...}`-Konstrukte (insbesondere **nicht** `post=WorldState(returns=3)` in `test_offline_core.py` und **nicht** `EBT(..., expect=False)` ohne `WorldState(expect=False)` in `test_ebt_contract_mutation.py` oder `test_ebt_arena_mutation.py`).
> 3. **Beide `EBT`-Aufrufe migrieren:** In `test_negative_none_contract_rejects_none` (`test_ebt_returns.py`) und `test_forbidden_exception_rejects_matching_exception_message` (`test_ebt_exception_contracts.py`) müssen jeweils **beide** `EBT`-Instanziierungen (`result` und `inverted`) umgestellt werden.

---

### AP 1.1: `tests/tests_ebt/test_ebt_quantors.py`

#### 1. Import-Block (Zeilen 1–3) — Ruff `I001` bereinigen
Ersetze Zeilen 1–3:
```python
from qb_cubie.ebt import EBT
from qb_cubie.protocols import WorldState
import pytest
```
durch:
```python
from qb_cubie.ebt import EBT
from qb_cubie.protocols import WorldState
```
*(Hinweis: `pytest` wird in `test_ebt_quantors.py` nirgends verwendet; falls gewünscht oder benötigt, standardkonform vor `from qb_cubie...` sortieren — das Entfernen des ungenutzten Imports behebt gleichzeitig `F401` und `I001`.)*

#### 2. Abschnitt `MIXED QUANTOR INVERTIONS` (Zeilen 113–158) — Subsumtion beseitigen & explizites `"quantor": "all"` nutzen
Ersetze die drei Funktionen `test_mixed_expect_exists_green`, `test_mixed_expect_exists_red_lower_bound` und `test_mixed_expect_exists_red_upper_bound` (Zeilen 113–158) durch:
```python
def test_mixed_expect_exists_green():
    """Verifies: Output = 3 (allowed). It yields a positive match and does not violate any negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(3,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=lambda v: 0 <= v <= 6),
                WorldState(returns=0, expect=False),
                WorldState(returns=6, expect=False),
            ],
        },
    ).run()

def test_mixed_expect_exists_red_lower_bound():
    """Verifies: Output = 0. Although it matches a declaration, it violates the strict negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(0,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=lambda v: 0 <= v <= 6),
                WorldState(returns=0, expect=False),
                WorldState(returns=6, expect=False),
            ],
        },
        expect=False,
    ).run()

def test_mixed_expect_exists_red_upper_bound():
    """Verifies: Output = 6. Violates the upper negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(6,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=lambda v: 0 <= v <= 6),
                WorldState(returns=0, expect=False),
                WorldState(returns=6, expect=False),
            ],
        },
        expect=False,
    ).run()
```

#### 3. Abschnitte `LOCAL EXPECT` & `NEGATIVE FILTERS` (Zeilen 181–232) — Explizites `"quantor": "all"` & identisches Bereichsprädikat
Ersetze die vier Funktionen `test_local_expect_false_green`, `test_local_expect_false_red`, `test_negative_filters_green` und `test_negative_filters_red` (Zeilen 181–232) durch:
```python
def test_local_expect_false_green():
    """Verifies: Local expect=False allows a matching positive state when the forbidden value is absent."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(1,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=int),
                WorldState(returns=99, expect=False),
            ],
        },
    ).run()


def test_local_expect_false_red():
    """Verifies: If the forbidden state occurs despite a positive type match, the test fails."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(99,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=int),
                WorldState(returns=99, expect=False),
            ],
        },
        expect=False,
    ).run()


# ========== NEGATIVE FILTERS ==========================================================================================

def test_negative_filters_green():
    """Verifies: Negative filters pass when a positive contract matches and no forbidden state occurs."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(200,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=lambda status: 200 <= status < 600),
                WorldState(returns=404, expect=False),
                WorldState(returns=500, expect=False),
            ],
        },
    ).run()


def test_negative_filters_red():
    """Verifies: Even when a positive range matches, hitting any negative filter fails the test."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(404,)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=lambda status: 200 <= status < 600),
                WorldState(returns=404, expect=False),
                WorldState(returns=500, expect=False),
            ],
        },
        expect=False,
    ).run()
```

---

### AP 1.2: `tests/tests_ebt/test_ebt_returns.py` (Zeilen 87–123)

Stelle in `test_negative_none_contract_accepts_non_none_values` und `test_negative_none_contract_rejects_none` **alle drei `EBT`-Aufrufe** auf `post={"quantor": "all", "states": [...]}` um:
```python
@pytest.mark.parametrize("actual", [42, 0, False])
def test_negative_none_contract_accepts_non_none_values(actual):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=None, expect=False)],
        },
        reporter=None,
    ).run()

    assert len(result.traces) == 2
    assert [trace.evaluation for trace in result.traces] == [True, False]
    assert result.evaluation is True


def test_negative_none_contract_rejects_none():
    post = {
        "quantor": "all",
        "states": [WorldState(returns=int), WorldState(returns=None, expect=False)],
    }
    result = EBT(
        target=echo,
        pre=WorldState(args=(None,)),
        post=post,
        reporter=None,
    ).run()

    assert len(result.traces) == 2
    # A matching negative post-state makes the overall contract fail.
    assert [trace.evaluation for trace in result.traces] == [False, True]
    assert result.evaluation is False

    inverted = EBT(
        target=echo,
        pre=WorldState(args=(None,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=None, expect=False)],
        },
        expect=False,
        reporter=None,
    ).run()
    assert inverted.evaluation is True
```

---

### AP 1.3: `tests/tests_ebt/test_ebt_exception_contracts.py` (Zeilen 76–111)

Stelle in `test_forbidden_exception_accepts_allowed_exception_message` und `test_forbidden_exception_rejects_matching_exception_message` **alle drei `EBT`-Aufrufe** auf `post={"quantor": "all", "states": [...]}` um:
```python
def test_forbidden_exception_accepts_allowed_exception_message(arena):
    result = EBT(
        target=operation, arena=arena, pre=WorldState(args=("wrong-message",)),
        post={
            "quantor": "all",
            "states": [
                WorldState(raises=expectation(ValueError)),
                WorldState(raises=expectation(match="^invalid order:"), expect=False),
            ],
        },
        reporter=None,
    ).run()
    assert [trace.evaluation for trace in result.traces] == [True, False]
    assert result.evaluation is True


def test_forbidden_exception_rejects_matching_exception_message(arena):
    result = EBT(
        target=operation, arena=arena, pre=WorldState(args=("value-error",)),
        post={
            "quantor": "all",
            "states": [
                WorldState(raises=expectation(ValueError)),
                WorldState(raises=expectation(match="^invalid order:"), expect=False),
            ],
        },
        reporter=None,
    ).run()
    assert [trace.evaluation for trace in result.traces] == [True, True]
    assert result.evaluation is False

    inverted = EBT(
        target=operation, arena=arena, pre=WorldState(args=("value-error",)),
        post={
            "quantor": "all",
            "states": [
                WorldState(raises=expectation(ValueError)),
                WorldState(raises=expectation(match="^invalid order:"), expect=False),
            ],
        },
        expect=False,
        reporter=None,
    ).run()
    assert inverted.evaluation is True
```

---

### AP 1.4: `tests/tests_ebt/test_ebt_return_reporting.py` (Zeilen 76–126)

Stelle die vier Testfunktionen in Zeilen 76–126 auf `post={"quantor": "all", "states": [...]}` um:
```python
@pytest.mark.parametrize("value", [None, 0, False, "", [], {}, (), set()])
def test_allowed_falsy_return_passes_with_negative_filter(value):
    result = EBT(
        target=echo,
        pre=WorldState(args=(value,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=value), WorldState(returns="forbidden", expect=False)],
        },
        reporter=None,
    ).run()

    assert result.evaluation is True
    assert [trace.evaluation for trace in result.traces] == [True, False]


@pytest.mark.parametrize("value", [None, 0, False, "", [], {}, (), set()])
def test_forbidden_falsy_return_reports_the_matching_value(value):
    case = EBT(
        target=echo,
        pre=WorldState(args=(value,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns="allowed"), WorldState(returns=value, expect=False)],
        },
    )
    with pytest.raises(AssertionError) as error:
        case.run()

    assert case.run_trace.evaluation is False
    assert [trace.evaluation for trace in case.run_trace.traces] == [False, True]
    lines = str(error.value).splitlines()
    state_line = lines.index("  [Q-State 1] Validation: Matched")
    assert lines[state_line + 1] == f"    - Returns: Expected {value} | Actual {value} (Match)"


def test_omitted_return_expectation_accepts_non_matching_negative_filter():
    """An unrestricted positive state passes when the negative return filter does not match."""
    result = EBT(
        target=lambda: "ok",
        post={
            "quantor": "all",
            "states": [WorldState(), WorldState(returns="forbidden", expect=False)],
        },
        reporter=None,
    ).run()

    assert result.evaluation is True
    assert [trace.evaluation for trace in result.traces] == [True, False]


def test_omitted_return_expectation_does_not_invent_a_return_comparison():
    """A forbidden unrestricted state fails without specifying returns."""
    case = EBT(
        target=lambda: None,
        post={"quantor": "all", "states": [WorldState(), WorldState(expect=False)]},
    )
    with pytest.raises(AssertionError) as error:
        case.run()

    assert case.run_trace.evaluation is False
    assert "Returns:" not in str(error.value)
    assert "UNSPECIFIED" not in str(error.value)
```

---

### AP 1.5: `tests/tests_ebt/test_ebt_run_isolation.py` (Zeilen 41–57)

Stelle `test_previous_negative_match_does_not_poison_next_run` und `test_previous_positive_match_does_not_mask_next_negative_match` auf `post={"quantor": "all", "states": [...]}` um:
```python
def test_previous_negative_match_does_not_poison_next_run(execution_mode):
    case = EBT(
        target=echo,
        pre=WorldState(args=(0,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=0, expect=False)],
        },
        reporter=None,
        multiprocessing=execution_mode,
    )
    assert case.run().evaluation is False
    case.pre = [WorldState(args=(1,))]
    assert case.run().evaluation is True


def test_previous_positive_match_does_not_mask_next_negative_match(execution_mode):
    case = EBT(
        target=echo,
        pre=WorldState(args=(1,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=0, expect=False)],
        },
        reporter=None,
        multiprocessing=execution_mode,
    )
    assert case.run().evaluation is True
    case.pre = [WorldState(args=(0,))]
    assert case.run().evaluation is False
```
*(Hinweis: Zeile 172 in `test_history_is_detached_from_nested_caller_owned_data` mutiert `post.expect = False` erst **nach** `case.run()` zur Snapshot-Prüfung und bleibt unverändert.)*

---

### AP 1.6: `tests/tests_ebt/test_ebt_contract_mutation.py` (Zeilen 14–45)

Übergib in `test_replacing_return_contract_cannot_rewrite_the_verdict` (Zeile 25) `post={"quantor": "all", "states": post}`, damit `post = WorldState(returns=7, expect=not forbidden)` weiterhin im Target `mutate()` mutiert werden kann und auch für `forbidden=True` (`expect=False`) `STATE-GUARD`-konform unter `"quantor": "all"` läuft:
```python
    case = EBT(
        target=mutate,
        post={"quantor": "all", "states": post},
        reporter=reporters[reporting],
    )
```

---

### AP 1.7: `tests/tests_ebt/test_ebt_persistent_reports.py` (Zeilen 136–150)

Verpacke in `test_json_retains_every_input_and_post_match_including_negative_states` die `post`-Liste in `{"quantor": "all", "states": [...]}`:
```python
def test_json_retains_every_input_and_post_match_including_negative_states(tmp_path):
    path = tmp_path / "report.json"
    result = EBT(
        target=echo,
        pre=[WorldState(args=(1,)), WorldState(args=(2,))],
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=2, expect=False)],
        },
        reporter=json_reporter(path),
    ).run()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["expect"] is True
    assert document["evaluation"] is False
    assert len(document["traces"]) == 4
    assert len({trace["step_id"] for trace in document["traces"]}) == 2
    assert [trace["evaluation"] for trace in document["traces"]] == [True, False, True, True]
    assert [trace["post"]["expect"] for trace in document["traces"]] == [True, False, True, False]
    assert document["run_id"] == result.run_id
```

---

### AP 1.8: `tests/test_offline_core.py` (Zeilen 160–166)

Verpacke im `elif feature == "ebt":`-Zweig die `post`-Liste in `{"quantor": "all", "states": [...]}` (**wichtig:** die 2 Elemente in `states` beibehalten, damit `len(trace.traces) == 4` in Zeile 166 erfüllt bleibt):
```python
    elif feature == "ebt":
        trace = EBT(
            target=sum,
            pre=[WorldState(args=([1, 2],)), WorldState(args=([3],))],
            post={
                "quantor": "all",
                "states": [WorldState(returns=3), WorldState(returns=99, expect=False)],
            },
        ).run()
        assert trace.evaluation is True and len(trace.traces) == 4
```

---

### AP 1.9: `tests/tests_arena/test_ebt_arena_mutation.py` (Zeilen 1–5 & 99–112)

#### 1. Import-Block (Zeilen 1–5) — Ruff `I001` & `E401` bereinigen
Ersetze Zeilen 1–5:
```python
import subprocess, sys
from pathlib import Path
from qb_cubie.ebt import EBT
from qb_cubie.protocols import WorldState
from qb_cubie.arenas.pyvenv import PyVenv
```
durch:
```python
from pathlib import Path
import subprocess
import sys

from qb_cubie.arenas.pyvenv import PyVenv
from qb_cubie.ebt import EBT
from qb_cubie.protocols import WorldState
```

#### 2. `test_volatile_metadata_with_strict_expectation_red` (Zeilen 99–112)
Stelle `post` auf `{"quantor": "all", "states": [...]}` um:
```python
def test_volatile_metadata_with_strict_expectation_red():
    """
    Verifies: If the user explicitly expects a failure (e.g., negative filter on the base state),
    the test correctly fails, proving the ignore-logic isn't bypassing the assertion engine.
    """
    EBT(
        target=target_generate_volatile_metadata,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=True),
                WorldState(arena=PyVenv(BASE_ARENA), expect=False),
            ],
        },
        expect=False,  # We expect it to fail, but it functionally matches, so the test turns red (expected failure works)
    ).run()
```

---

## 3. Arbeitspaket 2 (AP 2): Härtung & Kalibrierung der Meta-Gates (`test_gate_2.py` & `test_gate_3.py`)

> [!IMPORTANT]
> **Warum AP 2 vor AP 3 umgesetzt wird:**
> Beide Meta-Gates scannen sämtliche Python-Dateien unter `tests/`. Indem wir zuerst in AP 2 die Dict-Wrapper-Entpackung (`{"quantor": ..., "states": ...}`) und die aktualisierten Kalibrierungs-Probes in `test_gate_2.py` und `test_gate_3.py` einbauen, ist sichergestellt, dass die gesamte migrierte Test-Suite alle statischen Architektur-Invarianten erfüllt.

---

### AP 2.1: `tests/tests_meta/test_gate_2.py` (`META-EBT-CROSS-PRODUCT`)

1. **Dict-Wrapper-Entpackung für `pre` und `post` nachrüsten (Zeilen 91–105 & `visit_Call` Zeile 130–131):**
   - Ein `cst.Dict` der Form `{"quantor": ..., "states": ...}` muss in `_count_pre_states(module, pre_expr)` und `_count_positive_post_states(module, post_expr)` aufgelöst werden.
   - **Kritische Quantor-Differenzierung bei `post`:**
     - Ist `post` ein `cst.Dict` mit statischem `"quantor": "all"`, bilden die `WorldState`-Einträge eine **Konjunktion ($\forall q \in Q$)** für denselben `pre`-Zustand und **kein** disjunktives Kreuzprodukt. `_count_positive_post_states` gibt in diesem Fall **`1`** zurück!
     - Ist `post` hingegen ein `cst.Dict` mit `"quantor": "exists"` (oder einem nicht-all-Quantor), wird der Ausdruck unter `"states"` entpackt und die Anzahl der positiven `WorldState`s gezählt.
   - Ersetze `_count_pre_states`, `_count_positive_post_states` und die Aufrufe in `EbtCrossProductRule.visit_Call` durch:
     ```python
     def _extract_wrapper_field(
         module: cst.Module,
         expr: cst.BaseExpression,
         field_name: str,
     ) -> cst.BaseExpression | None:
         """Extract a static string-keyed value from a quantifier wrapper dict."""
         if not isinstance(expr, cst.Dict):
             return None
         for elem in expr.elements:
             if not isinstance(elem, cst.DictElement):
                 continue
             if _literal_string(module, elem.key) == field_name:
                 return elem.value
         return None


     def _count_pre_states(module: cst.Module, pre_expr: cst.BaseExpression | None) -> int:
         """Count statically declared pre-states in an EBT call (including dict wrappers)."""
         if isinstance(pre_expr, cst.Dict):
             pre_expr = _extract_wrapper_field(module, pre_expr, "states")
         if isinstance(pre_expr, (cst.List, cst.Tuple)):
             return len(pre_expr.elements)
         return 1


     def _count_positive_post_states(module: cst.Module, post_expr: cst.BaseExpression | None) -> int:
         """Count statically declared disjunctive positive post-states (expect != False/None)."""
         if isinstance(post_expr, cst.Dict):
             quantor_expr = _extract_wrapper_field(module, post_expr, "quantor")
             quantor = _literal_string(module, quantor_expr) if quantor_expr is not None else None
             if quantor == "all":
                 return 1
             post_expr = _extract_wrapper_field(module, post_expr, "states")
         if isinstance(post_expr, (cst.List, cst.Tuple)):
             return sum(1 for el in post_expr.elements if _is_positive_worldstate(el.value))
         if post_expr is not None and not _is_positive_worldstate(post_expr):
             return 0
         return 1
     ```
     Und in `EbtCrossProductRule.visit_Call` (Zeilen 130–131):
     ```python
             pre_n = _count_pre_states(self._module, params.get("pre"))
             positive_post_n = _count_positive_post_states(self._module, params.get("post"))
     ```

2. **Clean-Probes & Fault-Probes in `test_gate_2.py` aktualisieren (Meta-Gate 5 Kalibrierung):**
   - In `test_cross_product_rule_accepts_clean_probes` (Zeilen 167–168) die beiden Clean-Probes mit `expect=False` auf `post={"quantor": "all", "states": [...]}` umstellen und eine weitere Clean-Probe für `pre=[p1, p2]` mit rein positivem `post={'quantor': 'all', 'states': [WorldState(returns=int), WorldState(returns=3)]}` (`id="many-pre-conjunctive-post-all"`) ergänzen:
     ```python
             (
                 "EBT(target=f, pre=[p1, p2], "
                 "post={'quantor': 'all', 'states': [WorldState(returns=3), WorldState(returns=99, expect=False)]})\n"
             ),
             (
                 "EBT(target=f, pre=[p1, p2], "
                 "post={'quantor': 'all', 'states': [WorldState(returns=1, expect=False), WorldState(returns=2, expect=False)]})\n"
             ),
             (
                 "EBT(target=f, pre=[p1, p2], "
                 "post={'quantor': 'all', 'states': [WorldState(returns=int), WorldState(returns=3)]})\n"
             ),
     ```
   - In `test_cross_product_rule_detects_fault_probes` (Zeilen 209–261) neue Fault-Probes für unbegründete Kreuzprodukte mit Dict-Wrapper ergänzen:
     ```python
             (
                 "EBT(target=f, pre={'quantor': 'all', 'states': [p1, p2]}, "
                 + "post=[WorldState(returns=1), WorldState(returns=2)])\n",
                 1,
                 "2x2",
             ),
             (
                 "EBT(target=f, pre=[p1, p2], "
                 + "post={'quantor': 'exists', 'states': [WorldState(returns=1), WorldState(returns=2)]})\n",
                 1,
                 "2x2",
             ),
             (
                 "EBT(target=f, pre={'quantor': 'exists', 'states': [p1, p2]}, "
                 + "post={'quantor': 'exists', 'states': [WorldState(returns=1), WorldState(returns=2)]})\n",
                 1,
                 "2x2",
             ),
     ```
     mit den IDs `"dict-pre-list-post-2x2"`, `"list-pre-dict-post-exists-2x2"`, `"dict-pre-dict-post-exists-2x2"`.

---

### AP 2.2: `tests/tests_meta/test_gate_3.py` (`META-EBT-LONELY-NEGATION`)

1. **Dict-Wrapper-Entpackung in `_extract_post_worldstates()` (Zeilen 77–95 & Zeile 136):**
   - Erweitere `_extract_post_worldstates(module: cst.Module, post_expr: cst.BaseExpression | None)` so, dass auch `post={"quantor": ..., "states": ...}` entpackt wird (egal ob `"states"` ein einzelner `WorldState(...)`-Aufruf oder eine `cst.List`/`cst.Tuple` von `WorldState(...)`-Aufrufen ist):
     ```python
     def _extract_post_worldstates(
         module: cst.Module,
         post_expr: cst.BaseExpression | None,
     ) -> list[cst.BaseExpression] | None:
         """Return all statically declared WorldState calls in post, or None if unknown/empty."""
         if post_expr is None:
             return None
         if isinstance(post_expr, cst.Dict):
             states_expr: cst.BaseExpression | None = None
             for elem in post_expr.elements:
                 if isinstance(elem, cst.DictElement) and _literal_string(module, elem.key) == "states":
                     states_expr = elem.value
                     break
             if states_expr is None:
                 return None
             post_expr = states_expr
         if isinstance(post_expr, cst.Name) and post_expr.value == "None":
             return None
         if _is_named_call(post_expr, "WorldState"):
             return [post_expr]
         if isinstance(post_expr, (cst.List, cst.Tuple)):
             if not post_expr.elements:
                 return None
             states: list[cst.BaseExpression] = []
             for elem in post_expr.elements:
                 if isinstance(elem, cst.StarredElement) or not _is_named_call(elem.value, "WorldState"):
                     return None
                 states.append(elem.value)
             return states
         return None
     ```
     Und in `EbtLonelyNegationRule.visit_Call` (Zeile 136):
     ```python
             post_states = _extract_post_worldstates(self._module, params.get("post"))
     ```

2. **Alle 10 Clean-Probes mit statischem `expect=False` (Zeilen 177–178, 180, 183–210) auf `post={"quantor": "all", "states": ...}` umstellen:**
   Ersetze die betroffenen Clean-Probes in `test_lonely_negation_rule_accepts_clean_probes` durch ihre `STATE-GUARD`-konformen `"quantor": "all"`-Äquivalente:
   ```python
           "EBT(target=f, post={'quantor': 'all', 'states': [WorldState(returns=1), WorldState(returns=99, expect=False)]})\n",
           "EBT(target=f, post={'quantor': 'all', 'states': (WorldState(returns=99, expect=False), WorldState(returns=1))})\n",
           "EBT(target=f, post=WorldState(returns=1, expect=flag))\n",
           "EBT(target=f, post={'quantor': 'all', 'states': [q1, WorldState(returns=99, expect=False)]})\n",
           "EBT(target=f, post=expected_states)\n",
           (
               "EBT(target=f, post={'quantor': 'all', 'states': WorldState(returns=99, expect=False)}, "
               "tags={'meta:negative-invariant'})\n"
           ),
           (
               "EBT(target=f, post={'quantor': 'all', 'states': [WorldState(returns=404, expect=False), "
               "WorldState(returns=500, expect=False)]}, tags={'meta:negative-invariant', 'safety'})\n"
           ),
           (
               "EBT(target=f, post={'quantor': 'all', 'states': WorldState(returns=99, expect=False)}, "
               "tags=['meta:negative-invariant'])\n"
           ),
           (
               "EBT(target=f, post={'quantor': 'all', 'states': WorldState(returns=99, expect=False)}, "
               "tags=('meta:negative-invariant',))\n"
           ),
           (
               "EBT(target=f, post={'quantor': 'all', 'states': WorldState(returns=99, expect=False)}, "
               "tags={'meta:negative-invariant': 'Rejects sentinel error code'})\n"
           ),
           (
               "EBT(target=f, pre=[p1, p2], post={'quantor': 'all', 'states': [WorldState(returns=404, expect=False), "
               "WorldState(returns=500, expect=False)]}, "
               "tags={'meta:negative-invariant': True, 'meta:cross-product-reason': 'Status matrix'})\n"
           ),
           (
               "qb_cubie.EBT(target=f, post={'quantor': 'all', 'states': qb_cubie.WorldState(returns=99, expect=False)}, "
               "tags={'meta:negative-invariant'})\n"
           ),
   ```

3. **Neue Fault-Probes für einsame Negationen im Dict-Wrapper ergänzen (Zeilen 247–326):**
   Ergänze in `test_lonely_negation_rule_detects_fault_probes` zwei neue Sonden am Ende der Parametrisierung:
   ```python
           (
               "EBT(target=f, post={'quantor': 'all', 'states': WorldState(returns=99, expect=False)})\n",
               1,
               "0pos/1neg",
           ),
           (
               "EBT(target=f, post={'quantor': 'all', 'states': [WorldState(returns=404, expect=False), "
               + "WorldState(returns=500, expect=False)]})\n",
               1,
               "0pos/2neg",
           ),
   ```
   mit den IDs `"dict-wrapper-single-negative"` und `"dict-wrapper-two-negatives"`.

---

## 4. Arbeitspaket 3 (AP 3): Neue Red-Phase-Tests in `tests/tests_ebt/test_ebt_quantor_declaration.py`

> [!IMPORTANT]
> **Zwei kritische Konstruktionsregeln für AP 3 (aus `HYPOTHESIS.md`, Fragen 3–5):**
> 1. **Parametrisierte Variablen-Injektion statt literaler `EBT(..., post=WorldState(expect=False))`-Aufrufe:**
>    Genau wie alle bestehenden Guard-Tests in Gruppe E (`test_ebt_quantor_declaration.py:539-711`) müssen die ungültigen `pre_val`-/`post_val`-/`expect_val`-Konfigurationen über `@pytest.mark.parametrize`-Variablen (oder vorab aufgebaute Variablen) an `EBT(...)` übergeben werden. So werden die neuen Guard-Tests niemals fälschlich von den statischen CST-Scannern in `test_gate_2.py` oder `test_gate_3.py` als fehlerhafte Testverträge markiert.
> 2. **Mutations-Abdeckung für `evaluate_step_logic()` (`src/qb_cubie/protocols.py:129-140`):**
>    Weil `evaluate_step_logic` unter `post_quantor="all"` nach De Morgan denselben Wert wie die alte $Q^+/Q^-$-Formel berechnet und unter `post_quantor="exists"` künftig der `STATE-GUARD` in `EBT._arrange()` vorab wirft, muss Test 4 (`test_evaluate_step_logic_enforces_pure_quantor_invariants`) `evaluate_step_logic` direkt testen, damit kein unreparierter Core-Mutant in `protocols.py` überlebt.

### 4.1 Import-Ergänzung in `tests/tests_ebt/test_ebt_quantor_declaration.py` (Zeile 16)

Erweitere Zeile 16 von:
```python
from qb_cubie.protocols import ExceptionExpectation
```
auf:
```python
from qb_cubie.protocols import EvaluationTrace, ExceptionExpectation, evaluate_step_logic
```

### 4.2 Fünf neue Red-Phase-Testfunktionen am Ende von Gruppe E (ab Zeile 712)

Füge am Ende von `tests/tests_ebt/test_ebt_quantor_declaration.py` folgende **5 Testfunktionen** an:

```python
@pytest.mark.parametrize("ebt_expect", [True, False], ids=["ebt-expect-true", "ebt-expect-false"])
@pytest.mark.parametrize(
    "invalid_post",
    [
        WorldState(returns=99, expect=False),
        [WorldState(returns=int), WorldState(returns=99, expect=False)],
        {"quantor": "exists", "states": WorldState(returns=99, expect=False)},
        {
            "quantor": "exists",
            "states": [WorldState(returns=int), WorldState(returns=99, expect=False)],
        },
    ],
    ids=[
        "implicit-exists-single-negative",
        "implicit-exists-mixed-list",
        "explicit-exists-single-negative",
        "explicit-exists-mixed-list",
    ],
)
def test_guard_rejects_negative_worldstate_under_post_exists(
    tmp_path: Path,
    execution_mode: bool,
    ebt_expect: bool,
    invalid_post: Any,
) -> None:
    """STATE-GUARD verbietet WorldState(expect=False) unter post='exists' (implizit, explizit & nach Mutation)."""
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match="STATE-GUARD"):
        EBT(
            target=partial(record_call, marker),
            pre=WorldState(args=(42,)),
            post=invalid_post,
            expect=ebt_expect,
            reporter=None,
            multiprocessing=execution_mode,
        ).run()
    assert not marker.exists()

    # In-Place-Mutation von post[0].expect = False vor einem Zweitlauf muss ebenfalls abgewiesen werden.
    mutable_state = WorldState(returns=42, expect=True)
    case = EBT(
        target=partial(record_call, marker),
        pre=WorldState(args=(42,)),
        post=[mutable_state],
        expect=ebt_expect,
        reporter=None,
        multiprocessing=execution_mode,
    )
    first_trace = case.run()
    assert first_trace is not None
    marker.unlink()
    mutable_state.expect = False
    with pytest.raises(ValueError, match="STATE-GUARD"):
        case.run()
    assert not marker.exists()


@pytest.mark.parametrize(
    "invalid_pre",
    [
        WorldState(args=(42,), expect=False),
        [WorldState(args=(42,)), WorldState(args=(7,), expect=False)],
        {"quantor": "all", "states": [WorldState(args=(42,), expect=False)]},
        {"quantor": "exists", "states": [WorldState(args=(42,), expect=False)]},
    ],
    ids=[
        "single-pre-expect-false",
        "list-pre-expect-false",
        "wrapper-all-pre-expect-false",
        "wrapper-exists-pre-expect-false",
    ],
)
def test_guard_rejects_negative_worldstate_in_pre(
    tmp_path: Path,
    execution_mode: bool,
    invalid_pre: Any,
) -> None:
    """STATE-GUARD weist WorldState(expect=False) in pre in allen Strukturformen und nach Mutation ab."""
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match="STATE-GUARD"):
        EBT(
            target=partial(record_call, marker),
            pre=invalid_pre,
            post=WorldState(returns=42),
            reporter=None,
            multiprocessing=execution_mode,
        ).run()
    assert not marker.exists()

    mutable_pre = WorldState(args=(42,), expect=True)
    case = EBT(
        target=partial(record_call, marker),
        pre=[mutable_pre],
        post=WorldState(returns=42),
        reporter=None,
        multiprocessing=execution_mode,
    )
    assert case.run().evaluation is True
    marker.unlink()
    mutable_pre.expect = False
    with pytest.raises(ValueError, match="STATE-GUARD"):
        case.run()
    assert not marker.exists()


@pytest.mark.parametrize(
    "bad_expect",
    [None, 1, 0, "true", []],
    ids=["none", "int-one", "int-zero", "str-true", "empty-list"],
)
def test_guard_rejects_non_bool_expect_on_worldstate_and_ebt(
    tmp_path: Path,
    bad_expect: Any,
) -> None:
    """STATE-GUARD erzwingt striktes bool für WorldState.expect und EBT.expect (auch gegen int 1/0 und Mutation)."""
    marker = tmp_path / "called"

    with pytest.raises(TypeError, match="STATE-GUARD"):
        bad_ws = WorldState(returns=42, expect=bad_expect)
        EBT(
            target=partial(record_call, marker),
            pre=WorldState(args=(42,)),
            post={"quantor": "all", "states": [bad_ws]},
            reporter=None,
        ).run()
    assert not marker.exists()

    with pytest.raises(TypeError, match="STATE-GUARD"):
        EBT(
            target=partial(record_call, marker),
            pre=WorldState(args=(42,)),
            post=WorldState(returns=42),
            expect=bad_expect,
            reporter=None,
        ).run()
    assert not marker.exists()

    ws = WorldState(returns=42, expect=True)
    case = EBT(
        target=partial(record_call, marker),
        pre=WorldState(args=(42,)),
        post={"quantor": "all", "states": [ws]},
        reporter=None,
    )
    assert case.run().evaluation is True
    marker.unlink()

    ws.expect = bad_expect
    with pytest.raises(TypeError, match="STATE-GUARD"):
        case.run()
    assert not marker.exists()

    ws.expect = True
    case.expect = bad_expect
    with pytest.raises(TypeError, match="STATE-GUARD"):
        case.run()
    assert not marker.exists()


def test_evaluate_step_logic_enforces_pure_quantor_invariants() -> None:
    """evaluate_step_logic wertet Quantoren rein ohne Q+/Q--Split oder Vacuous-True unter 'exists' aus."""
    assert evaluate_step_logic([], "exists") is False
    assert evaluate_step_logic([], "all") is True

    pos_hit = EvaluationTrace(
        step_id="run_0",
        target="target_identity",
        pre=WorldState(args=(99,)),
        post=WorldState(returns=int, expect=True),
        outcome=WorldState(returns=99),
        evaluation=True,
    )
    neg_hit = EvaluationTrace(
        step_id="run_0",
        target="target_identity",
        pre=WorldState(args=(99,)),
        post=WorldState(returns=99, expect=False),
        outcome=WorldState(returns=99),
        evaluation=True,
    )
    neg_miss = EvaluationTrace(
        step_id="run_0",
        target="target_identity",
        pre=WorldState(args=(42,)),
        post=WorldState(returns=99, expect=False),
        outcome=WorldState(returns=42),
        evaluation=False,
    )

    assert evaluate_step_logic([pos_hit, neg_hit], "all") is False
    assert evaluate_step_logic([pos_hit, neg_miss], "all") is True

    with pytest.raises(ValueError, match="STATE-GUARD"):
        evaluate_step_logic([pos_hit, neg_hit], "exists")


def test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun(
    execution_mode: bool,
) -> None:
    """Explizite Quantoren überleben Zweitläufe ohne Neuzuweisung, springen bei Neuzuweisung aber auf den Standard zurück."""
    # --- Teil 1: post-Lebenszyklus ('all' -> Rerun bleibt 'all' -> In-Place bleibt 'all' -> Reassign wird 'exists') ---
    post_case = EBT(
        target=target_identity,
        pre=WorldState(args=(1,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=int), WorldState(returns=1)],
        },
        reporter=None,
        multiprocessing=execution_mode,
    )
    run1 = post_case.run()
    assert run1.evaluation is True and run1.post_quantor == "all"

    # Zweitlauf OHNE Neuzuweisung von post: post_quantor muss 'all' bleiben!
    post_case.pre = WorldState(args=(2,))
    run2 = post_case.run()
    assert run2.evaluation is False and run2.post_quantor == "all"

    # In-Place-Listenmutation auf post: post_quantor muss 'all' bleiben!
    post_case.post.append(WorldState(returns=lambda v: v > 0))
    run3 = post_case.run()
    assert run3.evaluation is False and run3.post_quantor == "all"

    # Attribut-Neuzuweisung einer einfachen Liste ohne Dict-Wrapper: post_quantor MUSS auf 'exists' zurückspringen!
    post_case.post = [WorldState(returns=1), WorldState(returns=2)]
    run4 = post_case.run()
    assert run4.post_quantor == "exists"
    assert run4.evaluation is True

    # Attribut-Neuzuweisung eines einzelnen WorldState bzw. None setzt post_quantor ebenfalls auf 'exists'
    post_case.post = {"quantor": "all", "states": [WorldState(returns=2)]}
    assert post_case.run().post_quantor == "all"
    post_case.post = WorldState(returns=2)
    assert post_case.run().post_quantor == "exists"
    post_case.post = {"quantor": "all", "states": [WorldState(returns=2)]}
    assert post_case.run().post_quantor == "all"
    post_case.post = None
    assert post_case.run().post_quantor == "exists"

    # --- Teil 2: pre-Lebenszyklus ('exists' -> Rerun bleibt 'exists' -> Reassign wird 'all') ---
    pre_case = EBT(
        target=target_identity,
        pre={
            "quantor": "exists",
            "states": [WorldState(args=(1,)), WorldState(args=(2,))],
        },
        post=WorldState(returns=1),
        reporter=None,
        multiprocessing=execution_mode,
    )
    pre_run1 = pre_case.run()
    assert pre_run1.evaluation is True and pre_run1.pre_quantor == "exists"

    # Zweitlauf OHNE Neuzuweisung von pre: pre_quantor muss 'exists' bleiben!
    pre_run2 = pre_case.run()
    assert pre_run2.evaluation is True and pre_run2.pre_quantor == "exists"

    # Attribut-Neuzuweisung einer einfachen Liste ohne Dict-Wrapper: pre_quantor MUSS auf 'all' zurückspringen!
    pre_case.pre = [WorldState(args=(1,)), WorldState(args=(2,))]
    pre_run3 = pre_case.run()
    assert pre_run3.pre_quantor == "all"
    assert pre_run3.evaluation is False
```

---

## 5. Arbeitspaket 4 (AP 4): Verifikations- & Abnahmeprotokoll (TGD Red-Phase)

Nach Umsetzung von AP 1, AP 2 und AP 3 müssen die folgenden **4 Verifikationsschritte** exakt das beschriebene Ergebnis liefern:

### Schritt 4.1: Alle 9 migrierten Testdateien (AP 1) laufen zu 100 % grün (`PASSED`)

```bash
.venv/bin/python -m pytest -q \
  tests/tests_ebt/test_ebt_quantors.py \
  tests/tests_ebt/test_ebt_returns.py \
  tests/tests_ebt/test_ebt_exception_contracts.py \
  tests/tests_ebt/test_ebt_return_reporting.py \
  tests/tests_ebt/test_ebt_run_isolation.py \
  tests/tests_ebt/test_ebt_contract_mutation.py \
  tests/tests_ebt/test_ebt_persistent_reports.py \
  tests/tests_ebt/test_ebt_args_normalization.py \
  tests/tests_arena/test_ebt_arena_mutation.py \
  tests/test_offline_core.py -k "not slow or test_core_feature"
```
- **Erwartetes Ergebnis:** `0 failed`, alle Tests **`PASSED`**.

### Schritt 4.2: Alle 3 Meta-Gates inkl. Repository-Scan über `tests/` (AP 2) laufen zu 100 % grün (`PASSED`)

```bash
.venv/bin/python -m pytest -q tests/tests_meta/test_gate_1.py tests/tests_meta/test_gate_2.py tests/tests_meta/test_gate_3.py
```
- **Erwartetes Ergebnis:** `0 failed`, sämtliche Clean-Probes, Fault-Probes und Repository-Scans (`test_repository_has_no_unjustified_ebt_cross_products`, `test_repository_has_no_lonely_ebt_negations`) bestehen mit **`0` Diagnosen**.

### Schritt 4.3: TGD Red-Phase-Nachweis in `test_ebt_quantor_declaration.py` (AP 3)

1. **Bestehende Tests in `test_ebt_quantor_declaration.py` (Gruppen A–E ohne die 5 neuen Tests):**
   ```bash
   .venv/bin/python -m pytest -q tests/tests_ebt/test_ebt_quantor_declaration.py \
     -k "not (test_guard_rejects_negative_worldstate_under_post_exists or test_guard_rejects_negative_worldstate_in_pre or test_guard_rejects_non_bool_expect_on_worldstate_and_ebt or test_evaluate_step_logic_enforces_pure_quantor_invariants or test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun)"
   ```
   - **Erwartetes Ergebnis:** **100 % `PASSED`** (`0 failed`).

2. **Die 5 neuen Red-Phase-Testfunktionen gegen den ungehärteten Core (`v0.0.8`):**
   ```bash
   .venv/bin/python -m pytest -q tests/tests_ebt/test_ebt_quantor_declaration.py \
     -k "test_guard_rejects_negative_worldstate_under_post_exists or test_guard_rejects_negative_worldstate_in_pre or test_guard_rejects_non_bool_expect_on_worldstate_and_ebt or test_evaluate_step_logic_enforces_pure_quantor_invariants or test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun"
   ```
   - **Erwartetes Ergebnis in der TGD Red-Phase:** Alle 5 neuen Testfunktionen (`24` parametrisierte Test-Items) schlagen gegen `v0.0.8` deterministisch **rot fehl (`24 failed`)** — und beweisen damit, dass die neuen Guards, die `evaluate_step_logic`-Reinheit und der Sticky-Quantor-Reset im Core noch fehlen.

### Schritt 4.4: Statische Code-Qualität (`ruff`, `mypy`, `pylint`) auf allen 12 bearbeiteten Testdateien

```bash
FILES="tests/tests_ebt/test_ebt_quantors.py \
  tests/tests_ebt/test_ebt_returns.py \
  tests/tests_ebt/test_ebt_exception_contracts.py \
  tests/tests_ebt/test_ebt_return_reporting.py \
  tests/tests_ebt/test_ebt_run_isolation.py \
  tests/tests_ebt/test_ebt_contract_mutation.py \
  tests/tests_ebt/test_ebt_persistent_reports.py \
  tests/tests_ebt/test_ebt_quantor_declaration.py \
  tests/tests_arena/test_ebt_arena_mutation.py \
  tests/test_offline_core.py \
  tests/tests_meta/test_gate_2.py \
  tests/tests_meta/test_gate_3.py"

.venv/bin/ruff check $FILES
MYPYPATH=src .venv/bin/mypy --ignore-missing-imports --warn-unreachable --check-untyped-defs $FILES
PYTHONPATH=src .venv/bin/pylint --disable=all --enable=unreachable $FILES
```
- **Erwartetes Ergebnis:**
  - `ruff check`: `All checks passed!` (`0` Fehler)
  - `mypy`: `Success: no issues found in 12 source files` (`0` Fehler)
  - `pylint`: `0` Fehler (Exit-Code `0`)

---

## 6. Ausblick & Übergabepunkt zur TGD Green-Phase (Folge-Arbeitspaket Core & Docs)

Sobald dieses Arbeitspaket (TGD Red-Phase) in `tests/` abgenommen ist, folgt die **TGD Green-Phase** in zwei synchronen Schritten:

1. **Core-Reparatur (`src/qb_cubie/protocols.py` & `src/qb_cubie/ebt.py`):**
   - `WorldState.expect` und `EBT.expect` strikt gegen `isinstance(val, bool)` prüfen (`TypeError("STATE-GUARD: ...")`).
   - `evaluate_step_logic(traces, post_quantor)` von der $Q^+/Q^-$-Partitionierung befreien, `expect=False` unter `post_quantor == "exists"` mit `ValueError("STATE-GUARD: ...")` abweisen und `results = [t.evaluation if t.post.expect else not t.evaluation for t in traces]` rein über `all(results)` bzw. `any(results)` auswerten.
   - In `EBT._arrange()` / `_parse_state_config()` `WorldState(expect=False)` in `pre` und unter `post_quantor == "exists"` mit `ValueError("STATE-GUARD: ...")` abweisen.
   - Über Property-Setter oder Referenz-Tracking für `self.pre` und `self.post` sicherstellen, dass eine Attribut-Neuzuweisung ohne Dict-Wrapper den Quantor auf `"all"` (`pre`) bzw. `"exists"` (`post`) zurücksetzt, während wiederholte `.run()`-Aufrufe ohne Neuzuweisung sowie In-Place-Listenmutationen den deklarierten Quantor bewahren.
   - **Green-Signal:** Alle 24 roten Test-Items aus AP 3 springen ohne Änderung an `tests/` auf **`PASSED`**.
2. **Dokumentations-Synchronisation (`docs/` & `README.md`):**
   - Die Live-Code-Snippets in `docs/GUIDE_Expect-Flags.md` (Z. 39–57, 80–101, 154–177) und `docs/GUIDE_EBT-Usage-Pattern.md` (Z. 147–169) sowie die Spezifikationstexte in `docs/GUIDE_Contract-Semantics.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/dev/DEV-GUIDE_2-1_EBT-Class.md`, `docs/dev/DEV-GUIDE_2-2_WorldState-Class.md` und `README.md` gemäß `ANALYSIS.md` (Teil 3) nachziehen.
   - **Green-Signal:** `pytest tests/test_styleguide.py` (`DocEnsurance`) läuft gegen den gehärteten Core zu **100 % `PASSED`**.

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../docs/.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../docs/GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../docs/GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../docs/GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../docs/GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../docs/GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../docs/GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../docs/GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../docs/services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
