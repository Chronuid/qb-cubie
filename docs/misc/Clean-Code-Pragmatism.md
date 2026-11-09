<center>

# Clean-Code Pragmatismus

![Cubie](../.assets/cubie-logo-written.png)

Dieser Essay diskutiert kontextabhängige Entwurfsentscheidungen und pragmatische Clean-Code-Prinzipien.

---

</center>

> **WICHTIG:** Dieser Design-Guide ist keine Heuristik-Sammlung für finale Lösungen, sondern eine Pragmatismus-Sammlung, welche zum Denken anstupst. Es gibt nicht die eine "Eierlegende-Wollmilch-Sau"-Lösung, sondern es kommt immer stark auf den jeweiligen Kontext an. Das SRP alleine bringt nichts, wenn du es einfach nur als Zeilenbegrenzung siehst, anstatt als Grund um ein Design aufzusetzen, welches SRP, die Kohäsion, Logik und den natürlichen Schutz fördert. 

In Sprachen wie Pascal oder C89 gab es eine strikte Regel: Alle Variablen müssen am Anfang eines Blocks (z. B. einer Funktion oder eines Programms) deklariert werden, bevor der erste Ausführungsbefehl kommt.

Diese Regel entstand aufgrund der Notwendigkeit für den Single-Pass-Compiler und der Übersichtlichkeit, etablierte sich aber weit darüber hinaus in den Entwickleralltag und fand seinen Weg auch in andere Sprachen wie Java. Neben den ursprünglichen Herausforderungen löste dieses Muster nämlich auch implizit eine ganze Reihe weiterer Herausforderungen. Diese strikte Vorab-Deklaration ist kein veraltetes Relikt, sondern ein massiv unterschätztes architektonisches Werkzeug, das Entwickler dazu zwingt, den Zustand ihrer Module proaktiv zu durchdenken.

### Warum machen das heute viele Entwickler nicht mehr so?

Nach vielen Interpretationen der Clean-Code-Prinzipien ist dieses Vorgehen aus folgenden Gründen verpöhnt:

* **Fehlende Thread-Sicherheit (Concurrency):** Wenn zwei verschiedene Prozesse (Threads) gleichzeitig eine Methode deiner Klasse aufrufen, überschreiben sie sich gegenseitig die Klassen-Attribute, da sie denselben Zustand manipulieren.
* **Verletzung des Gültigkeitsbereichs (Scope):** Eine Variable sollte nur so lange existieren, wie sie gebraucht wird. Wenn eine Methode eine Variable braucht, sollte sie lokal in der Methode definiert werden.
* **Seiteneffekte (Side Effects):** Wenn Methoden keine Parameter entgegennehmen und keine Werte zurückgeben, sondern nur heimlich Attribute der Klasse verändern, ist von außen völlig undurchsichtig, was die Methode eigentlich macht.

## Pragmatismus
* **Concurrency und das "Instanz pro Thread"-Argument:** Wenn man Thread-Sicherheit braucht, erstellt man einfach für jeden Thread eine neue Instanz der Klasse.
* **Scope und die "Einmalige Definition":** Eine Variable sollte nur einmal definiert werden, anstatt sie in allen Methoden verstreut unter unterschiedlichen Namen zu führen (DRY-Prinzip).
* **SRP und schlanke Klassen:** Wenn ich eine Klasse mit 4 Attributen und 3 Funktionen habe, dann muss ich nicht unbedingt eine `@dataclass;class State:...` hochziehen.
* **Seiteneffekte und das EVA-Prinzip (Input-Process-Output):** Man kann das EVA-Prinzip sauber einhalten, indem man die Attribute kontrolliert übergibt und ausgibt.


### Das Problem mit der "Enterprise-Krankheit"

Viele Interpretationen der "Clean Code"-Paradigmen stammen aus riesigen Enterprise-Anwendungen. Wichtig zur Einordnung: Mit der 'Enterprise-Krankheit' ist nicht die nützliche Strenge klassischer Sprachen wie Java gemeint. Gemeint ist vielmehr die dogmatische Über-Abstraktion (wie ausufernde Interface-Schichten oder erzwungene DTOs für winzige Zustände), die aus einer blinden Anwendung von Clean-Code-Regeln resultiert.
Sie wurden als "Idiotensicherungen" (Fail-Safes) für massive Teams entwickelt, in denen das Risiko groß ist, dass Klassen unkontrolliert wachsen.
Wenn man diese extrem defensiven Paradigmen jedoch auf kleinere, gut durchdachte Module anwendet, erschafft man oft redundante Klassen, die keinen echten funktionalen Vorteil mehr bieten. 
Oft erzeugt es sogar Nachteile: Eine Variable unter neuem Namen in jeder Methode zu führt schnell zu Spaghettie-Code und eine separate `@dataclass` hochzuziehen, die im Grunde nur die exakt gleichen Attribute spiegelt, die ohnehin zur Kernidentität der Hauptklasse gehören fügt lediglich eine sinnlose Abstraktionsschicht hinzu.

