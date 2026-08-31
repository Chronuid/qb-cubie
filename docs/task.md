## Ziel: Entwicklung des `ebt.py`-Moduls

Wir haben die theoretischen Grundlagen gefestigt und die Dokumentation vorbereitet. Wir befinden uns schon mitten in der Entwicklung vom `ebt.py`-Modul. 

- Hierfür bitte ich um deine volle Unterstützung im Code-Engineering. Ich werde ausschließlich als "Phasen-Orchestrator" und "HumanReviewer" agieren und vertraue auf deine Fähigkeiten im Coding.
- Ich habe die 1. Phase der 1. Etappe für Vorschläge gekennzeichnet, aber gerne kannst du jederzeit während jeder Phase meine Ideen, Reviews und Entscheidungen kritisieren, in Frage stellen und Ideen einwerfen. Ich bin schließlich auch nur ein Mensch und bin offen für neue Perspektiven und Änderungs-Vorschläge.
- Hier wird zwar schon die gesamte Entwicklung des ebt-Moduls als Ziel skizziert, aber zunächst gilt es erstmal den Fokus auf ein Sub-Ziel zu richten: Für diese Konversation ist die Phase 6 das fokussierte Ziel, welches wir erreichen wollen.

## Kontext

### Die Docs im Anhang
Ich habe dir im Anhang die folgenden Dokumente hinterlegt:

* `ebt.py`: Der aktuelle Code vom EBT-Modul.
* `GUIDE_EBT-Usage-Pattern.md`: die "Usage-Pattern" definieren die Anforderungen und das Verhalten für das EBT-Modul. 
* `DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`: das allgemeine Entwickler-Dokument für das Modul.
* `DEV-GUIDE_2.2_WorldState-Class.md`: Dedizierte Erklärungen zur WorldState-Klasse.
* `Design-Guide.md`: Richtlinien für Code-Design.
* `Style-Guide.md`: Richtlinien für Code-Ästhetik.

## Auftrag

Um das `ebt.py`-Modul zu entwickeln teilen wir die Entwicklung in Etappen und Phasen auf.  
Meine Prüfung stellt dabei die Kante dar, welche es ermöglicht von einer Phase zur nächsten zu kommen. Erst wenn ich grünes Licht gebe und die nächste Phase initiiere, gehen wir zur nächsten Phase über.

### Etappe 1: EBT-Foundation

Bestimmt hast du gemerkt, dass in den Usage-Pattern auch Shorthands wie `EBT(target=my_func, pre=(1, 2), post=3).run()` dokumentiert sind. Diese sind zwar wichtig für das Endergebnis, aber um die Entwicklung einfacher zu gestalten, werden wir diese vorerst ignorieren und uns ausschließlich auf die vollständigen Deklarationen fokussieren. Sobald es so weit ist, können wir dann die _arrange-Phase anpassen, aber vorerst gilt es die Shorthands und die "Auto-Inferenz" außen vorzulassen.
In dieser Etappe entwickeln wir das EBT-Modul vollkommen souverän und unabhängig von der ConventionMap.

* **Phase 1 (Wiederholung zu jeder neuen Konversation):** Rückfragen und Details besprechen, um Verständnis und Klarheit zu fördern. Gerne kannst du hier auch die Planung in Frage stellen oder Ideen einwerfen.

* **Phase 2:** Grundlegende Funktionalität → DONE

* **Phase 3:** Arena-Integration → DONE

* **Phase 4:** Dateisystem-Integration → DONE

* **Phase 5:** Quantoren → DONE

* **Phase 6:** Arena-Abgleich → Done

* **Phase 7 (OPEN):** Stabilisierung, Feinschliff und Wrap-Up. Etwaige Kleinigkeiten und Nebensächlichkeiten prüfen, optimieren und verbessern. Dazu alles ordentlich dokumentieren und die Etappe sauber abschließen.

### Etappe 2: ConventionMap
...

### Etappe 3: EBT-Extra
...

---

Nochmal zur Erinnerung: Wir gehen immer erst dann zur nächsten Phase über, wenn ich grünes Licht gebe und die nächste Phase initiiere.

Zusätzlich sei gesagt, dass die Phase 6 nicht ein einzelner Schritt darstellt, sondern eine ganze Phase, die wir noch in weitere Sub-Phasen aufteilen können. Wir One-Shotten hier nichts, sondern machen uns in aller Ruhe Gedanken und nehmen uns die Zeit, die es braucht, um das sauber und gut zu realisieren.

Wir sind aktuell bei der Etappe 1 in der ersten Phase. Wie verstehst du das Ganze? Hast du Rückfragen zur Entwicklung vom `ebt.py`-Modul, Vorschläge oder anderweitige Fragen?


