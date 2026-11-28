<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="30" -->
<div align="center">

# Knoten: PHASE_RED (Testaufbau, Gate-Kalibrierung & Test-Freeze)

![Cubie](../.assets/cubie-logo-written.png)

Erster Kernknoten von TGD: Übersetzt bestätigte Anforderungen und Fehler-Hypothesen in scharfe, reproduzierbar fehlschlagende Prüfkriterien (z. B. Tests), kalibriert Qualitäts-Wächter und friert das Prüfsystem vor der Umsetzung ein.

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
| **Rolle** | TGD-Kernknoten 1 — Aufbau der Prüfkriterien (z. B. Test-Spezifikation), Wächter-Kalibrierung & Prüf-Freeze (*Test-Freeze*) |
| **Eintrittsbedingungen ($P$)** | Bestätigte Zielvorgabe im `RUN`-Dokument (bei vorgelagerter `HYPOTHESIS` per *Consent-by-Exception* `EMPFEHLUNGEN: ALLE` + explizite Abweichungen, sonst direkte Aufgaben-/Fehlerbeschreibung), relevante Bestands-Prüfungen & Handbücher, saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich Dateien des Prüfsystems (z. B. Testmodule, Prüfumgebungen/Fixtures, Qualitäts- und Architektur-Wächter) |
| **Eingefrorene Bereiche (Tabu)** | Umsetzung/Arbeitsergebnis (z. B. Quellcode) und produktive Dokumentation (`0` Änderungen) |
| **Abnahme ($Q$)** | Dokumentiertes zweistufiges Differenzsignal (Bestand grün, exakt benannte neue Prüfkriterien/Verträge deterministisch rot), formale Hygiene der Prüfdateien bestanden (`0` Fehler), `0` Änderungen an Umsetzung und produktiver Doku, klarer Freeze-Checkpoint |
| **Einsatz & Folge-Knoten im Baukasten** | [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) *(Regelfall)*; bei Bedarf situatives Zuschalten von [`NODE_ANALYSIS`](./NODE_ANALYSIS.md) (Bestandsmessung) oder [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) im Modus *Post-Red-Kritik* *(noch vor dem endgültigen Freeze)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Bevor der Handwerker auf der Baustelle loslegt, stellt die Bauprüferin die verbindliche Abnahme-Checkliste zusammen. Dieses Prinzip gilt überall — egal ob ein Gebäude geprüft, ein Fachkonzept abgenommen oder eine Software-Funktion durch automatische Tests abgesichert wird. Damit die Checkliste wirklich trägt, macht die Prüferin zwei Proben: Zuerst hält sie ihre Messgeräte an bereits fertige, intakte Bereiche (dort muss alles **grün** bleiben). Danach hält sie die neuen Prüfpunkte an die noch unfertige Baustelle (dort muss die Prüfung eindeutig **rot** anschlagen — sonst würde das Messgerät später auch Fehler durchwinken). Erst dann wird die Checkliste versiegelt (**Test-Freeze**) und an die Umsetzung übergeben.
* **Für Experten & KI-Agenten (Formalisierung von $Q_{\text{Soll}}$, Differenzsignal & Schienen-Symmetrie):** `PHASE_RED` übersetzt die vereinbarten Soll-Verträge ($Q_{\text{Soll}}$), Invarianten und Fehler-Hypothesen (Mutanten `M1..Mn`) in ausführbare Falsifikationsversuche. Das **zweistufige Differenzsignal** beweist zweierlei: (1) Keine unbeabsichtigte Regression im bestehenden Prüfsystem und (2) reale Trennschärfe der neuen Prüfkriterien gegenüber dem noch unreparierten bzw. fehlenden Arbeitsergebnis. Dabei greift `PHASE_RED` symmetrisch auf beide Querschnitts-Schienen zu: Über die **Dokumentations- & Berichts-Schiene** liest der Knoten bestehende Handbücher und etwaige Analyse-/Hypothesenberichte als Vertrags-Basis (ohne produktive Handbücher selbst zu ändern), und über die **Stützräder-Schiene** kann bei kritischen Prüfsystemen vor dem endgültigen Freeze jederzeit eine Runde [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) (*Post-Red-Kritik*) eingeschoben werden.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Arbeitsverzeichnisses gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Änderungen an Umsetzung/Quellcode oder Dokumentation (Klasse 3) führen zum sofortigen Stopp.
2. **Freigabe-Prüfung (*Consent-by-Exception*) & Ziel-Konsistenz:**
   * Wurde vorab ein `HYPOTHESIS`-Bericht mit offenen Entscheidungspunkten (`E1..En` samt Standard-Empfehlungen) erstellt, genügt im `RUN`-Dokument das explizite Signal **`EMPFEHLUNGEN: ALLE`** plus eventuelle konkrete Abweichungen ([Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin)).
   * Nur wenn bei offenen Alternativen **weder** `EMPFEHLUNGEN: ALLE` **noch** Einzelentscheidungen vorliegen (etwa bei einem ungebundenen, isolierten „Ok.“ ohne Bezug), stoppt der Knoten vor der ersten Änderung und fragt gezielt nach.
   * Bei schlanken Vorhaben ohne vorgelagerte `HYPOTHESIS`-Phase genügt eine direkte, widerspruchsfreie Zielbeschreibung im `RUN`-Dokument, die eindeutig zur Rolle `PHASE_RED` passt.
