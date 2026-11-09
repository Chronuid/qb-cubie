# 📖 CUBIE-GUIDE: Example-Based-Testing (EBT)

Willkommen in der greifbarsten und gleichzeitig kompromisslosesten Disziplin der Qualitätssicherung.  
Wir definieren klare Realitäten und machen sie zu unserem "Golden Master" → dem unbestechlichen Standard, an dem sich jeder Code messen lassen kann.


---

### 1. Die Philosophie: Zustände definieren

Die Kernidee von EBT basiert auf dem klassischen Hoare-Tripel, das wir für unsere Zwecke aus der akademischen Welt direkt in die Praxis übersetzen. Anstatt mit Variablen zu jonglieren, definieren wir Welten:

* **P (Pre-Condition / Input):** Wie sieht die Welt *vor* der Ausführung aus?
* **Q (Post-Condition / Output):** Wie muss die exakte Welt *nach* der Ausführung aussehen?
* **S (Das Programmsegment):** Der Code, der den Weg von *P* nach *Q* bauen muss.

**Das Lichtschalter-Beispiel:**
Machen wir es greifbar. Stell dir vor, du betrittst ein Zimmer.
Wenn der Raum dunkel ist (**P**), und ich den Lichtschalter betätige (**S**), dann ist der Raum danach hell (**Q**).
Beim EBT testen wir nicht, *wie* der Strom durch die Kabel fließt (die abstrakte Logik). Wir prüfen lediglich: War es vorher dunkel? Ja. Wurde der Schalter gedrückt? Ja. Ist es jetzt hell? Ja. Test bestanden.

---

### 2. Die Dynamiken: Skalierbarkeit von der Funktion zum Repo

Das Schöne am EBT ist, dass es nicht auf primitive Datentypen beschränkt bleibt. Das Prinzip der eingefrorenen Vor- und Nachbedingungen skaliert fraktal durch alle Architekturebenen deines Projekts:

* **Die Funktions-Ebene:** Ein simples I/O-Paar. Ein Input ($P$) geht in die Funktion ($S$) hinein, ein Output ($Q$) kommt heraus.
* **Die Service-Ebene:** Hier agiert unser Vorzeige-Beispiel, der *MD-Cleaner*. Wir testen isolierte Dateitransformationen in eine Arena (dem Pytest-Gym). Ein rohes Wikipedia-Markdown-Dokument wird in den Workspace geladen ($P$); das Skript bereinigt es; die Validierung prüft am Ende gegen dein handverlesenes Ziel-Dokument ($Q$).
* **Die Repo-Ebene:** Hier vergleichen wir ganze Projektbäume. $P$ ist der unaufgeräumte Legacy-Ordner, $Q$ ist die perfekt strukturierte Refactoring-Vision. Der Test vergleicht nicht nur Codezeilen, sondern Ordnerstrukturen, Abhängigkeiten und die Existenz ganzer Module.


#### **Die goldene Regel der Kohärenz:**

Gerade, wenn wir uns in Richtung Service- und Repo-Dynamik bewegen, müssen wir das Systemverhalten genau verstehen. EBT gleicht *lediglich* statisch $P$ und $Q$ ab. Das bedeutet:  
**Die Qualität deiner Funktion ($S$) ist nur exakt so gut wie die Kohärenz deiner Testdaten.**

Es ist elementar, dass die Menge deiner Beispiele denselben, widerspruchsfreien Regeln folgt. Wenn sich in einem großen Datensatz auch nur wenige Beispiele gegenseitig widersprechen oder fehlerhafte Zielzustände fordern, passiert etwas Fatales: Die Komplexität des generierten Codes explodiert. Die Maschine versucht verzweifelt, eine Funktion zu schreiben, die allen (auch den falschen) Regeln gerecht wird. Der Code wird unleserlich, unzuverlässig oder lässt sich schlichtweg gar nicht erst finden.