### SRP und Kohäsion als natürlicher Schutz

Der Spruch "Teile-und-Herrsche" und das Single Responsibility Principle (SRP) sind die eigentlichen Schlüssel.
Das Anti-Pattern der *God Class* entsteht ja erst, weil Entwickler das SRP ignorieren und eine Klasse mit 30 Attributen und 50 Methoden bauen.

Wenn du eine Klasse mit 4 Attributen und 3 Funktionen hast:

* **Hohe Kohäsion:** Die 3 Funktionen arbeiten logisch eng mit genau diesen 4 Attributen zusammen.
* **Klare Verantwortung:** Die Klasse hat exakt einen Zweck.
* **Der Zustand *ist* die Klasse:** Die 4 Variablen definieren den legitimen Zustand dieser spezifischen Instanz.

In so einem Fall *sind* die Klassenattribute die sauberste, performanteste und lesbarste Lösung. Insbesondere in Python ist es absolut idiomatisch, den Zustand flach in der Instanz (`self`) zu halten, solange die Klasse stark fokussiert bleibt.
Für eine Zählschleife, die bis hundert zählt, baust du ja auch keine hundert Variabeln. Du nimmst eine Variabel und zählst sie bis hundert hoch, während du den Einsatz der Variabel sauber kontrollierst 

### Pipeline-Pattern als Brücke

Wenn man eine Klasse baut, die intern eine Pipeline abarbeitet – also Methode A aufruft, deren Resultat als internes Attribut speichert, welches Methode B dann als Input nimmt –, dann ist es völlig legitim das über ein dafür dediziertes Klassen-Attribut durchzuführen, **solange die Lebensdauer und der Scope der Klasse strikt kontrolliert sind**.

Es wird nur dann zum Problem, wenn diese Klasse im Singleton-Pattern als langlebiger Service im Hintergrund läuft und von außen wiederholt asynchron aufgerufen wird, während noch alte Zustände in den Attributen hängen. Für Multi-Threading empfiehlt es sich mehrere Instanzen der Klassen zu führen und sie sauber aufzuräumen.

> Wichtig hierbei ist noch immer: Das hier ist eine Pragmatismus-Sammlung, welche zum Denken anstupst.

Zu diesem Pipeline-Pattern gab es die Kritik: "Bei der Connascence of Execution hängt die semantische Korrektheit des Systems zwingend von der Ausführungsreihenfolge der Methoden ab. Wenn ein Entwickler Methode B vor Methode A aufruft, stürzt das Programm ab oder liefert falsche Werte, da der interne Zustand noch nicht vorbereitet ist."

Diese Kritik zeigt wunderbar den Grund dafür auf, warum man klassischerweise die Variablen und Attribute direkt zu Beginn definierte und sich darüber Gedanken machte, welche Variablen man benötigt und was sie abbilden. 
Genau hier zeigt sich die architektonische Überlegenheit des klassischen Ansatzes gegenüber modernen, rein dynamischen Paradigmen: Strikte Sprachen wie Java zwingen durch ihre Natur dazu, die Logik der Algorithmen zu begreifen und Attribute direkt zu Beginn als festen Bestandteil der Klasse zu definieren. Dieser klassische Umgang mit Variablen fördert die intelligente Gestaltung der Datenmuster und bietet implizite Lösungen, um die semantische Korrektheit zu wahren, Spaghettie-Code zu umgehen und Pipeline-Abstürze zu verhindern.

## Pragmatismus vor Dogma

Regeln wie "Nutze keine Attribute für Zwischenzustände" sind Stützräder. Wenn du das architektonische Verständnis hast um Variabeln durchdacht zu gestalten, das SRP sauber anzuwenden und Klassen klein und kohäsiv zu halten, brauchst du diese Stützräder nicht. Man muss nicht für jedes Datenpaket direkt eine formelle Datenstruktur erzwingen, wenn die Attribute im Kontext der Klasse bereits perfekt gekapselt sind und kein funktionaler Mehrwert durch eine Trennung entsteht. Wenn man dann aber doch die Design-Muster und Prinzipien benötigt, weil sie eine praktische Lösung wären, dann könnte man sie jederzeit als Werkzeug zur Hand nehmen.

Wenn man Architektur nicht als Religion, sondern als Werkzeugkasten betrachtet, kommt man zu den entscheidenden Fragen, an denen sich dogmatisches "Whiteboard-Design" von exzellentem Software-Engineering unterscheidet.

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
