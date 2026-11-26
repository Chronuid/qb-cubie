<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="30" -->
<div align="center">

# Knoten: PHASE_RED (Testaufbau, Gate-Kalibrierung & Test-Freeze)

![Cubie](../.assets/cubie-logo-written.png)

Erster verbindlicher Kernknoten von TGD: Übersetzt bestätigte Verträge und Mutanten in scharfe, reproduzierbar fehlschlagende Tests, kalibriert statische Wächter und friert die Test-Suite vor der Implementierung ein.

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Knoten-Steckbrief

| Eigenschaft | Verbindliche Festlegung |
| :--- | :--- |
| **Rolle** | Verbindlicher Kernknoten 1 — Test-Spezifikation, Wächter-Kalibrierung & Test-Freeze |
| **Eintrittsbedingungen ($P$)** | Bestätigte Spezifikation (explizite Beschlüsse `E1..En` aus `HYPOTHESIS` oder präziser Fehlerbericht), relevante Bestands-Fixtures & Handbücher, saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich Dateien der Test-Suite (Testmodule, Test-Fixtures, statische Wächter-Tests) |
| **Eingefrorene Bereiche (Tabu)** | Quellcode und Produkt-Dokumentation (`0` Änderungen) |
| **Abnahme ($Q$)** | Dokumentiertes zweistufiges Differenzsignal (Bestand grün, exakt benannte neue Verträge deterministisch rot), statische Test-Hygiene bestanden (`0` Linter-/Typfehler), `0` Änderungen an Quellcode und Doku, klarer Test-Freeze-Checkpoint |
| **Folge-Knoten** | [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) *(Regelfall)* oder optional [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) im Modus *Post-Red-Kritik* *(vor dem endgültigen Freeze)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Der Bauprüfer schreibt jetzt die verbindliche Checkliste für das kommende Bauvorhaben. Bevor der Handwerker loslegt, prüft der Bauprüfer seine Messgeräte an bereits fertigen Räumen (dort muss alles **grün** sein) und hält die neuen Anforderungen an die noch unfertige Baustelle (dort muss die Prüfung eindeutig **rot** anschlagen — sonst taugt das Messgerät nichts). Danach wird die Checkliste versiegelt (**Test-Freeze**), damit das Ziel unverrückbar feststeht.
* **Für Experten (Formalisierung von $Q_{\text{Soll}}$ & Schärfe-Nachweis):** `PHASE_RED` übersetzt die vereinbarten Verträge, Invarianten und Mutanten-Hypothesen in ausführbare Falsifikationsversuche. Das **zweistufige Differenzsignal** beweist zweierlei: (1) Keine versehentliche Regression in der Bestands-Suite und (2) reale Trennschärfe der neuen Tests gegenüber dem noch unreparierten bzw. fehlenden Quellcode. Ein sauberer Freeze-Commit bildet zugleich einen verlustfreien Wiederaufsetzpunkt bei Unterbrechungen oder Modellwechseln.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Änderungen in Quellcode oder Doku führen zum sofortigen Stopp.
2. **Beschluss- & Ziel-Prüfung:** Sicherstellen, dass alle offenen Architekturentscheidungen (`E1..En`) aus der Vorgänger-Phase im Arbeits-Ticket **explizit und eindeutig** beantwortet sind (ein vages „Ok.“ bei offenen Alternativen ist ungültig $\to$ Stopp und Rückfrage!). Zudem prüfen, ob Knoten-Rolle (`PHASE_RED`) und Zielbeschreibung widerspruchsfrei übereinstimmen.
3. **Bestandskontext lesen:** Vor dem Schreiben neuer Tests die relevanten Bestands-Tests, vorhandene Referenz-Fixtures im selben Testpaket und (bei Folgezyklen) das aktuelle Handbuch des vorherigen Zyklus lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Zweistufiges Differenzsignal aufbauen:**
   * **Schritt A (Bestand & Migration):** Bestehende Tests, die noch altes Fehlverhalten ($Q_{\text{Ist}}$) verlangen, sauber auf $Q_{\text{Soll}}$ migrieren. Sämtliche unveränderten und migrierten Bestandstests müssen gegen den aktuellen Quellcode **100 % grün (`PASSED`)** laufen *(Ausnahme: bewusst neu geschärfte Repo-weite Architektur-Wächter, die gerade den zu behebenden Alt-Verstoß aufdecken)*.
   * **Schritt B (Neue Verträge & Mutanten):** Alle neuen Vertrags-, Guard-, Kantenfall- und Mutanten-Tests hinzufügen und belegen, dass genau diese gegen den aktuellen Quellcode deterministisch **rot (`FAILED`)** fehlschlagen.
2. **Drei verbindliche Fixture-Hygiene-Regeln (F1–F3):**
   * **Regel F1 — Bestands-Fixture-Parität & Dry-Run vor Freeze:** Vor dem Entwurf einer neuen synthetischen Test-Fixture vorhandene Referenz-Fixtures im selben Testpaket prüfen. Nutzt eine Fixture ein produktives Konfigurations-Preset, müssen alle impliziten Voraussetzungen dieses Presets (z. B. erwartete Ziel-Dateien oder Pflicht-Sektionen) vollständig erfüllt sein — oder es wird gezielt ein selbstgenügsames Minimal-Preset gewählt. Soweit Bestandscode bereits existiert, wird die neue Fixture *noch vor dem Freeze* einmal isoliert dagegen trockengetestet, damit Fixture-Widersprüche nicht hinter Importfehlern fehlender Zielmodule verschwinden.
   * **Regel F2 — SSOT-Konstanten-Import statt Prosa-Duplikat:** Mehrzeilige Normtexte, Ausschlusslisten oder Konfigurations-IDs dürfen niemals als kopierter Literal-String im Test dupliziert werden — stattdessen wird die maßgebliche Konstante direkt aus der Single Source of Truth importiert.
   * **Regel F3 — Statische Test-Hygiene vor Freeze:** Linter und Typprüfer laufen bereits vor dem Freeze mit `0` Fehlern über alle neuen und geänderten Testdateien, damit `PHASE_GREEN` nicht über Lint-Fehler in eingefrorenen Tests stolpert.
