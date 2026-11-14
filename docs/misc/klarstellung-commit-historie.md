# Informationsdokument: Realität und Praxis der Git-Commit-Historie in qb-cubie

Dieses Dokument dient der verbindlichen Einordnung und Richtigstellung von Annahmen bezüglich der Commit-Historie des Repositories `qb-cubie`. In vorangegangenen quantitativen Repository-Untersuchungen und Audit-Notizen (insbesondere der Analyse über 162 Commits zwischen Juli und November 2026) wurden aus Commit-Frequenzen, Sicherungsankern und stilistischen Kontrasten Rückschlüsse auf einen vermeintlich hochgradig automatisierten, maschinell getriebenen Prozess gezogen. Die tatsächliche Entwicklungspraxis weicht von diesen theoretischen Modellannahmen grundlegend ab.

---

## 1. Hintergrund: Entstehung und Korrektur externer Analyse-Hypothesen

Im Rahmen von quantitativen Repository-Auswertungen entstand die Vermutung, dass die auffällige zeitliche Verdichtung der Entwicklungsaktivität – insbesondere die 96 Commits innerhalb von sechs Tagen zwischen dem 9. und 14. November 2026 – auf autonome oder hochfrequente Agenten-Iterationen zurückzuführen sei. Dabei wurde postuliert, dass kurze Taktungen, nummerierte Implementierungspakete und wiederholte Checkpoint-Saves die typische Handschrift maschineller Codegenerierung darstellten, während freiere, reflektierende Notizen die menschliche Aufsicht abbildeten.

Diese Annahme beruht auf einem grundlegenden Trugschluss über die Arbeitsweise des Maintainers. Das vorliegende Dokument stellt die tatsächliche Genese der Versionshistorie klar, um Fehlinterpretationen in künftigen Reviews, Studien oder Studienreplikationen vorzubeugen.

---

## 2. Tatsächliche Urheberschaft: Manuelle Entwicklung im Hochfrequenz-Takt

Nahezu die gesamte Versionshistorie des Repositories stammt manuell und unmittelbar aus der Hand des Maintainers. Die scheinbar maschinellen Merkmale der Versionskontrolle sind das Resultat einer intensiven, fokussierten Arbeitsweise und keineswegs das Produkt autonom agierender Skripte oder Pipelines:

*   **Manuelle Einzelausführung:** Sämtliche schnellen Zwischenstände, Code-Refactorings, Sprint-Commits und experimentellen Iterationen wurden vom Entwickler persönlich initiiert, formuliert und committet.
*   **Hohe manuelle Schlagzahl:** Die beobachteten kurzen Zeitabstände zwischen einzelnen Ständen spiegeln konzentrierte Arbeitssitzungen wider, in denen Teilschritte in schneller Folge lokal gesichert wurden, um logische Zwischenstände festzuhalten.
*   **Rolle von KI-Agenten:** Lediglich eine sehr geringe Anzahl einzelner Commits wurde überhaupt durch KI-Agenten ausgeführt. Diese wenigen Vorgänge fanden ausnahmslos unter direkter, naher Beobachtung und strikter menschlicher Kontrolle statt; es gab zu keinem Zeitpunkt eine unüberwachte oder autonome Commit-Schleife.

---

## 3. Die stilistische Inversion: Das Paradoxon der Commit-Nachrichten

Eine der prägnantesten Fehlinterpretationen betrifft die sprachliche Form der Commit-Nachrichten. Während automatisierte Analyse-Tools dazu neigen, strukturierte und standardisierte Texte maschinellen Prozessen und freie Formulierungen menschlichen Akteuren zuzuordnen, liegt in `qb-cubie` genau das gegenteilige Muster vor.

Die stilistische Verteilung im Projekt stellt sich wie folgt dar:

| Erscheinungsbild der Commit-Message | Tatsächliche Urheberschaft | Funktion und Entstehungskontext |
| :--- | :--- | :--- |
| **Konventionell / Formal („Professionell“)**<br>*(z. B. strikte Conventional Commits, standardisierte Präfixe wie `feat(...)`, `chore(release): ...`)* | **KI-Agenten**<br>*(unter naher menschlicher Aufsicht)* | Entstand dort, wo Agenten für spezifische Teilaufgaben angewiesen wurden und dabei standardisierte Prompt- und Rollenmuster für formale Git-Nachrichten reproduzierten. |
| **Pragmatisch / Informell / Freitext**<br>*(z. B. Arbeitskommentare, knappe Notizen, Checkpoints, persönliche Gedanken)* | **Maintainer (Mensch)**<br>*(manuelle Entwicklung)* | Menschliche Arbeitsnotizen, die den unmittelbaren Kontext, situative Überlegungen oder schlicht den aktuellen Sicherungsstand festhalten. |

