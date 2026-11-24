<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](.assets/cubie-logo-written.png)

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Verschlankung von @GUIDE_Quality-Assurance.md und Erzeugung eines neuen QA-Handbuchs namens @GUIDE_TGD.md

## Kontext

Wir müssen die Erklärungen nochmal verdeutlichen und außerdem ist das Haupt-Handbuch etwas überladen. 
Um das mal auf den Punkt zu bringen:

TGD ist praktisch TDD. 
TDD bedeutet Test-Driven-Development
TDD ist im Grunde: Phase Red -> Phase Green
TGD bedeutet Test-Guided-Development
TGD ist im Grunde: Während der Phase Green darfst du das Produkt aus Phase Red hinterfragen. Auch die QA macht Fehler. Wir haben hier klare erkenntnistheoretische Grenzen. 
Erinnere dich an Karl Poppers Epistemologie.

---

Im Grunde ist TGD also einfach nur: Phase Red, Phase Green + eine Möglichkeit während der Phase Green Fehler aus der Phase Red aufzudecken und einen Reperatur-Prozess der Test-Suite anzustoßen.

---

Dazu stehen aktuell in dem Abschnitt "## 3. Test-Guided Development (TGD) in fünf Schritten" fünf Schritte die ich mir unterwegs einfach aus dem Ärmel geschüttelt habe, weil es damit besser funktionierte.

Die Analyse ist, damit man versteht was überhaupt gerade Sache ist. 
Die Hypothese ist eine Idee was gerade Sache sein könnte und mit weiteren Ideen die man ausprobieren kann. Sich hier an die wissenschaftliche Sprache zu halten ist sauberer, weil man ja auch falsch könnte. Dann bleibt die Formulierung einfach stabiler und ordentlicher. 

Die Erklärung aus ''### Schritt 1: Baseline, Exploratives Audit & Meta-QA-Hypothesenbildung (`ANALYSIS` & `HYPOTHESIS`)' sind Stützräder.
Ich habe bemerkt, bei komplizierten Sachen ist es für Agenten besser zuerst eine Analyse-Phase durchzuführen und zu dokumentieren. 
Ich habe zudem bemerkt, eine Hypothesen-Phase kann für den Aufbau eines Testmoduls operationsfähig nützlich sein, um Fehler aus der Analyse sauber abzufangen und ein besseres Testmodul zu bekommen. Das ist rein optional, aber oft nützlich. 

Im Grunde braucht man aber nur: Phase Red -> Phase Green + eine Tür, um während der Phase Green nochmal zurück zur Phase Red zu gehen. 

Dazu braucht es auch noch: Phase Living-Documentation, damit die Docs sauber bleiben und man im nächsten Zyklus das nutzen kann. 

## Auftrag

Verschiebe den aktuellen Abschnitt '## 3. Test-Guided Development (TGD) in fünf Schritten' in das neue @GUIDE_TGD.md Handbuch. 
Erkläre darin meine Erklärung für Einsteiger und Experten geeignet, so wie wir es bereits im @GUIDE_Quality-Assurance.md Handbuch etablierten.
Baue das Sauber nach den @docs/dev/DEV-GUIDE_DocFrame-Conventions.md auf.
Hinterlege im @GUIDE_Quality-Assurance.md eine Kurzfassung mit einer Referenz auf das neue Handbuch.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./README.md)  
[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./dev/README.md)  
[↦ | Core-Internals | ↤](./dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
