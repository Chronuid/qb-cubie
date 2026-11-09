<center>

# FP-OOP-Isomorphismus

![Cubie](../.assets/cubie-logo-written.png)

Dieser Essay untersucht Beziehungen zwischen funktionaler und objektorientierter Programmierung.

---

</center>

Kurz gesagt: Ja, OOP lässt sich theoretisch nahtlos in FP übersetzen (und umgekehrt). Sie sind mathematisch gesehen isomorph zueinander.
Wenn man den Zustand (die Attribute) komplett aus der Funktion herauslöst, in eine reine Datenstruktur überführt und die Logik über reine Kompositionsfunktionen steuert, hat man OOP effektiv in FP überführt.
Hier ist die analytische Aufschlüsselung, warum deine Aussage stimmt, wo die theoretische Brücke liegt und wo in der Praxis die Nuancen liegen:

## Das mathematische Prinzip: Closures vs. Objekte
Es gibt ein berühmtes Zitat des Programmierers Anton van Straaten, das diesen Dualismus perfekt beschreibt:

„Ein Objekt ist eine Datensammlung mit angehängten Funktionen. Eine Closure (Funktion mit Kontext) ist eine Funktion mit angehängten Daten.“

Wenn du in FP eine Funktion schreibst, die eine andere Funktion zurückgibt, schließt diese innere Funktion ihren Zustand (Kontext) ein. Das verhält sich exakt wie ein Objekt in der OOP.
### Der „Cast“ (Die Übersetzung)
Schauen wir uns genau das Szenario an, das du beschrieben hast: Wir nehmen ein klassisches OOP-Objekt und „casten“ es in reines FP, indem wir Zustand und Verhalten strikt trennen.

| Konzept | OOP-Ansatz | FP-Ansatz (Dein „Cast“) |
|---|---|---|
| Zustand | Attribute im Objekt (self.x) | Reine, unveränderliche Datenstruktur (Immutable Dict / NamedTuple) |
| Verhalten | Methoden verändern self direkt | Reine Funktionen erhalten Zustand als Argument und geben neuen Zustand zurück |
| Kapselung | Das Objekt schützt seine Daten | Sichtbarkeit über Module; Zustand ist für Funktionen readonly |

### Konkretes Code-Beispiel des „Casts“ in Python:

Der OOP-Weg (Zustand und Methode gekoppelt):
```python
class Bankkonto:
    def __init__(self, saldo):
        self.saldo = saldo  # Zustand im Objekt
        
    def einzahlen(self, betrag):
        self.saldo += betrag  # Veränderung des Kontexts (Seiteneffekt!)
```

Der FP-Weg:
Hier ziehen wir sämtliche Attribute in eine reine Datenstruktur (das "Interface") und nutzen eine Kompositionsfunktion:
```python
from typing import NamedTuple
# 1. Das reine Daten-Interface (Kontext) ohne Logik
class KontoKontext(NamedTuple):
    saldo: float
# 2. Die reine Funktion (bezieht Kontext über das Interface)
einzahlen_fp = lambda kontext, betrag: KontoKontext(kontext.saldo + betrag)
# 3. Komposition (Zustandsveränderung durch Funktionskette)
start_kontext = KontoKontext(100.0)
neuer_kontext = einzahlen_fp(start_kontext, 50.0)  # Gibt neues Interface zurück

print(start_kontext.saldo)  # 100.0 (Unverändert)
print(neuer_kontext.saldo)  # 150.0 (Neuer Zustand)
```

In diesem FP-Beispiel fungiert das NamedTuple als dein Interface. Die Funktion einzahlen_fp verändert nichts, sondern nimmt den Kontext entgegen und gibt einen neuen, transformierten Kontext zurück.

## Warum sie in der Praxis dennoch nicht "identisch" sind: Die Achse der Erweiterbarkeit
Obwohl sie theoretisch ineinander überführbar sind, unterscheiden sie sich fundamental darin, in welche Richtung sich Code einfach erweitern lässt. Das wird in der Informatik als das Expression Problem bezeichnet:

