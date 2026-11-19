# Reperatur vom Cubie-Core

## Ziele: 
* Reperatur vom Cubie-Core.
* Härtung der Quantoren-Deklaration in der EBT-Klasse.
* Sicherstellung des Standart-Verhaltens von EBT-Fällen:  
  - `EBT.pre`-Standart-Verhalten: All-Quantor  
  - `EBT.post`-Standart-Verhalten: Existenz-Quantor  

Aktuell scheinen die expect-Flags in den WorldStates das Standart-Verhalten umzuschreiben. Das war vermutlich mein Fehler, weil ich den Auftrag dazu gab, ohne mir die Details genau anzusehen. Das müssen wir jetzt nochmal im Nachhinein glattziehen. Aufgrund der Entstehungs-Historie von diesem Bug wird er vermutlich auch innerhalb des Testsuite selbst eingebettet sein.

## Weiteres

### **Deine Workspaces**: 
- 'tests': hier kannst du Dateien anlegen.
- 'docs': Da stehen Infos.

### **Dein Bericht**: 
'tests/ANALYSIS.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.

### **Im Bericht**:
Halte dich grob an die Konvention mit dem Provenance-Kopf im Header des Dokuments:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Neon" effort="High" -->
    # Analysis: Reperatur vom Cubie-Core
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Neon
    - **Reasoning-Effort:** High
    - **Analysedatum:** 19. November 2026, ~ 20:30 (CET)
    - **Synthesebasis:** # Das hier musst du noch ausfüllen.
    - **Stand**: qb-cubie (v0.0.8) 
    - **Git-Log**: #`git log -n 1`
    ```text
    commit 312e84d5fed67a75a49539bcb6a6d85287f86c5f (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Thu Nov 19 02:32:11 2026 +0100
    
        Added the Mutation disclaimer to the other docs too.
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du deine Analyse rein.
```

### Aktuell relevante Docs: 
- 'docs/GUIDE_Quality-Assurance.md'
- 'docs/GUIDE_Contract-Design.md'
- 'docs/GUIDE_Expect-Flags.md'
- 'docs/GUIDE_Quantifiers.md'

## Auftrag

Hinterfrage meine Behauptung. Habe ich das richtig gesehen, dass der expect-Flag das Standart-Quantoren-Verhalten überschreibt?

Finde bitte heraus, ob es Tests gibt, welche dafür verantwortlich sein könnten, dass das Standart-Quantor-Verhalten der EBT-Klasse im Post-Attribut nicht wie erwartet zuverlässig als Existenz-Quantor agiert und vom expect-Flag überschrieben wird.
Finde auch heraus, welche Docs an welchen Stellen überarbeitet werden müssten, um eine saubere Erwartungs-Haltung für das Standart-Verhalten von `EBT.pre` und `EBT.post` zu dokumentieren. Der expect-Flag darf das Verhalten der Quantoren nicht überschreiben.