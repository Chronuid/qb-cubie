# QA-Bench
> *Simple and customizable **Quality Assurance** Builder*

 Warum komplexen Test-Code schreiben, wenn uns das maschinelle Lernen bereits vorgemacht hat, wie man Validierungs-Mechanismen elegant, skalierbar und universell gestaltet? Lass uns ein Code-Gym bauen!
* (optional) **Auto-Assurance:** scanned den Source-Code, prüft welche Tests existieren und welche nicht und bereitet alle fehlenden Test-Schablonen zum Ausfüllen vor, um die Entwicklung zu vereinfachen.

* **Info-Reports:** gute Einsehbarkeit der Coverage, Validations-Grade und Zustände.

---

---

Die Kern-Ideen basieren auf einigen Prinzipien der mathematischen Programmverifikation. Um den Kern zu verstehen, sagen wir vereinfacht, dass wir logische Bedingungen wie Datentypen behandeln können:
* **P** = Vorbedingung (z. B. "Eingabe ist eine Zahl")  
* **S** = Programmsegment (die auszuführende Funktion)  
* **Q** = Nachbedingung (z. B. "Ausgabe ist das Quadrat der Zahl")

Das klassische **Hoare-Tripel** beschreibt, wie ein Programm den Zustand einer Berechnung verändert:
$$\text{Hoare-Tripel} = \{P\}\; S\; \{Q\}$$

> Wenn die Vorbedingung $P$ vor der Ausführung von $S$ zutrifft, dann gilt nach der Ausführung von $S$ die Nachbedingung $Q$.

Da wir in modernen Sprachen direkt mit Funktionen arbeiten, stellen wir dieses Tripel einfach auf das Verhalten von $S$ um:
$$\{P\}\; S\; \{Q\} \quad \equiv \quad S: P \to Q$$

> Das Programmsegment $S$ ist eine Abbildung (Funktion), die Daten des Typs $P$ (Eingabe) entgegennimmt und Daten des Typs $Q$ (Ausgabe) liefert.

---
Das Projekt ist darauf ausgelegt die Prinzipien der Programmverifikation einfach und zugänglich umsetzen und automatisieren zu können, um für die synthetische Software-Generierung und Code-ML-Projekte verwendet werden zu können. Hierfür lässt sich die eben definierte Umstellung um den Suchraum des Code-Generators ($S \in \Sigma^*$) erweitern: 

 $$\mathcal{S}_{\text{summ}} = \{ S \in \Sigma^* \mid S: P \to Q \}$$

> **Für Einsteiger übersetzt:** 
> * $\Sigma^*$ (Sigma-Star) ist das unendliche Chaos – die Menge aller denkbaren Zeichenketten und Code-Zeilen, die man tippen könnte.
> * $\mathcal{S}_{\text{summ}}$ ist am Ende die saubere "Kiste", in die wir alle funktionierenden Programme $S$ hineinsortieren.
>
> *Lesehilfe für die Formel:* "Die Lösungsmenge $\mathcal{S}_{\text{summ}}$ besteht aus allen Quellcodes $S$ aus dem unendlichen Chaos $\Sigma^*$, für die gilt: Das Programm $S$ überführt die Eingabe $P$ korrekt in die Ausgabe $Q$."

--- 

Um die Nicht-Funktionalen Eigenschaften (wie z. B. Ausführungsgeschwindigkeit, Speicherverbrauch oder Linter-Styleguides) ebenfalls abdecken zu können, verknüpfen wir die funktionale Lösung mit weiteren Bedingungen ($C$ für Constraints):

$$\mathcal{S}_{\text{summ}} \cap C = \{ S \in \Sigma^* \mid S: P \to Q \} \cap C$$

> Jedes Programm in unserer finalen Auswahl muss nun nicht mehr nur funktional korrekt sein, sondern zusätzlich das "Qualitäts-Sieb" $C$ passieren (Schnittmenge $\cap$). Erfüllt der Code den Styleguide oder das Zeitfenster nicht, fliegt er einfach raus.

---

---

> **Hinweise:** 
> * Dieses Projekt baut auf PyTest auf. Wir wollen das Rad nicht neu erfinden, sondern nur Templates, Automatisierungen und Test-Utilties entwickeln, damit diese dabei helfen einfacher Tests zu definieren, bewährte Muster ohne Aufwand umzusetzen und Best Practices mit Leichtigkeit in Code gießen zu können.
> * Die folgenden Skizzen sind ein erster Entwurf zur Realisierung der definierten Aussagen und könnten sich noch anpassen oder ausgetauscht werden.

---

### Test-Utilities: Form und Funktion

Um jede Art von Test schnell definieren zu können, empfiehlt es sich Utils zur Verfügung zu stellen, die einfach und zuverlässig wiederverwendbar sind.

* **Form:** Definiert die Regeln und Muster für die "Form" vom Code mit dem konkreten Syntax-Baum:  
  **→ Kontext** *(Decorators u.Ä.)*  
  **→ Input-Interface** *(Konstruktor)*  
  **→ Objekt-Körper** *("Funktions"-Body)*  
  **→ Output-Interface** *("Return"-Body)*

* **Func:** Definiert das Verhalten, die Funktionen und die Fähigkeiten der Code-Ausführung mit dem abstrakten Syntax-Baum:  
  **→ Objekt-Ausführung**  


### Test-Rollen: Golden und Synthetisch  

