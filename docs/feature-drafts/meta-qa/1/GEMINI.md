Hi Gemini! Lass uns mal ein Meta-Gate bauen und schauen was passiert.

### Meta-Gate 1: Der Import-Kanonizitäts-Wächter (`CstRule`)

* **Was es schützt:** Verhindert gespaltene Modul-Namensräume (z. B. `from src.qb_cubie...` statt `from qb_cubie...`), weil `tests/conftest.py` bereits `src/` in `sys.path` einhängt.
* **Mechanismus (Ablauf):**
  1. `CstLinter` liest alle `.py`-Dateien unter `tests/` (und optional `src/`).
  2. Eine `CstRule` besucht jeden `Import`- und `ImportFrom`-Knoten im Syntaxbaum.
  3. Beginnt der Modulpfad mit `src.qb_cubie` oder lautet exakt `src`, meldet die Regel die Diagnose `META-CANONICAL-IMPORT` mit Datei und Zeile.
  4. Der Meta-Test prüft `diagnostics == []`.

Das folgende kleine Beispiel zeigt, wie eine solche `CstRule` direkt mit Cubies eigenem `CstLinter` aufgebaut und gegen gültige sowie verbotene Imports geprüft wird:

```python
import libcst as cst
from qb_cubie import CstLinter, CstRule


class CanonicalImportRule(CstRule):
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        mod = self._module.code_for_node(node.module) if (self._module and node.module) else ""
        if mod == "src" or mod.startswith("src.qb_cubie"):
            self.add_diagnostic(node, "META-IMPORT", f"Verwende 'qb_cubie' statt '{mod}'.")


bad_test = "from src.qb_cubie.rbt import RBT\n"
good_test = "from qb_cubie.rbt import RBT\n"
linter = CstLinter(rules=[CanonicalImportRule()])
print("Bad:", [(d.rule_id, d.line) for d in linter.check(bad_test)])
print("Good:", linter.check(good_test))
```

<details>
<summary>Ergebnis</summary>

```text
Bad: [('META-IMPORT', 1)]
Good: []
```
</details>

## Weiteres
* **Das neue Test-Package:** 'tests/tests_meta'
* **Dein Workspace**: 
  * 'docs/feature-drafts/meta-qa/1', hier kannst du Dateien anlegen.
  * 'tests/tests_meta/tests_gate_1.py', da soll das neue Gate gebaut werden.
* **Dein Bericht**: 'docs/feature-drafts/meta-qa/1/META_GATE_1.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.
* **Im Bericht**: Halte dich grob an die Provenance-Kopf mit dem Header:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="High" -->
    # Meta-Gate 1
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Hydrogen
    - **Reasoning-Effort:** High
    - **Analysedatum:** 18. November 2026, ~18:15 (CET)
    - **Synthesebasis:** # Das hier musst du noch ausfüllen!
    - **Stand**: qb-cubie (v0.0.7) 
    - **Git-Log**: #`git log -n 1`
     ```text
    commit 12304f166f233e146258536674c5db9911ba4d33 (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Wed Nov 18 17:07:16 2026 +0100
    
        Questions about the meta-question.
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du dein Bericht rein. 
# Bitte formuliere sie in einfacher Sprache und als einsteigerfreundliches "Lehrbuch".
```

## Auftrag
* Analysiere die Details für das geplante Meta-Gate 1.
* Baue das neue Meta-Gate in 'tests/tests_meta/tests_gate_1.py'.
* Führe die Tests aus und schaue was passiert. 
  * **VERÄNDERE NOCH KEINEN CODE in 'src'** 
  * **BAUE NUR DAS NEUE META-GATE UND SCHAUE WAS PASSIERT**.
* Schreibe deinen Bericht.