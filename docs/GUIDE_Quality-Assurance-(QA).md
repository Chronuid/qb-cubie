# QA-Bench
> *The **Quality Assurance** Builder*

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

> **Sprich:** Wenn die Vorbedingung $P$ vor der Ausführung von $S$ zutrifft, dann gilt nach der Ausführung von $S$ die Nachbedingung $Q$.

Da wir in modernen Sprachen direkt mit Funktionen arbeiten, stellen wir dieses Tripel einfach auf das Verhalten von $S$ um:
$$\{P\}\; S\; \{Q\} \quad \equiv \quad S: P \to Q$$

> **Sprich:** Das Programmsegment $S$ ist eine Abbildung (Funktion), die Daten des Typs $P$ (Eingabe) entgegennimmt und Daten des Typs $Q$ (Ausgabe) liefert.

---
Das Projekt ist darauf ausgelegt die Prinzipien der Programmverifikation einfach und zugänglich umsetzen und automatisieren zu können, um für die synthetische Software-Generierung und Code-ML-Projekte verwendet werden zu können. Hierfür lässt sich die eben definierte Umstellung um den Suchraum des Code-Generators ($S \in \Sigma^*$) erweitern: 

 $$\mathcal{S}_{\text{summ}} = \{ S \in \Sigma^* \mid S: P \to Q \}$$

> **Für Einsteiger übersetzt:**  
> * $\Sigma^*$ (Sigma-Star) ist das unendliche Chaos – die Menge aller denkbaren Zeichenketten und Code-Zeilen, die man tippen könnte.
> * $\mathcal{S}_{\text{summ}}$ ist am Ende die saubere "Kiste", in die wir alle funktionierenden Programme $S$ hineinsortieren.


> **Sprich:** "Die Lösungsmenge $\mathcal{S}_{\text{summ}}$ besteht aus allen Quellcodes $S$ aus dem unendlichen Chaos $\Sigma^*$,  
> für die gilt: Das Programm $S$ überführt die Eingabe $P$ korrekt in die Ausgabe $Q$."

--- 

Um die Nicht-Funktionalen Eigenschaften (wie z. B. Ausführungsgeschwindigkeit, Speicherverbrauch oder Linter-Styleguides) oder auch abstrakte, semantisch definierte Intentionen abzudecken, verknüpfen wir die funktionale Lösung mit weiteren Bedingungen ($C$ für Constraints).
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

* EBT: FOL
* PBT: (HOL → EBT)
* FVT: (FOL & HOL) #z.B mit Isabelle
* RBT: Any$\cap$Prüfverfahren #bzw. Reviewer

---

</details>

---

### Review-Based-Testing (RBT)

Die simpelste und gleichzeitig komplexeste Art des Testens! Das RBT ist perfekt für Bootstrapping und Experimente und ist so mächtig, dass die menschliche Gesellschaft auf diese Weise alle Wissenschaften und Berufe bootstrappen konnte! 

* Dokumentiere einfach die Regeln, welche geprüft werden sollen und lasse dich anpingen, wenn es Zeit für eine Review wird! 
* *(Alternativ lässt sich auch ein LLM exakt darauf einspielen.)*


***... Done!***

<details> 

#### RBT: Any $\cap$ Prüfverfahren

* **Einordnung:** RBT ist die Schnittmenge aus *allem* (Any) und dem jeweiligen Reviewer, was später Vertrauens-Scores für die maschinelle Verarbeitung benötigt.
* **Interpretation & Schärfung:** RBT ist das einzige Testverfahren, das sich nicht in eine formale Schachtel pressen lässt, weil es als Brücke zwischen der "weichen" Realität (natürliche Sprache, Intentionen, Ästhetik) und dem formalen System fungiert.
  * Das **Prüfungsverfahren** (ob Mensch oder LLM oder ein anderweitiges Verfahren) agiert hier als semantischer Compiler.
  * **Confidence-Metriken** sind für die spätere Automatisierung relevant: Wenn ein KI-Agent die RBT-Rolle übernimmt, ist das Ergebnis nicht mehr binär (`True`/`False`), sondern probabilistisch. Damit das deterministische EBT aus diesen RBT-Reviews klare $P$ und $Q$ ableiten kann, brauchen wir Metriken (wie *Logprobs*, *Temperature-Evaluations* oder *Self-Consistency-Scores*).

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

#### EBT: FOL (bzw. Propositional / Ground Terms)

* **Einordnung:** EBT entspricht First-Order Logic (FOL), da Variablen hier konkrete, individuelle Objekte sind.
* **Interpretation & Schärfung:** Das ist konzeptionell eine hervorragende Brücke, auch wenn EBT streng formallogisch sogar noch eine Ebene *unter* der vollen FOL angesiedelt ist. FOL nutzt Quantoren (wie den Allquantor $\forall$ oder Existenzquantor $\exists$). EBT hingegen arbeitet komplett quantorenfrei mit sogenannten "Ground Terms" oder Aussagenlogik. Es sagt nicht "Für alle $x$...", sondern prüft lediglich absolute Fakten: "Für exakt diese isolierten Objekte $P$ gilt die Transformation nach $Q$". Dennoch: Da der *Scope* von EBT auf festen, individuellen Datenpunkten (Objekten) liegt, fügt sich EBT als das fundamentale Fundament der FOL perfekt in diese Skala ein.

---

</details>

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

<details> 

#### PBT: (HOL → EBT) bzw. ($\forall$ → EBT)

* **Einordnung:** PBT als Pfeil, der aus einer höheren Logik konkrete EBTs generiert.
* **Interpretation & Schärfung:** Die Notation `(HOL → EBT)` trifft die *Mechanik* des Property-Based-Testing meisterhaft. Wenn du eine Eigenschaft (Property) definierst (z. B. "Für alle validen Markdown-Dateien gilt..."), bedienst du dich eines Allquantors ($\forall$) über eine gesamte Domäne. Du definierst das Gesetz auf einer Meta-Ebene (FOL/HOL), aber die Ausführung (der Pfeil $\to$) kompiliert dieses Gesetz gnadenlos in zehntausende, deterministische EBT-Paare hinunter, um das System empirisch zu fluten. Das ist reine, angewandte Falsifikation.

---

</details>

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

<details> 

#### FVT: (FOL & HOL)

* **Einordnung:** Formale Verifikation nutzt beide Welten, z. B. Isabelle.
* **Interpretation & Schärfung:** Die FVT teilt sich in der Praxis in zwei Lager:  
  * **FOL (SMT-Solver wie Z3):** Diese beweisen blitzschnell und hochgradig automatisiert Eigenschaften über individuelle Objekte und einfache Strukturen (z. B. "Die Länge der Output-Liste ist immer $\ge$ der Input-Liste").
  * **HOL (Theorem Provers wie Isabelle/HOL, Coq):** Diese erlauben es dir, über Funktionen, Prädikate und komplexe mathematische Strukturen zu quantifizieren. Hier tauscht du Automatisierbarkeit gegen absolute, unbegrenzte Ausdruckskraft.

---

</details>

---