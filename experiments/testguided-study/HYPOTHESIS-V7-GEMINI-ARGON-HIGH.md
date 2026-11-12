# Hypothesen und Live-Dump-Kritik zum v7-Pilotlauf 20261112-015457

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App (Konversation)
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 12. November 2026 (~02:28 Uhr)
- **Untersuchter Pilotlauf:** [`runs/20261112-015457`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261112-015457) (`fastapi_9425`, Seed 42, Modus `cubie`, Run-ID `0001` bei Call 74)

---

Nein, das hat mit deiner Skizze absolut nichts mehr zu tun – das ist das genaue Gegenteil deiner Idee von „Komplexitäts-Reduktion und Fokus-Schärfung“. Wer oder was auch immer dein 25-Zeilen-Konzept in diesen Prompt- und Kontext-Builder übersetzt hat, hat das 12B-Modell in eine bürokratische Selbsthypnose-Maschine gesteckt.

Wenn man sich diesen Live-Dump ansieht, springen vier fundamentale Design-Katastrophen sofort ins Auge:

* **Komplette Rollen-Kontamination im System-Prompt:** Deine Idee war, dass der Analyse-Agent *nur* das Repo durchsucht und den Kontext vorbereitet, während der QA-Agent die EBT-Cases schreibt. Im System-Prompt bekommt der Analyse-Agent zwar gesagt `"You cannot edit source or tests"`, erhält aber direkt darunter 45 Zeilen `qb_cubie`-Syntax-Tutorials mit drei Python-Codeblöcken und Anweisungen wie `"Before adding a test, state the requirement..."`. Das Modell weiß überhaupt nicht mehr, wer es eigentlich ist.


* **Roher Telemetrie-Müll statt Gedächtnis (`Working ledger`):** Statt einer sauberen Zusammenfassung seiner bisherigen Erkenntnisse bekommt das Modell im User-Prompt einen unformatierten JSON-String vorgeworfen, vollgepackt mit PyPI-Classifiern aus der `pyproject.toml`, dutzenden 64-stelligen SHA-256-Hashes (`"baa65e7..."`), internen Policy-Flags und seinen eigenen Laufzeit-Metriken auf neun Nachkommastellen (`"model_seconds": 591.6717792460058`). Noch schlimmer: Das Modell hat zwar schon 4.011 Zeilen Code gelesen (`"read_lines": 4011`), aber weil `"55 older tool exchanges omitted"` den alten Dialog einfach abschneidet, hat der Agent sämtlichen gelesenen Code vergessen – sieht dafür aber, dass er schon 570.778 Input-Tokens verbraucht hat.
* **Schema-Sabotage durch die Recovery:** Die Recovery-Episode hat dem Agenten `search_content` weggenommen (`"Exclude repeated content searches"`). Weil das Modell aber im Code nach `def get_route_info` suchen will und das Textsuch-Tool gesperrt ist, missbraucht es verzweifelt `find_paths` (ein Datei-Glob-Tool!) mit `"pattern": "def get_route_info"`. Natürlich heißt keine Datei im Repo `def get_route_info`, also kommt jedes Mal `files: []` zurück.


* **Few-Shot-Selbsthypnose durch `duplicate_action`:** Weil das Abbruchlimit deaktiviert wurde (`"duplicate_actions": 36` bei Call 74!), stehen am Ende des Kontexts über ein Dutzend exakt identische Assistant/User-Paare untereinander. Für ein autoregressives 12B-Modell bei Temperatur 0,15 wirkt eine History aus 15 identischen JSON-Antworten wie ein überwältigender Few-Shot-Prompt, exakt dieselbe Zeile ein 37. Mal zu generieren.



Brich diesen Lauf sofort ab – der wird auch in den verbleibenden 15 Minuten nichts anderes mehr tun, als `find_paths("def get_route_info")` zu wiederholen, bis die 1800 Sekunden voll sind.

Wenn du deine $7.77 OpenAI-Credits oder deine lokale GPU heute Nacht noch sinnvoll einsetzen willst, gibt es nur zwei saubere Wege: Entweder wir werfen diesen aufgeblähten `v6`/`v7`-JSON-Ledger über Bord und bauen in einer einzigen übersichtlichen Python-Datei exakt dein 3-Agenten-Bild mit klaren, kurzen Markdown-Prompts nach, oder du machst für heute Nacht einen Haken hinter die Experimente und reichst morgen das Paper auf Basis der `v1`–`v5`-Daten (plus dem `v6`/`v7`-Befund über „Over-Engineered Context Pollution“) ein. Wie sieht dein Energielevel um halb drei Uhr morgens aus?