Ein sauberes, kohärentes "Golden Dataset" bewirkt exakt das Gegenteil: Es schnürt das Korsett der Anforderungen so präzise, dass die Entwicklung der Funktionalität ($S$) wesentlich schlanker, schneller und zuverlässiger stattfinden kann.


---

### 3. Das Vorzeige-Beispiel: Der MD-Cleaner im RL-Gym

Um die Meso-Dynamik (Service-Ebene) in der Praxis zu verstehen, betrachten wir ein reales Transformations-Szenario: Die Bereinigung von Wikipedia-Artikeln.

Unser Ziel ist ein Skript ($S$), das rohes, von Web-Clippern generiertes HTML-Markdown in perfektes, lesbares LaTeX-Markdown überführt.


#### **Das Setup (Die Goldenen Datensätze):**

Wir verzichten auf abstrakte Beschreibungen und definieren stattdessen harte Fakten in unserem Dateisystem:

* **Der Input ($P$):** Eine Datei `kalkuel_raw.md` (voll mit störenden HTML-Tags und fehlerhaften Bild-Links).
* **Der Output ($Q$):** Eine Datei `kalkuel_normalized.md` (von uns handverlesen und perfekt formatiert).

Dieses Setup zwingt den Code, exakt die Transformation durchzuführen, die wir als Architekten vorgegeben haben – ohne dass wir ihr erklären müssen, *wie* sie das tun soll.

---


### 4. Die Gefahr der Unterspezifikation

EBT ist kompromisslos, hat aber eine gewaltige konzeptionelle Schwäche: **Die Maschine durchsucht den gesamten Lösungsraum, den wir mit unseren Definitionen abgesteckt haben - und je nachdem wie wir unsere Code-Generierung betreiben, erhalten wir dabei zunächst ausschließlich eine Lösung, welche mit dem geringsten Widerstand gefunden wurde.**

Wir definierten dabei den Lösungsraum für die eigentlich gewünschte Lösung, aber erhalten damit eine ganze Menge an Lösungen. Das Netz, welches durch eine geringe Menge an Datenpunkten gesponnen wird, liefert nahezu unzählig viele Lösungsmuster, welche die Anforderungen mathematisch erfüllen und potentiell unserer intentierten Funktion entsprechen könnten.


#### **Die Illusion der Abdeckung:**

Nehmen wir ein simples Beispiel: Wir definieren als Input ($P$) die Zahl `2` und als Output ($Q$) die Zahl `4`.
Unser Ziel ist es eigentlich, dass wir Funktionen finden, die den Input verdoppelt (`x * 2`). Die Maschine könnte aber genauso gut einfach `return 4` oder `return x + 2` schreiben. Beide Wege bestehen den Test mit Bravour.

Das ist das Problem der **Unterspezifikation**. Ein Golden Dataset beweist *nicht*, dass der Code universell korrekt unserer Intention entspricht. Es beweist lediglich, dass der Code *für dieses spezifische Beispiel* nicht falsch ist. Es können extrem komplexe, völlig fehlerhafte Programme entstehen, die den Lösungsraum schlichtweg überanpassen (Overfitting), um die Tests zu bestehen.

---

### 5. Die Lösungs-Matrix: Orthogonalität

Ein einzelnes I/O-Paar reicht niemals aus. Ein gutes Golden Dataset muss die Koordinaten der Domäne präzise abstecken. Ein gutes Golden Dataset muss die Koordinaten der Domäne abstecken. Um das Problem der intentierten Verdopplungsfunktion von eben zu lösen, fügen ein zweites Beispiel hinzu: Input `3`, Output `6`. Plötzlich schlägt der trickreiche `return 4`-Code fehl. Die Maschine wird gezwungen, die zugrundeliegende Struktur (`x * 2`) zu abstrahieren.

Um eine EBT-Suite zu bauen, die Code in die Enge treibt, müssen wir die Natur der Mehrdeutigkeit verstehen und dem System durch strategische Datenpunkte den Ausweg abschneiden.