* OOP macht es einfach, neue Datentypen (Klassen) hinzuzufügen. Wenn du eine neue Klasse erstellst, die ein Interface implementiert, musst du bestehenden Code nicht anfassen. Es ist aber schwer, neue Operationen (Methoden) für alle bestehenden Klassen hinzuzufügen.
* FP macht es einfach, neue Operationen (Funktionen) hinzuzufügen. Du schreibst einfach eine neue Funktion, die das bestehende Daten-Interface akzeptiert. Es ist aber schwer, neue Datentypen hinzuzufügen, da du dann oft alle bestehenden Funktionen (z.B. deren Pattern Matching oder Typ-Prüfungen) anpassen musst.

---

---

Auf mathematischer Ebene verhalten sich Objekte und Closures (FP) wie die zwei Seiten derselben Medaille. Dieser Dualismus wurde in den 1970er Jahren formalisiert (unter anderem durch [John C. Reynolds](https://www.google.com/search?q=john+c.+reynolds&kgmid=/m/07zp52)) und besagt: Es geht beim Casten in keine der beiden Richtungen Information verloren.
Die Transformationen sind mathematisch sauber (isomorph), was bedeutet, dass du verlustfrei vor- und zurückrechnen kannst.
Hier sind die exakten mathematisch-analytischen Regeln und Operationsketten für beide Richtungen.

---

## Der Cast von OOP zu FP (Defunktionalisierung)
In der theoretischen Informatik nennt man diesen Prozess Defunktionalisierung (oder Datenzentrierung). Das Ziel ist es, die in Objekten gekapselten Methoden und Zustände in reine Funktionen und Datenstrukturen zu zerlegen.

### Die Operations-Kette:

   1. Zustand extrahieren: Alle Instanzvariablen (Attribute) des Objekts werden aus der Klasse herausgelöst und in ein reines Produkt-Tupel (oder ein unteilbares Daten-Interface / Record) überführt.
   2. Methoden isolieren: Jede Methode wird zu einer globalen, reinen Funktion (Pure Function).
   3. Kontext injizieren: Das implizite self (oder this) der OOP-Methode wird explizit als erstes Argument in die neue FP-Funktion hineingereicht.
   4. Immutabilität erzwingen: Statt den Zustand des übergebenen Objekts in-place zu mutieren, gibt die Funktion ein neues Tupel mit den aktualisierten Werten zurück.

$$\text{OOP: } \text{Objekt}.\text{methode}(x) \implies \text{FP: } \text{funktion}(\text{Zustand}, x) \to \text{NeuerZustand}$$ 

---

## Der Cast von FP zu OOP (Refunktionalisierung / Closurization)
Dieser Weg nutzt das mathematische Konzept der Closure. Eine Closure ist eine Funktion, die ihre lexikalische Umgebung (den Scope, in dem sie definiert wurde) "mitgibt".

### Die Operations-Kette:

   1. Kontext einfangen: Variablen, die eine FP-Funktion aus ihrer Umgebung benötigt, werden als Zustand aufgefasst.
   2. Instanziierung via Konstruktor: Die übergeordnete FP-Funktion (Higher-Order Function), die den Scope erzeugt, wird zum Konstruktor der OOP-Klasse.
   3. Methodenbindung: Die zurückgegebene innere Funktion (Closure) entspricht einer Methode. Sie erhält exklusiven Zugriff auf den eingefangenen Kontext (self).
   4. Zustands-Kapselung: Der zuvor freie Datenkontext wird hinter der Schnittstelle der Methode verborgen.

$$\text{FP: } \text{hohereFunktion}(a)(b) \implies \text{OOP: } (\text{new Klasse}(a)).\text{methode}(b)$$ 

---

## Direktvergleich der Operationsketten
Die folgende Tabelle zeigt, wie die Elemente mathematisch eins zu eins ineinander übersetzt werden:

| Ausgangspunkt: OOP | Transformations-Regel | Zielpunkt: FP |
|---|---|---|
| Klasse / Konstruktor | $\to$ extrahiere Struktur / Typdefinition $\to$ | Daten-Interface (Record / Tuple) |
| Objekt-Instanz | $\to$ trenne Daten von Logik $\to$ | Wert / Zustand (State Value) |
| Objekt-Methode | $\to$ mache Kontext (self) zu explizitem Argument $\to$ | Reine Funktion (Pure Function) |
| Zustandsänderung | $\to$ ersetze Mutation durch Kopie $\to$ | Rückgabe eines neuen Zustands |

---

## Gehen Informationen verloren? (Der mathematische Beweis)
Es gehen keine Informationen verloren. Mathematisch spricht man von einem Isomorphismus zwischen zwei Algebren:

* Die OOP-Sichtweise ist Co-Algebren-basiert (sie ist beobachterzentriert: Was kann ich mit dem Objekt tun? Welche Methoden kann ich aufrufen?).
* Die FP-Sichtweise ist Algebren-basiert (sie ist konstruktorzentriert: Wie sind die Daten aufgebaut? Aus welchen Elementen setzen sie sich zusammen?).

Da beide Algebren dieselbe zugrundeliegende Berechenbarkeit (Lambda-Kalkül und Turing-Maschine) abbilden, lässt sich jede OOP-Struktur ohne Informationsverlust in eine FP-Struktur transformieren.

## Die formale Einschränkung der Praxis:

Der einzige "Verlust", der auftritt, ist nicht mathematischer Natur, sondern betrifft die Architektur (wie im Expression Problem erwähnt). Wenn du OOP zu FP castest, tauschst du die leichte Erweiterbarkeit von Datentypen gegen die leichte Erweiterbarkeit von Operationen. Der Code verhält sich mathematisch exakt gleich, liest und wartet sich aber völlig anders.

---

---

Der Isomorphismus bezieht sich ausschließlich auf den abstrakten Syntaxbaum (AST) und die dahinterliegende Semantik (die mathematische Logik), nicht auf den konkreten Syntaxbaum (CST).
Der konkrete Syntaxbaum (auch Parse Tree genannt) spiegelt die exakte grammatikalische Struktur des Quellcodes einer spezifischen Programmiersprache wider. Da FP und OOP völlig unterschiedliche Schlüsselwörter, Grammatiken und syntaktische Konstrukte verwenden, sind ihre CSTs grundlegend verschieden.
Hier ist die detaillierte analytische Begründung, warum der Isomorphismus auf dem AST und der Semantik operiert:

## Warum der CST nicht isomorph ist
Der CST enthält alle rein syntaktischen Details wie Klammern, Schlüsselwörter (class, def, lambda), Doppelpunkte und Semikolons.

* Wenn du eine OOP-Klasse in Python schreibst, erzwingt die Grammatik der Sprache einen CST mit einem ClassDef-Knoten.
* Wenn du dasselbe Verhalten in FP als Funktionen ausdrückst, erzeugt der Parser einen CST mit FunctionDef- oder Lambda-Knoten.

Ein struktureller (isomorpher) Vergleich auf CST-Ebene ist unmöglich, da die Grammatiken für OOP und FP nicht eins zu eins aufeinander abbildbar sind.

## Warum der AST (und die Semantik) isomorph ist
Der AST bereinigt den Code von sprachspezifischem syntaktischen Ballast und konzentriert sich auf die strukturelle Bedeutung und den Datenfluss.
Auf dieser Ebene (oder spätestens auf der Ebene der operationalen Semantik) wird sichtbar, dass beide Paradigmen dieselbe mathematische Struktur beschreiben:

* Zustandsbindung: Ob Daten im AST als „Instanzvariable an ein Objekt gebunden“ (self.x) oder als „Argument an eine Closure gebunden“ deklariert werden, ist strukturell äquivalent. Beide sind Zuordnungen von Bezeichnern zu Werten in einem lokalen Gültigkeitsbereich (Scope).
* Kontrollfluss und Zustandstransformation: Die Mutation einer Objekteigenschaft durch eine Methode und das Erzeugen eines neuen Daten-Records durch eine reine Funktion lassen sich im AST auf dieselbe mathematische Funktion abbilden: $f: S \times A \to S$ (Ein Zustand $S$ und ein Argument $A$ führen zu einem Zustand $S$).

## Einsteins Analogie im Compilerbau
Moderne Compiler (wie die von Scala, Rust oder auch F#) nutzen genau diesen AST-Isomorphismus aus. Sie erlauben dem Programmierer, in OOP oder FP zu schreiben, transformieren aber beide Paradigmen während der Kompilierung (oft im Zwischencode, der Intermediate Representation, die einem optimierten AST entspricht) in dieselbe fundamentale Struktur.
Für die CPU existiert am Ende weder OOP noch FP – dort gibt es nur Daten im Speicher und Operationen, was beweist, dass die Information auf der abstrakten, semantischen Ebene völlig identisch war.

---

---

Damit sich das Casting in der Entwicklungspraxis (also auf Ebene des Quellcodes und des konkreten Syntaxbaums) wirklich isomorph verhält, benötigst du zwingend ein starkes, vereinheitlichendes Typisierungssystem, das die konkrete Semantik beider Welten formal beschreibt.
Ohne diese Typisierung wäre der "Cast" in der Praxis ein Blindflug. Das Typisierungssystem fungiert hier als die mathematische Brücke, die garantiert, dass die strukturellen Garantien von FP (wie Unveränderlichkeit) und OOP (wie Kapselung) beim Wechsel des Paradigmas nicht verloren gehen.
In der modernen Entwicklungspraxis wird diese Brücke über folgende Mechanismen geschlagen:

## Die algebraischen Datentypen (ADTs) als Bindeglied
Um den CST isomorph zu halten, nutzen moderne Multi-Paradigmen-Sprachen (wie Rust, Scala oder TypeScript mit fortgeschrittenen Typen) Algebraische Datentypen:

* Produkttypen (Records/Tuples): Sie typisieren den reinen Zustand (die Attribute).
* Summentypen (Enums/Unions): Sie typisieren die verschiedenen Zustandsformen oder Verhaltensweisen.

Ein starkes Typsystem erlaubt es, ein OOP-Interface und eine FP-Funktionssignatur auf dieselbe algebraische Struktur abzubilden. Der Compiler sieht dann trotz unterschiedlichem CST, dass die Typ-Semantik identisch ist.

### Wie das in der Praxis aussieht: Das "Casting" über Typen
Wenn du in einer typisierten Sprache von OOP zu FP castest, übersetzt das Typsystem die konkrete Semantik eins zu eins:

OOP (Konkrete Semantik im CST)        FP (Konkrete Semantik im CST)
Interface/Klasse                      Algebraischer Datentyp (ADT)
Methodensignatur: (A) -> B            Funktionssignatur: (State, A) -> (State, B)
Zustandsmutation                      Monadischer Übergang oder Lineare Typen

Gibt es hierbei keine Typisierung der Semantik, weiß die Entwicklungsumgebung (und der Compiler) nicht, ob die FP-Funktion wirklich alle Seiteneffekte des OOP-Gegenstücks abdeckt. Die Typisierung erzwingt, dass beim Vorwärts- und Rückwärts-Casten keine Felder oder logischen Pfade vergessen werden.

### Fortgeschrittene Typkonzepte für den perfekten Praxis-Cast
In der theoretischen Informatik und in Sprachen wie Haskell oder Scala nutzt man hochentwickelte Typkonzepte, um diesen Isomorphismus im echten Code perfekt zu machen:

* Existenzielle Typen (Existential Types): Sie erlauben es FP, Daten so zu "verstecken", wie es OOP mit privaten Attributen tut.
* Lineare Typen / Ownership (wie in Rust): Sie erlauben es FP, die Effizienz von OOP-Mutationen im Speicher zu nutzen, während mathematisch (semantisch) die absolute Unveränderlichkeit garantiert bleibt.

## Kurz gefasst

Während der Isomorphismus auf rein mathematischer Ebene (im AST) immer existiert, wird er für uns Entwickler im echten Code (CST) erst durch eine explizite Typisierung der Semantik nutzbar und überprüfbar. Sie sorgt dafür, dass sich der Code beim Paradigmenwechsel nicht nur theoretisch, sondern auch praktisch fehlerfrei verhält.


---

---

Um die Brücke zwischen FP und OOP in der echten Entwicklungspraxis stabil zu halten, müssen Styleguides, Entwurfsmuster und statisches Type-Checking (wie mit mypy in Python) an einem zentralen Punkt zusammenlaufen.
In Python nutzt man dafür primär Protocols (Strukturelles Subtyping / Duck Typing) aus dem typing-Modul. Sie erlauben es, Schnittstellen rein über ihre Struktur (Methoden und Typen) zu definieren, ohne eine feste Klassenhierarchie zu erzwingen.
Hier ist die konkrete Architektur, wie du dieses System zentralisierst, Typsicherheit garantierst und es flexibel für Sonderfälle (wie unvorhergesehene FP-Transformatoren oder OOP-Kapselungen) erweiterst.

## Die zentrale Architektur (Das Protokoll)
Wir definieren ein zentrales Protokoll, das den mathematischen Zustand (State) und die Transformationslogik vorschreibt. Jede Struktur – ob FP-Datenstruktur oder OOP-Klasse – muss sich diesem Protokoll fügen.

```python
from typing import Protocol, TypeVar, Generic, Any
# Generischer Typ für den inneren ZustandS = TypeVar("S", covariant=True)  # State ist schreibgeschützt (FP-freundlich)A = TypeVar("A")                  # Argument für die Transformation
class IsomorpherKontext(Protocol[S]):
    """Das zentrale Protokoll, das die semantische Struktur erzwingt."""
    @property
    def state(self) -> S:
        """Liefert den aktuellen, unveränderlichen Zustand."""
        ...

    def transform(self, action: str, argument: Any) -> "IsomorpherKontext[S]":
        """
        Zentrale Mutations-Schnittstelle. 
        Gibt immer eine konforme Struktur zurück (Isomorphie-Garantie).
        """
        ...
```

---

## Implementierung der beiden Welten unter dem zentralen Auge des Type-Checkers
Der statische Type-Checker überwacht nun penibel, dass sowohl das funktionale Datenobjekt als auch das objektorientierte Gegenstück die semantischen Regeln einhalten.

### Der FP-Zweig (Immutable Record + Pure Function)

```python
from typing import NamedTuple
class BankState(NamedTuple):
    saldo: float
class FPBankKontext:
    def __init__(self, state: BankState):
        self._state = state

    @property
    def state(self) -> BankState:
        return self._state

    def transform(self, action: str, argument: Any) -> "FPBankKontext":
        if action == "einzahlen":
            # Reine FP-Transformation ohne In-Place-Mutation
            return FPBankKontext(BankState(self._state.saldo + float(argument)))
        return self
```

### Der OOP-Zweig (Klassische Kapselung)

```python
class OOPBankKontext:
    def __init__(self, saldo: float):
        self._saldo = saldo

    @property
    def state(self) -> BankState:
        # Castet internen Zustand für die Außenwelt in das isometrische Interface
        return BankState(self._saldo)

    def transform(self, action: str, argument: Any) -> "OOPBankKontext":
        if action == "einzahlen":
            # OOP-typische Mutation des internen Zustands
            self._saldo += float(argument)
        return self
```

---

## Erweiterung um Sonderfälle (Extensibility)
In der echten Softwareentwicklung treten immer Sonderfälle auf (z. B. Logging, asynchrone Effekte, oder Legacy-Klassen, die sich nicht an das Protokoll halten). Du erweiterst dieses zentralisierte System über zwei primäre Mechanismen, ohne die Typsicherheit zu brechen:
### A. Sonderfall: Partielle Funktionen & Decorator (Der FP-Weg)
Wenn eine Funktion eine andere Signatur hat, nutzen wir Funktionskomposition (functools.partial), um sie zur Laufzeit in das erwartete Format des Protokolls zu "gießen" (Adapter-Pattern für FP).
### B. Sonderfall: Dynamische Typerweiterung mit TypeGuard
Wenn ein Sonderfall eintritt, bei dem sich die Struktur je nach Zustand anders verhalten muss (z. B. ein gesperrtes Konto), nutzen wir TypeGuard für ein sicheres, statisches Type-Narrowing zur Laufzeit:
```python
from typing import TypeGuard
def ist_premium_kontext(kontext: IsomorpherKontext[Any]) -> TypeGuard[OOPBankKontext]:
    """Prüft zur Laufzeit einen Sonderfall und garantiert dem Type-Checker das exakte OOP-Objekt."""
    return hasattr(kontext, "_saldo") and kontext.state.saldo > 1000000
```

## Zusammenfassung des Styleguide-Regelwerks
Um dieses System im Team als Standard (Styleguide) zu etablieren, gelten drei goldene Regeln für den Type-Checker:

   1. No Direct Mutation: Modifikationen am Systemzustand dürfen nur über die zentrale .transform()-Schnittstelle des Protokolls laufen.
   2. Read-Only States: Die Eigenschaft .state liefert ausschließlich unteilbare, gefrorene Objekte (NamedTuple, frozenset).
   3. Strict Return Types: Jede abgeleitete Methode muss sich selbst (oder eine neue Instanz, die das Protokoll erfüllt) zurückgeben (-> IsomorpherKontext).

---

---

<center>

![Error while trying to load the image](../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](../dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
