<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`)

![Cubie](../.assets/cubie-logo-written.png)

---

> [!Note]  
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

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./virtualization/README.md)  

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./GUIDE_Benchmarks.md)  

</div>
<!-- /qb:frame -->
