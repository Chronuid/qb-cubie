## Auftrag: Reparatur & Migration der Test-Suite (`qb-cubie`, TGD Red-Phase)

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini-4-Hydrogen" effort="High" -->
# Analysis: Reperatur vom Cubie-Core

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini-4-Hydrogen
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 20:50 (CET)
- **Synthesebasis:** 
  - `docs/GUIDE_Quality-Assurance.md`
  - `docs/GUIDE_Contract-Design.md`
  - `docs/GUIDE_Expect-Flags.md`
  - `docs/GUIDE_Quantifiers.md`
  - `tests/ANALYSIS.md`
  - "Konversations-Prompts"
  - "Unbekannte Informationen aus dem Memory-System der Gemini-App"
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

### 1. Ziel & Architektur-Grundsatz

Die Test-Suite von `qb-cubie` soll so umgebaut werden, dass `WorldState(..., expect=False)` niemals mehr heimlich das Standard-Existenzquantor-Verhalten (`post="exists"`) überschreibt. Stattdessen gelten die Quantoren strikt rein (`pre="all"` als UND-Verknüpfung, `post="exists"` als ODER-Verknüpfung), und Negationen über `WorldState(..., expect=False)` werden ausschließlich innerhalb eines explizit deklarierten Allquantors (`post={"quantor": "all", "states": [...]}`) verwendet.

Im Sinne von **Test-Guided Development (TGD)** wird in diesem Auftrag **ausschließlich `tests/**` bearbeitet (`src/qb_cubie/` und `docs/` bleiben in diesem Schritt noch unverändert):

* Bestehende Tests mit implizitem Misch-Muster werden auf die saubere, explizite Deklaration umgestellt.


* Neue Guard-Tests werden ergänzt, die gegen den ungehärteten Core zunächst als **Red-Phase-Nachweis** rot schlagen und nach der anschließenden Core-Reparatur grün werden.



---

### 2. Wie wir die Tests reparieren (Reparatur-Mechanik)

Die Reparatur folgt drei klaren Transformationsregeln:

1. **Explizites Wrapping statt impliziter Quantor-Überschreibung:**
Überall dort, wo in `post` positive Zielmuster und negative Ausschlussmuster (`expect=False`) gemischt werden, wird die bisherige Liste in das explizite Quantor-Dictionary mit `"quantor": "all"` überführt:


```python
# Vorher (implizites Veto unter post="exists"):
post=[
    WorldState(returns=int),
    WorldState(returns=99, expect=False),
]

# Nachher (explizite Konjunktion unter post="all"):
post={
    "quantor": "all",
    "states": [
        WorldState(returns=int),
        WorldState(returns=99, expect=False),
    ],
}

```


2. **Vertragsebene (`EBT.expect`) bleibt unverändert:**
Tests, die `EBT(..., expect=False)` mit rein positiven `post`-Zuständen zur Invertierung des Gesamtergebnisses nutzen, überschreiben keinen Quantor und bleiben unverändert.


3. **Bereits saubere `"all"`-Tests bleiben erhalten:**
`tests/tests_ebt/test_ebt_quantor_declaration.py` (Z. 387–434) und `tests/tests_ebt/test_ebt_args_normalization.py` (Z. 338–381) nutzen bereits `post={"quantor": "all", ...}` und bleiben unverändert gültig.



---

### 3. Konkrete Arbeitspakete

#### Arbeitspaket 1: Migration der 9 betroffenen Testdateien (21 Testfunktionen)

Folgende 9 Dateien verlassen sich aktuell auf das implizite `AND`-Veto im Standard-`post` (`"exists"`) und müssen migriert werden:

1. **`tests/tests_ebt/test_ebt_quantors.py`**:


* *Z. 113–158 (`test_mixed_expect_exists_green`, `test_mixed_expect_exists_red_lower_bound`, `test_mixed_expect_exists_red_upper_bound`):* Auf ein logisch sauberes `post={"quantor": "all", "states": [WorldState(returns=lambda v: 0 <= v <= 6), WorldState(returns=0, expect=False), WorldState(returns=6, expect=False)]}` (oder einen reinen `exists`-Vertrag ohne redundante Verbote) umstellen.


* *Z. 181–232 (`test_local_expect_false_green`, `test_local_expect_false_red`, `test_negative_filters_green`, `test_negative_filters_red`):* Auf `post={"quantor": "all", "states": [...]}` umstellen.




2. **`tests/tests_ebt/test_ebt_returns.py` (Z. 87–123)**:


* `test_negative_none_contract_accepts_non_none_values` und `test_negative_none_contract_rejects_none` auf `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=None, expect=False)]}` umstellen.




3. **`tests/tests_ebt/test_ebt_exception_contracts.py` (Z. 76–111)**:


* `test_forbidden_exception_accepts_allowed_exception_message` und `test_forbidden_exception_rejects_matching_exception_message` auf `post={"quantor": "all", "states": [...]}` umstellen.