3. **Wächter-Kalibrierungs-Triade (für statische Architektur- & Meta-Gates):** Jeder neue oder verschärfte statische Prüfer wird dreifach kalibriert:
   * *Clean-Probes:* Minimaler gültiger Code muss `0` Diagnosen auslösen.
   * *Fault-Probes:* Bewusst eingefügte Regelverstöße müssen deterministisch mit exakter Regel-ID und Position fehlschlagen.
   * *Ziel-Scan:* Lauf gegen das reale Repository dokumentiert den erwarteten Ausgangsstand.
4. **Stateless Test-Adapter, Äquivalenzklassen & harte Isolations-Proben:**
   * Komplexe Ergebnisobjekte über kleine, zustandsfreie Test-Adapter auf die fachlich wesentlichen Felder reduzieren.
   * Eindeutige `1×1`-Verträge (ggf. parametrisiert) statt mehrdeutiger Mischlisten; Grenzwerte (*Off-by-One*), strenge Typ-Guards (z. B. `bool` vs. `int`) und Lebenszyklus-Übergänge gezielt abdecken.
   * Für Isolations-, Lazy-Import- oder Atomaritäts-Verträge echte Subprozess-/Import-Blocker bzw. gezielte *Fault-Injection* nutzen, statt sich auf schwache Nebeneffekte zu verlassen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Ein neuer Vertrags-Test läuft unerwartet sofort `PASSED`** | Prüfen, ob der Test zu schwach/tautologisch ist oder das Verhalten bereits existiert. Test schärfen oder den Befund transparent melden — niemals ungeprüft als „scharf“ einfrieren. | Echtes Red-Signal oder geklärter Befund |
| **Versuchung, „nur schnell“ eine Signatur oder Hilfsfunktion im Quellcode anzulegen** | Strikt verboten! Quellcode bleibt in `PHASE_RED` zu 100 % unberührt (Import- oder Attributfehler neuer Module sind das erwartete Red-Signal). | Saubere Schreibgrenze (`Quellcode = 0`) |
| **Test-Linter oder Typprüfer meldet Fehler in den neuen Testdateien** | Noch innerhalb von `PHASE_RED` vor dem Freeze beheben (Regel F3). | Sauberer, lint-freier Test-Freeze |
| **Unklarheit, ob die neue Test-Suite Subsumtionen oder blinde Flecken enthält** | Vor dem endgültigen Übergang zu `PHASE_GREEN` optional eine kurze Runde [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) im Modus *Post-Red-Kritik* einschieben. | Gehärtete Test-Suite vor Implementierung |
| **Fehlende oder informelle Beschluss-Freigabe (`Ok.`) bei offenen Design-Optionen** | Vor dem ersten Test-Edit stoppen und eindeutige Entscheidung (`E1..En`) einfordern. | Eindeutige Spezifikationsgrundlage |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `PHASE_RED` gilt genau dann als abgeschlossen (**Test-Freeze**), wenn alle vier objektiven Kriterien erfüllt sind:

1. **Exaktes Differenzsignal dokumentiert:** Die Test-Ausführung belegt klar benannt, dass bestehende/migrierte Tests grün (`PASSED`) und exakt die neuen Vertrags-, Guard-, Mutanten- bzw. neuen Wächter-Tests deterministisch rot (`FAILED`) sind.
2. **Fixture- & statische Test-Hygiene bestanden:** Regeln **F1–F3** sind eingehalten; Linter und Typprüfer melden `0` Fehler auf allen neuen und geänderten Testdateien.
3. **Schreibgrenzen-Nachweis erbracht:** Der Status des Versionierungssystems zeigt ausschließlich Änderungen in der Test-Suite (neben ggf. einem unveränderten Ticket) und **`0` Änderungen** an Quellcode und Produkt-Dokumentation.
4. **Freeze-Checkpoint gesetzt:** Die Test-Suite ist als eingefrorene Baseline dokumentiert (idealerweise als eigener Freeze-Commit) und bereit zur Übergabe an [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md).

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Fixture-Referenzen:** Die projektspezifischen `pytest`-, Linter- und `mypy`-Aufrufe sowie konkrete Hinweise zu Bestands-Fixtures und SSOT-Konstanten stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](../services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | Knoten: ANALYSIS (Bestandsaufnahme & Ist-Vermessung) | ↤](./NODE_ANALYSIS.md)  
[↦ | Knoten: HYPOTHESIS (Falsifizierbares Design & Meta-QA) | ↤](./NODE_HYPOTHESIS.md)  
[↦ | Knoten: PHASE_RED (Testaufbau, Gate-Kalibrierung & Test-Freeze) | ↤](./NODE_PHASE_RED.md)  
[↦ | Knoten: PHASE_GREEN (Implementierung unter Test-Freeze) | ↤](./NODE_PHASE_GREEN.md)  
[↦ | Knoten: GREEN_AUDIT (Kontrollierter Rücksprung aus Phase Green) | ↤](./NODE_GREEN_AUDIT.md)  
[↦ | Knoten: LIVING_DOCS (Dokumentations-Synchronisation & Hygiene) | ↤](./NODE_LIVING_DOCS.md)  

</div>
<!-- /qb:frame -->
