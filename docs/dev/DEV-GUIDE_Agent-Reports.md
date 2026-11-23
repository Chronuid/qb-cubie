<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`)

![Cubie](../.assets/cubie-logo-written.png)

Kurzanleitung für Agenten zum korrekten Ausfüllen des `CUBIE_DOC_FRAME_2`-Provenance-Headers und zum strukturierten Aufbau von Analysen, Hypothesen, Audits und TGD-Protokollen.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
>
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ...heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Wann `CUBIE_DOC_FRAME_2` verwenden?

`CUBIE_DOC_FRAME_2` ist der verbindliche Provenance-Rahmen für **Agenten- und Untersuchungsberichte**:

* **Geeignet für:** Analysen (`ANALYSIS*.md`), Audits, Hypothesen, TGD-Protokolle (`TGD_*.md`), Experiment- und Feldberichte.
* **Nicht geeignet für:** reguläre Handbücher und Dev-Guides (`CUBIE_DOC_FRAME_1`) sowie Ordner-Indizes (`CUBIE_DOC_FRAME_3`).

---

## 2. Aufbau des `CUBIE_DOC_FRAME_2`-Headers

Jedes `CUBIE_DOC_FRAME_2`-Dokument benötigt **zwei geschlossene Rahmen-Zonen** (andernfalls schlägt `DOCFRAME-MISSING` fehl):

1. `zone="head"` ganz am Dateianfang (`TitleSlot` → `ProvenanceBlock` → `---` → optionaler `PromptSlot`).
2. `zone="foot"` ganz am Dateiende (wird von `DocFrame` automatisch mit Navigation befüllt).

### Pflichtfelder (`DOCFRAME-PROVENANCE-INCOMPLETE`)

Drei Felder sind verbindlich und dürfen nicht leer sein. Sie werden idealerweise direkt als Kurz-Attribute im öffnenden `head`-Tag gesetzt und im Bullet-Block gespiegelt:

| Tag-Attribut | Provenance-Feld im Header | Typische Werte / Konvention |
| :--- | :--- | :--- |
| `env="..."` | `Plattform / Umgebung` | z. B. `Antigravity-CLI`, `Gemini-CLI`, `Codex` |
| `model="..."` | `Modell` | z. B. `Gemini 4 Neon`; bei Modellwechsel transparent verketten (`Argon -> Gemini 4 Neon`) |
| `effort="..."` | `Reasoning-Effort` | z. B. `Low`, `Medium`, `High` (bei Wechsel analog `High -> Medium`) |

> [!NOTE]
> **Sync-Verhalten von `DocFrame.update()`:**
> * Die Tag-Attribute (`env`, `model`, `effort`) haben Vorrang und überschreiben beim Update die jeweiligen Werte im Bullet-Block.
> * **Vor dem ersten `---`** bewahrt `ProvenanceBlock` ausschließlich Bullet-Zeilen im Format `- **Schlüssel:** Wert` (sowie die optionale `# H1`-Überschrift).
> * **Unterhalb des ersten `---`** liegt der `PromptSlot`: Hier gehören optionaler Aufgaben-/Prompt-Kontext oder mehrzeilige Codeblöcke (z. B. `git log -n 1`) hin, damit sie bei `DocFrame.update()` vollständig erhalten bleiben.

### Empfohlene Zusatzfelder (vor dem ersten `---`)

* `- **Analysedatum:**` (oder `Durchführungsdatum`) – Datum, ungefähre Uhrzeit und Zeitzone (z. B. `21. November 2026, ~07:00 (CET)`).
* `- **Synthesebasis:**` – konkret gelesene Quellen (Dateien, Module, Tests, CI-Logs, Vorgänger-Berichte).
* `- **Stand:**` – Paketversion aus `pyproject.toml`, Branch und kurzer Ausgangs-Commit (z. B. `qb-cubie (v0.0.10, Branch main, Commit 93830b69)`).
* `- **Git-Log:**` – einzeiliger Verweis auf `HEAD` (ausführlicher `git log -n 1`-Block bei Bedarf unterhalb von `---`).

### Kopiervorlage

````markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Neon" effort="Medium" -->
# Analyse: <Präziser Titel>

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** Medium
- **Analysedatum:** <TT. Monat JJJJ, ~HH:MM (ZEITZONE)>
- **Synthesebasis:** `<pfad/a.py>`, `<pfad/b.md>`, `<CI-Run / Testlauf>`
- **Stand:** qb-cubie (`vX.Y.Z`, Branch `<branch>`, Commit `<hash>`)
- **Git-Log:** `<kurzer Commit-Hash>` ("<Commit-Message>")

---

```text
<optional: vollständige Ausgabe von `git log -n 1` oder Aufgabenstellung / Leitfragen>
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

...

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->
<!-- /qb:frame -->
````

---

## 3. Leitlinien für Analysen, Hypothesen, Audits & TGD-Berichte

Halte Berichte **knapp, überprüfbar und entscheidungsreif** (Einordnung der TGD-Phasen `ANALYSIS`, `HYPOTHESIS` und `GREEN_AUDIT` im [TGD-Handbuch](../GUIDE_TGD.md)):

1. **Kurzfassung zuerst:** Starte mit einer kurzen *Executive Summary* (2–5 Kernbefunde, Blocker oder Entscheidungen), damit Leser und Folge-Agenten das Ergebnis in 30 Sekunden erfassen.
2. **Belege statt Behauptungen:** Verankere jede technische Aussage an konkreten Dateipfaden, Zeilennummern, Symbolnamen, Kommandos oder echten Test-/CI-Ausgaben.
3. **Fakten, Hypothesen und Maßnahmen trennen:** Mache jederzeit sichtbar, was **beobachtet/gemessen** ist (`Ist`), was eine **Annahme oder ein Risiko** bleibt (`Hypothese`) und was der konkrete **Handlungsvorschlag** ist (`Soll`).
4. **Befunde klassifizieren & Scope benennen:** Markiere Einzelbefunde mit klaren Labels (z. B. `[BLOCKER]`, `[RISIKO]`, `[ABWEICHUNG]`, `[HINWEIS]`) und nenne explizit den Scope (z. B. „rein lesendes Audit, kein Code unter `src/` geändert“).
5. **Verifikation & Besonderheiten protokollieren:** Halte ausgeführte Prüfkommandos mit exaktem Ergebnis fest (kompakte Tabelle `Prüfschritt | Kommando | Ergebnis`). Dokumentiere Abbrüche, Quota-Interrupts oder Modellwechsel kurz und ehrlich.
6. **Saubere Abgrenzung zu `KNOWN_ISSUES.md`:** Herleitungen, Alternativen und Messdaten gehören in den Bericht; bestätigte, offene Bugs werden zusätzlich knapp gemäß [Bugs dokumentieren](./DEV-GUIDE_Write-down-the-bugs.md) festgehalten.

---

## 4. Synchronisieren & Verifizieren

Nachdem der Bericht angelegt wurde, lassen sich Kopf- und Fußrahmen über `DocFrame` idempotent synchronisieren (Details im [DocFrame-Handbuch](../services/GUIDE_DocFrame.md)):

```bash
qb-cubie docframe update <pfad/zum/bericht.md>
.venv/bin/python -m pytest -q tests/test_styleguide.py
```

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`) | ↤](./DEV-GUIDE_Agent-Reports.md)  
[↦ | DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten | ↤](./DEV-GUIDE_DocFrame-Conventions.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Service-Architektur & strikte Service-Isolation | ↤](./DEV-GUIDE_Services.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
