# Post-Studien-Audit

## Ziele: 
* Untersuchung der Forschungsansätze, der Methodik, der Praktiken und Dynamiken einer agilen Studie.
* Wertungsfreier Audit. Untersuchung der empirischen Datenlage, Einordnung der Dimensionalitäten mit jeweiliger Identifikation der gemeinsamen Muster.

## Hintergrund: 
Die Experimente und der Versuchsaufbau in 'experiments/testguided-study' sind allesamt aus dem Stehgreif heraus entstanden.
Dabei haben wir unsere Praktiken zusammen mit der Forschung weiterentwickelt und versucht zu verfeinern.
Die Daten aus 'experiments/testguided-study' bestehen grob aus folgenden Dimensionalitäten: 
* **A**: Die Experimente mit Gemma als Developer-Agent selbst. Also, alles was in 'experiments/testguided-study/runs' enthalten ist und was die Forschung untersuchte.
* **B**: Die Forschung selbst. Alle Dokumente, die flach in 'experiments/testguided-study' enthalten sind. 
        - B.1: KI-generierte Datenanalyse mit dem Ziel der wertungsfreien Audits der generierten Artefakte mit der Synthese-Basis der runs.
        - B.2: KI-generierte Hypothesen mit dem Ziel die Eigenschaften der Ist-Zustände zu verstehen und mögliche Verbesserungen für die nächste Generation der Soll-Zustände zu hypothetisieren.
        - B.3: KI-generierte Software-Design-Dokumente mit dem Ziel, die Soll-Zustände zu erreichen, mit der Synthese-Basis der zu den jeweiligen Zeitpunkten aktuellen Code-Ständen, Audits und Hypothesen.
        - B.4: KI-generierte QA-Dokumente zur Übersetzung der Software-Design-Dokumente in operationsfähige Test-Module, mit der Synthese-Basis der zu den jeweiligen Zeitpunkten aktuellen Code-Ständen und Design-Dokumenten
        - B.5: KI-generierte Test-Suites und Quell-Codes.
* **C**: Der Prozess zur Erzeugung der synthetisch generierten Papers. 

## Weiteres
* **Dein Workspace**: 'experiments/post-analysis', hier kannst du Dateien anlegen.
* **Dein Bericht**: 'experiments/post-analysis/ANALYSIS_1.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.
* **Im Bericht**: Halte dich grob an die Provenance-Kopf mit dem Header:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="XHigh" -->
    # Post-Hoc Audit 1
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Hydrogen
    - **Reasoning-Effort:** XHigh
    - **Analysedatum:** 17. November 2026, 07:15 (CET)
    - **Synthesebasis:** `experiments/testguided-study`
    - **Stand**: qb-cubie (v0.0.7) 
    - **Git-Log**: #`git log -n 1`
    ```text
    commit 7e08e2ac7a39586fe4ce9dfff209ee11810ea0ca (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Mon Nov 16 08:50:29 2026 +0100
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du dein Audit-Ergebnis rein.
```

---

Nachtrag, nachdem der Audit startete: "Fokussiere dich auf die Dimension 'B'."
Zusätzlich habe ich die Artefakte in eigene Ordner refaktorisiert. 
Zu Beginn gab es nur 'experiments/post-analysis/ANALYSIS_1.md'.
Jetzt gibt es:
* 'experiments/post-analysis/post-analysis-1'
* 'experiments/post-analysis/post-analysis-2'