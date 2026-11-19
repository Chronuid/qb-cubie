<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Neon" effort="High" -->
# Analysis: Reperatur vom Cubie-Core

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Neon
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 20:20 (CET)
- **Synthesebasis:** `GEMINI-1.md`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `src/qb_cubie/reporter.py`, `src/qb_cubie/arenas/tempfs.py`, `src/qb_cubie/arenas/pyvenv.py`, `tests/tests_ebt/test_ebt_quantors.py`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `tests/tests_ebt/test_ebt_args_normalization.py`, `tests/tests_ebt/test_ebt_returns.py`, `tests/tests_ebt/test_ebt_return_reporting.py`, `tests/tests_ebt/test_ebt_exception_contracts.py`, `tests/tests_ebt/test_ebt_run_isolation.py`, `tests/tests_ebt/test_ebt_contract_mutation.py`, `tests/tests_ebt/test_ebt_persistent_reports.py`, `tests/tests_ebt/test_ebt_state_validation.py`, `tests/test_offline_core.py`, `tests/tests_arena/test_ebt_arena_mutation.py`, `tests/tests_meta/test_gate_1.py`, `tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `tests/test_styleguide.py`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_Contract-Semantics.md`, `docs/GUIDE_EBT-Usage-Pattern.md`, `docs/GUIDE_Example-Based-Testing.md`, `docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`, `docs/dev/DEV-GUIDE_2-1_EBT-Class.md`, `docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`, `docs/feature-drafts/meta-qa/1/META_GATE_3.md`, `META_QUESTION.md`, `README.md`, Git-Historie (`4a129d55` bis `312e84d5`)
- **Stand**: qb-cubie (v0.0.8)
- **Git-Log**:

```text
commit 312e84d5fed67a75a49539bcb6a6d85287f86c5f (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 19 02:32:11 2026 +0100

    Added the Mutation disclaimer to the other docs too.
```

---

---

<!-- /qb:frame -->

# Analyse: Quantoren-Semantik, `expect`-Flag-Interferenz und Reparaturbedarf im Cubie-Core

## Executive Summary (Kurzurteil)

