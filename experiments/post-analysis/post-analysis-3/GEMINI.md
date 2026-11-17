# Post-Studien-Audit

## Ziele

* Untersuchung der Forschungsansätze, der Methodik, der Praktiken und Dynamiken einer agilen Entwicklung.
* Wertungsfreier Audit. Untersuchung der empirischen Datenlage, Einordnung der Dimensionalitäten mit jeweiliger Identifikation der gemeinsamen Muster.
* Auditiere explizit die Git-Historie darauf, was während der Entwicklung von `DocEnsurance` und `DocFrame`-Prototypen geschehen ist und zeige die Muster auf.

## Hintergrund

Die Experimente und der Versuchsaufbau in 'experiments/testguided-study' sind allesamt aus dem Stehgreif heraus entstanden.
Dabei haben wir unsere Praktiken zusammen mit der Forschung weiterentwickelt und versucht zu verfeinern.
Die Daten aus 'experiments/testguided-study' bestehen grob aus folgenden Dimensionalitäten: 
* **A**: Die Experimente mit Gemma als Developer-Agent selbst. Also, alles was in 'experiments/testguided-study/runs' enthalten ist und was die Forschung untersuchte.
* **B**: Die Forschung selbst. Alle Dokumente, die flach in 'experiments/testguided-study' enthalten sind.
* **C**: Der Prozess zur Erzeugung der synthetisch generierten Papers. 

Wir haben inzwischen eine Service-Ebene hochgezogen und mit der Entwicklung von Services begonnen.
Der `DocEnsurance`-Service wurde bereits durch diverse explorative Experimente gehärtet, könnte aber noch diverse Fehler haben.
Der `DocFrame`-Service ist erst noch ein Prototyp und wurde nach der Design-Phase innerhalb von kürzester Zeit hochgezogen.
Dazu haben wir mit der kontinuirlichen Weiterentwicklung von unserem QA-Handbuch ('docs/GUIDE_Quality-Assurance.md') begonnen.

## Weiteres

* **Dein Workspace**: 'experiments/post-analysis/post-analysis-3', hier kannst du Dateien anlegen.
* **Dein Bericht**: 'experiments/post-analysis/ANALYSIS_3.md', dort soll am Ende dein fertiger Bericht stehen. Du kannst ihn unterwegs so viel bearbeiten wie du möchtest.
* **Im Bericht**: Halte dich grob an die Provenance-Kopf mit dem Header:
```text
<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Argon" effort="High" -->
# Post-Hoc Audit 3

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 17. November 2026, ~ 09:00 (CET)
- **Synthesebasis:**
  # Du musst das hier noch ausfüllen
- **Stand:** qb-cubie (v0.0.7)
- **Git-Log:** `git log -n 1`
        ```text
        commit 7e08e2ac7a39586fe4ce9dfff209ee11810ea0ca (HEAD -> main, origin/main)
        Author: Chronuid <Dominickwirzba@gmail.com>
        Date:   Mon Nov 16 08:50:29 2026 +0100
        
            Double-Check
        ```
---

---

<!-- /qb:frame -->


# Hier packst du dein Audit-Ergebnis rein.
```

## Auftrag 

* Ignoriere die anderen Daten innerhalb vom 'experiments'-Ordner komplett.  

* Fokussiere dich auf die Daten aus dem 'src/qb_cubie'-Package und der Dazugehörigen `tests`-Suite.  

* Auditiere explizit die Git-Historie darauf, was während der Entwicklung von `DocEnsurance` und `DocFrame`-Prototypen geschehen ist und zeige die Muster auf.  