# Arbeitsauftrag: Aktualisierung des qb-cubie-Gutachtens durch unabhängige Befundprüfung und Synthese

**Dokument-Informationen & Herkunft:**
- **Herkunft:** `Mensch (:3)` + `ChatGPT-Web-Konversation + Deep-Research (kostenlos: unbekanntes Modell und unbekannter Effort)`
- **Ausgangs-Commit:** `20c4b42b` (HEAD -> main, tag: v0.1.3, origin/main) chore(release): prepare v0.1.3
- **Analysedatum:** 28. November 2026, ~ 10:10 (im Schwarzwald)

## 1. Zielsetzung

Aktualisiere das bestehende Gutachten `GUTACHTEN.md` auf Grundlage einer erneuten Prüfung des aktuellen Repository-Stands und einer kritischen Synthese mit dem vorliegenden Deep-Research-Bericht.

Ziel ist ein nachvollziehbares, fachlich belastbares Gutachten über den TGD-Ansatz und seine konkrete Umsetzung in qb-cubie.

Der Deep-Research-Bericht ist dabei eine eigenständige externe Erkenntnisquelle. Seine Aussagen dürfen weder ungeprüft übernommen noch pauschal verworfen werden. Prüfe sie anhand der aktuellen Dokumentation, der Implementierung, der Tests und der Git-Historie.

Das Ergebnis soll insbesondere deutlich machen:

1. Welche früheren Befunde durch die erneute Prüfung bestätigt werden.
2. Welche Befunde präzisiert, eingeschränkt oder korrigiert werden müssen.
3. Welche Aussagen aufgrund fehlender Belege weiterhin offenbleiben.
4. Welche zusätzlichen Erkenntnisse bei der erneuten Prüfung entstehen.
5. Welche Verbesserungen tatsächlich sinnvoll und verhältnismäßig erscheinen.

Es handelt sich um eine Begutachtung und Dokumentensynthese, nicht um einen Entwicklungsauftrag.

## 2. Ausgangsmaterial und Dokumentenrouting

Verwende folgende Dateien als primäre Einstiegspunkte:

| Zweck | Repository-Pfad |
|---|---|
| Allgemeines Dokumentations-Routing | `docs/README.md` |
| TGD-Routing und Knotenübersicht | `docs/tgd/README.md` |
| Projektbezogenes TGD-Workflow-Profil | `docs/dev/DEV-GUIDE_TGD-Workflow.md` |
| Konventionen für Agent-Reports | `docs/dev/DEV-GUIDE_Agent-Reports.md` |
| Vorliegender Deep-Research-Bericht | `docs/misc/lake/deep-research-report(2).md` |
| Zu aktualisierendes Gutachten | `GUTACHTEN.md` |

Nutze die beiden README-Dateien als Routing-Indizes. Folge den dort ausgewiesenen Verweisen zu den für die Begutachtung relevanten Dokumenten. Insbesondere sind die TGD-Knoten-Handbücher und die generische TGD-Anleitung einzubeziehen.

Prüfe außerdem den bestehenden Inhalt von `GUTACHTEN.md`, bevor du Änderungen vornimmst. Erhalte sinnvolle bestehende Erkenntnisse und deren Provenance. Veraltete oder widerlegte Aussagen sollen nicht unkommentiert fortgeschrieben werden.

## 3. Wichtige Einordnung: Entwicklungsstand und Dokumentationskonventionen

qb-cubie befindet sich weiterhin in einer experimentellen und explorativen Entwicklungsphase. DocFrame ist noch ein Prototyp.

Behandle daher die Dokumentations- und Agent-Report-Konventionen mit der gebotenen Differenzierung:

