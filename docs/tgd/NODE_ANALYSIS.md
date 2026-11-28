<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="10" -->
<div align="center">

# Knoten: ANALYSIS (Bestandsaufnahme & Ist-Vermessung)

![Cubie](../.assets/cubie-logo-written.png)

Rein lesende Bestandsaufnahme (optionales Stützrad 1, in jedem Knoten zuschaltbar): Vermisst den realen Ist-Zustand ($Q_{\text{Ist}}$) gegen das fachliche Ziel ($Q_{\text{Soll}}$) mit überprüfbaren Belegen, ohne Umsetzung, Prüfsystem oder produktive Handbücher zu verändern.

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
| **Rolle** | Optionales Stützrad 1 (frei positionierbar an jedem Knoten) — rein lesende Ist-Vermessung ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$) und Evidenzsammlung |
| **Eintrittsbedingungen ($P$)** | Klare Fragestellung oder Untersuchungsauftrag im `RUN`-Dokument, sauberer Ausgangsstand gemäß [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell), benannter Zielpfad für den Analysebericht |
| **Erlaubte Schreibziele** | Ausschließlich der designierte Analysebericht (auf der Dokumentations- & Berichts-Schiene) |
| **Eingefrorene Bereiche (Tabu)** | Umsetzung/Arbeitsergebnis (z. B. Quellcode), Prüfsystem (z. B. Test-Suite) und bestehende produktive Handbücher (`0` Änderungen) |
| **Abnahme ($Q$)** | Evidenzbasierter Bericht mit Kurzfassung, konkreten Quellen-/Messbelegen, strikter Trennung von `Ist`, `Hypothese` und `Evidenzlücke` sowie Verifikationstabelle; Format- und Doku-Prüfungen auf dem Bericht bestanden; `0` Änderungen an Umsetzung, Prüfsystem und produktiven Handbüchern |
| **Einsatz & Folge-Knoten im Baukasten** | Situativ vor oder während **jedes** Knotens — z. B. vor [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) oder [`NODE_PHASE_RED`](./NODE_PHASE_RED.md), zur Ursachen-Isolierung bei unerwarteten Fehlschlägen in [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md), als Faktenprüfung in [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) oder zur Drift-Inventur vor größeren Umbauten in [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Bevor auf einer Baustelle auch nur eine einzige Wand eingerissen wird, kommt eine Vermessungsingenieurin vorbei, misst alle Räume exakt aus, prüft, wo Leitungen liegen, und schreibt objektiv auf, was tatsächlich vorhanden ist. Genau das macht `ANALYSIS` — und zwar völlig unabhängig davon, ob du ein Haus umbaust, ein Fachkonzept überarbeitest oder Software entwickelst: **erst beobachten, messen und verstehen, noch nichts umbauen**. Wichtig im TGD-Baukasten: Die Vermessung ist **keine starre Pflicht-Vorstufe**, die nur ganz am Anfang stattfinden darf. Du kannst dieses Stützrad jederzeit dazuholen — auch mitten in der Umsetzung (`NODE_PHASE_GREEN`), wenn plötzlich etwas Unerwartetes klemmt, oder vor einer größeren Aktualisierung der Handbücher (`NODE_LIVING_DOCS`).
* **Für Experten & KI-Agenten (Epistemologie, Hoare-Vertrag & Baukasten-Symmetrie):** `ANALYSIS` trennt die **empirische Bestandsaufnahme ($Q_{\text{Ist}}$)** strikt von der **Hypothesenbildung und Zielspezifikation ($Q_{\text{Soll}}$)**. Im Sinne von Karl Poppers kritischem Rationalismus verlangt dieser Knoten maximale Belegtreue innerhalb eines klaren Hoare-Vertrags $\{P\}\ S\ \{Q\}$: Jede Tatsachenbehauptung muss an realen Artefakten, Fundstellen, Messwerten oder Verlaufsdaten verankert sein, während blinde Flecken (etwa fehlende Historie oder nicht reproduzierbare Daten) explizit als **Evidenzlücken** ausgewiesen werden, statt sie spekulativ zu füllen. Zugleich zeigt sich hier die Symmetrie der beiden Querschnitts-Schienen aus dem [TGD-Handbuch](../GUIDE_TGD.md): `ANALYSIS` agiert auf der unteren **Stützräder-Schiene** und legt sein Ergebnis als strukturierten Bericht auf der oberen **Dokumentations- & Berichts-Schiene** ab, während produktive Handbücher, Prüfsystem und Umsetzung bei `0` Diff eingefroren bleiben.

---

## 3. Eintritt & Pre-Flight ($P$)

Vor Beginn der Untersuchung werden drei Vorbedingungen geprüft:

1. **Pre-Flight-Triage des Arbeitsverzeichnisses:** Status des Arbeitsverzeichnisses (z. B. im Versionierungssystem) gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen. Fremde Altlasten in Umsetzung, Prüfsystem oder produktiven Handbüchern (Klasse 3) führen zum sofortigen Stopp, damit sie niemals still in einen Analyse-Stand rutschen.
2. **Auftrags- und Scope-Prüfung (`RUN`-Dokument):** Gemäß [Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin) prüfen, ob das `RUN`-Dokument eindeutig den Knoten `ANALYSIS` benennt und den Zielpfad für den Analysebericht festlegt. Fordert der Zielabschnitt stattdessen direkte Eingriffe an der Umsetzung oder am Prüfsystem, sofort vor der ersten Änderung stoppen und den Widerspruch melden.
3. **Eingangsquellen sichern:** Alle benannten Problembeschreibungen, Fehlerprotokolle, bestehenden Handbücher sowie die zu untersuchenden Arbeits- und Prüf-Artefakte als Lese-Basis erfassen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Direkt vermessen statt schätzen:** Umfänge, Strukturen, Abhängigkeiten, Schnittstellen, Aufruf- bzw. Verweisstellen und Prüfergebnisse (in der Software-Entwicklung z. B. Modul- und Funktionsgrößen, Symbol-Abhängigkeiten und reale Test-Läufe) werden direkt am realen Bestand erhoben — niemals aus dem Gedächtnis geschätzt.
2. **Konflikt-Inventar am bestehenden Prüfsystem ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$):** Systematisch erfassen, welche bestehenden Prüfkriterien oder Tests noch das alte Verhalten ($Q_{\text{Ist}}$) voraussetzen, wo bestehende Prüfungen lückenhaft oder wirkungslos sind (z. B. *Vacuous Passes*, die ohne echten Prüfgegenstand grün durchlaufen) und welche Qualitäts-Gates von geplanten Änderungen berührt werden.
3. **Duplikat-, Schnittstellen- und Kopplungs-Katalog:** Mehrfach gepflegte Regeln oder Konstanten, versteckte Querkopplungen zwischen Teilbereichen und brüchige Übergänge tabellarisch mit konkreten Fundstellen (z. B. Dateipfaden und Zeilennummern) erfassen.
4. **Strikte Trennung von `Ist`, `Hypothese` und `Evidenzlücke`:**
   * **`Ist`:** Direkt am Bestand beobachtet oder reproduzierbar gemessen.
   * **`Hypothese`:** Erklärende Vermutung oder erste Leitfrage für den Folge-Knoten — sprachlich klar als Vermutung gekennzeichnet (*„Hypothese: …“*).
   * **`Evidenzlücke`:** Alles, was aus den vorhandenen Quellen *nicht* sicher ablesbar ist und nicht geraten werden darf.