Die atomare Validierungs-Logik ist für "Golden Datasets" und "Synthetische Datasets" zwar gleich, weswegen es im "Kern" der QA keine spezielle Differenzierung benötigt, aber für die Orchestrierung und die Anbindung an externe Systeme und auch für die Weiterentwicklung komplexerer Algorithmen, kann man diese "Test-Rollen" einfach mittels Tags im Test markieren.

* **Golden-Datasets:** Ground Zero der definierten Regeln.
* **Synthetische-Datasets:** Die Golden-Datasets können höhergradigere Test-Regeln induzieren, aus denen sich wiederum weitere Tests deduzieren lassen. Das sind synthetische Tests.   
  (**→ validierte Derivate:** Synthetische Derivate, welche zu einem bestimmten Maß validiert wurden.)

Ob hierbei "golden"/"synthetic" oder ein f"auth-lvl_{x}" für die tags verwendet wird, steht noch nicht fest und wird später auf dem Kern aufbauend dazu entwickelt. 


### Test-Typen: Beispiele, Regeln und abstrakte Formeln
* **RBT:** Review-Based-Testing
* **EBT:** Example-Based-Testing
* **PBT:** Property-Based-Testing
* **FVT:** Formal-Verification-Testing

---

---

### Review-Based-Testing (RBT)

Die simpelste und gleichzeitig komplexeste Art des Testens! Das RBT ist perfekt für Bootstrapping und Experimente und ist so mächtig, dass die menschliche Gesellschaft auf diese Weise alle Wissenschaften und Berufe bootstrappen konnte! 

* Dokumentiere einfach die Regeln, welche geprüft werden sollen und lasse dich anpingen, wenn es Zeit für eine Review wird! 
* *(Alternativ lässt sich auch ein LLM exakt darauf einspielen.)*


***... Done!***

---

### Example-Based-Testing (EBT)

Betrachte deine Test-Datensätze als eine Sammlung von Eingaben und Ausgaben, als die Zustände der Szenarien und Resultate, als die Umgebung welche die jeweilige Funktion erhält und die Umgebung, welche die jeweilige Funktion hinterlassen soll - Betrachte deine Test-Datensätze als eine Sammlung von Input- und Output-Paaren!: 

- Definiere die Pre-Conditions / die Inputs. 
- Definiere die Post-Conditions / die Outputs.

#### Beispiel: Nehme ein Dokument deiner Wahl und ... 
 - ... Dupliziere dein Dokument in den Input-Ordner der Funktion
 - ... Dupliziere dein Dokument in den Output-Ordner der Funktion
 - ... Bearbeite das Dokument im Output-Ordner nach deinen Wünschen

***... Done!*** (Erstelle so viele weitere Beispiele, wie du für sinnvoll erachtest.)

---

### Property-Based-Testing (PBT)

Genug von der Erstellung einzelner Beispiele? Dann definiere die Bereiche und stecke die Landschaften ab! Während ein empirisches Beispiel nur einen einzigen Pfad validiert, flutet die Stochastik das System mit tausenden automatisierten, adversariellen Variationen, um die unsichtbaren Sollbruchstellen (Thresholds) deines Codes aufzuspüren!:

- Definiere den Suchraum (Domain).
- Lass die Maschine die Grenzen kollabieren.

#### Beispiel: Nehme deine Dokumenten-Funktion und...
 - ... Sage QA-Bench, dass der Input *prinzipiell* jede beliebige PDF-Datei sein darf.
 - ... QA-Bench generiert autonom tausende Dokumente: extrem riesige, leere, strukturell beschädigte oder negativ formatierte Files.
 - ... Sobald der Code bricht, schrumpft (shrinckt) QA-Bench das gigantische Fehler-Dokument vollautomatisch auf das exakte, minimale Byte zurück, das den Absturz verursacht hat.

***... Done!*** (Du erhältst den rauschfreien, mathematisch präzisen Edge Case.)

---

### Formal-Verification-Testing (FVT)

Mit der Empirie und der Stochastik hast du die Werkzeuge um alles zu validieren, aber mit der formalen Validierung kannst du deine Tests zu einer ultimativen Modellierung digitieren, welche den Spieß umdreht und dir das Repertoir mathematische Verfahren und Algorithmen eröffnet! Betrachte deine Test-Datensätze als Gleichungen und mathematische Sätze, welche die Landschaften modellieren!:

- Definiere die Gesetze deines Codes.
- Lass die Mathematik nach einem Widerspruch suchen.

#### Beispiel: Nehme deine Dokumenten-Funktion und...
 - ... Definiere das unumstößliche Gesetz: *"Die Ausgabedatei darf strukturell niemals weniger Tabellenspalten enthalten als die Eingabedatei."*
 - ... QA-Bench übersetzt den Kontrollfluss deines Parsers in logische Formeln und übergibt sie dem SMT-Solver.
 - ... Der Solver sucht nicht blind, sondern berechnet mathematisch, ob ein theoretischer Input *existieren kann*, der dieses Gesetz verletzt.
 - ... Findet er einen (**SAT**), liefert er dir das exakte, mathematische Gegenbeispiel (Counterexample). Findet er keinen (**UNSAT**), ist dein Code für alle Ewigkeit mathematisch bewiesen.

***... Done!*** (Sicherheit auf Krypto-Niveau, ganz ohne Code-Ausführung.)

---