- Agent-Reports sind kein verpflichtender Bestandteil jedes TGD-Durchlaufs.
- Die in `DEV-GUIDE_Agent-Reports.md` beschriebene Struktur ist eine Konvention, kein hartes Prozess-Gate.
- Die zugehörigen Regeln sind als Orientierung und Erinnerung an mögliche Vorgehensweisen gedacht, nicht als universelle Pflichtanforderungen.
- CUBIE-DOC-FRAMEs sollen entsprechend der jeweiligen Situation sinnvoll eingesetzt werden. Es ist nicht das Ziel, jede Dokumentationssituation schematisch in ein bestimmtes Frame-Format zu zwingen.
- Die Verwendung eines Frames oder Agent-Reports ist für sich genommen kein Qualitätsnachweis.
- Das Fehlen eines optionalen Agent-Reports ist umgekehrt nicht automatisch ein Prozessmangel.

Unterscheide in deiner Bewertung konsequent zwischen:

1. ausdrücklich definierten Prozessanforderungen und Invarianten,
2. empfohlenen Vorgehensweisen,
3. Dokumentationskonventionen,
4. experimentellen oder prototypischen Hilfsmitteln,
5. deinen eigenen Verbesserungsvorschlägen.

Erhebe keine Konvention nachträglich zu einer verbindlichen Anforderung. Behandle auch nicht jede im Dokument erwähnte Möglichkeit als zwingende Implementierungs- oder Dokumentationspflicht.

Beurteile die vorhandenen Mechanismen anhand ihrer tatsächlichen Zweckmäßigkeit und Aussagekraft, nicht anhand eines künstlich verschärften Regelwerks.

## 4. Erneute Repository-Prüfung

Stelle zunächst den tatsächlichen Prüfstand fest:

- aktueller Branch und HEAD-Commit,
- Arbeitsbaumstatus,
- Versionsangabe aus den maßgeblichen Projektdateien,
- vorhandene Tags und relevante Release-Commits,
- gegebenenfalls verfügbare Remote-Referenzen.

Prüfe ausdrücklich, ob v0.1.3 noch dem aktuellen Stand entspricht oder ob inzwischen relevante Weiterentwicklungen vorhanden sind.

Nutze die vorhandene Git-Historie, um die Änderungen zwischen v0.1.2 und v0.1.3 nachvollziehbar zu untersuchen. Beziehe dabei insbesondere die im Deep-Research-Bericht erwähnten Änderungen ein, unter anderem:

- `rule_profiles.py` und die zugehörigen Regelprofil-Abstraktionen,
- `DocFrameRuleSet`, `DocRuleSet` und deren Integration,
- DocFrame-Regeln und ihre Konfigurierbarkeit,
- relevante Service-Core-Änderungen,
- die dazugehörigen Tests,
- die Weiterentwicklung der TGD-Dokumentation und des Workflow-Profils.

Beschränke dich nicht auf Commit-Nachrichten oder Dateinamen. Untersuche die tatsächliche Implementierung dort, wo sie für eine Aussage relevant ist.

Prüfe auch, ob die Tests die behaupteten Eigenschaften tatsächlich abdecken. Unterscheide dabei zwischen vorhandenen Tests, nachgewiesenen Testergebnissen und bloßen Annahmen über die Testwirkung.

Falls bestimmte Prüfungen wegen fehlender Ressourcen, Quotas, Abhängigkeiten oder Zeit nicht durchgeführt werden können, benenne diese Einschränkung konkret. Ersetze fehlende Prüfungen nicht durch Vermutungen.

## 5. Inhaltliche Prüfschwerpunkte

Untersuche die folgenden Themen. Nutze sie als fachliche Prüfschwerpunkte, nicht als starre Checkliste, die unabhängig von ihrer Relevanz vollständig abgearbeitet werden muss.

### 5.1 Rollen und Schreibgrenzen der TGD-Knoten

- Sind Zuständigkeiten und Rollen der einzelnen Knoten verständlich voneinander abgegrenzt?
- Sind Schreibgrenzen ausreichend präzise?
- Gibt es unbeabsichtigte Überschneidungen oder Widersprüche?
- Stimmen die dokumentierten Grenzen mit dem vorgesehenen Ablauf überein?
- Werden optionale Hilfsmittel und verbindliche Vorgaben ausreichend unterschieden?