1. **Prüfung deiner Behauptung — JA, mit wichtiger logischer und historischer Präzisierung:**
   - **Code-Befund:** Ja, `WorldState.expect=False` (und sogar `expect=None`) **übersteuert faktisch das Standard-Existenzquantor-Verhalten** von `EBT.post` (`post_quantor="exists"`). In [`src/qb_cubie/protocols.py:129-140`](../src/qb_cubie/protocols.py#L129-L140) partitioniert `evaluate_step_logic()` die Post-Zustände in $Q^+$ (`expect` truthy) und $Q^-$ (`expect` falsy), wendet `post_quantor` **ausschließlich auf $Q^+$** an und verknüpft $Q^-$ hart verdrahtet als **Allquantor ($\forall$)** per Konjunktion (`AND`): `satisfies_pos and not any(t.evaluation for t in negatives)`. Ein einzelnes `expect=False` überstimmt damit ein positives Match im `"exists"`-Modus; bei rein negativen Listen ($Q^+ = \emptyset$) wird `post_quantor` sogar vollständig wirkungslos.
   - **Abgrenzung:** `EBT(..., expect=False)` (Vertragsebene) überschreibt die Quantoren dagegen **nicht** — es negiert lediglich das fertig quantifizierte Gesamtergebnis am Ende (`ebt.py:302`). `pre[i].expect` wird stillschweigend ignoriert.
   - **Historische Präzisierung:** Dieser Mechanismus entstand **nicht erst** durch die jüngsten Aufträge (`1e0794d8` / `adef18e8`), sondern war **bereits seit Commit `4a129d55` (28. August 2026)** exakt so im Core angelegt. Die jüngsten Commits haben ihn jedoch durch **Meta-Gate 3 (`1e0794d8`)**, die **Quantor-Erweiterung (`adef18e8`)** und die **ausgelagerten Guides (`bc59a5f7`, `eb42f402`)** tief in der Test-Suite und Dokumentation zementiert.
   - **Kritisches Hinterfragen (Prädikatenlogische Warnung):** Ein naives „`WorldState.expect=False` einfach unter `post="exists"` mit `OR` (`any`) auswerten“ wäre **mathematisch fatal**, da `any(sat(t))` bei negierten Zuständen massive *False Positives* erzeugt und Verbote unwirksam macht (Nachweis in Abschnitt 1.3). Eine saubere Reparatur erfordert daher eine klare Architekturentscheidung (**Option A: `STATE-GUARD` erzwingt `post="all"` für `WorldState.expect=False`** oder **Option B: Abschaffung/Deprecation von `WorldState.expect`**).

2. **Betroffene Tests in der Test-Suite:**
   - **9 Testdateien (21 Testfunktionen)** prüfen und erzwingen aktiv genau dieses `post="exists"` + `WorldState.expect=False`-Veto-Verhalten (allen voran `tests/tests_ebt/test_ebt_quantors.py`, sowie die in Commit `1e0794d8` umgebauten Tests in `test_ebt_returns.py`, `test_ebt_exception_contracts.py`, `test_ebt_return_reporting.py`, `test_ebt_run_isolation.py`, `test_ebt_arena_mutation.py`, plus `test_ebt_contract_mutation.py`, `test_ebt_persistent_reports.py`, `test_offline_core.py`).
   - **2 weitere Testdateien** (`test_ebt_quantor_declaration.py`, `test_ebt_args_normalization.py`) testen `WorldState.expect=False` unter explizitem `post={"quantor": "all", ...}` (unter Option A weiterhin logisch rein!).
   - **3 strukturelle Wächter-Tests** (`tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `tests/test_styleguide.py` via `DocEnsurance`) zementieren das gemischte $Q^+/Q^-$-Muster statisch bzw. über die ausführbaren Doku-Snippets.

3. **Betroffene Dokumentation:**
   - Alle **4 genannten Guides** (`GUIDE_Expect-Flags.md`, `GUIDE_Quality-Assurance.md`, `GUIDE_Quantifiers.md`, `GUIDE_Contract-Design.md`) **sowie 5 weitere Dokumente** (`GUIDE_Contract-Semantics.md`, `GUIDE_EBT-Usage-Pattern.md`, `DEV-GUIDE_2-1_EBT-Class.md`, `DEV-GUIDE_2-2_WorldState-Class.md`, `README.md`) müssen gezielt überarbeitet werden. Besonders kritisch: `GUIDE_Contract-Semantics.md` und `DEV-GUIDE_2-1_EBT-Class.md` dokumentieren bislang noch nicht einmal das neue `{"quantor": ..., "states": ...}`-Interface aus `v0.0.8`.

---

## Teil 1: Hinterfragen der Behauptung — Technische & Logische Analyse des Cubie-Core

### 1.1 Was der Quellcode tatsächlich tut

Die gesamte Quantor- und `expect`-Auswertung in `qb-cubie` (v0.0.8) konzentriert sich auf drei Stellen im Core:

1. **Konfiguration & Defaults — [`src/qb_cubie/ebt.py:131-133`](../src/qb_cubie/ebt.py#L131-L133):**
   ```python
   self.pre, self.pre_quantor = self._parse_state_config(pre, "pre", "all")
   self.post, self.post_quantor = self._parse_state_config(post, "post", "exists")
   self.expect = expect
   ```
   Auf den ersten Blick wirken die Defaults sauber: `pre_quantor = "all"`, `post_quantor = "exists"`.

2. **Schritt-Auswertung (`EBT.post`) — [`src/qb_cubie/protocols.py:129-140`](../src/qb_cubie/protocols.py#L129-L140):**
   ```python
   def evaluate_step_logic(traces: List["EvaluationTrace"], post_quantor: Quantor = "exists") -> bool:
       """Evaluate one step's success from positive and negative post-state traces."""
       positives = [t for t in traces if t.post.expect]
       negatives = [t for t in traces if not t.post.expect]
       violates_neg = any(t.evaluation for t in negatives)
       if not positives:
           satisfies_pos = True
       elif post_quantor == "all":
           satisfies_pos = all(t.evaluation for t in positives)
       else:
           satisfies_pos = any(t.evaluation for t in positives)
       return satisfies_pos and not violates_neg
   ```

3. **Lauf-Aggregation (`EBT.pre` & `EBT.expect`) — [`src/qb_cubie/ebt.py:299-302`](../src/qb_cubie/ebt.py#L299-L302):**
   ```python
   steps = self._group_traces_by_step()
   successes = [self._evaluate_step_logic(traces, self.post_quantor) for traces in steps.values()]
   success = all(successes) if self.pre_quantor == "all" else any(successes)
   self._run_evaluation = success if self.expect else not success
   ```

#### Formale Aufschlüsselung: Warum `WorldState.expect` tatsächlich den Quantor überschreibt

Sei $Q$ die Liste der deklarierten Post-Zustände, $m(q) \in \{\top, \bot\}$ das rohe Match-Ergebnis (`t.evaluation = not bool(diffs)`), $Q^+ = \{q \in Q \mid \text{bool}(q.\text{expect}) = \top\}$ und $Q^- = \{q \in Q \mid \text{bool}(q.\text{expect}) = \bot\}$.

`evaluate_step_logic()` berechnet exakt:

$$\text{step\_ok}(p) = \underbrace{\begin{cases} \top & \text{falls } Q^+ = \emptyset \\ \exists q \in Q^+ : m(q) & \text{falls } Q^+ \neq \emptyset \land \text{post\_quantor}=\text{"exists"} \\ \forall q \in Q^+ : m(q) & \text{falls } Q^+ \neq \emptyset \land \text{post\_quantor}=\text{"all"} \end{cases}}_{\text{Quantor gilt NUR für } Q^+} \quad \wedge \quad \underbrace{\neg\big(\exists q \in Q^- : m(q)\big)}_{\equiv\; \forall q \in Q^- : \neg m(q)\; (\text{IMMER Allquantor!})}$$

Damit treten **drei direkte Quantor-Überschreibungen** durch `WorldState.expect` auf:

1. **Verdeckter Quantor-Wechsel auf $Q^-$ ($\forall$ statt $\exists$):** Durch De Morgan gilt $\neg(\exists q \in Q^- : m(q)) \equiv \forall q \in Q^- : \neg m(q)$. Jeder Zustand mit `expect=False` verlässt also die Existenzquantor-Disjunktion (`OR`) und wird zwangsweise **allquantifiziert (`AND`)** — sowohl untereinander als auch gegen $Q^+$.
2. **Veto über positives Existenz-Match:** Im Standard-Modus (`post_quantor="exists"`) führt ein einzelner negativer Zustand dazu, dass ein **tatsächlich erfüllter** positiver Zustand (`m(q) == True`) nicht mehr für den Erfolg ausreicht (`True AND False = False`).
3. **Vollständige Deaktivierung von `post_quantor` bei $Q^+ = \emptyset$:** Besteht `post` ausschließlich aus `expect=False`-Zuständen, setzt `if not positives: satisfies_pos = True` den `post_quantor` komplett außer Kraft — `"exists"` und `"all"` liefern identische Ergebnisse (beide rechnen rein $\forall q \in Q^-: \neg m(q)$).

#### Empirische Verifikation gegen `qb-cubie` (v0.0.8)

Alle Befunde wurden direkt gegen das installierte Paket im Workspace (`.venv/bin/python`) verifiziert:

| Probe | Konfiguration (`EBT`) | `post_quantor` | Rohe Traces (`m(q)`) | Ergebnis (`evaluation`) | Befund |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Case 1** | `target=lambda: 99`, `post=[WS(returns=int), WS(returns=99, expect=False)]` | `"exists"` | `[True, True]` | `False` | `expect=False` überstimmt das positive Existenz-Match (`int`). |
| **Case 2** | `target=lambda: 404`, `post=[WS(returns=404, expect=False), WS(returns=500, expect=False)]` | `"exists"` | `[True, False]` | `False` | `Q+` leer $\rightarrow$ reine Allquantifizierung über `Q-`; `post_quantor` ist tot. |
| **Case 3** | `target=lambda: 99`, `post=[WS(returns=int), WS(returns=99, expect=None)]` | `"exists"` | `[True, True]` | `False` | `expect=None` wird mangels Typ-Guard stillschweigend als `expect=False` (Veto) gewertet! |
| **Case 4** | Erst `post={"quantor": "all", "states": [WS(returns=int)]}`, dann `case.post = [WS(returns=1), WS(returns=2)]`, erneut `.run()` | `"all"` (!) | `[True, False]` | `False` | **Sticky-Quantor-Bug** in `_arrange()` (`ebt.py:170-171`): einfache Liste setzt `post_quantor` nicht auf `"exists"` zurück! |
| **Case 5** | `target=lambda x: x`, `pre=WS(args=1, expect=False)`, `post=WS(returns=1)` | `"exists"` (`pre="all"`) | `[True]` | `True` | `pre.expect=False` wird stillschweigend ignoriert (kein `STATE-GUARD`). |
| **Case 6** | Nur `Q-`: `post={"quantor": "exists", ...}` vs. `post={"quantor": "all", ...}` bei Outcome `200` | `"exists"` vs. `"all"` | `[False, False]` | `True` vs. `True` | Bei leerem `Q+` sind `"exists"` und `"all"` ununterscheidbar. |

#### Klare Differenzierung der drei `expect`-Stellen im Core

| Stelle | Überschreibt Quantoren? | Aktuelles Verhalten | Bewertungs-Fazit |
| :--- | :---: | :--- | :--- |
| **`WorldState.expect` in `post`** | **JA** | Partitioniert `post` in $Q^+$/$Q^-$, erzwingt $\forall$ + `AND`-Veto auf $Q^-$, macht `post_quantor` bei $Q^+=\emptyset$ wirkungslos. Akzeptiert `None` als `False`. | **Kernursache des Problems.** |
| **`EBT.expect` (Vertragsebene)** | **NEIN** | Invertiert ausschließlich das fertige boolesche Endergebnis nach Auswertung beider Quantoren (`ebt.py:302`). | **Sauber.** (Einzige Härtung: `isinstance(expect, bool)` per `STATE-GUARD` absichern.) |
| **`WorldState.expect` in `pre`** | **NEIN** *(aber tote Konfiguration)* | Wird nirgends in `ebt.py` ausgewertet, lediglich in `TempFS.get_state()` (`tempfs.py:98`) / `PyVenv.get_state()` (`pyvenv.py:138`) nach `outcome.expect` kopiert. | **Stille Fehlerquelle** — sollte per `STATE-GUARD` abgelehnt werden, wenn `expect` nicht `True` ist. |

---

### 1.2 Historische Einordnung: Woher der Bug wirklich kommt

Deine Vermutung in `GEMINI-1.md` war:
> *„Das war vermutlich mein Fehler, weil ich den Auftrag dazu gab, ohne mir die Details genau anzusehen. […] Aufgrund der Entstehungs-Historie von diesem Bug wird er vermutlich auch innerhalb des Testsuite selbst eingebettet sein.“*

Die Git-Historie zeigt ein differenzierteres Bild in **drei Phasen**:

1. **Ursprung bereits am 28. August 2026 — Commit `4a129d55` (*„Quantors added and async-ready-preps integrated.“*):**
   Bereits die allererste Quantor-Implementierung in `src/ebt.py` führte `WorldState.expect` und `_evaluate_step_logic()` exakt mit der Aufspaltung `positives` / `negatives` + `satisfies_pos and not violates_neg` ein — zusammen mit den ersten Tests in `tests/tests_ebt/test_ebt_quantors.py`. Der Fehler entstand also **nicht** erst durch deinen Auftrag vom 18. November 2026.
2. **Verfestigung durch Meta-Gate 3 — Commit `1e0794d8` (18. November 2026):**
   Weil `if not positives: satisfies_pos = True` den *Vacuous Pass* ermöglichte, wurde Meta-Gate 3 (`META-EBT-LONELY-NEGATION`) gebaut. Statt `WorldState.expect=False` im `"exists"`-Modus abzuschaffen, wurden alle **10** gefundenen „einsame Negation“-Tests in **6 Testdateien** so umgebaut, dass jedes `expect=False` neben einem positiven `WorldState` im selben Standard-`post=[pos, neg]` steht. Damit wurde das **gemischte `exists`+`AND`-Veto-Muster** breit in die bestehende Test-Suite eingebettet.
3. **Kodifizierung in Quantor-Deklaration & Doku — Commits `adef18e8`, `bc59a5f7`, `eb42f402` (18./19. November 2026):**
   Bei der Implementierung der expliziten Quantor-Deklaration (`{"quantor": ..., "states": ...}`) wurde `evaluate_step_logic()` nach `protocols.py` verschoben und `post_quantor` lediglich als `if/elif`-Zweig auf `positives` aufgepfropft, während `negatives` unangetastet als hartes `AND`-Veto blieben. Anschließend wurden die neuen Handbücher (`GUIDE_Expect-Flags.md`, `GUIDE_Quantifiers.md`, `GUIDE_Quality-Assurance.md`) genau auf diese gemischte Semantik ausgerichtet.

---

### 1.3 Kritisches Hinterfragen: Die prädikatenlogische Falle bei naiver Reparatur

**Achtung — wichtigster Denkpunkt vor jeder Code-Änderung:**
Man könnte reflexartig versuchen, `evaluate_step_logic()` „einfach zu reparieren“, indem man jeden `WorldState` individuell nach seinem `expect`-Flag auswertet:

```python
# ACHTUNG: NAIVER, FEHLERHAFTER REPARATURVERSUCH!
def naive_sat(trace: EvaluationTrace) -> bool:
    return trace.evaluation if trace.post.expect else (not trace.evaluation)

# post_quantor == "exists": any(naive_sat(t) for t in traces)
# post_quantor == "all":    all(naive_sat(t) for t in traces)
```

**Warum diese naive Umsetzung im Standard-Modus (`post_quantor="exists"`) brandgefährlich ist**, zeigt die Wahrheitstabelle:

| Vertrag (`post_quantor="exists"`, Standard) | Beobachtete Rückgabe | `sat(q0)` | `sat(q1)` | Naives `any` (`OR`) | Fachliches Urteil |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `[WS(returns=85), WS(returns=-10, expect=False)]` | **`999`** (komplett falsch!) | `False` | `True` *(999 != -10)* | **`True` (GRÜN!)** | **Katastrophaler False Positive:** jeder Schrottwert ungleich `-10` besteht! |
| `[WS(returns=int), WS(returns=-10, expect=False)]` | **`-10`** (explizit verboten!) | `True` *(-10 ist int)* | `False` *(-10 == -10)* | **`True` (GRÜN!)** | **Verbot tot:** das positive Match überstimmt `expect=False` vollständig! |
| `[WS(returns=404, expect=False), WS(returns=500, expect=False)]` | **`404`** (explizit verboten!) | `False` *(404 == 404)* | `True` *(404 != 500)* | **`True` (GRÜN!)** | **Verbote heben sich gegenseitig auf:** `404` besteht, weil es nicht `500` ist! |

**Mathematische Erkenntnis:**
Ein Verbot (`expect=False`, also $\neg m(q)$) ist von Natur aus eine **einschränkende Bedingung (Konjunktion / `AND`)**. In einer **Disjunktion (`OR` / `"exists"`)** ist $\neg m(q)$ semantisch fast immer nutzlos oder brandgefährlich, weil $\phi \lor \neg \psi$ bereits wahr wird, sobald das Ziel irgendetwas außerhalb von $\psi$ zurückgibt.
Umgekehrt ist unter **`post_quantor="all"` (`AND`)** die reine, einheitliche Formel

$$\forall t \in \text{post} : \text{sat}(t) \quad \text{mit} \quad \text{sat}(t) = \begin{cases} m(t) & \text{falls } t.\text{post.expect} = \top \\ \neg m(t) & \text{falls } t.\text{post.expect} = \bot \end{cases}$$

**100 % logisch rein, symmetrisch und ohne jede Quantor-Überschreibung!** Denn:

$$\forall t \in Q : \text{sat}(t) \;\equiv\; \Big(\forall q \in Q^+ : m(q)\Big) \;\wedge\; \Big(\forall q \in Q^- : \neg m(q)\Big)$$

---

### 1.4 Architekturelle Reparatur-Optionen für den Cubie-Core

Aus dem Ziel *„`EBT.pre` = All-Quantor, `EBT.post` = Existenz-Quantor als Standard, und der `expect`-Flag darf das Quantor-Verhalten nicht überschreiben“* ergeben sich genau **zwei logisch konsistente Core-Reparaturen** (plus eine verworfene Option C):

| Option | Kern-Regel im Core | Verhalten von `EBT.post` (Standard `"exists"`) | Verhalten von `post={"quantor": "all", ...}` | Bewertung |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Empfohlen):** **`STATE-GUARD` für `WorldState.expect=False` unter `post="exists"`** | `evaluate_step_logic()` wertet **einheitlich ohne `Q+`/`Q-`-Split** aus (`all(sat)` vs. `any(sat)`). Zusätzlich verbietet ein **`STATE-GUARD`** im `_arrange()`/`_parse_state_config()` jedes `WorldState(expect=False)` in `post`, sobald `post_quantor == "exists"` *(und `expect=False` in `pre` sowie nicht-boolesches `expect` wie `None` überall)*. | **Reiner Existenz-Quantor ($\exists q \in Q : m(q)$).** Kein `expect=False` erlaubt $\rightarrow$ kein implizites Umschreiben auf `AND`, kein *Vacuous Pass*, keine *False Positives*. | **Reiner All-Quantor ($\forall q \in Q : \text{sat}(q)$).** Positive Bedingungen und `expect=False`-Verbote funktionieren hier vollständig homogen per `all(sat(t))`. *(Optional: `STATE-GUARD` gegen rein negative Listen ohne positiven Zustand oder Meta-Gate 3 beibehalten.)* | **Beste Balance:** Härtet den Core kompromisslos, behält `WorldState.expect=False` dort, wo es logisch sauber ist (`post="all"`), und erzwingt explizite Klarheit statt versteckter Magie. |
| **Option B (Radikal minimal):** **`WorldState.expect` entfernen / deprecaten** | `WorldState` verliert das Feld `expect` (oder es wird als veraltet per `STATE-GUARD` abgewiesen). Negation geschieht ausschließlich über `EBT(..., expect=False)` (Vertragsebene) oder direkt im Prädikat (`lambda v: v != 99`). | **Reiner Existenz-Quantor ($\exists q \in Q : m(q)$).** | **Reiner All-Quantor ($\forall q \in Q : m(q)$).** | **Maximal einfach & orthogonal** (nur noch ein einziges `expect`-Konzept in der gesamten API), aber **Breaking Change** für alle Nutzer von `WorldState.expect=False` (auch bei `post="all"` und `raises`/`fs`/`arena`-Negationen, für die Prädikate umständlicher sind). |
| **Option C (Status quo dokumentieren):** Zwei-Klassen-Semantik behalten | `evaluate_step_logic()` bleibt unverändert `(Quantor(Q+)) AND (ALL(NOT Q-))`, wird aber ehrlich nicht mehr als reiner Existenzquantor bezeichnet. | Kein reiner Existenzquantor, sondern Disjunktion mit Veto-Filter. | Konjunktion mit Veto-Filter. | **Verfehlt deine Zielvorgabe** (*„Der expect-Flag darf das Verhalten der Quantoren nicht überschreiben“*). |

#### Zusätzliche Core-Härtungen (unabhängig von Option A oder B empfohlen)

1. **Typ-Guard auf `WorldState.expect` (`protocols.py:73, 80-92`) und `EBT.expect` (`ebt.py:133`):** `expect` muss strikt `bool` sein (`isinstance(val, bool)`), nicht `Optional[bool]`. `expect=None` darf nicht stillschweigend als `False` interpretiert werden (`TypeError("STATE-GUARD: ...")`).
2. **Guard gegen `pre.expect=False` (`ebt.py`):** Ein `WorldState(..., expect=False)` in `pre` darf nicht stillschweigend wirkungslos bleiben, sondern muss vor der Ausführung mit `ValueError("STATE-GUARD: ...")` abgelehnt werden.
3. **Fix des Sticky-Quantor-Bugs bei Mutation (`ebt.py:170-171`):**
   Aktuell speichert `EBT` in `__init__` die entpackte Liste in `self.pre` / `self.post` und übergibt in `_arrange()` `self.pre_quantor` / `self.post_quantor` als `default_quantor`. Wird `case.post = [ws1, ws2]` nach einem `{"quantor": "all", ...}`-Lauf neu zugewiesen, bleibt `post_quantor` irrtümlich auf `"all"` kleben (Case 4).
   - **Saubere Lösung:** `self._post_list_ref` / Property-Setter für `pre` und `post` nutzen, sodass eine Neuzuweisung `case.post = [...]` (ohne Dict-Wrapper) `self.post_quantor` sauber auf `"exists"` zurücksetzt (und `case.pre = [...]` auf `"all"`), während In-Place-Mutationen derselben Liste den zuvor deklarierten Quantor behalten (und weiterhin revalidiert werden).

---

## Teil 2: Verantwortliche und betroffene Tests in der Test-Suite

### 2.1 Übersicht (Baseline-Lauf auf `HEAD` `312e84d5`)

Ein gezielter Lauf der Quantor- und Meta-Gate-Tests auf `HEAD` zeigt, dass die aktuelle Test-Suite vollständig grün läuft und das bisherige Verhalten fest absichert:
- `.venv/bin/python -m pytest -q tests/tests_ebt/test_ebt_quantors.py tests/tests_ebt/test_ebt_quantor_declaration.py tests/tests_ebt/test_ebt_args_normalization.py tests/tests_meta/` $\rightarrow$ **`283 passed in 16.75s`**.

Eine vollständige AST- und Referenz-Analyse über alle Dateien unter `tests/` identifiziert **14 betroffene Testdateien** in **3 klaren Verantwortungs-Kategorien**.

---

### 2.2 Kategorie 1: Direkt verantwortliche Tests — Erzwingen `WorldState.expect=False` als `AND`-Veto unter Standard-`post` (`post_quantor="exists"`)

Diese **9 Dateien (21 Testfunktionen)** sind unmittelbar dafür verantwortlich, dass eine Core-Reparatur (Option A oder B) sofort rot wird, weil sie das Überschreiben des Standard-Existenzquantors durch `WorldState.expect=False` als Soll-Verhalten voraussetzen:

| # | Testdatei & Zeilen | Testfunktion(en) | Aktuelles Muster (Standard `post="exists"`) | Ursache / Entstehung & Migrationsrichtung |
| :-: | :--- | :--- | :--- | :--- |
| **1** | [`tests/tests_ebt/test_ebt_quantors.py:113-158`](../tests/tests_ebt/test_ebt_quantors.py#L113-L158) | `test_mixed_expect_exists_green`, `test_mixed_expect_exists_red_lower_bound`, `test_mixed_expect_exists_red_upper_bound` | `post=[WS(returns=0, expect=False), WS(1..5), WS(returns=6, expect=False)]` | **Hauptverantwortlich (seit `4a129d55`)!** Mischt explizit 5 positive Alternativen mit 2 negativen Veto-Filtern im `"exists"`-Modus. *(Hinweis: In diesem konkreten Beispiel sind `0` und `6` sogar logisch redundant/subsumiert durch `{1..5}`!)* Migration: auf reines `exists` oder `post={"quantor": "all", "states": [WS(returns=lambda v: 0 <= v <= 6), WS(0, expect=False), WS(6, expect=False)]}` umstellen. |
| **2** | [`tests/tests_ebt/test_ebt_quantors.py:181-232`](../tests/tests_ebt/test_ebt_quantors.py#L181-L232) | `test_local_expect_false_green`, `test_local_expect_false_red`, `test_negative_filters_green`, `test_negative_filters_red` | `post=[WS(returns=int), WS(returns=99, expect=False)]` und `post=[WS(returns=lambda s: 200<=s<600), WS(404, expect=False), WS(500, expect=False)]` | **In `1e0794d8` (Meta-Gate 3) umgebaut!** Prüft direkt, dass ein positives Match (`int` / Range `200..600`) durch `expect=False` überstimmt wird. Bei Option A: explizit `post={"quantor": "all", "states": [...]}` setzen (und neuen `STATE-GUARD`-Test ergänzen, dass genau das unter Default-`exists` abgewiesen wird!). |
| **3** | [`tests/tests_ebt/test_ebt_returns.py:87-123`](../tests/tests_ebt/test_ebt_returns.py#L87-L123) | `test_negative_none_contract_accepts_non_none_values`, `test_negative_none_contract_rejects_none` | `post=[WS(returns=int), WS(returns=None, expect=False)]` | In `1e0794d8` umgebaut (zuvor einsames `WS(returns=None, expect=False)`). Bei Option A: `post={"quantor": "all", "states": [...]}` verwenden. |
| **4** | [`tests/tests_ebt/test_ebt_exception_contracts.py:76-111`](../tests/tests_ebt/test_ebt_exception_contracts.py#L76-L111) | `test_forbidden_exception_accepts_allowed_exception_message`, `test_forbidden_exception_rejects_matching_exception_message` | `post=[WS(raises=ValueError), WS(raises=match("^invalid order:"), expect=False)]` | In `1e0794d8` umgebaut. Testet direkt das Überschreiben eines passenden `ValueError`-Matches durch das negative Regex-Muster im Default-`exists`-Modus (`[True, True] -> False`). Bei Option A: `post={"quantor": "all", "states": [...]}`. |
| **5** | [`tests/tests_ebt/test_ebt_return_reporting.py:76-126`](../tests/tests_ebt/test_ebt_return_reporting.py#L76-L126) | `test_allowed_falsy_return_passes_with_negative_filter`, `test_forbidden_falsy_return_reports_the_matching_value`, `test_omitted_return_expectation_accepts_non_matching_negative_filter`, `test_omitted_return_expectation_does_not_invent_a_return_comparison` | `post=[WS(returns="allowed"), WS(returns=value, expect=False)]` und `post=[WS(), WS(expect=False)]` | In `1e0794d8` umgebaut. Insbesondere Z. 120 (`[WS(), WS(expect=False)]`) verlässt sich voll darauf, dass `WS(expect=False)` das universelle positive `WS()` überstimmt! Bei Option A: `post={"quantor": "all", "states": [...]}`. |
| **6** | [`tests/tests_ebt/test_ebt_run_isolation.py:41-57`](../tests/tests_ebt/test_ebt_run_isolation.py#L41-L57) *(sowie Z. 172)* | `test_previous_negative_match_does_not_poison_next_run`, `test_previous_positive_match_does_not_mask_next_negative_match` *(und `test_history_is_detached_from_nested_caller_owned_data`)* | `post=[WS(returns=int), WS(returns=0, expect=False)]` | In `1e0794d8` umgebaut. Bei Option A: `post={"quantor": "all", "states": [...]}`. *(Z. 172 mutiert `post.expect = False` erst **nach** `.run()` zum Snapshot-Test — bleibt unter Option A grün, unter Option B anpassen.)* |
| **7** | [`tests/tests_ebt/test_ebt_contract_mutation.py:14-45`](../tests/tests_ebt/test_ebt_contract_mutation.py#L14-L45) | `test_replacing_return_contract_cannot_rewrite_the_verdict` (`forbidden=True`) | `post = WorldState(returns=7, expect=not forbidden)` (einzelner negativer Zustand im Standard-`exists`-Modus!) | Ursprünglicher Audit-Test (B1). Wenn Option A `expect=False` bei `post="exists"` generell per `STATE-GUARD` ablehnt, muss der `forbidden=True`-Fall explizit `post={"quantor": "all", "states": post}` (oder `EBT(..., expect=False)`) nutzen. |
| **8** | [`tests/tests_ebt/test_ebt_persistent_reports.py:136-150`](../tests/tests_ebt/test_ebt_persistent_reports.py#L136-L150) | `test_json_retains_every_input_and_post_match_including_negative_states` | `post=[WS(returns=int), WS(returns=2, expect=False)]`, `assert document["evaluation"] is False` | Verlangt im impliziten `exists`-Modus, dass `2` trotz `int`-Match wegen `expect=False` scheitert. Bei Option A: `post={"quantor": "all", "states": [...]}`. |
| **9** | [`tests/test_offline_core.py:160-166`](../tests/test_offline_core.py#L160-L166) | `feature == "ebt"` (Offline-Smoke-Test) | `post=[WS(returns=3), WS(returns=99, expect=False)]` | Mischt positives + negatives Muster im Standard-`exists`-Modus. Migration: entweder nur positives `WS(returns=3)` oder explizites `post={"quantor": "all", ...}`. |
| **10** | [`tests/tests_arena/test_ebt_arena_mutation.py:99-112`](../tests/tests_arena/test_ebt_arena_mutation.py#L99-L112) | `test_volatile_metadata_with_strict_expectation_red` | `post=[WS(returns=True), WS(arena=PyVenv(BASE_ARENA), expect=False)]` + `expect=False` | In `1e0794d8` umgebaut. Doppel-Negation, die darauf basiert, dass `expect=False` das positive `WS(returns=True)` im Default-`exists`-Modus überstimmt. Bei Option A: `post={"quantor": "all", "states": [...]}` (oder noch sauberer ohne Doppel-Negation direkt mit `post=WS(returns=True, arena=PyVenv(BASE_ARENA))` + `EBT(..., expect=True)` / Gegenprobe!). |

---

### 2.3 Kategorie 2: Tests mit explizitem `post={"quantor": "all", ...}` + `expect=False` (2 Dateien)

Diese Tests kombinieren `WorldState.expect=False` **bereits** ausschließlich mit explizitem `post={"quantor": "all", ...}`:

| # | Testdatei & Zeilen | Testfunktion | Bewertung unter Option A vs. Option B |
| :-: | :--- | :--- | :--- |
| **11** | [`tests/tests_ebt/test_ebt_quantor_declaration.py:387-434`](../tests/tests_ebt/test_ebt_quantor_declaration.py#L387-L434) | `test_post_quantor_all_with_negative_worldstate_expect_false` | **Option A:** Bleibt **100 % gültig und logisch rein!** Zusätzlich fehlen hier aber neue Guard-Tests (Gruppe E) für: (a) Ablehnung von `WorldState.expect=False` unter `post="exists"` (implizit & explizit), (b) Ablehnung von `pre.expect=False`, (c) Ablehnung von `expect=None` / Nicht-`bool`, (d) Rücksetzen des Quantors bei Neuzuweisung `case.post = [...]` (Sticky-Quantor-Fix). **Option B:** Muss auf Prädikat/Vertrags-`expect` umgestellt werden. |
| **12** | [`tests/tests_ebt/test_ebt_args_normalization.py:338-381`](../tests/tests_ebt/test_ebt_args_normalization.py#L338-L381) | `test_explicit_post_all_with_negative_filter_worldstate` | **Option A:** Bleibt **100 % gültig** (nutzt bereits `post={"quantor": "all", ...}`). **Option B:** Umstellung auf Prädikat. |

---

### 2.4 Kategorie 3: Strukturelle Wächter & Lebende Doku-Tests (3 Dateien — kritisch!)

Diese 3 Dateien testen nicht nur Einzelfälle, sondern **erzwingen systemweit** die bisherige `Q+`/`Q-`-Semantik:

1. **[`tests/tests_meta/test_gate_3.py`](../tests/tests_meta/test_gate_3.py) (`META-EBT-LONELY-NEGATION`, gesamte Datei, insb. Z. 67–153, 177–178):**
   - **Rolle am Problem:** Meta-Gate 3 war der **Auslöser** dafür, dass in Commit `1e0794d8` alle 10 älteren Tests auf `post=[WorldState(...), WorldState(..., expect=False)]` im Standard-`exists`-Modus umgebaut wurden — seine Clean-Probes (`Z. 177-178`) deklarieren genau dieses gemischte `exists`+`expect=False`-Muster ausdrücklich als „sauber“!
   - **Zusätzlicher blinder Fleck:** `_extract_post_worldstates()` (`Z. 77-94`) kennt das neue Dict-Wrapper-Format `{"quantor": ..., "states": ...}` noch gar nicht und gibt bei jedem `cst.Dict` pauschal `None` zurück!
   - **Anpassungsbedarf:**
     - Unter **Option A**: Gate 3 auf den Dict-Wrapper erweitern (`post={"quantor": "all", "states": [...]}` parsen, damit einsame Negationen auch im Wrapper erkannt werden); die bisherigen Clean-Probes `Z. 177-178` auf `post={"quantor": "all", "states": [...]}` umstellen (oder ein neues Gate / eine Regel ergänzen, die statisch vor `expect=False` im impliziten `exists`-Modus warnt).
     - Unter **Option B**: Gate 3 wird gegenstandslos bzw. wandelt sich zu einem Verbot von `WorldState(..., expect=...)`.

2. **[`tests/tests_meta/test_gate_2.py`](../tests/tests_meta/test_gate_2.py) (`META-EBT-CROSS-PRODUCT`, Z. 71–105, 167–168, 216–219):**
   - **Rolle am Problem:** `_is_positive_worldstate()` (`Z. 71-88`) und `_count_positive_post_states()` (`Z. 98-104`) spiegeln direkt die alte $Q^+/Q^-$-Aufspaltung wider (inklusive `expect=None` als negativ!).
   - **Zusätzlicher blinder Fleck:** Auch Gate 2 ignoriert das Dict-Wrapper-Format `{"quantor": ..., "states": ...}` komplett (`_count_pre_states` / `_count_positive_post_states` prüfen nur `cst.List` / `cst.Tuple` und liefern bei `cst.Dict` immer `1`!).
   - **Anpassungsbedarf:** Dict-Wrapper-Unterstützung nachrüsten (bei `post={"quantor": "all", ...}` ist eine Mehrfach-Prädikat-Liste logisch eine Konjunktion und *kein* unterspezifiziertes Kreuzprodukt; bei `post={"quantor": "exists", ...}` hingegen schon!).

3. **[`tests/test_styleguide.py:107-120`](../tests/test_styleguide.py#L107-L120) (`test_docs_code_examples` via `DocEnsurance`):**
   - Führt **alle** Python-Beispiele in `docs/` (inkl. `GUIDE_Expect-Flags.md` Z. 39–57, 80–101, 154–177 und `GUIDE_EBT-Usage-Pattern.md` Z. 147–169) live gegen den Core aus!
   - Jede Reparatur im Core, die `WorldState.expect=False` unter `post="exists"` abweist, lässt `test_docs_code_examples` sofort scheitern, bis die betroffenen Dokumentations-Beispiele synchron aktualisiert wurden.

### 2.5 Unkritische Tests (kein Handlungsbedarf)

Alle Tests, die ausschließlich **`EBT(..., expect=False)`** auf Vertragsebene mit positiven `post`-Zuständen nutzen — darunter `tests/tests_ebt/test_ebt_demo.py`, `tests/tests_ebt/test_ebt_ignores.py`, `tests/tests_ebt/test_ebt_fs.py`, `tests/tests_ebt/test_ebt_fs_collisions.py`, `tests/tests_ebt/test_ebt_state_validation.py` sowie die `EBT(..., expect=False)`-Fälle in `test_ebt_quantors.py` (Z. 33–44, 61–72, 94–108, 171–178) — sind **nicht betroffen**, weil `EBT.expect` die Quantoren nicht überschreibt.

---

## Teil 3: Dokumentations-Audit — Welche Docs an welchen Stellen überarbeitet werden müssen

### 3.1 Die vier in `GEMINI-1.md` genannten Kern-Handbücher

#### 1. [`docs/GUIDE_Expect-Flags.md`](../docs/GUIDE_Expect-Flags.md) *(höchster Überarbeitungsbedarf)*

| Abschnitt & Zeilen | Aktueller Inhalt (Problem) | Erforderliche Überarbeitung (unter Option A / sinngemäß Option B) |
| :--- | :--- | :--- |
| **Einleitung** ([Z. 8](../docs/GUIDE_Expect-Flags.md#L8)) | Beschreibt *„Soll-Ziele und Negativ-Filter im selben `post`“* und *„Vacuous Pass“* als allgemeines Muster ohne Quantor-Bindung. | Klarstellen, dass `expect` **niemals** Quantoren überschreibt: `WorldState.expect=False` ist (bei Option A) ausschließlich im konjunktiven `post={"quantor": "all", ...}` zulässig; im Standard-`post` (`"exists"`) gelten nur erlaubte Alternativen. |
| **Abschnitt 1: Tabelle & Auswertungsregel** ([Z. 22–32](../docs/GUIDE_Expect-Flags.md#L22-L32)) | Tabelle Z. 28 definiert `WorldState(..., expect=True)` als $Q^+$ („mindestens ein positives Muster“) und `expect=False` als Veto $Q^-$. Absatz Z. 31 formuliert die alte Zweiklassen-Regel (*„Mindestens ein positives Muster … und kein negatives Muster“*) und dokumentiert `pre.expect` als „steuert nicht“. | Tabelle und Regel komplett bereinigen: **Strikte Orthogonalität** dokumentieren (`EBT.expect` negiert den gesamten Vertrag; `WorldState.expect=False` ist unter Option A nur im `post={"quantor": "all", ...}`-Vertrag erlaubt und wird bei `post="exists"` sowie in `pre` per `STATE-GUARD` abgewiesen). |
| **Abschnitt 2: Best Practice 1 (Code-Snippet)** ([Z. 35–66](../docs/GUIDE_Expect-Flags.md#L35-L66)) | Live-Beispiel nutzt `post=[WorldState(returns=85), WorldState(returns=lambda v: v < 0, expect=False)]` im impliziten Standard-`exists`-Modus! *(Wird von `DocEnsurance` ausgeführt!)* | Auf explizites `post={"quantor": "all", "states": [WorldState(returns=85), WorldState(returns=lambda value: value < 0, expect=False)]}` umstellen (oder unter Option B durch ein einzelnes Prädikat / `EBT(..., expect=False)` ersetzen) — und genau erklären, **warum** hier `"all"` zwingend nötig ist! |
| **Abschnitt 3: Best Practice 2 (Bug-Nachweis-Snippet)** ([Z. 69–112](../docs/GUIDE_Expect-Flags.md#L69-L112)) | Live-Beispiel nutzt `post=[WorldState(returns=lambda v: v >= 0), WorldState(returns=-10, expect=False)]` im impliziten Standard-`exists`-Modus. | Auf `post={"quantor": "all", "states": [...]}` umstellen (oder bei Option B über `EBT(..., expect=False)` am Bug-Muster / positives Soll-Gesetz). |
| **Abschnitt 5: Anti-Pattern „einsame Negation“** ([Z. 150–188](../docs/GUIDE_Expect-Flags.md#L150-L188)) | Live-Beispiel baut direkt auf der alten Sonderregel *„bei leerem $Q^+$ gilt der positive Teil automatisch als erfüllt“* auf und zeigt `post=WorldState(returns=-1, expect=False)` (einsam im Standard-`exists`) vs. `post=[WorldState(returns=int), WorldState(returns=-1, expect=False)]` (gemischt im Standard-`exists`). | Komplett neu zuschneiden: Zeigen, dass der **`STATE-GUARD`** das Mischen von `expect=False` mit dem Standard-Existenzquantor (`"exists"`) bereits vorab blockiert, und das *Vacuous-Pass*-Risiko gezielt für `post={"quantor": "all", "states": [WorldState(returns=-1, expect=False)]}` (reines Verbot ohne positives Ziel) erklären. |

---

#### 2. [`docs/GUIDE_Quality-Assurance.md`](../docs/GUIDE_Quality-Assurance.md)

| Abschnitt & Zeilen | Aktueller Inhalt (Problem) | Erforderliche Überarbeitung |
| :--- | :--- | :--- |
| **Baustein B (`expect`-Flags)** ([Z. 81–91](../docs/GUIDE_Quality-Assurance.md#L81-L91)) | Punkt 1 (Z. 85) empfiehlt das Mischen von `expect=True` und `expect=False` in `post` ohne Hinweis auf `quantor="all"`; `CAUTION`-Box (Z. 88–89) verweist auf die bisherige *Vacuous-Pass*-Mechanik im Standard-`post`. | Klarstellen, dass `expect` die Standard-Quantoren (`pre="all"`, `post="exists"`) **nicht** überschreibt; Verbote neben positiven Bedingungen erfordern explizit `post={"quantor": "all", ...}` (Option A) bzw. Prädikate/`EBT.expect` (Option B). |
| **Baustein C (`all` vs. `exists`)** ([Z. 93–105](../docs/GUIDE_Quality-Assurance.md#L93-L105)) | Nennt die Standardregeln (`pre="all"`, `post="exists"`), aber Z. 98 sagt einschränkend *„mindestens ein **erlaubtes** Zielmuster“* und erwähnt die Unveränderlichkeit gegenüber `expect` nicht. | Formulierung zu **„mindestens ein Zielmuster“** glätten und explizit hervorheben: *Die Standard-Quantoren gelten strikt und werden von keinem `expect`-Flag umgeschrieben.* |
| **Spickzettel-Tabelle** ([Z. 112](../docs/GUIDE_Quality-Assurance.md#L112)) | Empfiehlt `WorldState(..., expect=True)` + `WorldState(..., expect=False)` ohne `post={"quantor": "all", ...}`. | Auf `post={"quantor": "all", "states": [...]}` präzisieren (bzw. unter Option B auf Prädikat/`EBT.expect`). |
| **Schritt 4 TGD** ([Z. 150](../docs/GUIDE_Quality-Assurance.md#L150)) & **Abschnitt 5, Punkt 1** ([Z. 173](../docs/GUIDE_Quality-Assurance.md#L173)) | Empfiehlt pauschal das Umdrehen eines `WorldState` über `expect=False` am selben Zustand. | Präzisieren, dass die Negation eines Vertrags über `EBT(..., expect=False)` oder eines einzelnen Verbots nur innerhalb eines expliziten `post={"quantor": "all", ...}`-Vertrags erfolgt. |
| **Abschnitt 4: Hoare-Analogie** ([Z. 162](../docs/GUIDE_Quality-Assurance.md#L162)) | Schreibt wörtlich die alte Semantik fest: *„Jeder ausgeführte Eingang aus `pre` muss mindestens einen positiven Zustand aus `post` (`expect=True`) erfüllen und darf keinen negativen Zustand (`expect=False`) verletzen.“* | Aktualisieren auf das saubere Standard-Verhalten (`pre` = Allquantor, `post` = Existenzquantor; explizit umkehrbar über `{"quantor": ..., "states": ...}`) ohne verdeckte `expect`-Überschreibung. |

---

#### 3. [`docs/GUIDE_Quantifiers.md`](../docs/GUIDE_Quantifiers.md)

| Abschnitt & Zeilen | Aktueller Inhalt (Problem) | Erforderliche Überarbeitung |
| :--- | :--- | :--- |
| **Abschnitt 1: Standardregeln** ([Z. 22–29](../docs/GUIDE_Quantifiers.md#L22-L29)) | Z. 27 spricht von *„mindestens einem der **erlaubten** Zielmuster“* — impliziert die $Q^+$/$Q^-$-Aufspaltung. | Zu einer klaren, ausnahmslosen Aussage schärfen: `pre` ist standardmäßig ein **reiner Allquantor** (`"all"`), `post` ist standardmäßig ein **reiner Existenzquantor** (`"exists"`). Beide lassen sich ausschließlich über den Quantor-Wrapper umstellen — niemals implizit über `expect`. |
| **Abschnitt 2: `post` mit `"all"`** ([Z. 33–36](../docs/GUIDE_Quantifiers.md#L33-L36)) | Z. 35: *„Verbotene Werte (`expect=False`) bleiben dabei natürlich weiterhin strikte Verbote“* (klingt nach einer zusätzlichen Sonderregel). | Bei Option A klarer formulieren: Gerade **weil** `post` hier auf `"all"` steht, wirken positive und negative (`expect=False`) `WorldState`-Einträge völlig einheitlich unter demselben Allquantor (UND-Verknüpfung). Optional ein kurzes Beispiel mit `expect=False` direkt hier verankern. |
| **Abschnitt 4: Leitplanken & `STATE-GUARD`s** ([Z. 102–111](../docs/GUIDE_Quantifiers.md#L102-L111)) | Z. 105 und Z. 110 erwähnen nicht, dass `WorldState.expect=False` im `"exists"`-Modus (und in `pre`) ein `STATE-GUARD`-Fehler ist und dass `expect` nur `bool` akzeptiert. | Die neuen `STATE-GUARD`-Invarianten explizit aufnehmen: (1) kein `WorldState.expect=False` bei `post_quantor="exists"`, (2) kein `pre.expect=False`, (3) `expect` strikt `bool`, (4) Neuzuweisung einer einfachen Liste ohne Wrapper stellt den Standard-Quantor wieder her. |

---

#### 4. [`docs/GUIDE_Contract-Design.md`](../docs/GUIDE_Contract-Design.md)

| Abschnitt & Zeilen | Aktueller Inhalt (Problem) | Erforderliche Überarbeitung |
| :--- | :--- | :--- |
| **Abschnitt 2: Anti-Pattern** ([Z. 143](../docs/GUIDE_Contract-Design.md#L143)) | *„`pre` wirkt als Allquantor (für jede Eingabe) und **die positiven Zustände** in `post` wirken als Existenzquantor…“* | Einschränkung *„die positiven Zustände“* entfernen $\rightarrow$ *„`pre` wirkt standardmäßig als Allquantor und `post` als reiner Existenzquantor“*. |
| **Weiterführender Tipp** ([Z. 181–182](../docs/GUIDE_Contract-Design.md#L181-L182)) | Verweist auf `GUIDE_Expect-Flags.md` für *„erwartete und verbotene Ergebnisse über `expect`-Flags kombinieren“*. | Ergänzen, dass Kombinationen aus positiven und verbotenen Bedingungen explizit `post={"quantor": "all", ...}` voraussetzen (oder gemäß gewählter Option B anpassen). |

---

### 3.2 Weitere betroffene Dokumente im Repository (nicht in `GEMINI-1.md` gelistet, aber zwingend mitzuziehen!)

Diese **5 Dokumente** gehören direkt zur offiziellen Produkt- und Entwickler-Dokumentation und enthalten die alte $Q^+/Q^-$-Semantik (und teils zusätzlich veraltete Stände ohne Dict-Wrapper):

| Dokument | Betroffene Stellen (Zeilen) | Konkreter Befund & Änderungsbedarf |
| :--- | :--- | :--- |
| **[`docs/GUIDE_Contract-Semantics.md`](../docs/GUIDE_Contract-Semantics.md)** *(Single Source of Truth!)* | [Z. 25–26](../docs/GUIDE_Contract-Semantics.md#L25-L26), [Z. 30–31](../docs/GUIDE_Contract-Semantics.md#L30-L31), [Z. 49–66](../docs/GUIDE_Contract-Semantics.md#L49-L66), [Z. 89](../docs/GUIDE_Contract-Semantics.md#L89), [Z. 108–109](../docs/GUIDE_Contract-Semantics.md#L108-L109), [Z. 227–228](../docs/GUIDE_Contract-Semantics.md#L227-L228) | **Kritischster Doku-Befund im gesamten Repo:** (1) Die Tabelle (`Z. 25-26`) und die *Endliche Auswertungsregel* (`Z. 49-66`) dokumentieren noch **nicht einmal** die in `v0.0.8` eingeführte explizite Quantor-Deklaration (`{"quantor": ..., "states": ...}`, `pre_quantor`, `post_quantor`)! (2) `Z. 55-62` kodifiziert wörtlich die überschreibende $Q^+/Q^-$-Sonderformel (`Q+ ist leer ODER mindestens ein q aus Q+ passt UND kein q aus Q- passt`). Muss als maßgebliche Referenz **zuerst** auf die saubere, einheitliche Quantor-Formel plus `STATE-GUARD`-Regeln umgestellt werden (inkl. `JsonReporter`-Felder `pre_quantor`/`post_quantor` in Z. 227). |
| **[`docs/GUIDE_EBT-Usage-Pattern.md`](../docs/GUIDE_EBT-Usage-Pattern.md)** | [Z. 143–185](../docs/GUIDE_EBT-Usage-Pattern.md#L143-L185), [Z. 187–192](../docs/GUIDE_EBT-Usage-Pattern.md#L187-L192) | **Wird live durch `DocEnsurance` ausgeführt!** Z. 156–163 mischt `WorldState(returns="OK")`, `WorldState(returns="WARN")` und `WorldState(returns="ERROR", expect=False)` im Standard-`exists`-Modus (obwohl Z. 179 sogar selbst einräumt, dass `"ERROR"` bereits ausgeschlossen ist!). Z. 189 schränkt den Existenzquantor noch auf *„positive Zustände“* ein. Muss auf saubere Trennung von `"exists"` (Alternativen ohne `expect=False`) und `"all"` (Konjunktion inkl. Verbote) umgebaut werden. |
| **[`docs/dev/DEV-GUIDE_2-1_EBT-Class.md`](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md)** | [Z. 23](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md#L23), [Z. 27](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md#L27), [Z. 44–46](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md#L44-L46) | (1) Z. 23 nennt noch die gelöschte Methode `_ensure_list` statt `_parse_state_config` und verschweigt Dict-Wrapper. (2) Z. 27 & Z. 44–46 beschreiben noch die alte fest verdrahtete `Q+/Q-`-Aggregation und festes UND über `pre`. Muss auf die gehärtete Quantor-Pipeline und neue `evaluate_step_logic()`-Semantik aktualisiert werden. |
| **[`docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`](../docs/dev/DEV-GUIDE_2-2_WorldState-Class.md)** | [Z. 45](../docs/dev/DEV-GUIDE_2-2_WorldState-Class.md#L45) | Z. 45 beschreibt `WorldState.expect` noch ohne Bindung an `post_quantor="all"` und nennt `pre.expect` lediglich wirkungslos statt `STATE-GUARD`-geschützt. *(Nebenfund Z. 39: behauptet noch fälschlich, ein Feld für erwartete Exceptions existiere nicht — `raises` existiert seit v0.0.7!)* |
| **[`README.md`](../README.md)** | [Z. 122](../README.md#L122) | Spricht pauschal von *„erlaubter und verbotener Zielmuster“* — ggf. präzisieren, dass `pre` (Allquantor) und `post` (Existenzquantor) die Standard-Quantoren bilden. |

*(Hinweis: Historische Audit- und Draft-Dokumente wie `docs/feature-drafts/meta-qa/1/META_GATE_3.md`, `META_QUESTION.md` und `GUTACHTEN.md` dokumentieren vergangene Entwicklungsstände und sind bewusst von `DocEnsurance` ausgenommen; sie müssen nicht rückwirkend umgeschrieben werden, sollten aber bei einem späteren Refactoring von Gate 3 im Feature-Draft ergänzt werden.)*

---

## Teil 4: Empfohlener Reparatur- & Migrationsfahrplan

Damit die Reparatur im Sinne von Cubie-TGD sauber, widerspruchsfrei und ohne Regressionen über alle Prüf-Schichten gelingt, empfiehlt sich folgende Reihenfolge:

1. **Schritt 1 — Verbindliche Design-Entscheidung (Option A vs. Option B):**
   - **Empfehlung: Option A** (`evaluate_step_logic` einheitlich ohne $Q^+/Q^-$-Split + `STATE-GUARD` lehnt `WorldState.expect=False` bei `post_quantor="exists"` und in `pre` sowie nicht-boolesches `expect` überall ab).
   - Vorteil: `EBT.pre` (Standard `"all"`) und `EBT.post` (Standard `"exists"`) arbeiten als **100 % reine Quantoren**, `expect` überschreibt niemals mehr einen Quantor, und trotzdem bleibt `WorldState(..., expect=False)` für konjunktive Verträge (`post={"quantor": "all", ...}` — insbesondere auch für `raises`, `fs` und `arena`) sauber nutzbar.
2. **Schritt 2 — Core-Härtung (`src/qb_cubie/`):**
   - `src/qb_cubie/protocols.py`:
     - `WorldState.expect: bool = True` + Validierung `isinstance(self.expect, bool)` in `validate_exception_contract()` (oder eigener `validate_contract()`-Methode).
     - `evaluate_step_logic(traces, post_quantor)` auf einheitliche Quantor-Auswertung umstellen:
       ```python
       def evaluate_step_logic(traces: List["EvaluationTrace"], post_quantor: Quantor = "exists") -> bool:
           """Evaluate one step's success strictly according to the declared post quantifier."""
           results = [t.evaluation if t.post.expect else not t.evaluation for t in traces]
           return all(results) if post_quantor == "all" else any(results)
       ```
   - `src/qb_cubie/ebt.py`:
     - `STATE-GUARD` für `isinstance(self.expect, bool)`.
     - `STATE-GUARD`: `any(not s.expect for s in self.pre)` $\rightarrow$ `ValueError("STATE-GUARD: pre states do not support expect=False.")`.
     - `STATE-GUARD`: `self.post_quantor == "exists" and any(not s.expect for s in self.post)` $\rightarrow$ `ValueError("STATE-GUARD: WorldState(expect=False) is not allowed with post quantor 'exists'; use post={'quantor': 'all', ...} or EBT(..., expect=False).")`.
     - **Sticky-Quantor-Fix** für Neuzuweisung von `case.pre` / `case.post` zwischen wiederholten `.run()`-Aufrufen.
3. **Schritt 3 — Test-Suite & Meta-Gates aktualisieren:**
   - Die **9 Testdateien aus Kategorie 1** auf explizites `post={"quantor": "all", "states": [...]}` (oder reine `exists`-Verträge / `EBT(..., expect=False)`) migrieren.
   - In `tests/tests_ebt/test_ebt_quantor_declaration.py` neue **Red-to-Green-Guard-Tests** für alle neuen `STATE-GUARD`s (`expect=False` bei `post="exists"`, `pre.expect=False`, `expect=None`, Sticky-Quantor-Reset) ergänzen.
   - `tests/tests_meta/test_gate_2.py` und `tests/tests_meta/test_gate_3.py` um Dict-Wrapper-Unterstützung (`{"quantor": ..., "states": ...}`) und die neue Semantik erweitern.
4. **Schritt 4 — Dokumentation synchronisieren & über alle Schichten abnehmen:**
   - Zuerst `docs/GUIDE_Contract-Semantics.md` als zentrale Referenz aktualisieren.
   - Danach `GUIDE_Expect-Flags.md`, `GUIDE_Quantifiers.md`, `GUIDE_Quality-Assurance.md`, `GUIDE_Contract-Design.md`, `GUIDE_EBT-Usage-Pattern.md` sowie `DEV-GUIDE_2-1` / `DEV-GUIDE_2-2` und `README.md` angleichen.
   - Abschließende Gesamtverifikation über `pytest`, `tests/tests_meta/`, `tests/test_styleguide.py` (`DocEnsurance`), `ruff`, `mypy` und `pylint`.