3. **Bestandskontext lesen:** Vor dem Anlegen neuer Prüfkriterien die relevanten Bestands-Prüfungen, vorhandene Referenz-Vorlagen (z. B. Bestands-Fixtures im selben Testpaket) und geltende Fach- bzw. Architektur-Handbücher lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Zweistufiges Differenzsignal aufbauen:**
   * **Schritt A (Bestand & Migration von $Q_{\text{Ist}}$ auf $Q_{\text{Soll}}$):** Bestehende Prüfungen/Tests, die noch altes Fehlverhalten ($Q_{\text{Ist}}$) konservieren, sauber auf die Soll-Spezifikation ($Q_{\text{Soll}}$) migrieren. Sämtliche unveränderten und migrierten Bestands-Prüfungen müssen gegen den aktuellen Bestand **100 % grün (`PASSED`)** laufen *(Ausnahme: bewusst neu geschärfte übergreifende Struktur-/Architektur-Wächter, die exakt den zu behebenden Alt-Verstoß aufdecken)*.
   * **Schritt B (Neue Verträge, Kantenfälle & Mutanten):** Alle neuen Vertrags-, Schutz-, Kantenfall- und Mutanten-Prüfungen hinzufügen und nachweisen, dass genau diese gegen das noch unreparierte Arbeitsergebnis deterministisch **rot (`FAILED`)** fehlschlagen.
2. **Drei verbindliche Hygiene-Regeln für Prüfumgebungen & Vorlagen (F1–F3):**
   * **Regel F1 — Bestands-Parität & Trockenlauf vor dem Freeze:** Vor dem Aufbau einer neuen künstlichen Prüfumgebung (in der Software-Entwicklung z. B. einer synthetischen Test-Fixture) vorhandene Referenz-Vorlagen im selben Bereich prüfen. Nutzt eine Prüfumgebung ein produktives Konfigurations-Preset, müssen alle impliziten Voraussetzungen dieses Presets (z. B. erwartete Begleitdateien oder Pflicht-Sektionen) vollständig erfüllt sein — oder es wird gezielt ein selbstgenügsames Minimal-Preset gewählt. Soweit Bestandskomponenten bereits existieren, wird die neue Prüfumgebung *noch vor dem Freeze* einmal isoliert dagegen trockengetestet, damit Vorlagen-Fehler nicht hinter fehlenden Zielkomponenten verborgen bleiben.
   * **Regel F2 — Direktbezug aus der Wahrheitsquelle (SSOT) statt Text-Duplikaten:** Mehrzeilige Normtexte, Ausschlusslisten oder Konfigurations-IDs dürfen niemals als kopierter Freitext in Prüfdateien dupliziert werden — stattdessen wird die maßgebliche Quelle/Konstante direkt referenziert bzw. importiert.
   * **Regel F3 — Formale & statische Hygiene des Prüfsystems vor dem Freeze:** Alle für das Prüfsystem geltenden Qualitäts-Checks (in der Software-Entwicklung z. B. Linter und Typprüfer) laufen bereits vor dem Freeze mit `0` Fehlern über sämtliche neuen und geänderten Prüfdateien, damit `PHASE_GREEN` nicht über formale Mängel im eingefrorenen Prüfsystem stolpert.
3. **Wächter-Kalibrierungs-Triade (für automatische Struktur-, Architektur- & Meta-Gates):** Jeder neue oder verschärfte Qualitäts-Wächter wird dreifach kalibriert:
   * *Clean-Probes:* Minimaler gültiger Prüfgegenstand muss `0` Diagnosen auslösen.
   * *Fault-Probes:* Bewusst eingefügte Regelverstöße müssen deterministisch mit exakter Regel-Kennung und Fundstelle fehlschlagen.
   * *Ziel-Scan:* Lauf gegen den realen Bestand dokumentiert den erwarteten Ausgangsstand.
