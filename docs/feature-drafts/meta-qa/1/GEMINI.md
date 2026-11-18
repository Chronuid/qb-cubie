Hi Gemini! Lass uns mal das dritte Meta-Gate bauen und schauen was passiert.

### Meta-Gate 3: Der Einsame-Negation-Wächter (`META-EBT-LONELY-NEGATION`)

* **Was es schützt:** Verhindert *Vacuous Passes*, bei denen ein `EBT`-Vertrag ausschließlich verbietet (`expect=False`), was nicht passieren darf, aber vergisst vorzuschreiben, was stattdessen passieren **muss** (`expect=True`).
* **Mechanismus (Ablauf):**
  1. Der AST-/CST-Scanner prüft bei jedem `EBT(...)`-Aufruf alle `WorldState(...)`-Einträge in `post`.
  2. Besitzt jeder Eintrag in `post` explizit `expect=False` (und auch auf `EBT(...)` ist kein positives Ziel verankert), zählt dieser Test als *einsame Negation*.
  3. Ausnahme: Tests, die explizit als reine Negativ-Invariante dokumentiert sind (z. B. über ein definiertes Tag `tags={"meta:negative-invariant"}` im `EBT`-Aufruf), werden bewusst durchgelassen – alle anderen schlagen mit `META-EBT-LONELY-NEGATION` fehl.

## Weiteres
* **Das neue Test-Package:** 'tests/tests_meta'
* **Dein Workspace**: 
  * 'docs/feature-drafts/meta-qa/1', hier kannst du Dateien anlegen.
  * 'tests/tests_meta/test_gate_3.py', da soll das neue Gate gebaut werden.
* **Dein Bericht**: 'docs/feature-drafts/meta-qa/1/META_GATE_3.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.
* **Im Bericht**: Halte dich grob an die Provenance-Kopf mit dem Header:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="High" -->
    # Meta-Gate 3
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Hydrogen
    - **Reasoning-Effort:** High
    - **Analysedatum:** 18. November 2026, ~21:30 (CET)
    - **Synthesebasis:** # Das hier musst du noch ausfüllen!
    - **Stand**: qb-cubie (v0.0.7) 
    - **Git-Log**: #`git log -n 1`
     ```text
    commit bb62e7ab7184c845465f3522ccee9af1ca7eeb23 (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Wed Nov 18 19:08:49 2026 +0100
    
        Crafted the prototype 'tests/tests_meta/test_gate_2.py'
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du dein Bericht rein. 
# Bitte formuliere deinen Bericht in einfacher Sprache und als einsteigerfreundliches "Lehrbuch".
```

## Auftrag
* Analysiere die Details für das geplante Meta-Gate 3.
* Baue das neue Meta-Gate in 'tests/tests_meta/test_gate_3.py'.
* Führe die Tests aus und schaue was passiert. 
  * **VERÄNDERE NOCH KEINEN CODE in 'src'** 
  * **BAUE NUR DAS NEUE META-GATE UND SCHAUE WAS PASSIERT**.
* Schreibe deinen Bericht.