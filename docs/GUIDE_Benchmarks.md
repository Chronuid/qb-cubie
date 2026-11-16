<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`)

![Cubie](.assets/cubie-logo-written.png)

---

> ### ⚠️ WICHTIGER HINWEIS / DISCLAIMER: BESTANDTEIL DER `testguided-study`
> 
> 
> DIESES DOKUMENT (`GUIDE_Benchmarks.md`) IST EIN EXPLIZITER BESTANDTEIL DER `testguided-study` UND KEIN BESTANDTEIL DES `qb-cubie` CORE.
> 
> 
> * **Ungeprüfte „Threads of Validity“:** Sämtliche Dokumente, Konzepte und Spezifikationen aus der `testguided-study` weisen diverse **„Threads of Validity“** auf, die durch den Projektverantwortlichen noch abschließend geprüft, validiert und bereinigt werden müssen.
> * **Versionshinweis & Kurzfassung:** Die ursprüngliche Vollfassung dieses Dokuments wurde in der aktuellen Dokumentation durch die nachfolgende Kurzfassung ersetzt. Die vollständige Originalfassung bleibt über die vergangenen Versionen in der Versionshistorie einsehbar (bzw. ist im Paket über `cubie-bench guide` hinterlegt).
> 
> 
> 
>

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Kurzbeschreibung (`GUIDE_Benchmarks.md`)



Das Dokument spezifiziert den separaten, experimentellen Benchmark-Bereich (`cubie_benchmarks`, CLI `cubie-bench`, Extras `benchmarks` und `swebench`), der der Konfiguration, Ausführung und Auswertung von Agenten-Benchmarks dient.

* **Domänenmodell:** Die Architektur gliedert Messungen in **Szenarien** (sichtbarer Arbeitsauftrag plus private Bewertungsreferenz), **Pakete** (versionierte Szenariobündel), **Sets/Suites** (Auswahl von Paketen, Agenten, Wiederholungen und Budgets), **Pläne** (Aufschlüsselung in Einzelversuche) und **Ergebnisarchive** (Antworten, Bewertungen und Nachweise).


* **CLI-Workflow & Infrastrukturtests:** Über `cubie-bench` werden Vorlagen und Suiten initialisiert (`init-example`, `init-suite`, `init-agent`, `init-scenario`), statisch sowie gegen private Referenzen und Mutanten validiert (`validate`, `--check-references`, `validate-agent`), geplant (`plan`) und ausgeführt (`run`). Deterministische Beispiel- und Fake-Agenten (`shipping-demo`, `builtin:fake`) ermöglichen modellfreie Smoke-Tests der Infrastruktur.


* **Agenten-Schnittstelle & Protokoll (`jsonl-v1`):** Agenten werden als lokale Subprozesse ohne Shell-Ausführung und ohne Vererbung von Umgebungsvariablen oder Zugangsdaten gestartet. Die Kommunikation erfolgt über UTF-8-JSONL (`stdin`/`stdout`, max. 1 MiB pro Zeile, `stderr`-Archivierung bis 4 MiB) und beginnt mit einem Capability-Handshake (5 Sekunden Timeout). Abgegebene Artefakte werden vom Runner per SHA-256-Hash sowie auf Pfadintegrität geprüft; bei Zeitüberschreitung wird unter POSIX die gesamte Prozessgruppe beendet.


* **Modell-Provenienz:** Agentenkonfigurationen können unter `[model]` Modell-ID, Revision, Provider, Adapter-Version, Prompt-SHA256 und Parameter deklarieren, die beim Handshake exakt bestätigt werden müssen. Läufe werden entsprechend als `agent_evaluation`, `mixed` oder `infrastructure_only` klassifiziert, wobei die Deklaration eine Selbstauskunft des Adapters darstellt.


* **Prüfverfahren nach Aufgabentyp:**
* **Review-Aufgaben (`review_agent`):** Agenten erzeugen strukturierte Befunde im `review_v1`-Format (`review.json` mit `criterion_results`, `findings`, `sources`), die gegen definierte Referenzfelder abgeglichen werden.


* **Entwicklungsaufgaben (`developer_agent`):** Agenten durchlaufen in einer Sitzung die Phasen `test_design → red → green → refactor`. Nach dem Testentwurf friert der Runner den Testbaum ein und prüft in der Rotphase auf ein fachliches Scheitern (`assertion_failure` oder eine deklarierte `expected_red_exception` für `NotImplementedError`-Stubs) sowie in Grün/Refactor auf bestandene Regressionen. Die Endabnahme erfolgt nach Beendigung des Agentenprozesses über unabhängige `pytest`-Abnahmetests im privaten Evaluatorbaum.




* **Weiterführende Systemfunktionen:** Das Dokument verweist zudem auf Funktionen für Lauf- und Versionsvergleiche, Basis- und Pilotdatensätze, gespiegelte Developer-Aufgaben (Gegenüberstellung Cubie vs. Pytest), den Import öffentlicher Reparaturaufgaben (SWE-bench), eingefrorene CI-Messläufe (Gates), Nachbewertungen sowie die Python-API.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Error while trying to load the image](.assets/cubie-small.png)

[↦ | Qualitätssicherung: Handbuch & Methodik | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  

[↦ | DocEnsurance: Lebende Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame: Dokument-Rahmen & Router | ↤](./services/GUIDE_DocFrame.md)  
[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</div>
<!-- /qb:frame -->
