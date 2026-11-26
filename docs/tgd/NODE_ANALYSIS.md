<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="10" -->
<div align="center">

# Knoten: ANALYSIS (Bestandsaufnahme & Ist-Vermessung)

![Cubie](../.assets/cubie-logo-written.png)

Rein lesende Bestandsaufnahme (Stützrad 1): Vermisst den realen Ist-Zustand ($Q_{\text{Ist}}$) gegen das fachliche Ziel ($Q_{\text{Soll}}$) mit überprüfbaren Belegen, ohne Quellcode, Test-Suite oder Produkt-Handbücher zu verändern.

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
| **Rolle** | Optionales Stützrad 1 — rein lesende Ist-Vermessung und Evidenzsammlung |
| **Eintrittsbedingungen ($P$)** | Klare Problemstellung oder Bug-Referenz, sauberer Ausgangsstand gemäß [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell), benannter Zielpfad für den Analysebericht |
| **Erlaubte Schreibziele** | Ausschließlich der designierte Analysebericht |
| **Eingefrorene Bereiche (Tabu)** | Quellcode, Test-Suite und bestehende Produkt-Handbücher (`0` Änderungen) |
| **Abnahme ($Q$)** | Evidenzbasierter Bericht mit Kurzfassung, Pfad-/Messbelegen, strikter Ist/Hypothese-Trennung und Verifikationstabelle; Doku-Prüfung auf dem Bericht bestanden; `0` Änderungen an Code, Tests und Handbüchern |
| **Folge-Knoten** | [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) *(bei Design- oder Architekturfragen)* oder direkt [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) *(bei eindeutig lokalem Bug)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Bevor auf einer Baustelle auch nur eine einzige Wand eingerissen wird, kommt eine Vermessungsingenieurin vorbei, misst alle Wände exakt aus, prüft wo Leitungen liegen und schreibt objektiv auf, was tatsächlich vorhanden ist. Genau das macht `ANALYSIS`: erst beobachten, messen und verstehen — noch nichts umbauen. Wer sofort drauflos programmiert, übersieht fast immer versteckte Abhängigkeiten.
* **Für Experten (Epistemologie & Methodik):** `ANALYSIS` trennt die **empirische Bestandsaufnahme ($Q_{\text{Ist}}$)** sauber von der **Hypothesenbildung und Zielarchitektur ($Q_{\text{Soll}}$)**. Im Sinne des kritischen Rationalismus verlangt dieser Knoten maximale Belegtreue: Jede Tatsachenbehauptung muss an realen Dateien, Symbolen, Messwerten oder Verlaufsdaten verankert sein, während blinde Flecken (etwa fehlende Historie oder nicht reproduzierbare Laufzeitdaten) explizit als **Evidenzlücken** benannt werden, statt sie mit Vermutungen zu füllen.

---

## 3. Eintritt & Pre-Flight ($P$)

Vor Beginn der Untersuchung werden drei Vorbedingungen geprüft:

1. **Pre-Flight-Triage des Arbeitsverzeichnisses:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen. Fremde Änderungen in Quellcode, Tests oder Handbüchern führen zum sofortigen Stopp (sie dürfen niemals still in einen Analyse-Commit rutschen).
2. **Auftrags- und Scope-Prüfung:** Prüfen, ob das Arbeits-Ticket eindeutig den Knoten `ANALYSIS` meint und den Zielpfad für den Analysebericht benennt. Fordert der Text im Zielabschnitt plötzlich Code- oder Teständerungen, sofort stoppen und den Widerspruch melden.
3. **Eingangsquellen sichern:** Alle benannten Problembeschreibungen, Fehlerberichte, Protokolle oder betroffenen Quell- und Testmodule als Lese-Basis erfassen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Direkt vermessen statt schätzen:** Datei- und Modulgrößen, Funktionslängen, Symbol-Abhängigkeiten, Aufrufstellen und Test-Anzahlen werden direkt am realen Bestand oder durch reale Prüfläufe ermittelt — niemals aus dem Gedächtnis geschätzt.
2. **Konflikt-Inventar auf der Bestands-Test-Suite ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$):** Systematisch erfassen, welche bestehenden Tests noch das alte Verhalten ($Q_{\text{Ist}}$) voraussetzen, wo bestehende Prüfungen lückenhaft sind (z. B. *Vacuous Passes*) und welche statischen Wächter von geplanten Änderungen berührt werden.
3. **Duplikat- und Kopplungs-Katalog:** Wiederkehrende Logik, Querkopplungen zwischen Modulen und verstreute Konstanten tabellarisch mit konkreten Dateipfaden und Zeilennummern erfassen.
4. **Strikte Trennung von `Ist`, `Hypothese` und `Evidenzlücke`:**
   * **`Ist`:** Direkt beobachtet oder reproduzierbar gemessen.
   * **`Hypothese`:** Erklärende Vermutung oder erste Leitfrage für den Folge-Knoten — klar als solche gekennzeichnet.
   * **`Evidenzlücke`:** Alles, was aus den vorhandenen Daten *nicht* sicher ablesbar ist.
