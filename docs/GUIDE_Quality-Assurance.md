# 📖 CUBIE-GUIDE: Quality Assurance


**CUBIE ist nicht einfach nur deine "Quailtäts-Benchmark".**  → *Unter der Haube ist es dein **CUBE of QUANTS**.*

* **QUANTS (Die Quantoren):** Die wahre Macht liegt nicht im isolierten Testfall, sondern in der iterativen Orchestrierung von Mengen-Mappings über formallogische Quantoren ( $\forall$ und $\exists$ ).


* **CUBE (Der orthogonale Raum):** Ein einzelner Datenpunkt ist flach. Erst wenn du das System zwingst, Randfälle und strukturbrechende Beispiele zu verarbeiten, spannst du den Lösungsraum *orthogonal* in die Breite und Tiefe auf. Du baust buchstäblich einen mehrdimensionalen "Würfel" aus harten, deterministischen Fakten, aus dem fehlerhafter Code nicht mehr entkommen kann. Die gesamte Testsuite wird zum übergeordneten Allquantor.

---

---

Die Kern-Ideen basieren auf einigen Prinzipien der mathematischen Programmverifikation. Um den Kern zu verstehen, sagen wir vereinfacht, dass wir logische Bedingungen wie Datentypen behandeln können:
* **P** = Vorbedingung (z. B. "Eingabe ist eine Zahl")  
* **S** = Programmsegment (die auszuführende Funktion)  
* **Q** = Nachbedingung (z. B. "Ausgabe ist das Quadrat der Zahl")

Das klassische **Hoare-Tripel** beschreibt, wie ein Programm den Zustand einer Berechnung verändert:
$$\text{Hoare-Tripel} = \{P\}\; S\; \{Q\}$$

> **Sprich:** Wenn die Vorbedingung $P$ vor der Ausführung von $S$ zutrifft, dann gilt nach der Ausführung von $S$ die Nachbedingung $Q$.

Da wir in modernen Sprachen direkt mit Funktionen arbeiten, stellen wir dieses Tripel einfach auf das Verhalten von $S$ um:
$$\{P\}\; S\; \{Q\} \quad \equiv \quad S: P \to Q$$

> **Sprich:** Das Programmsegment $S$ ist eine Abbildung (Funktion), die Daten des Typs $P$ (Eingabe) entgegennimmt und Daten des Typs $Q$ (Ausgabe) liefert.

---
Das Projekt ist darauf ausgelegt die Prinzipien der Programmverifikation einfach und zugänglich umsetzen und automatisieren zu können. Hierfür lässt sich die eben definierte Umstellung um den Suchraum des Code-Generators ($S \in \Sigma^*$) erweitern: 

 $$\mathcal{S}_{\text{summ}} = \{ S \in \Sigma^* \mid S: P \to Q \}$$

> **Für Einsteiger übersetzt:**  
> * $\Sigma^*$ (Sigma-Star) ist das unendliche Chaos – die Menge aller denkbaren Zeichenketten und Code-Zeilen, die man tippen könnte.
> * $\mathcal{S}_{\text{summ}}$ ist am Ende die saubere "Kiste", in die wir alle funktionierenden Programme $S$ hineinsortieren.


> **Sprich:** "Die Lösungsmenge $\mathcal{S}_{\text{summ}}$ besteht aus allen Quellcodes $S$ aus dem unendlichen Chaos $\Sigma^*$,  
> für die gilt: Das Programm $S$ überführt die Eingabe $P$ korrekt in die Ausgabe $Q$."

--- 

Um die Nicht-Funktionalen Eigenschaften (wie z. B. Ausführungsgeschwindigkeit, Speicherverbrauch oder Linter-Styleguides) oder auch abstrakte, semantisch definierte Intentionen und Regeln abzudecken, verknüpfen wir die funktionale Lösung mit weiteren Bedingungen ($C$ für Constraints).
$$\mathcal{S}_{\text{summ}} \cap C = \{ S \in \Sigma^* \mid S: P \to Q \} \cap C$$

> **Für Einsteiger übersetzt:**  
> 
> Jedes Programm in unserer Auswahl muss nun nicht mehr nur funktional korrekt sein, sondern zusätzlich das "Qualitäts-Sieb" $C$ passieren.  
> In der reinen Logik betrachten wir $C$ als die Menge aller denkbaren Programme, die unsere speziellen Anforderungen erfüllen.  
>
> **Bilden wir die Schnittmenge ($\cap$), bedeutet das in der Praxis ganz simpel:**  
> * Erfüllt ein Code ($S$) deinen Styleguide, das Zeitfenster oder die semantischen RBT-Vorgaben ($C$) nicht, dann ist er einfach raus.  
> Alles, was die Prüfungen nicht besteht, ist kein Teil der verifizierten Schnittmenge ($\cap$).  
> * Erfüllt ein Code ($S$) deine Prüfungen ($C$), dann ist er einfach drinnen.  
> Alles, was die Prüfungen besteht, ist ein Teil der verifizierten Schnittmenge ($\cap$).   

> **Sprich:**  
> "Die finale Menge der verifizierter Lösungen besteht aus exakt jenen Programmen des unendlichen Suchraums $\Sigma^*$,  
> die sowohl funktional korrekt die Eingaben $P$ in die jeweils dazugehörigen Ausgaben $Q$ überführen,  
> als auch den Rastern und Prüfungen aller definierten Qualitäten und Bedingungen $C$ entsprechen."
---

---

