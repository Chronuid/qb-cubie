# Example-Based-Testing

```python
#PSEUDOCODE
from core import CubieBase
from typing import Any
from dataclasses import dataclass

class EBT(CubieBase):
    def __init__(
        self,
        arena,
        target,
        pre,
        post
    ):
        self.arena = arena
        self.target = target
        self.pre = pre
        self.post = post

           
@dataclass
class WorldState:
    arena: Any = None
    args: Any = None
    kwargs: Any = None
    returns: Any = None
    fs: Any = None
```


Das Example-Based-Testing (EBT) fungiert als kompromisslose Basis der Qualitätssicherung, indem es deterministische Realitäten als "Golden Master" definiert. Basierend auf dem klassischen Hoare-Tripel $\{P\}S\{Q\}$ spannt das Konzept den Raum von einfachen In-Memory-Funktionen bis hin zu komplexen Datei- und Ordner-Transformationen auf.

---

## `class EBT`
Die `EBT`-Klasse ist die zentrale Orchestrierungs-Engine des Frameworks. Sie dient als direkte architektonische Übersetzung des formalen P S Q Paradigmas in ausführbaren Code. Die Klasse selbst agiert dabei als direktes Interface für die Definition der Test-Fälle.

**Kern-Verantwortlichkeiten:**

* **Auto-Inferenz:**
Um die Entwickler-Erfahrung (DX) schlank zu halten und Boilerplate-Code zu minimieren, fungiert die Klasse als intelligenter Übersetzer. Sie nimmt Datentypen entgegen und konvertiert diese implizit in vollumfängliche, standardisierte `WorldState`-Objekte.

* **Erweiterte Formallogische Engine (Quantoren-Auflösung):**
Die Klasse steuert den iterativen Prüfprozess für komplexe Lösungsräume.

   * Werden Vorbedingungen (`pre`) als WorldState-Listen übergeben, wendet die Klasse deterministisch das Prinzip des beschränkten Allquantors ($\forall$) an, führt jeden Zustand isoliert aus und verknüpft die Assertions mit einem logischen UND.

   * Werden Nachbedingungen (`post`) als WorldState-Listen übergeben, schaltet die Engine auf das Prinzip des beschränkten Existenzquantors ($\exists$) um und bewertet den Test als bestanden (ODER-Verknüpfung), sobald der Output mit einem Element der Zielmenge übereinstimmt.

---

## `class ConventionMap`

Die `ConventionMap` fungiert ausschließlich als Mapping-Registry für die Auto-Inferenz von primitiven Datentypen (Shorthands) in die vollumfänglichen `WorldState`-Attribute. Sie differenziert dabei strikt zwischen der semantischen Auswertung von Vor- und Nachbedingungen.

* **Wahrung der Usage-Patterns:** Die bloße Existenz dieser Datenklasse darf unter keinen Umständen die nach außen definierten Standart-Konventionen und Usage-Patterns beeinträchtigen oder Anforderungen stellen.
* **Pragmatismus via Pytest:** Die `ConventionMap` löst das Problem abweichender Nutzerpräferenzen, ohne dass das Framework mit Parsern für Custom-Configs aufgebläht wird.
* **Der Override-Mechanismus:** Die `EBT`-Engine konsumiert die Standard-Konventionen intern. Möchte der Nutzer diese überschreiben, definiert er in seiner lokalen `conftest.py` lediglich eine spezifische Pytest-Fixture (z. B. `ebt_convention`), die eine modifizierte Instanz der `ConventionMap` zurückgibt. Das Framework fängt diese Fixture dynamisch zur Laufzeit ab und überschreibt die internen Mapping-Regeln. Das hält die Architektur strikt modular, verhindert Boilerplate im Test-Code und gibt dem Nutzer die absolute Kontrolle über die Inferenz, ohne die Kern-Mechanismen des Cubie-Frameworks anzutasten.

---

## `class WorldState`

Die `WorldState`-Klasse ist ein Zustands-Deklarator, der alle Variablen einer Test-Welt kapselt. Sie dient als standardisierte Datenstruktur zur Definition von Zuständen. Seien es nun Vorbedingungen ($P$) oder Nachbedingungen ($Q$) innerhalb des EBT-Paradigmas.
Die Klasse ist konzeptionell die Antwort auf die Frage, wie man komplexe Tests sauber abbildet, ohne den Code mit Boilerplate zu überladen. 
Sie fungiert als das einheitliche Ziel-Schema, in welches die übergeordnete `EBT`-Klasse alle primitiven Eingaben (Shorthands) implizit konvertiert.