#### 5.1. Das Problem der Mehrdeutigkeit

Im Kern ist EBT reine Mustererkennung. Je mehr Datenpunkte aus einer Folge die Maschine sieht, desto besser kann sie die dahinterliegende Funktion ableiten, welche künftige (noch maskierte) Datenpunkte korrekt vorhersagt. Wenn wir ihr jedoch nur sehr wenige Datenpunkte vorgeben, lassen sich unzählige verschiedene mentale Modelle und Funktionen konstruieren, die diese wenigen Kriterien problemlos erfüllen. Um eine hohe Gewissheit darüber zu erlangen, ob wirklich die exakt richtige Funktion ersonnen wurde, benötigen wir schlichtweg eine ausreichende Menge an Datenpunkten.

Anstatt also davon auszugehen, dass die Maschine uns absichtlich "austricksen" will, sollten wir das Phänomen als logischen Ausschluss-Prozess betrachten: Falsche Annahmen kollabieren automatisch, sobald der Lösungsraum durch neue Datenpunkte weit genug aufgespannt wird.

#### 5.2. Der Kollaps falscher Funktionen (Beispiele)

**Beispiel 1: Die geometrische Täuschung (Das Moser-Kreis-Problem)**
Stell dir vor, wir setzen Punkte auf den Rand eines Kreises, verbinden alle Punkte vollständig miteinander und zählen die entstehenden Flächen.

* 1 Punkt = 1 Fläche
* 2 Punkte = 2 Flächen
* 3 Punkte = 4 Flächen
* 4 Punkte = 8 Flächen
* 5 Punkte = 16 Flächen

Wenn die Maschine nur diese ersten fünf Beispiele sieht, greift sie zum unweigerlich einfachsten mentalen Modell: *"Verdopple einfach den vorherigen Wert!"* ($2^{n-1}$). Wenn unser Lösungsraum hier endet, ist diese Verdoppelungsfunktion vorerst absolut legitim.
Doch dann bringen wir den entscheidenden, sechsten Datenpunkt ins Spiel:

* 6 Punkte = **31** Flächen (nicht 32!)

In diesem exakten Moment kollabiert die simple Verdoppelungsfunktion. Der neue Datenpunkt zwingt das System dazu, das naive Muster zu verwerfen und die weitaus komplexere geometrische Realität der Kreise in seine Funktion aufzuschlüsseln, um auch die 31 korrekt vorhersagen zu können.

**Beispiel 2: Die Text-Formatierungs-Falle**
Ein typischer, greifbarerer Fall aus der direkten Code-Generierung: Wir fordern eine Funktion, die jeden Anfangsbuchstaben eines Strings großschreibt.

* Input: `"hello world"` → Output: `"Hello World"`
* Input: `"guten morgen"` → Output: `"Guten Morgen"`

Die Maschine nimmt den Weg des geringsten Widerstands und implementiert ein schlichtes `return text.title()`. Die Tests leuchten grün.
Nun weiten wir den Raum durch ein orthogonales Beispiel (einen Randfall) aus:

* Input: `"it's a trap"` → Output: `"It's A Trap"`

Der EBT-Test schlägt plötzlich fehl. Die simple `.title()`-Methode behandelt den Apostroph als Trennzeichen und generiert fälschlicherweise `"It'S A Trap"` mit einem großen `"S"`. Das initiale Modell bricht in sich zusammen. Um nun alle drei Tests gleichzeitig bestehen zu können, wird die Maschine gezwungen, Wortgrenzen syntaktisch korrekt zu behandeln (beispielsweise durch den Einsatz von regulären Ausdrücken).

#### 5.3. Den Raum aufspannen (Orthogonale Beispiele)

Je orthogonaler – also inhaltlich vielfältiger und unabhängiger – die Datensätze sind, desto schmaler wird der Korridor für fehlerhaften Code. Indem wir neben dem "Happy Path" gezielt Randfälle, Ausreißer oder Null-Werte einstreuen, verwehren wir der Maschine die Möglichkeit zum Overfitting. Wir füttern das System so lange mit strukturbrechenden Datenpunkten, bis alle bequemen, falschen Interpretationen kollabieren und nur noch die exakt von uns intendierte Funktion als einzige logische Wahrheit übrig bleibt.

