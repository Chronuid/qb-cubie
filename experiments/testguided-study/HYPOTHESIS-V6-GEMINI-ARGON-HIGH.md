# Hypothesen und Quick-Fixes zum v6-Pilotlauf 20261112-002038

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 12. November 2026
- **Untersuchter Pilotlauf:** [`runs/20261112-002038`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261112-002038)
- **Synthesebasis:** [`PILOTANALYSE-20261112-002038.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PILOTANALYSE-20261112-002038.md) (Antigravity) und [`PILOTANALYSE-V6-20261112-002038-CODEX.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md) (Codex)

---

Die beiden Analysen des v6-Pilotlaufs `20261112-002038` (Codex und Antigravity) zeigen einen klaren Befund: Während `think = false` die Token-Starvation aus v5 vollständig behoben hat (65 von 66 Aufrufen lieferten kompaktes JSON, ein einzelner 8.192-Token-Ausreißer in `rich_3278` wurde über `output_repairs` abgefangen), endeten alle sechs Läufe vorzeitig durch `stagnation` in einem **Analysis-Lock-in**. Das Multi-Agenten-System kam nicht ins Spiel, weil der Analyse-Agent die Orientierungsphase in keinem einzigen Lauf verließ.

**Die vier mechanischen Ursachen der Orientierungs-Blockade**

* **Null-Aktivierung von QA und Dev:** Alle 66 Modellaufrufe entfielen auf die `analysis`-Rolle im Zustand `orient`, während `publish_context`, `handoff`, QA und Dev nullmal aufgerufen wurden.


* **Stille Leermengen bei Pfadirrtümern:** Bei `requests_6589` suchte der Agent in `requests/utils.py` statt `src/requests/utils.py` und erhielt wegen fehlender Existenzprüfung in `self.store.check(scope)` kommentarlos `hits: []`.


* **Parameter-Verwechslung und Note-Drift:** In `fastapi_9425` wurde `start = 860` bei `search_content` als Treffer-Offset statt Startzeile gewertet, während Lauf 0001 trotz neuer Absicht im `note`-Feld viermal identisch suchte.


* **Fehlgeleiteter Recovery-Prompt:** Der Hinweis *"Read a different relevant source or run a focused diagnostic"* bei `idle >= 3` trieb das Modell in weitere Suchen, statt `publish_context` und `handoff` einzufordern.



**Chirurgische Quick-Fixes für `team.py` und `workspace.py` vor dem Nachtlauf**

Mit vier kleinen Eingriffen im Controller und Workspace-Tooling lässt sich dieser Lock-in aufbrechen, bevor du den großen Lauf über Nacht startest:

1. **Zwang zum Handoff bei Recovery:** Ändere den Recovery-Text in `orient` auf die strikte Anweisung, sofort `publish_context` und `handoff` aufzurufen, oder blende `search_content` nach N Lese-/Suchschritten im Schema aus.
2. **Harte Pfadprüfung in `workspace.py`:** Wirf in `search_content` bei nicht existierendem `scope`-Pfad einen Fehler samt Pfadvorschlag aus dem Baum (z. B. `src/requests/utils.py`), statt eine stille leere Trefferliste zu liefern.
3. **Parameter-Entkopplung:** Benenne `start` in `search_content` in `offset` um (oder werte es als Startzeile aus), damit das Modell den Parameter nicht mit der Zeilennummer aus `read_file` verwechselt.
4. **Ein-Schritt-Übergabe:** Kombiniere `publish_context` und `handoff` in `orient` optional zu einem einzigen Übergabe-Schritt (oder erlaube Auto-Handoff an QA direkt beim Aufruf von `publish_context`), um die Übergabehürde (`V6-H8`) zu halbieren.

Willst du diese vier Anpassungen in `team.py` und `workspace.py` noch kurz vor dem Nachtlauf einziehen, um QA und Dev im nächsten Smoke-Test garantiert in Aktion zu sehen?