5. **Klare Befund-Klassifikation & Struktur:** Den Bericht mit einer kompakten **Kurzfassung (Executive Summary)** beginnen (2–5 Kernbefunde), Einzelbefunde einheitlich klassifizieren (`[BLOCKER]`, `[RISIKO]`, `[ABWEICHUNG]`, `[HINWEIS]`) und mit präzisen Leitfragen an den Folge-Knoten abschließen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Fremde lokale Änderungen im Arbeitsverzeichnis (Klasse 3)** | Keine Datei bearbeiten; verschmutzten Stand sofort an die Orchestrierung melden. | Harter Stopp vor Analyse-Start |
| **Offensichtlicher „Quick-Fix“-Impuls für einen entdeckten Bug** | Dem Impuls strikt widerstehen! Bug präzise mit Reproduktionsbeleg im Analysebericht dokumentieren, aber `0` Zeilen Quellcode oder Tests ändern. | Saubere Übergabe an `NODE_HYPOTHESIS` / `NODE_PHASE_RED` |
| **Unvollständige Historie oder fehlende Laufzeitdaten** | Nichts extrapolieren oder raten; Lücke explizit als **Evidenzlücke** im Bericht ausweisen. | Ehrliche, fallibilistische Datengrundlage |
| **Problemstellung widerspricht den realen Fakten im Code** | Widerspruch anhand konkreter Code- und Testbelege sauber herausarbeiten und als `[BLOCKER]` bzw. offene Klärungsfrage an den Anfang der Kurzfassung stellen. | Korrigiertes Lagebild vor jedem Design-Entscheid |
| **Bericht enthält nicht-ausführbare Code-Skizzen** | Skizzen ausschließlich in nicht-ausführbare Text-, Markdown- oder Diagramm-Blöcke setzen, damit automatische Doku-Prüfungen nicht fälschlich auslösen. | Grüne Doku-Prüfung auf dem Bericht |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `ANALYSIS` gilt genau dann als abgeschlossen, wenn alle vier objektiven Kriterien erfüllt sind:

1. **Bericht vollständig und belegt:** Der designierte Analysebericht enthält eine Kurzfassung, konkrete Pfad-/Zeilen- und Messbelege, eine sichtbare Trennung von `Ist`, `Hypothese` und `Evidenzlücken`, eine Verifikationstabelle der ausgeführten Prüfschritte sowie klare Leitfragen für den nächsten Knoten.
2. **Berichts- und Dokumentations-Checks grün:** Alle für Berichte geltenden Format-, Rahmen- und Doku-Prüfungen laufen auf dem erstellten Analysebericht mit `0` Diagnosen und idempotent durch.
3. **Schreibgrenzen-Nachweis erbracht:** Der Status des Versionierungssystems zeigt ausschließlich den neu erstellten bzw. aktualisierten Analysebericht (neben ggf. einem unveränderten Klasse-1-Ticket) und **`0` Änderungen** an Quellcode, Test-Suite und bestehenden Produkt-Handbüchern.
4. **Übergabe benannt:** Der empfohlene Folge-Knoten ([`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) bei Architektur-/Designfragen oder [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) bei eindeutig lokalem Fix) ist klar ausgewiesen.

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Berichtsformat:** Die projektspezifischen Prüfbefehle und Ablagepfade stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) sowie im [Leitfaden für Agenten-Berichte](../dev/DEV-GUIDE_Agent-Reports.md).

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