4. **`tests/tests_ebt/test_ebt_return_reporting.py` (Z. 76–126)**:


* `test_allowed_falsy_return_passes_with_negative_filter`, `test_forbidden_falsy_return_reports_the_matching_value`, `test_omitted_return_expectation_accepts_non_matching_negative_filter` und `test_omitted_return_expectation_does_not_invent_a_return_comparison` auf `post={"quantor": "all", "states": [...]}` umstellen.




5. **`tests/tests_ebt/test_ebt_run_isolation.py` (Z. 41–57)**:


* `test_previous_negative_match_does_not_poison_next_run` und `test_previous_positive_match_does_not_mask_next_negative_match` auf `post={"quantor": "all", "states": [...]}` umstellen.




6. **`tests/tests_ebt/test_ebt_contract_mutation.py` (Z. 14–45)**:


* In `test_replacing_return_contract_cannot_rewrite_the_verdict` beim `forbidden=True`-Fall `post={"quantor": "all", "states": post}` (oder `EBT(..., expect=False)`) verwenden, da ein einzelnes `WorldState(returns=7, expect=False)` im Standard-`exists`-Modus künftig durch den `STATE-GUARD` abgewiesen wird.




7. **`tests/tests_ebt/test_ebt_persistent_reports.py` (Z. 136–150)**:


* `test_json_retains_every_input_and_post_match_including_negative_states` auf `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=2, expect=False)]}` umstellen.




8. **`tests/test_offline_core.py` (Z. 160–166)**:


* Den `feature == "ebt"`-Smoke-Test entweder auf ein reines `post=WorldState(returns=3)` oder explizites `post={"quantor": "all", "states": [WorldState(returns=3), WorldState(returns=99, expect=False)]}` umstellen.




9. **`tests/tests_arena/test_ebt_arena_mutation.py` (Z. 99–112)**:


* `test_volatile_metadata_with_strict_expectation_red` auf `post={"quantor": "all", "states": [...]}` umstellen (oder alternativ ohne Doppel-Negation direkt mit positivem `WorldState(returns=True, arena=PyVenv(BASE_ARENA))` prüfen).





#### Arbeitspaket 2: Neue Red-Phase-Tests für `STATE-GUARD`s & Sticky-Quantor-Reset

In **`tests/tests_ebt/test_ebt_quantor_declaration.py`** vier neue Tests ergänzen, die das gehärtete Soll-Verhalten des Cores erzwingen:

1. **Verbot von `WorldState(expect=False)` bei `post="exists"`:** Sowohl implizit (`post=[WorldState(returns=int), WorldState(returns=99, expect=False)]`) als auch explizit (`post={"quantor": "exists", "states": [...]}`) muss vor der Ausführung ein `ValueError` mit `"STATE-GUARD"` ausgelöst werden.


2. **Verbot von `pre.expect=False`:** `pre=WorldState(args=1, expect=False)` muss mit `ValueError("STATE-GUARD: ...")` abgewiesen werden, statt stillschweigend ignoriert zu werden.


3. **Strikte Typprüfung auf `expect`:** `WorldState(..., expect=None)` und `EBT(..., expect=None)` (sowie andere Nicht-`bool`-Werte) müssen mit `TypeError("STATE-GUARD: ...")` abgewiesen werden.


4. **Sticky-Quantor-Reset bei Neuzuweisung:** Wird ein `EBT`-Objekt zunächst mit `post={"quantor": "all", "states": [...]}` ausgeführt und danach per Neuzuweisung `case.post = [WorldState(returns=1), WorldState(returns=2)]` wiederverwendet, muss `case.post_quantor` sauber auf `"exists"` zurückgesetzt werden.



#### Arbeitspaket 3: Anpassung der Meta-Gates (`test_gate_2.py` & `test_gate_3.py`)

1. **`tests/tests_meta/test_gate_3.py` (`META-EBT-LONELY-NEGATION`):**
* `_extract_post_worldstates()` (Z. 77–94) um Unterstützung für das `{"quantor": ..., "states": ...}`-Dictionary erweitern, da `cst.Dict` bisher ignoriert wird.


* Die Clean-Probes (Z. 177–178) von gemischten Listen im Standard-`post` auf `post={"quantor": "all", "states": [...]}` umstellen und sicherstellen, dass `WorldState(..., expect=False)` statisch nur innerhalb eines expliziten `"quantor": "all"`-Wrappers akzeptiert wird.




2. **`tests/tests_meta/test_gate_2.py` (`META-EBT-CROSS-PRODUCT`):**
* `_count_pre_states()` und `_count_positive_post_states()` (Z. 71–105) um Unterstützung für das `{"quantor": ..., "states": ...}`-Dictionary erweitern.