* **Die Kernidentität:** Die Klasse fungiert als strikter "Zustands-Deklarator". Sie ist das standardisierte Objekt, das eine konkrete "Welt" (sei es $P$ oder $Q$) kapselt.

* **Die Trennung der Ebenen:** Ihre wichtigste strukturelle Eigenschaft ist die klare Trennung: Sie separiert die funktionale Ausführungsebene, wie Code-Inputs (`args`) oder Outputs (`returns`), strikt von der topologischen Dateisystem-Ebene (`fs`).

* **Das Normalisierungs-Ziel:** Das `WorldState`-Objekt ist das interne Zielformat der `EBT`-Klasse. Die `EBT`-Klasse nutzt Auto-Inferenz, um einfache Datentypen (Shorthands) unter der Haube implizit in vollumfängliche `WorldState`-Objekte umzuwandeln.

---

## Weiterführende Dokumentation der Kernkomponenten

Um die interne Funktionsweise und die architektonischen Details der einzelnen Komponenten tiefgehender zu verstehen, existieren dedizierte Spezifikationen:

* **[EBT Orchestration Engine (DEV-GUIDE_2-1)](DEV-GUIDE_2-1_EBT-Classes.md):** Details zur Auto-Inferenz, Quantoren-Auflösung ($\forall$ und $\exists$) sowie den Kaskadierungs-Mechanismen der Arenen.
* **[WorldState Deklarator (DEV-GUIDE_2-2)](DEV-GUIDE_2-2_WorldState-Class.md):** Spezifikation der Zustandsobjekte, der topologischen Dateisystem-Ebene (`fs`) und der kontextuellen Dualität zwischen Pre- und Post-Phasen.
* **[ConventionMap Registry (DEV-GUIDE_3-1)](DEV-GUIDE_3-1_ConventionMap-Class.md):** Funktionsweise des Fluent Interfaces zur dynamischen Konfiguration von Typ-Mappings und Shorthands via Pytest-Fixtures.

---

## Zukunftsfähigkeit & Erweiterbarkeit


Die aktuellen Usage-Patterns sind bewusst auf pragmatische In-Memory- und topologische Datei-Transformationen optimiert (Shorthand-First). Für zukünftige Erweiterungen (z. B. vollständige VM-Isolierung oder UI-Automatisierung via CUA) gelten folgende Design-Empfehlungen für die Internas:

* **Schnittstellen-Konstanz:** Die Attribute `arena`, `pre` und `post` müssen auf Engine-Ebene polymorph verarbeitet werden. Die Kern-Engine sollte nicht strukturell davon abhängen, dass die Attribute immer statisch den bisher dokumentierten Usage-Pattern entsprechen.
* **Kapselung des Lifecycles:** Die Phasen Hydration, Execution und Assertion sollten im Code semantisch so weit entkoppelt sein, dass die Execution-Phase später durch alternative Treiber (z. B. VM-Controller, Screen-Parser) ersetzt werden kann.

### 1. Interner Polymorphismus für `arena`

Aktuell wird `arena` als einfacher `str` (Pfad zu einer Pytest-Sandbox) behandelt. Um die Engine zukunftssicher zu machen, ohne die Shorthand-Syntax zu brechen, sollte der interne Arena-Evaluator von Anfang an polymorph aufgebaut werden:

*  **Jetzt:** Wenn `type(arena) == str`, initialisiert die Engine die Standard-Pytest-Sandbox.

* **Zukunft:** Übergibt man später ein Objekt (z. B. `arena=VM("ubuntu-24.04")`), greift die Engine auf eine andere Implementierung zurück. Die API für den Nutzer bleibt identisch, die interne Ausführung skaliert mit.

### 2. Entkopplung von `Execution` und `Assertion` durch Abstraktion

* Wenn wir den Ausführungs- und Evaluierungs-Lebenszyklus (die 3 Phasen: *Hydration*, *Execution*, *Assertion*) intern sauber in Protokolle oder abstrakte Basisklassen zerlegen, ist es völlig egal, ob die `Execution`-Phase ein Python-Skript füttert oder CLI-Argumente, Klicks und Tastatureingaben an ein UI-Element sendet.

* `args` und `kwargs` können im Fall von UI-Interaktionen später intern als Event-Payloads oder Command-Sequenzen interpretiert werden, ohne dass das strukturelle Schema des `WorldState`-Objekts kollabiert.