---

### 6. Nutzungs-Muster und -Beispiele

#### 6.1. In-Memory ohne Ballast

Für reine Funktionen brauchen wir überhaupt kein `State`-Objekt. Wenn `pre` ein `tuple` oder `dict` ist, interpretiert Cubie das automatisch als `args` bzw. `kwargs`.

```python
# Shorthand für reine Funktionsaufrufe
EBT(target=my_func, pre=(1, 2), post=3)
EBT(target=my_func, pre={"x": 1, "y": 2}, post=3)
```

Weitere Beispiele verschoben nach: "GUIDE_Example-Based-Testing_usage-pattern.md"

---


### 7. Grenzbereiche des EBT

Was, wenn wir zusätzlich ganze Mengen deterministisch über Pytest-Parametrisierung in die EBT-Definitionen eines Test-Cases jagen?
Es besteht rein konzeptuell kein Unterschied zwischen parametrisierten EBT-Tests und boilerplate-formulierten EBT-Tests. Das eine wäre lediglich die Kurzschreibweise des Anderen, solange die Parametrisierung sich eindeutig zuordnungsbarer Entitäten bedient.

Aber was, wenn man ein P-Element zu einer ganzen Q-Menge verweist und den Test grün leuchten soll, solange das Ergebnis von P einem Element aus der definierten Q-Menge entspräche? 


### 7.1. Deterministische Mengen als Input

* **Formallogisch:** Streng akademisch gesehen bleibt es dennoch auf der Ebene der Aussagenlogik (Ground Terms). Ein echter Allquantor ($\forall$) in der FOL iteriert über eine *unbegrenzte* oder abstrakt generalisierte Domäne. Eine Pytest-Parametrisierung ist jedoch endlich. Der Test-Runner übersetzt deine Liste faktisch nur in eine massive Kette von logischen UND-Verknüpfungen: `(p1 → q1) AND (p2 → q2) AND (p3 → q3)`.
* **Architektonisch:** In der Praxis simulieren wir hier aber einen **beschränkten Allquantor** ($\forall x \in M$). Wir definieren eine endliche Menge und iterieren darüber. Das ist genau der induktive Grenzübergang: Wir bauen das Fundament für eine abstrakte Regel, bleiben aber noch in der kompromisslosen, deterministischen Blase des EBT.


### 7.2. Eine $P$-Eingabe gegen eine $Q$-Menge (Zustandsräume)

Wenn der Test grün leuchtet, sobald das Ergebnis von $S(P)$ *irgendeinem* Element der definierten Menge $Q$ entspricht, verändern wir die mathematische Natur der Nachbedingung fundamental.

* **Formallogisch:** Wir verlassen die einfache Gleichung $S(P) = Q$ und führen eine logische Disjunktion (ODER) ein: $S(P) = q_1 \lor S(P) = q_2 \dots$.  
In der Sprache der First-Order Logic greifen wir hier zu einem **beschränkten Existenzquantor** ($\exists$): *"Es existiert mindestens ein Element in der erlaubten Ziel-Menge $Q$, das mit dem Output identisch ist."*
* **Architektonisch:** Oft gibt es nicht *den einen* perfekten String oder Zustand als Lösung, sondern einen validen Lösungsraum. Das EBT validiert hier nicht mehr gegen einen starren Punkt, sondern prüft die Mitgliedschaft in einer korrekten Menge.


#### Zusammenfassend: 
Sobald wir im EBT anfangen, Eingaben über Listen zu iterieren oder Ausgaben gegen Zustandsräume zu validieren, reizen wir das Paradigma bis an die absolute Grenze der First-Order Logic aus. Du spannst den Raum der Orthogonalität auf.