### 5.2 Test-Freeze und Phasenübergänge

Untersuche insbesondere den vorgesehenen Übergang:

`PHASE_GREEN → GREEN_AUDIT → PHASE_GREEN`

- Ist nachvollziehbar, unter welchen Bedingungen dieser Rückweg vorgesehen ist?
- Sind die jeweiligen Verantwortlichkeiten und zulässigen Tätigkeiten verständlich?
- Ist der Test-Freeze ausreichend definiert?
- Ist die Trennung zwischen Prüfung, Korrektur und erneuter Implementierung sinnvoll?
- Wird verhindert, dass ein Test-Freeze nur formal eingehalten wird, während die zugrunde liegenden Erwartungen unbemerkt verändert werden?

Bewerte dabei die tatsächliche Prozessdefinition. Leite nicht allein aus allgemeinen TDD-Empfehlungen zusätzliche verbindliche Anforderungen ab.

### 5.3 Ein- und Austrittskriterien, Handoff-Artefakte

- Sind die Übergänge zwischen den Knoten ausreichend nachvollziehbar?
- Ist klar, welche Ergebnisse ein Knoten an den nächsten übergibt?
- Sind die geforderten Artefakte angemessen und zweckmäßig?
- Werden unnötige Dokumentationspflichten vermieden?
- Ist der Status eines abgeschlossenen oder unterbrochenen Durchlaufs eindeutig erkennbar?

### 5.4 Kontextfrische und Unabhängigkeit

- Wie wird mit veralteten Kontextinformationen umgegangen?
- Ist ausreichend erkennbar, auf welchem Repository-Stand eine Prüfung basiert?
- Werden vorherige Analyseergebnisse kritisch weiterverwendet oder unreflektiert übernommen?
- Gibt es sinnvolle Mechanismen, um unabhängige Prüfungen und erneute Bewertungen zu ermöglichen?
- Welche Grenzen hat die tatsächliche Unabhängigkeit eines Agenten, wenn er auf bereits vorhandene Berichte und Ergebnisse zurückgreift?

### 5.5 Falsifizierbarkeit und Mutanten-Mapping

- Sind Hypothesen und erwartete Eigenschaften hinreichend konkret formuliert?
- Lassen sich relevante Behauptungen durch Tests oder andere Prüfverfahren widerlegen?
- Ist die Zuordnung zwischen Anforderungen, Tests und möglichen Mutationen nachvollziehbar?
- Wo liefert das Verfahren tatsächlich einen belastbaren Nachweis und wo lediglich eine Plausibilitätsbewertung?

Verlange keine pauschale Mutationstest-Abdeckung, sofern das Projekt dies nicht selbst als verbindliche Anforderung definiert. Bewerte vielmehr, ob die vorhandenen Prüfmechanismen zur jeweiligen Behauptung passen.

### 5.6 Aussagekraft der Gates

Unterscheide zwischen:

- einem tatsächlich überprüften Gate,
- einem formal dokumentierten Gate,
- einem aufgrund fehlender Evidenz offenen Gate,
- einer Empfehlung oder Konvention ohne Gate-Charakter.

Bewerte, welche Aussagen ein erfolgreicher Gate-Durchlauf tatsächlich erlaubt und welche Schlussfolgerungen daraus nicht gezogen werden dürfen.

### 5.7 RUN-Dateien und Plattformneutralität

- Sind RUN-Dateien verständlich, reproduzierbar und möglichst plattformneutral?
- Enthalten sie nur die für den jeweiligen Durchlauf notwendigen Informationen?
- Sind Umgebungsannahmen ausreichend dokumentiert?
- Werden konkrete Laufhistorie und generische Prozessbeschreibung sinnvoll voneinander getrennt?

Die beiden beigefügten Beispiele dienen als zusätzliche Kontextinformationen:

1. Ein RUN-Dokument mit einem Quota-bedingten Abbruch während der Prüfung.
2. Ein voll-autonomer TGD-Durchlauf mit einem dokumentierten Phasen- und Arbeitsauftrag.

Berücksichtige insbesondere, dass ein unterbrochener Run nicht automatisch als vollständig abgeschlossener Durchlauf bewertet werden darf. Zugleich soll ein Quota-Abbruch nicht dazu führen, dass bereits erarbeitete Teilergebnisse ihren dokumentarischen Wert verlieren.

### 5.8 Synchronität der TGD-Dokumentation

- Stimmen generische TGD-Anleitung, Knoten-Handbücher und das qb-cubie-spezifische Workflow-Profil überein?
- Sind Abweichungen bewusst projektspezifisch oder unbeabsichtigte Dokumentationsdrifts?
- Sind die Routing-Indizes ausreichend, um die jeweils maßgeblichen Dokumente zu finden?
- Gibt es widersprüchliche oder veraltete Regelungen?

### 5.9 Epistemische Grenzen und Eskalation

- Ist hinreichend transparent, was ein Agent tatsächlich geprüft hat?
- Werden Unsicherheiten und fehlende Belege offengelegt?
- Gibt es klare Grenzen für Schlussfolgerungen aus unvollständigen Prüfungen?
- Sind Eskalations- und Abbruchentscheidungen nachvollziehbar?
- Ist erkennbar, wann menschliche Prüfung erforderlich bleibt?

### 5.10 Prozessaufwand und Verhältnismäßigkeit

Bewerte kritisch, ob die vorhandenen Prozessmechanismen einen nachvollziehbaren Qualitätsgewinn erzielen.

Achte insbesondere auf:

- unnötige Wiederholungen,
- übermäßige Dokumentationslast,
- unnötig starre Phasenübergänge,
- redundante Prüfungen,
- zu weitreichende Formalisierung experimenteller Abläufe.

Ziel ist nicht, TGD möglichst umfangreich oder formal erscheinen zu lassen. Entscheidend ist ein angemessenes Verhältnis zwischen Prüftiefe, Nachvollziehbarkeit und praktischem Aufwand.

## 6. Kritische Auswertung des Deep-Research-Berichts

Prüfe den Bericht `docs/misc/lake/deep-research-report(2).md` systematisch.

Behandle seine Aussagen mindestens in folgenden Kategorien:

**Bestätigt:** Die Aussage wird durch die aktuelle Repository-Prüfung gestützt.

**Präzisiert:** Der Befund ist grundsätzlich zutreffend, benötigt aber eine genauere Einordnung.

**Eingeschränkt:** Die Aussage gilt nur unter bestimmten Voraussetzungen oder ist nicht so weitreichend, wie sie zunächst formuliert wurde.

**Widerlegt:** Die erneute Prüfung zeigt, dass die Aussage nicht zutrifft oder auf einer falschen Annahme beruht.

**Offen:** Die vorhandenen Informationen reichen nicht für eine belastbare Entscheidung.

**Ergänzt:** Die erneute Prüfung liefert zusätzliche Erkenntnisse, die im ursprünglichen Bericht nicht enthalten waren.

Gehe besonders kritisch mit Aussagen um, die der ursprüngliche Bericht selbst als nicht abschließend geprüft oder nur vermutet gekennzeichnet hat.

Übernimm keine allgemeinen Empfehlungen aus dem Deep-Research-Bericht allein deshalb, weil sie sich auf bekannte Entwicklungsprinzipien oder externe Best Practices berufen. Prüfe stets, ob sie für den tatsächlichen Zweck, Entwicklungsstand und die Architektur von qb-cubie relevant sind.

Externe Fachquellen können eine Einordnung unterstützen. Sie ersetzen aber keine projektspezifischen Belege.

## 7. Provenance und Nachvollziehbarkeit

Das aktualisierte Gutachten muss die Herkunft seiner Aussagen klar unterscheiden.

