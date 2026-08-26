## Ziel: Entwicklung des `ebt.py`-Moduls

Wir haben die theoretischen Grundlagen gefestigt und die Dokumentation vorbereitet. Wir befinden uns schon mitten in der Entwicklung vom `ebt.py`-Modul. 

- Hierfür bitte ich um deine volle Unterstützung im Code-Engineering. Ich werde ausschließlich als "Phasen-Orchestrator" und "HumanReviewer" agieren und vertraue auf deine Fähigkeiten im Coding.
- Ich habe die 1. Phase der 1. Etappe für Vorschläge gekennzeichnet, aber gerne kannst du jederzeit während jeder Phase meine Ideen, Reviews und Entscheidungen kritisieren, in Frage stellen und Ideen einwerfen. Ich bin schließlich auch nur ein Mensch und bin offen für neue Perspektiven und Änderungs-Vorschläge.
- Hier wird zwar schon die gesamte Entwicklung des ebt-Moduls als Ziel skizziert, aber zunächst gilt es erstmal den Fokus auf ein Sub-Ziel zu richten: Für diese Konversation ist die Phase 4 das fokussierte Sub-Ziel, welches wir erreichen wollen.

## Kontext

### Die Docs im Anhang
Ich habe dir im Anhang die folgenden Dokumente hinterlegt:

* `ebt.py`: Der aktuelle Code vom EBT-Modul.
* `pyvenv.py`: Die Arena, welches vom EBT-Modul genutzt wird.
* `GUIDE_EBT-Usage-Pattern.md`: die "Usage-Pattern" definieren die Anforderungen und das Verhalten für das RBT-Modul. 
* `DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`: das allgemeine Entwickler-Dokument für das Modul.
* `DEV-GUIDE_2.2_WorldState-Class.md`: Dedizierte Erklärungen zur WorldState-Klasse.
* `Design-Guide.md`: Richtlinien für Code-Design.
* `Style-Guide.md`: Richtlinien für Code-Ästhetik.

### Funktionen des Moduls 

Dir wird sicherlich aufgefallen sein, dass in der "API-Dokumentation" noch keinerlei Funktionen dokumentiert sind. Das war eine bewusste Entscheidung, da sich die internen Mechanismen und Funktionen erst jetzt mit der Entwicklung herausbilden werden. 

Weiterführende Funktionen und Mechanismen sollen sich zwar aus der Entwicklung ergeben, aber dennoch ist es erwünschenswert, dass dabei folgendes Muster angestrebt wird:
* **Konzeptuelle Phasen:** `_arrange` (die Konstrukt-Interpretation, Initialisierungen und Vorbereitungen), `_validate` (die Ausführung des eigentlichen Test-Laufs), `_report` (Die Assertion- und Berichts-Übergabe an Pytest. Keine Magie hier, sondern einfach nur eine simple Asssertion). Das hier sind keine einzelnen Funktionen, sondern Phasen, also Bereiche in denen beliebig viele Funktionen als Steps definiert und die bei Bedarf zu Kompositions-Funktionen für diese Phase gebündelt werden könnten.
* `run()`: die Haupt-Funktion, die nach außen hin aufgerufen wird und als Pipeline die Phasen orchestriert. Also der Einstiegspunkt, welche alle anderen Kompositions-Funktionen komponiert.

## Auftrag

Um das `ebt.py`-Modul zu entwickeln teilen wir die Entwicklung in Etappen und Phasen auf.  
Meine Prüfung stellt dabei die Kante dar, welche es ermöglicht von einer Phase zur nächsten zu kommen. Erst wenn ich grünes Licht gebe und die nächste Phase initiiere, gehen wir zur nächsten Phase über.

### Etappe 1: EBT-Foundation

Bestimmt hast du gemerkt, dass in den Usage-Pattern auch Shorthands wie `EBT(target=my_func, pre=(1, 2), post=3).run()` dokumentiert sind. Diese sind zwar wichtig für das Endergebnis, aber um die Entwicklung einfacher zu gestalten, werden wir diese vorerst ignorieren und uns ausschließlich auf die vollständigen Deklarationen fokussieren. Sobald es so weit ist, können wir dann die _arrange-Phase anpassen, aber vorerst gilt es die Shorthands und die "Auto-Inferenz" außen vorzulassen.
In dieser Etappe entwickeln wir das EBT-Modul vollkommen souverän und unabhängig von der ConventionMap.

* **Phase 1 (Wiederholung zu jeder neuen Konversation):** Rückfragen und Details besprechen, um Verständnis und Klarheit zu fördern. Gerne kannst du hier auch die Planung in Frage stellen oder Ideen einwerfen.

* **Phase 2 (DONE):** Grundlegende Funktionalität → test_1 und test_2 aus den Usage-Pattern im Format der vollständigen Deklaration. Hier entwickeln wir das gesamte funktionale Skellet des Moduls (ohne Arena, ohne FS und ohne Quantoren). Also das grundlegende Fundament und die wichtigsten Mechanismen.

* **Phase 3 (DONE):** Arena-Integration → test_3 aus den Usage-Pattern im Format der vollständigen Deklaration. Um die dokumentierten Anforderungen zu erfüllen, gilt es hierfür eine dedizierte PyVenv-Klasse zu realisieren, die sich per DI einsetzen, konfigurieren und austauschen lässt. Der Abgleich der Arenen innerhalb der WorldStates als Test kommt erst später, zunächst geht es nur um die Arenen für das statische EBT.arena-Attribut.

* **Phase 4 (OPEN):** Dateisystem-Integration → test_4, test_5 und test_6. Hier könnten wir die Pytest-nativen Lösungen wie tmp-path und tmp-path-factory zurückgreifen.

* **Phase 5 (OPEN):** Quantoren → test_7, test_8, test_9, test_10 und test_11. Hier stellen wir sicher, dass man mit der reinen Deklaration WorldState-Listen im Konstruktur gleich eine ganze Reihe von Tests anstoßen kann. Dabei müssen wir lediglich zwischen Allquantoren und Existenzquantoren differenzieren und die Testlogik entsprechend umleiten, sowie wir sicherstellen, dass die Ergebnisse im Pytest-Report ohne Redundanz und verständlich dargestellt werden.

* **Phase 6 (OPEN):** Arena-Abgleich → test_12. Hier verarbeiten wir die Arenen-Deklaration in den jeweiligen WorldStates. In der Theorie ist das zwar die gleiche Logik wie bei den vorherigen Tests, aber mir wurde gesagt, dass das ziemlich ineffizient werden könnte, weswegen wir das hier in einer eigenen Phase nochmal dediziert behandeln und uns effizientere Methoden für den Abgleich überlegen.

* **Phase 7 (OPEN):** Stabilisierung, Feinschliff und Wrap-Up. Etwaige Kleinigkeiten und Nebensächlichkeiten prüfen, optimieren und verbessern. Dazu alles ordentlich dokumentieren und die Etappe sauber abschließen.

### Etappe 2: ConventionMap

* **Phase 1:** Vorbereitung 
* **Phase 2:** Entwicklung der agnostischen ConventionMap
* **Phase 3:** Feinschliff, Dokumentation

### Etappe 3: EBT-Extra

* **Phase 1:** Vorbereitung
* **Phase 2:** Integration der Convention-Map und Weiter-Entwicklung des EBT-Moduls.
* **Phase 3:** Feinschliff, Dokumentation

---

Wir sind aktuell bei der Etappe 1 in der ersten Phase. Wie verstehst du das Ganze? Hast du Rückfragen zur Entwicklung vom `ebt.py`-Modul, Vorschläge oder anderweitige Fragen?
