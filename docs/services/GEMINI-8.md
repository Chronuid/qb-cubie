<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](../.assets/cubie-logo-written.png)

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Entwicklung des neuen Service-Cores. Behandlung eines `GREEN_AUDIT`-Events

## Kontext

Die beiden Services DocEnsurance und DocFrame waren historisch gewachsen. Die Topologie von DocFrame war noch eine reine Projektion von DocEnsurance. Es bestand noch kein gemeinsamer Kern. Ich möchte gerne weitere Services ausarbeiten. Hierfür haben wir versucht einen Service-Core zu bauen, welcher Services vereinheitlicht, stabilisiert und verbessert, sowie den Aufbau neuer Services vereinfacht.

Während dem Zyklus 2 in der Phase Green ist ein GREEN_AUDIT-Event aufgetreten. Damit kehren wir nun zurück in die Phase Red.
Zur Behandlung des Events überlasse ich dir die Entscheidungs-Gewalt. Führe voll-autonom die Phase Red durch.

## Weiteres

@docs/GUIDE_TGD.md  
@docs/services/ANALYSIS.md  
@docs/services/HYPOTHESIS.md  
@docs/services/GUIDE_Service-Core.md  
@tests/GREEN_AUDIT.md


## Ablaufs-Empfehlung

Behandle `tests/GREEN_AUDIT.md` als widerlegbare Hypothese und durchlaufe diesen Knoten als eigenständigen Mikro-TGD-Zyklus auf der Test-Suite:
`MICRO-ANALYSIS → MICRO-HYPOTHESIS → MICRO-RED → MICRO-GREEN → AUDIT-DOCS`

* **Schreibgrenze:** `src/` und `docs/` bleiben in diesem Knoten unverändert; bearbeitet werden ausschließlich `tests/` (inkl. `tests/GREEN_AUDIT.md`).
* **MICRO-ANALYSIS & MICRO-HYPOTHESIS:** Prüfe beide Fehlschläge aus `tests/GREEN_AUDIT.md` unabhängig am Code (insb. Test 2) und wäge die Lösungsoptionen eigenständig ab.
* **MICRO-RED:** Reproduziere die Fehlschläge deterministisch vor jeder Änderung.
* **MICRO-GREEN:** Repariere die betroffene Test-Suite in `tests/` (falls sich das Audit bestätigt) – oder dokumentiere eine begründete Widerlegung des Audits, falls doch ein Defekt in `src/` vorliegt. Hinweis: Da `src/` bereits implementiert ist, ist ein direktes `PASSED` nach einem validen Fixture-Fix zulässig.
* **AUDIT-DOCS:** Dokumentiere Entscheidung, Begründung und Prüfergebnis abschließend in `tests/GREEN_AUDIT.md` (Living-Docs-Abschluss dieses Mikro-Zyklus).

---

## Auftrag

* Zyklus 2, GREEN_AUDIT-Event: PHASE_RED

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

[↦ | Service-Core | ↤](./GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