4. **Schlanke Prüf-Adapter, Äquivalenzklassen & echte Isolations-Proben:**
   * Komplexe Ergebnisstrukturen über kleine, zustandsfreie Prüf-Adapter (*Stateless Adapters*) auf die fachlich wesentlichen Eckdaten verdichten.
   * Eindeutige `1×1`-Verträge statt mehrdeutiger Mischlisten; repräsentative Normalfälle, exakte Grenzwerte (*Off-by-One*), strenge Eingangs-Wächter (`STATE-GUARD`s, in Python z. B. strikte Unterscheidung von `bool` und `int`) sowie Lebenszyklus-Übergänge bei wiederverwendeten Objekten gezielt abdecken.
   * Für Isolations- oder Atomaritäts-Anforderungen echte Trennungs- und Störproben (z. B. Prozess-/Import-Isolation oder gezielte *Fault-Injection*) einsetzen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Ein neues Prüfkriterium / ein neuer Test läuft unerwartet sofort `PASSED`** | Prüfen, ob das Kriterium zu schwach bzw. tautologisch formuliert ist oder die Anforderung bereits im Bestand erfüllt wird. Prüfung schärfen oder Befund transparent melden — niemals ungeprüft als „scharf“ einfrieren. | Echtes Red-Signal oder geklärter Befund |
| **Versuchung, „nur schnell“ ein Gerüst oder eine Hilfsfunktion in der Umsetzung (z. B. im Quellcode) anzulegen** | Strikt verboten! Das Arbeitsergebnis bleibt in `PHASE_RED` zu 100 % unberührt (fehlende Komponenten oder Schnittstellen sind ein völlig normales Red-Signal). | Saubere Schreibgrenze (`Umsetzung = 0`) |
| **Qualitäts-Prüfer (z. B. Linter/Typprüfer) meldet Fehler in den neuen Prüfdateien** | Noch innerhalb von `PHASE_RED` vor dem Freeze beheben (Regel F3). | Sauberer, formal fehlerfreier Freeze |
| **Unklarheit, ob das neue Prüfsystem Subsumtionen, Tautologien oder blinde Flecken enthält** | Vor dem endgültigen Übergang zu `PHASE_GREEN` situativ das Stützrad [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) im Modus *Post-Red-Kritik* zuschalten. | Gehärtetes Prüfsystem vor der Umsetzung |
| **Fehlende Freigabe (weder `EMPFEHLUNGEN: ALLE` noch Einzelbeschlüsse, z. B. nur ein ungebundenes „Ok.“) bei offenen Optionen** | Vor der ersten Änderung am Prüfsystem stoppen und eine eindeutige Bestätigung gemäß *Consent-by-Exception* einfordern. | Eindeutige Spezifikationsgrundlage |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `PHASE_RED` gilt genau dann als abgeschlossen (**Freeze des Prüfsystems / Test-Freeze**), wenn alle vier objektiven Kriterien erfüllt sind:

1. **Exaktes Differenzsignal dokumentiert:** Die Prüfausführung belegt klar benannt, dass bestehende und migrierte Prüfungen grün (`PASSED`) und exakt die neuen Vertrags-, Schutz-, Mutanten- bzw. Wächter-Prüfungen deterministisch rot (`FAILED`) sind.
2. **Vorlagen- & formale Prüf-Hygiene bestanden:** Die Regeln **F1–F3** sind eingehalten; alle formalen/statischen Qualitäts-Prüfer melden `0` Fehler auf sämtlichen neuen und geänderten Prüfdateien.
3. **Schreibgrenzen-Nachweis erbracht:** Der Status des Arbeitsverzeichnisses zeigt ausschließlich Änderungen im Prüfsystem (neben ggf. einem unveränderten Klasse-1-`RUN`-Dokument) und **`0` Änderungen** an Umsetzung/Quellcode und produktiver Dokumentation.
4. **Freeze-Checkpoint gesetzt:** Das Prüfsystem ist als eingefrorene Baseline dokumentiert (idealerweise als eigener Freeze-Stand im Versionierungssystem) und bereit zur Übergabe an [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md).

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Die projektspezifischen `pytest`-, `ruff`- und `mypy`-Aufrufe sowie die konkreten Referenzen für F1–F3 (`_seed_synced_docframe_workspace`, `EPISTEMIC_NOTICE_TEXT`, `DOC_EXCLUDES`) stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

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