Berücksichtige dabei mindestens drei Erkenntnisebenen:

**A. Ursprünglicher Deep-Research-Bericht**
- Welche Dokumente und Quellen wurden dort herangezogen?
- Welche Aussagen stammen aus dieser Untersuchung?
- Welche Einschränkungen wurden dort ausdrücklich benannt?

**B. Erneute unabhängige Repository-Prüfung**
- Welche Dateien, Commits, Tests und Implementierungsdetails wurden von dir tatsächlich untersucht?
- Welche Befunde konntest du eigenständig nachvollziehen?
- Welche früheren Aussagen wurden bestätigt, korrigiert oder verworfen?

**C. Gemeinsame Synthese und Bewertung**
- Welche Schlussfolgerungen ergeben sich aus der Kombination beider Prüfungen?
- Wo besteht eine tragfähige gemeinsame Erkenntnisbasis?
- Wo bleiben unterschiedliche Einschätzungen oder offene Fragen bestehen?

Führe die Quellen und Belege so auf, dass ein späterer Leser die wesentlichen Aussagen zurückverfolgen kann.

Verwende nach Möglichkeit konkrete Pfade, Abschnittsüberschriften, Zeilenangaben, Commit-Hashes und Testergebnisse. Behaupte keine Prüfung, die nicht tatsächlich stattgefunden hat.

Erfinde keine Quellenangaben, Testergebnisse, Commit-Informationen oder Provenance-Daten.

## 8. Aufbau des aktualisierten Gutachtens

Überarbeite `GUTACHTEN.md` als zusammenhängendes Dokument. Ein bloßes Anhängen des Deep-Research-Berichts ist nicht ausreichend.

Die konkrete Gliederung darf sich am vorhandenen Gutachten orientieren und bei Bedarf verbessert werden. Inhaltlich sollte das Ergebnis mindestens Folgendes enthalten:

1. **Dokumentinformationen und Prüfstand**
   - Datum und Repository-Stand
   - Branch, Commit und Versionsangabe
   - verwendete Untersuchungsgrundlagen
   - Provenance und Synthesebasis

2. **Management Summary**
   - wichtigste Erkenntnisse
   - wesentliche Stärken
   - wichtigste Risiken und offene Punkte
   - Gesamtbewertung

3. **TGD-Prozessmodell**
   - Knoten, Rollen und Verantwortlichkeiten
   - Übergänge, Gates und Handoff-Artefakte
   - Test-Freeze und Audit-Rückwege

4. **Implementierung und Testbasis**
   - relevante Architektur- und Implementierungsbefunde
   - Bezug zwischen Dokumentation, Code und Tests
   - tatsächliche Grenzen der Verifikation

5. **Auswertung des Deep-Research-Berichts**
   - bestätigte, präzisierte, eingeschränkte und widerlegte Befunde
   - offene Punkte
   - ergänzende Erkenntnisse

6. **Kritische Gesamtbewertung**
   - Stärken
   - Risiken und Schwächen
   - epistemische Grenzen
   - Verhältnismäßigkeit und Prozessaufwand

7. **Priorisierte Empfehlungen**
   - konkrete Problemstellung
   - Begründung und Belege
   - erwarteter Nutzen
   - Priorität und gegebenenfalls Aufwand
   - Kennzeichnung, wenn es sich lediglich um eine optionale Verbesserung handelt

8. **Threads of Validity / Gültigkeitsgrenzen**
   - welche Teile der Begutachtung belastbar sind
   - welche Teile eingeschränkt gelten
   - welche Punkte noch nicht abschließend untersucht werden konnten
   - welche zusätzlichen Prüfungen erforderlich wären

9. **Quellen und Provenance**
   - Repository-interne Grundlagen
   - externe Quellen des Deep-Research-Berichts
   - eigenständig ergänzte Quellen
   - nachvollziehbare Trennung der jeweiligen Beiträge

