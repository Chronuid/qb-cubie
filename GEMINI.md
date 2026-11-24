<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](./docs/.assets/cubie-logo-written.png)

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

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Restrukturierung der Projekt-Strukturen.

## Kontext

Ich will die Projekt-Strukturen verbessern. Sowohl die Dokument-, als auch die Code-Strukturen. Dazu gehören:

* 'GUIDE_Benchmarks.md' gehört eher noch zu 'docs/feature-drafts'. Habe es daher dort hin verschoben.
* 'CI_PLATFORM_STATUS.md' sollte schneller ins Auge fallen, wenn man sich das Projekt ansieht. Es gehört also eher in die Root neben die Haupt-README. Habe es daher dort hin verschoben.
* Wir haben zudem oft Dokumente, die sich nicht genau einordnen lassen und überall aufploppen, jedoch die Übersicht beeinträchtigen können. Das kann gerne weiterhin überall aufploppen, während wir gerade dran sind. Aber wir sollten die Strukturen auch regelmäßig aufräumen. Für Dokumente die sich nicht genau einordnen lassen, habe ich einen 'docs/misc/lake'-Ordner angelegt.
* die @KNOWN_ISSUES.md: Ich habe 'docs/misc/lake/SOLVED_ISSUES.md' erstellt. Es scheint sinnvoll das Archiv von den offenen Bugs seperat zu führen.

'tests/tests_meta/test_gate_4.py' erscheint mir zwar eine Art Meta-Gate zu sein, aber 'tests/tests_meta' war eigentlich für die Gates gedacht, die sich auf die Test-Suite selbst beziehen. 'tests/tests_meta/test_gate_4.py' scheint aber viel eher ein Meta-Gate für den Quellcode zu sein und nicht für die Test-Suite, wenn ich das richtig interpretiere? Wenn ja, dann wäre es wahrscehinlich sinnvoller, dass unter 'tests/tests_core/tests_services' zu führen.

## Auftrag

* Bereinige das Archiv in @KNOWN_ISSUES.md. Der archivierte Bug ist bereits im CHANGELOG aufgegangen und muss nicht mehr im Archiv stehen.
* Aktualisiere @docs/dev/DEV-GUIDE_Write-down-the-bugs.md und erkläre dort das neue Archiv mit @docs/misc/lake/SOLVED_ISSUES.md
* Gehe unterwegs grob die Routing-Listen mit den Hyperlinks durch (Also: Die 'foot'-Zone in den Dokumenten und die README-Indizes in den Ordnern.) und überlege ob man diese sinnvoller aufbauen könnte. Wenn ja, dann baue sie sinnvoller auf.
* Denke über @tests/tests_meta/test_gate_4.py nach und entscheide, wo es am besten geführt werden könnte.
* Analysiere die aktuellen Änderungen seit dem letzten Release und dokumentiere sie bereits vorab als unreleased im @CHANGELOG.md

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
