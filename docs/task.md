## Ziel: Entwicklung des `rbt.py`-Moduls

Wir haben die theoretischen Grundlagen gefestigt und die Dokumentation vorbereitet. Nun gilt es, das `rbt.py`-Modul mit Leben zu füllen und zu entwickeln. 

- Hierfür bitte ich um deine volle Unterstützung im Code-Engineering. Ich werde ausschließlich als "Phasen-Orchestrator" und "HumanReviewer" agieren und vertraue auf deine Fähigkeiten im Coding.
- Ich habe zwar die 1. Phase für Vorschläge gekennzeichnet, aber gerne kannst du jederzeit während jeder Phase meine Ideen, Reviews und Entscheidungen kritisieren und in Frage stellen. Ich bin schließlich auch nur ein Mensch und bin offen für neue Perspektiven und Änderungs-Vorschläge.

## Kontext

### Die Docs im Anhang
Ich habe dir im Anhang die folgenden Dokumente hinterlegt:
* `GUIDE_RBT-Usage-Pattern.md`: die "Usage-Pattern" definieren die Anforderungen und das Verhalten für das RBT-Modul. 
* `DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md`: das allgemeine Entwickler-Dokument für das Modul. 
* `DEV-GUIDE_1-1_RBT-Classes.md`: die "API-Dokumentation" mit den Modul-Klassen und den dazugehörigen Klassen-Attributen.
* `rbt.py`: Das Modul mit ein paar vorbereiteten Skizzen.
* `Design-Guide.md`: Richtlinien für Code-Design.
* `Style-Guide.md`: Richtlinien für Code-Ästhetik.

### Funktionen des Moduls 

Dir wird sicherlich aufgefallen sein, dass in der "API-Dokumentation" noch keinerlei Funktionen dokumentiert sind. Das war eine bewusste Entscheidung, da sich die internen Mechanismen und Funktionen erst jetzt mit der Entwicklung herausbilden werden. 

- Aus dem Usage-Pattern-Dokument ergibt sich bereits implizit, dass die EBT-Klasse eine run()-Funktion benötigt. 
- Aus dem "RBT-Classes"-Dokument ergibt sich bereits explizit das Protokoll für die `Reviewer`-Klassen, wobei sowohl die erwartete `review()`-Funktion, als auch die `ReviewData`-Datenklasse vordefiniert sind. 

Weiterführende Funktionen und Mechanismen sollen sich zwar aus der Entwicklung ergeben, aber dennoch ist es erwünschenswert, dass dabei folgendes Muster angestrebt wird:
* **Konzeptuelle Phasen:** `arrange` (die Call-Interpretation und weiteren Details), `review` (die Übergabe an den Reviewer), `report` (Die Assertion- und Berichts-Übergabe an Pytest. Keine Magie hier, sondern einfach nur eine simple Asssertion mit der Übergabe vom report als String. Später können wir noch darüber nachdenken hier Hilfsfunktionen für die Formatierung aufzusetzen). Das hier sind keine einzelnen Funktionen, sondern Phasen, also Bereiche in denen beliebig viele Funktionen als Steps definiert und die bei Bedarf zu Kompositions-Funktionen für diese Phase gebündelt werden könnten.
* `run()`: soll die Haupt-Funktion sein, die nach außen hin aufgerufen wird und als Pipeline die Phasen orchestriert. Also der Einstiegspunkt, welche alle anderen Kompositions-Funktionen komponiert.

## Auftrag

Um das `rbt.py`-Modul zu entwickeln teilen wir die Entwicklung in Phasen auf. Um das zu ermöglichen, kürzen wir zunächst die "HumanReview"-Klasse aus dem Modul raus und arbeiten zu Beginn mit einer "MockReview"-Klasse, welche einfach nur ein paar Sekunden wartet und das `ReviewData`-Klasse.  
Meine Prüfung stellt dabei die Kante dar, welche es ermöglicht von einer Phase zur nächsten zu kommen. Erst wenn ich grünes Licht gebe und die nächste Phase initiiere, gehen wir zur nächsten Phase über.

Die Phasen werden wie folgt gegliedert sein
* **Phase 1:** On-Boarding, Rückfragen und Vorschläge (Jetzt)
* **Phase 2:** RBT-Skellet (MockReviewer)
* **Phase 3:** RBT-Full (HumanReviewer)

---

Wir sind aktuell in der Phase 1. Wie verstehst du das Ganze? Hast du Rückfragen zur Entwicklung vom `rbt.py`-Modul, Vorschläge oder anderweitige Fragen?