Die Annahme, dass unkonventionelle oder humorvolle Commit-Nachrichten die einzigen menschlichen Spuren im Projekt seien, verkehrt die Realität ins Gegenteil: Die gesamte Bandbreite der Entwicklungsarbeit – von den tiefgreifenden architektonischen Umbauten über komplexe Service-TDD-Zyklen bis hin zu knappen Checkpoint-Saves – wurde manuell gesteuert.

---

## 4. Workflow-Philosophie: Versionskontrolle als persönliches Message-Board

Die Verwendung von Git im Projekt folgte bisher bewusst nicht den rigiden Konventionen eines kollaborativen Großunternehmens, sondern diente einem agilen, individuellen Entwicklungsansatz.

Die Commit-Nachrichten wurden primär als persönliches **Message-Board** und dynamisches Logbuch verwendet:

1.  **Gedankenprotokollierung im Fluss:** Commit-Texte dienten dazu, spontane Erkenntnisse, offene Skepsis, methodische Zwischenstände oder Arbeitsabsichten im Moment des Speicherns festzuhalten, ohne den Programmierfluss durch formale Konventionen zu unterbrechen.
2.  **Sicherungsnetz für explorative Pfade:** Schnelle Checkpoints fungierten als lokale Retusche- und Sicherungsanker, um risikolos radikale Umbauten (wie den Ausbau von Services oder das Entschlacken historischer Altlasten) auszuprobieren.
3.  **Transparente Selbstreflexion:** Die Nachrichten spiegeln den ungeschminkten Denkprozess des Entwicklers wider und sind als authentische Werkstattberichte zu verstehen, nicht als glattpolierte Marketing-Artefakte.

---

## 5. Systemarchitektur: Abwesenheit strukturabhängiger Automatisierungen

Ein wesentlicher Grund für den Verzicht auf starre Commit-Konventionen liegt in der technischen Ausgestaltung der Release- und Build-Infrastruktur von `qb-cubie`.

Im aktuellen Entwicklungsstadium existieren keine automatisierten Werkzeuge, die auf eine strukturierte Commit-Syntax angewiesen wären:

*   **Kein Semantic Release über Commit-Parsing:** Es sind keine Werkzeuge wie `semantic-release` oder automatisierte Commit-Parser im Einsatz, die Versionen, Release-Entscheidungen oder Changelog-Einträge syntaktisch aus Commit-Präfixen ableiten.
*   **Entkoppelte Release-Pipeline:** Gemäß dem verbindlichen Release-Leitfaden des Projekts basiert die Release-Automatisierung auf dedizierten Git-Tags (`vX.Y.Z`) und der zentralen Versionsangabe in der Konfigurationsdatei `pyproject.toml`.
*   **Manuelle Changelog-Kuration:** Die Release-Notes werden verbindlich und inhaltlich kuratiert in der zentralen Datei `CHANGELOG.md` gepflegt, aus welcher der Veröffentlichungs-Workflow die entsprechenden Abschnitte extrahiert.

Da somit kein nachgelagertes System von einer formalisierten Commit-Struktur profitiert hätte, bestand kein technischer oder betrieblicher Anlass, den manuellen Entwicklungsfluss durch einengende Commit-Korsette zu verlangsamen.

---

## 6. Zusammenfassung und Richtlinie für Audits

Für künftige Code-Audits, Forschungsanalysen und externe Gutachten gilt folgende Richtlinie zur Interpretation der Repository-Daten:

1.  Die Versionshistorie von `qb-cubie` ist das Abbild eines hochgradig manuellen, intensiven Software-Engineering-Prozesses.
2.  Formale Conventional-Commit-Muster weisen im vorliegenden Repository auf den punktuellen, engmaschig überwachten Einsatz von Hilfsagenten hin, während pragmatische und informelle Einträge die originäre Handschrift des Maintainers darstellen.
3.  Die Taktung der Commits darf nicht als Maßstab für unbeaufsichtigte Automatisierung gewertet werden, sondern dokumentiert eine iterative Checkpoint-Strategie im Rahmen menschlicher Problemlösung.

---

## 7. Human Note

KI-Agenten neigen dazu Dinge, die sich ähnlich klingen, zu verdrehen und zu vermischen, wenn man diese Dinge nicht ausdrücklich formuliert und die Differenzen hervorhebt. Diese Datei hier wurde von Gemini formuliert, nachdem ich auf das Missvertändnis hingewiesen habe. 
Vorallem die strukturierte Gutachten-Empfehlungs-Nr.-Implementationen könnten möglicherweise zur Hypothese veranlassen, dass das ein automatisierter Prozess war. Ja, irgendwie war es das, denn für die Zwischenstände konnte ich im Terminal einfach mit der Pfeiltaste nach oben die letzten Commands wiederherstellen und musste nur noch die Nummerierung hoch ziehen. Diese Datei hier dient als beispielhaftes Exemplar im Kleinen Maßstab dafür, wie die "hochfrequenten" Commits entstanden :3