Die Threads of Validity sollen nicht aus Gründen einer scheinbar höheren Vollständigkeit entfernt oder künstlich aufgelöst werden. Aktualisiere ihren Status anhand der neuen Erkenntnisse.

## 9. Arbeitsweise und Ressourcenbewusstsein

Dieser Auftrag erfordert eine sorgfältige Analyse, aber keinen vollständigen autonomen TGD-Zyklus.

Arbeite deshalb in klaren Untersuchungsschritten:

1. Repository- und Dokumentenstand feststellen.
2. Routing-Indizes und relevante TGD-Dokumentation untersuchen.
3. Deep-Research-Bericht und bestehendes Gutachten auswerten.
4. Relevante Git-Deltas, Implementierungen und Tests prüfen.
5. Frühere Befunde systematisch bewerten.
6. Synthese erstellen und `GUTACHTEN.md` aktualisieren.
7. Ergebnis und Einschränkungen abschließend prüfen.

Priorisiere die Prüfung der entscheidenden Aussagen gegenüber einer möglichst umfangreichen Untersuchung nebensächlicher Details.

Führe keine unnötigen vollständigen Testläufe, Mutationstest-Suiten oder weiteren Agenten-Zyklen durch. Nutze gezielte Prüfungen, wenn sie einen konkreten Befund tatsächlich verifizieren können.

Sollte ein individuelles Quota-Limit erreicht werden:

- Kennzeichne den erreichten Arbeitsstand eindeutig.
- Stelle bereits erarbeitete Erkenntnisse nicht als vollständig geprüft dar.
- Versuche nicht, durch unbelegte Formulierungen ein abgeschlossenes Gutachten vorzutäuschen.
- Lasse das bestehende `GUTACHTEN.md` unverändert, solange die notwendige Synthese nicht verantwortbar abgeschlossen werden kann.

## 10. Schreib- und Änderungsgrenzen

**Erlaubte Änderung:**
- Aktualisierung von `GUTACHTEN.md`.

**Nicht erlaubt:**
- Änderungen an `src/`, `tests/`, `pyproject.toml` oder CI-Konfigurationen.
- Änderungen an den TGD-Handbüchern oder DEV-Guides.
- Änderungen am Deep-Research-Bericht.
- Erstellung oder Änderung von Issues und Pull Requests.
- Commits, Pushes oder sonstige Veröffentlichungsschritte.
- Automatische Archivierung oder Bereinigung anderer Repository-Dateien.

Alle übrigen Projektdateien sind Untersuchungsgrundlage und bleiben unverändert.

Nimm keine Änderungen am Repository vor, die über das aktualisierte Ziel-Gutachten hinausgehen.

## 11. Abschluss

Nach erfolgreicher Aktualisierung:

- Prüfe den vollständigen Inhalt von `GUTACHTEN.md`.
- Verifiziere, dass alle wesentlichen Aussagen nachvollziehbar belegt oder ausdrücklich als Einschätzung gekennzeichnet sind.
- Prüfe, ob die unterschiedlichen Erkenntnisebenen und Gültigkeitsgrenzen verständlich auseinandergehalten werden.
- Prüfe den abschließenden Git-Status und bestätige, dass ausschließlich `GUTACHTEN.md` verändert wurde.

Gib anschließend eine kurze Zusammenfassung mit:

1. dem aktualisierten Prüfstand,
2. den wichtigsten bestätigten oder korrigierten Befunden,
3. den wichtigsten neuen Erkenntnissen,
4. den weiterhin offenen Threads of Validity,
5. dem Speicherort des aktualisierten Gutachtens,
6. gegebenenfalls nicht durchführbaren Prüfungen.

**Maßstab für die Qualität des Ergebnisses:** Das Gutachten soll nicht möglichst viele Regeln, Empfehlungen oder vermeintliche Mängel enthalten. Es soll möglichst präzise darstellen, was qb-cubie tatsächlich leistet, worauf diese Einschätzung beruht und wo die Grenzen der Aussagekraft liegen.