> **Hinweise:** 
> * Dieses Projekt baut auf PyTest auf. Wir wollen das Rad nicht neu erfinden, sondern nur Templates, Automatisierungen und Test-Utilties entwickeln, damit diese dabei helfen einfacher Tests zu definieren, bewährte Muster ohne Aufwand umzusetzen und Best Practices mit Leichtigkeit in Code gießen zu können.
> * Die folgenden Skizzen sind ein erster Entwurf zur Realisierung der definierten Aussagen und könnten sich noch anpassen oder ausgetauscht werden.

---

### Test-Rollen: Golden und Synthetisch  

Die atomare Validierungs-Logik ist für "Golden Datasets" und "Synthetische Datasets" zwar gleich, weswegen es im "Kern" der QA keine spezielle Differenzierung benötigt, aber für die Orchestrierung und die Anbindung an externe Systeme und auch für die Weiterentwicklung komplexerer Algorithmen, kann man diese "Test-Rollen" einfach mittels Tags im Test markieren.

* **Golden-Datasets:** Ground Zero der definierten Regeln.
* **Synthetische-Datasets:** Die Golden-Datasets können höhergradigere Test-Regeln induzieren, aus denen sich wiederum weitere Tests deduzieren lassen. Das sind synthetische Tests.   
  (**→ validierte Derivate:** Synthetische Derivate, welche zu einem bestimmten Maß validiert wurden.)

Ob hierbei "golden"/"synthetic" oder ein f"auth-lvl_{x}" für die tags verwendet wird, steht noch nicht fest und wird später auf dem Kern aufbauend dazu entwickelt. 


---

---

### Prädikatenlogik
In der Logik und Informatik sind die Prädikatenlogik erster Stufe (FOL) und die Logik höherer Stufe (HOL) formale Sprachen, die zur Formulierung mathematischer Aussagen und zur Verifizierung von Beweisen dienen. Der wesentliche Unterschied liegt in der Ausdrucksstärke: Während sich Quantoren in der FOL nur auf einzelne Objekte beziehen, erlaubt die HOL auch die Quantifizierung über Prädikate und Funktionen. 

<details> 

#### Prädikatenlogik erster Stufe (FOL)
  * **Geltungsbereich:** Variablen beziehen sich nur auf einzelne Objekte (z. B. „alle Menschen“, „eine bestimmte Zahl“). 
  * **Möglichkeiten:** Man kann $(\forall x (P(x) \implies Q(x)))$ formulieren, jedoch nicht über die Eigenschaft P selbst quantifizieren. 
  * **Vorteile:** Sie ist semantisch vollständig (jede logisch wahre Aussage ist beweisbar) und lässt sich hervorragend automatisieren, weshalb sie den Standard für die meisten automatisierten Theorembeweiser darstellt. 

#### Logik höherer Stufe (HOL) 
* **Geltungsbereich:** Variablen können sich auf Relationen, Funktionen und Mengen von Objekten beziehen. 
* **Möglichkeiten:** Man kann über Prädikate quantifizieren (z. B. „für alle Eigenschaften P gilt: Wenn P für 0 zutrifft...“). 
* **Vorteile:** Sie bietet eine weitaus größere Ausdrucksstärke. Komplexe mathematische Theorien (wie etwa die der reellen Zahlen oder die Mengenlehre) lassen sich direkt formulieren, ohne dass komplizierte Metasprachen erforderlich sind. Allerdings geht bei Verwendung der Standardsemantik die Vollständigkeit verloren, und die Automatisierung gestaltet sich schwieriger.


---

</details>

---

### Review-Based-Testing (RBT)

Die simpelste und gleichzeitig komplexeste Art des Testens! Das RBT ist perfekt für Bootstrapping und Experimente und ist so mächtig, dass die menschliche Gesellschaft auf diese Weise alle Wissenschaften und Berufe bootstrappen konnte! 

* Dokumentiere einfach die Regeln, welche geprüft werden sollen und lasse dich anpingen, wenn es Zeit für eine Review wird!


***... Done!***

<details> 

#### RBT: Any $\cap$ Prüfverfahren

* **Einordnung:** RBT ist die Schnittmenge aus *allen Testarten* (Any) und den Fähigkeiten des jeweiligen Reviewers.
* **Interpretation & Schärfung:** RBT ist das einzige Testverfahren, das sich nicht in eine formale Schachtel pressen lässt, weil es als Brücke zwischen der Unendlichkeit des Sigma-Sterns und dem formalen System fungiert.
  * Das **Prüfungsverfahren** (ob Mensch oder LLM oder ein anderweitiges Verfahren) agiert hier als semantischer Compiler.

---

</details>

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

<details> 

#### EBT:

* **Interpretation & Schärfung:** EBT nutzt Quantoren (wie den Allquantor $\forall$ oder Existenzquantor $\exists$). Einzelne EBT-Tests basieren zwar komplett quantorenfrei auf der reinen Aussagenlogik (sogenannten "Ground Terms"), werden aber durch die Test-Strukturen und die iterierte Menge der Test-Datensätze in ihrer Mächtigkeit und Handhabung mit FOL-Definitionen gleichgesetzt. Ein isolierter Test sagt nicht "Für alle $x$...", sondern prüft lediglich absolute Fakten: "Für exakt diese isolierten Objekte $P$ gilt die Transformation nach $Q$".  
**Dennoch:** Da der Scope von EBT auf festen, individuellen Datenpunkten (Objekten) liegt und durch diese Mengen ein ganzer Raum orthogonal aufgespannt werden kann, fügt sich EBT als das unbestechliche Fundament perfekt in diese Skala ein.

---

</details>

---