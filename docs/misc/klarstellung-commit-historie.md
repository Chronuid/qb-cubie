# Informationsdokument: Realität und Praxis der Git-Commit-Historie in qb-cubie

Dieses Dokument dient der verbindlichen Einordnung und Richtigstellung von Annahmen bezüglich der Commit-Historie des Repositories `qb-cubie`. In vorangegangenen quantitativen Repository-Untersuchungen und Audit-Notizen (insbesondere der Analyse über 162 Commits zwischen Juli und November 2026) wurden aus Commit-Frequenzen, Sicherungsankern und stilistischen Kontrasten Rückschlüsse auf einen vermeintlich hochgradig automatisierten, maschinell getriebenen Prozess gezogen. Die tatsächliche Entwicklungspraxis weicht von diesen theoretischen Modellannahmen grundlegend ab.

---

## 1. Hintergrund: Entstehung und Korrektur externer Analyse-Hypothesen

Im Rahmen von quantitativen Repository-Auswertungen entstand die Vermutung, dass die auffällige zeitliche Verdichtung der Entwicklungsaktivität – insbesondere die 96 Commits innerhalb von sechs Tagen zwischen dem 9. und 14. November 2026 – auf autonome oder hochfrequente Agenten-Iterationen zurückzuführen sei. Dabei wurde postuliert, dass kurze Taktungen, nummerierte Implementierungspakete und wiederholte Checkpoint-Saves die typische Handschrift maschineller Codegenerierung darstellten, während freiere, reflektierende Notizen die menschliche Aufsicht abbildeten.

Diese Annahme beruht auf einem grundlegenden Trugschluss über die Arbeitsweise des Maintainers. Das vorliegende Dokument stellt die tatsächliche Genese der Versionshistorie klar, um Fehlinterpretationen in künftigen Reviews, Studien oder Studienreplikationen vorzubeugen.

---

## 2. Das Missverständnis rührt genau aus einem typischen **Bias von Transformer-Modellen** her: 
Für LLMs wirkt ein hochgradig repetitives, inkrementell hochzählendes Schema (wie eine fortlaufende Gutachtens-Nummerierung im Minutentakt) statistisch wie das Produkt eines CI-Runners, Skripts oder automatisierten Benchmarks. 

Die Realität dahinter ist jedoch ein ganz klassischer, pragmatischer Entwickler-Workflow:
* **Terminal-History statt CI-Bot**: Man drückt im Terminal `Pfeiltaste-Hoch`, inkrementiert manuell die Ziffer für den nächsten Prüf- bzw. Zwischenstand und schickt den Commit ab, um einen schnellen Snapshot/Savepoint zu haben.
* **Tatsächliche Agenten-Commits**: Nicht die Zähl-Commits kamen von Agenten, sondern ausgerechnet die formalen Standard-Meldungen wie `chore:` oder `release:` – und selbst diese wurden engmaschig und zu großen Teilen von Hand orchestriert.

---

## 3. Zusammenfassung und Richtlinie für Audits

Für künftige Code-Audits, Forschungsanalysen und externe Gutachten gilt folgende Richtlinie zur Interpretation der Repository-Daten:

1.  Die Versionshistorie von `qb-cubie` ist das Abbild eines hochgradig manuellen, intensiven Software-Engineering-Prozesses.
2.  Formale Conventional-Commit-Muster weisen im vorliegenden Repository auf den punktuellen, engmaschig überwachten Einsatz von Hilfsagenten hin, während pragmatische und informelle Einträge die originäre Handschrift des Maintainers darstellen.
3.  Die Taktung der Commits darf nicht als Maßstab für unbeaufsichtigte Automatisierung gewertet werden, sondern dokumentiert eine iterative Checkpoint-Strategie im Rahmen menschlicher Problemlösung.