* Dabei differenzieren: Bei `post={"quantor": "all", ...}` bilden mehrere `WorldState`-Einträge eine gewünschte Konjunktion (kein Kreuzprodukt-Verstoß), während `post={"quantor": "exists", ...}` mit mehreren Zuständen weiterhin als Kreuzprodukt-Kandidat geprüft wird.





---

### 4. Leitplanken & Abnahmekriterien

* **Keine Manipulation von Prüfzielen:** Bestehende fachliche Assertions dürfen nicht abgeschwächt und Meta-Gates oder Linter (`ruff`, `mypy`, `pylint`) nicht deaktiviert werden.


* **Klare Trennung zu `docs/`:** `tests/test_styleguide.py` (`test_docs_code_examples` via `DocEnsurance`) führt Code-Snippets aus `docs/` live aus und wird erst im Anschluss gemeinsam mit Core und Dokumentation abgenommen.


* **Verifikation nach Abschluss:**
* Alle migrierten Tests in `tests/tests_ebt/`, `tests/tests_arena/`, `tests/test_offline_core.py` sowie `tests/tests_meta/` laufen mit `pytest` sauber durch (lediglich die 4 neuen Guard-Tests aus Arbeitspaket 2 schlagen erwartungsgemäß rot fehl, bis im nächsten Schritt `src/qb_cubie/` angepasst wird).


* Statische Prüfungen (`ruff`, `mypy`, `pylint`) auf `tests/` melden 0 Fehler.

---

---

User: 
Ich habe mir das Arbeitspaket nicht ganz durchgelesen. Das ist mir zu viel. Aber zur Sicherheit, hier nochmal ein paar ursprüngliche Prompts:

---

# Reperatur vom Cubie-Core

## Ziele: 
  * Reperatur vom Cubie-Core.
  * Härtung der Quantoren-Deklaration in der EBT-Klasse.
  * Sicherstellung des Standart-Verhaltens von EBT-Fällen:  
    - `EBT.pre`-Standart-Verhalten: All-Quantor  
    - `EBT.post`-Standart-Verhalten: Existenz-Quantor  

Aktuell scheinen die expect-Flags in den WorldStates das Standart-Verhalten umzuschreiben. Das war vermutlich mein Fehler, weil ich den Auftrag dazu gab, ohne mir die Details genau anzusehen. Das müssen wir jetzt nochmal im Nachhinein glattziehen. Aufgrund der Entstehungs-Historie von diesem Bug wird er vermutlich auch innerhalb des Testsuite selbst eingebettet sein.

[...]

## Auftrag

Hinterfrage meine Behauptung. Habe ich das richtig gesehen, dass der expect-Flag das Standart-Quantoren-Verhalten überschreibt?

Finde bitte heraus, ob es Tests gibt, welche dafür verantwortlich sein könnten, dass das Standart-Quantor-Verhalten der EBT-Klasse im Post-Attribut nicht wie erwartet zuverlässig als Existenz-Quantor agiert und vom expect-Flag überschrieben wird.
Finde auch heraus, welche Docs an welchen Stellen überarbeitet werden müssten, um eine saubere Erwartungs-Haltung für das Standart-Verhalten von `EBT.pre` und `EBT.post` zu dokumentieren. Der expect-Flag darf das Verhalten der Quantoren nicht überschreiben.

---

Das mit dem Expect-Flag kann mit den neuen expliziten Quantor-Einstellungen realisiert werden. Man kann einfach sagen: "quantor":"all", wenn ein expect-flag mit gezählt werden muss. Man muss also nur das automatische überschreiben durch den expect-flag rausnehmen und durch eine explizite Deklaration ersetzen.

---

## Weiteres

### **Deine Workspaces**: 
- 'tests': hier kannst du Dateien anlegen.
- 'docs': Da stehen Infos.

### **Dein Bericht**: 
'tests/HYPOTHESIS.md', dort soll am Ende deine Hypothesen stehen. Du kannst das unterwegs so viel bearbeiten wie du möchtest.

### **Im Bericht**:
Halte dich grob an die Konvention mit dem Provenance-Kopf im Header des Dokuments:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Argon" effort="High" -->
    # Analysis: Reperatur vom Cubie-Core
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Argon
    - **Reasoning-Effort:** High
    - **Analysedatum:** 19. November 2026, ~ 21:30 (CET)
    - **Synthesebasis:** # Das hier musst du noch ausfüllen.
    - **Stand**: qb-cubie (v0.0.8) 
    - **Git-Log**: #`git log -n 1`
    ```text
    commit db96ea4b404c7b462e350f9e0bc5b8335c4f4d82 (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Thu Nov 19 20:33:16 2026 +0100
    
        Found a critical bug. Analysed it. Gotta think about it.
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du deine Hypothesen rein.
```

Erstelle ein sauberes Hypothesen-Dokument zur Reperatur der Testsuite mit überprüfbaren Teil-Hypothesen und Hinterfrage das Arbeitspaket. Stelle die Fragen der Meta-QA.