<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`)

![Cubie](../.assets/cubie-logo-written.png)

Kurzanleitung zum einheitlichen, reproduzierbaren Erfassen und Pflegen von Bugs in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Zweck

[`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) im Repository-Root ist die zentrale Anlaufstelle für alle bekannten Bugs, Randfälle und reproduzierbaren Fehlverhalten in `qb-cubie`.  
Ein guter Eintrag sorgt dafür, dass **jede Person (und jeder Agent)** den Fehler ohne Rückfragen nachstellen, einordnen und beheben kann.

---

## 2. Empfohlener Aufbau von `KNOWN_ISSUES.md`

Halte die Datei übersichtlich mit klaren Hauptabschnitten:

* `## Offene Bugs` – aktive, noch nicht behobene Fehler (neueste oder kritischste oben).
* `## Bekannte Einschränkungen / Plattform-Spezifika` – z. B. OS-bedingte Besonderheiten (Windows/Linux), die vorerst bewusst bestehen.
* `## Behoben (Archiv)` *(optional)* – kurzfristige Ablage für frisch gefixte Bugs mit Verweis auf Version/Commit, bevor sie im [`CHANGELOG.md`](../../CHANGELOG.md) aufgehen.

---

## 3. Vorlage für einen Bug-Eintrag

Kopiere diesen Block für jeden neuen Bug in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) und fülle ihn knapp und konkret aus:

````markdown
### [BUG-001] Kurzer, präziser Titel des Problems

- **Status:** Offen *(Offen | In Arbeit | Workaround | Behoben in vX.Y.Z)*
- **Schweregrad:** Mittel *(Kritisch | Hoch | Mittel | Niedrig)*
- **Bereich:** `pfad/zum/modul.py` *(oder Subsystem, z. B. `TempFS`, `AstLinter`)*
- **Umgebung / Version:** `v0.0.x` / Commit `<hash>`, Python `3.12`, Linux/Windows

**Ist-Verhalten:**  
Was passiert konkret? (Gerne mit kurzer Fehlermeldung oder Traceback-Ausschnitt.)

**Soll-Verhalten:**  
Was wäre das erwartete Ergebnis?

**Reproduktion:**  
Minimale Schritte, Kommando oder kurzes Code-Snippet:
```bash
uv run pytest tests/... -k "test_name"
```

**Workaround:** *(optional)*  
Wie lässt sich das Problem aktuell umgehen?

**Hinweise / Ursache:** *(optional)*  
Vermutete Root Cause, betroffene Zeilen oder verwandte PRs/Dokumente.
````

---

## 4. Kurzes Beispiel

```markdown
### [BUG-001] `TempFS` räumt schreibgeschützte Dateien unter Windows nicht auf

- **Status:** Offen
- **Schweregrad:** Mittel
- **Bereich:** `qb_cubie/arenas/tempfs.py`
- **Umgebung / Version:** `v0.0.4`, Python `3.12`, Windows 11

**Ist-Verhalten:**  
Beim Verlassen des Context-Managers bricht `shutil.rmtree` mit `PermissionError` ab, wenn im temporären Verzeichnis eine Read-Only-Datei (z. B. aus `.git/`) liegt.

**Soll-Verhalten:**  
Die Arena entfernt alle temporären Dateien rückstandslos, ohne eine Exception zu werfen.

**Reproduktion:**  
Datei im `TempFS` mit `os.chmod(path, 0o444)` anlegen und den `with`-Block beenden.

**Workaround:**  
Schreibschutz vor dem Beenden der Arena manuell entfernen.
```

---

## 5. Fünf goldene Regeln

1. **Ein Bug = ein Eintrag:** Keine Sammelpunkte für verschiedene Probleme – lieber zwei kleine, klare Einträge mit eigener ID (`BUG-001`, `BUG-002`, …).
2. **Reproduzierbarkeit schlägt Prosa:** Ein minimales Kommando, Code-Snippet oder ein fehlschlagender EBT-Fall ist wertvoller als eine lange Beschreibung.
3. **Fakten vor Vermutungen:** Exakte Fehlermeldung, betroffene Datei/Version und (falls relevant) OS/Python-Version nennen. Vermutungen klar unter *Hinweise* trennen.
4. **Sofort festhalten:** Lieber direkt beim Entdecken mit den wichtigsten Eckdaten eintragen, statt ihn später zu vergessen – Details lassen sich jederzeit ergänzen.
5. **Beim Fix sauber schließen:** Status auf `Behoben in vX.Y.Z` (oder Commit-Hash) setzen, Eintrag ins Archiv verschieben bzw. entfernen und relevante Fixes im [`CHANGELOG.md`](../../CHANGELOG.md) vermerken.

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
