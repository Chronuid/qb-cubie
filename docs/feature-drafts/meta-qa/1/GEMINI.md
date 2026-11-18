Hi Gemini! Lass uns mal das zweite Meta-Gate bauen und schauen was passiert.

Die ursprüngliche Skizze sah wie folgt aus:

---

### Meta-Gate 2: Der Kreuzprodukt-Wächter (`META-EBT-CROSS-PRODUCT`)

* **Was es schützt:** Verhindert die Kreuzprodukt-Falle bei `EBT`-Aufrufen – also dass mehrere verschiedene Eingaben (`pre=[P1, P2]`) gemeinsam gegen mehrere verschiedene positive Ergebnisse (`post=[Q1, Q2]`) geprüft werden und dadurch nur noch ein schwaches „irgendein Q passt schon“ getestet wird.
* **Mechanismus (Ablauf):**
  1. Ein `ast`- oder `CstRule`-Scanner durchläuft alle Testdateien in `tests/`.
  2. Bei jedem Aufruf von `EBT(...)` untersucht er die Argumente `pre` und `post`.
  3. Zählt `pre` mehr als `1` Element (Liste/Tupel) **und** enthält `post` gleichzeitig mehr als `1` positives `WorldState`-Objekt (also ohne `expect=False`), schlägt das Gate sofort an.
  4. *Wichtige Feinheit:* Mehrere `pre`-Elemente gegen **genau ein** gemeinsames `post=WorldState(...)` bleiben ausdrücklich erlaubt (z. B. zwei Schreibweisen desselben Eingabewerts, die beide `"text"` liefern sollen). Ebenso bleibt ein `post=[Q_pos, Q_neg_with_expect_false]` erlaubt, da hier nur **ein** positiver Zielzustand existiert.

Das folgende Mini-Gate demonstriert diesen AST-Scanner für zwei typische `EBT`-Schreibweisen in der Praxis:

```python
import ast


def check_ebt_calls(source: str) -> list[str]:
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "EBT":
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            pre_n = len(kw["pre"].elts) if isinstance(kw.get("pre"), (ast.List, ast.Tuple)) else 1
            post_n = len(kw["post"].elts) if isinstance(kw.get("post"), (ast.List, ast.Tuple)) else 1
            if pre_n > 1 and post_n > 1:
                findings.append(f"Zeile {node.lineno}: {pre_n}x{post_n} Kreuzprodukt-Falle")
    return findings


sample = "EBT(target=f, pre=[p1, p2], post=[q1, q2])\nEBT(target=f, pre=[p1, p2], post=q_all)"
print(check_ebt_calls(sample))
```

<details>
<summary>Ergebnis</summary>

```text
['Zeile 1: 2x2 Kreuzprodukt-Falle']
```
</details>

* **Ausbau-Stufe (Laufzeit-Guard):** Zusätzlich zum statischen AST-Scan kann man im `EBT`-Kontext oder in einem Test-Plugin warnen, sobald zur Laufzeit `len(pre_states) > 1` und `len(positive_post_states) > 1` zusammenfallen – das fängt sogar dynamisch gebaute Listen ab.
---

Allerdings denke ich, dass ein solches Kreuzprodukt doch irgendwo vielleicht etwas bringen könnte. Daher möchte ich die Regel so gestalten, dass man auch eine explizite Begründung angeben muss, warum man das Kreuzprodukt genutzt hat, damit es durch das Gate durch kommt.

## Weiteres
* **Das neue Test-Package:** 'tests/tests_meta'
* **Dein Workspace**: 
  * 'docs/feature-drafts/meta-qa/1', hier kannst du Dateien anlegen.
  * 'tests/tests_meta/test_gate_2py', da soll das neue Gate gebaut werden.
* **Dein Bericht**: 'docs/feature-drafts/meta-qa/1/META_GATE_2.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.
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
    commit 6c959ab4cae6ede0b019f3d2774bc305e09e39a6 (HEAD -> main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Wed Nov 18 18:43:28 2026 +0100
    
        Crafted the prototype 'tests/tests_meta/test_gate_1.py'
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du dein Bericht rein. 
# Bitte formuliere sie in einfacher Sprache und als einsteigerfreundliches "Lehrbuch".
```

## Auftrag
* Analysiere die Details für das geplante Meta-Gate 2.
* Baue das neue Meta-Gate in 'tests/tests_meta/test_gate_2.py'.
* Führe die Tests aus und schaue was passiert. 
  * **VERÄNDERE NOCH KEINEN CODE in 'src'** 
  * **BAUE NUR DAS NEUE META-GATE UND SCHAUE WAS PASSIERT**.
* Schreibe deinen Bericht.