5. **Klare Befund-Klassifikation & Struktur:** Den Bericht mit einer kompakten **Kurzfassung (Executive Summary)** beginnen (2–5 Kernbefunde), Einzelbefunde einheitlich klassifizieren (`[BLOCKER]`, `[RISIKO]`, `[ABWEICHUNG]`, `[HINWEIS]`) und mit präzisen Leitfragen für den aufrufenden bzw. nächsten Knoten abschließen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Fremde lokale Änderungen im Arbeitsverzeichnis (Klasse 3)** | Keine Datei bearbeiten; verschmutzten Stand sofort an die Orchestrierung melden. | Harter Stopp vor Analyse-Start |
| **Offensichtlicher „Quick-Fix“-Impuls für einen entdeckten Mangel** | Dem Impuls strikt widerstehen! Mangel präzise mit Reproduktionsbeleg im Analysebericht dokumentieren, aber `0` Änderungen an Umsetzung oder Prüfsystem vornehmen. | Saubere Übergabe an den zuständigen Knoten |
| **Unvollständige Historie oder fehlende Mess-/Laufzeitdaten** | Nichts extrapolieren oder raten; Lücke explizit als **Evidenzlücke** im Bericht ausweisen. | Ehrliche, fallibilistische Datengrundlage |
| **Aufgabenstellung im `RUN`-Dokument widerspricht den realen Fakten im Bestand** | Widerspruch anhand konkreter Belege aus Umsetzung und Prüfsystem herausarbeiten und als `[BLOCKER]` bzw. Klärungsfrage an den Anfang der Kurzfassung stellen. | Korrigiertes Lagebild vor jedem Entwurf |
| **Bericht enthält erläuternde Skizzen, Vorlagen oder Beispiel-Fragmente** | Skizzen ausschließlich in nicht-ausführbare Text-, Markdown- oder Diagramm-Blöcke setzen, damit automatische Doku-Prüfungen sie nicht als ausführbaren Produktiv-Code missverstehen. | Grüne Doku-Prüfung auf dem Bericht |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `ANALYSIS` gilt genau dann als abgeschlossen, wenn alle vier objektiven Kriterien erfüllt sind:

1. **Bericht vollständig und belegt:** Der designierte Analysebericht enthält eine Kurzfassung, konkrete Quellen-/Zeilen- und Messbelege, eine sichtbare Trennung von `Ist`, `Hypothese` und `Evidenzlücken`, eine Verifikationstabelle der ausgeführten Prüfschritte sowie klare Leitfragen für den nächsten Schritt.
2. **Berichts- und Dokumentations-Checks grün:** Alle für Berichte geltenden Format-, Rahmen- und Doku-Prüfungen laufen auf dem erstellten Analysebericht mit `0` Diagnosen und idempotent durch.
3. **Schreibgrenzen-Nachweis erbracht:** Der Status des Arbeitsverzeichnisses zeigt ausschließlich den neu erstellten bzw. aktualisierten Analysebericht (neben ggf. einem unveränderten Klasse-1-`RUN`-Dokument) und **`0` Änderungen** an Umsetzung/Quellcode, Prüfsystem/Test-Suite und bestehenden produktiven Handbüchern.
4. **Übergabe im Baukasten benannt:** Der empfohlene nächste Baustein (z. B. [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) bei offenen Gestaltungsfragen, [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) bei direkt prüfbarem Befund oder Rückkehr in [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) / [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md)) ist klar ausgewiesen und der Lebenszyklus des Berichts folgt dem [3-Zustands-Modell](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte).

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Sämtliche projektspezifischen Prüfbefehle, Rahmen-Presets und Ablagepfade stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) sowie im [Leitfaden für Agenten-Berichte](../dev/DEV-GUIDE_Agent-Reports.md).

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
