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

Aktualisierung des Service-Core-Handbuchs und Integration aller Neuerungen aus Zyklus 2 in alle relevanten Dokumentationen.

## Kontext

Die beiden Services DocEnsurance und DocFrame waren historisch gewachsen. Die Topologie von DocFrame war noch eine reine Projektion von DocEnsurance. Es bestand noch kein gemeinsamer Kern. Ich möchte gerne weitere Services ausarbeiten. Hierfür haben wir versucht einen Service-Core zu bauen, welcher Services vereinheitlicht, stabilisiert und verbessert, sowie den Aufbau neuer Services vereinfacht.

Zyklus 1 (Kern-Fundament) ist abgeschlossen und dokumentiert. Zyklus 2 (Äußeres: `markdown.py`, `cli_spec.py`, Lazy-CLI für `docframe` & `docensurance`, Service-Anbindung und Fassaden) wurde vollständig implementiert; ein während der Phase Green aufgetretenes `GREEN_AUDIT`-Event wurde geordnet im Mikro-TGD-Zyklus in Phase Red aufgelöst, sodass die gesamte Test-Suite grün läuft. Nun schließen wir Zyklus 2 mit der Phase Living-Documentation ab.

## Weiteres

@docs/GUIDE_TGD.md  
@docs/services/ANALYSIS.md  
@docs/services/HYPOTHESIS.md  
@docs/services/GUIDE_Service-Core.md  
@docs/dev/DEV-GUIDE_Services.md  
@docs/dev/DEV-GUIDE_DocFrame-Conventions.md  
@tests/GREEN_AUDIT.md

## Leitplanken

* **Schreibgrenze:** Bearbeitet werden ausschließlich Dokumentationsdateien (z. B. `docs/**/*.md` sowie bei Bedarf `README.md`). Produktivcode unter `src/` und Testcode unter `tests/` (einschließlich `tests/GREEN_AUDIT.md`) bleiben unverändert.
* **Code als Wahrheitsquelle:** Gleiche alle API-Namen, Signaturen, CLI-Befehle, Exit-Codes (`0`/`1`/`2`) und Verhaltensdetails direkt gegen den tatsächlichen Stand unter `src/qb_cubie/core/service_core/`, `src/qb_cubie/cli.py` sowie `src/qb_cubie/core/services/` ab — übernimm Entwürfe aus `HYPOTHESIS.md` nicht ungeprüft.
* **Vollständige Synchronisation:** Aktualisiere insbesondere `docs/services/GUIDE_Service-Core.md` um die Zyklus-2-Bausteine (`markdown.py`, `cli_spec.py`, Lazy-CLI, Service-Anbindung) und prüfe angrenzende Handbücher (`GUIDE_DocEnsurance.md`, `GUIDE_DocFrame.md`, `DEV-GUIDE_Services.md`, `DEV-GUIDE_DocFrame-Conventions.md`, relevante `README.md`-Einträge) auf veraltete Beispiele, Syntax-Hinweise oder CLI-Beschreibungen.
* **Verifikation:** Synchronisiere alle betroffenen Rahmen mit `DocFrame` und stelle sicher, dass `DocEnsurance`, `DocFrame` und die gesamte Test-Suite (`pytest`) ohne Fehler grün durchlaufen.

---

## Auftrag

* Zyklus 2, Phase Living-Documentation

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