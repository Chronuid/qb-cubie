## `class ConventionMap`
> HINWEIS: Wir behalten die ConventionMap samt ihrer dynamischen Registrierungs-Logik vorerst strikt im internen dev-Bereich. So bewahren wir uns die absolute Freiheit, unter der Haube alles jederzeit neu zu verdrahten, ohne dass die öffentlichen Verträge (die Usage-Patterns) brechen. Erst wenn sich die Mechanik in der Praxis beweist, gießt man sie in ein offizielles Feature.  
    Die "User-Experience in der `conftest.py`", welche am Ende dieses Dokuments vorgestellt wird, ist noch kein fest vorgegebenes Nutzungsmuster, aber könnte sich noch in der Zukunft zu so einem klaren Feature entwickeln.

### Abstrakte Funktionsweise

Wenn eine Ausführungs-Engine (z. B. `EBT` oder `RBT`) einen primitiven Datentyp oder eine Shorthand-Struktur als Parameter entgegennimmt, konsultiert sie eine zentrale Übersetzungsschicht. Diese Layer arbeitet nach folgenden Prinzipien:

1. **Klassen- und Kontextsensitivität:** Die Map ist völlig agnostisch gegenüber den aufrufenden Test-Klassen. Ein und derselbe Datentyp (z. B. ein String) kann je nach Test-Typ (z. B. `EBT` vs. `RBT`) und Parameter (z. B. `pre` vs. `test`) eine völlig andere strukturelle Bedeutung annehmen.
2. **Typ-Inferenz:** Die Layer ordnet eingehende Datentypen deterministisch einem Ziel-Attribut oder Zustandsobjekt zu (z. B. `WorldState.args` oder direkten Test-Direktiven).
3. **Pluggable Overrides:** Die Standard-Konventionen des Frameworks sind nicht hardcodiert, sondern als austauschbare Registry definiert. Dadurch bleibt das System offen für Erweiterungen (Open-Closed-Principle).

Die `ConventionMap` fungiert ausschließlich als Mapping-Registry für die Auto-Inferenz von primitiven Datentypen (Shorthands) in die vollumfänglichen Ziel-Objekte. Sie differenziert dabei strikt anhand der anfragenden Klasse und des spezifischen Parameters.

### Das "Fluent Interface" (Der semantische Ansatz)

```python
#PSEUDOCODE

# Interne Hilfsklassen (für den Nutzer unsichtbar)
class _Mapper:
    def __init__(self, registry: dict, target_class: type, param_name: str, incoming_type: type):
        self.registry = registry
        # ... Temporäre Speicherung der Zuweisungskette ...

    def maps_to(self, target_param: str, target_attribute: Any):
        # Speichert die finale Zuweisungsregel in der Registry
        pass

class _ParamSelector:
    def is_type(self, incoming_type: type) -> _Mapper:
        pass

class _ClassSelector:
    def when(self, param_name: str) -> _ParamSelector:
        pass

class ConventionMap:
    def __init__(self):
        # Standard-Konventionen direkt im Konstruktor setzen
        
        # EBT Mappings
        self.for_class(EBT).when("pre").is_type(tuple).maps_to("pre", WorldState.args)
        self.for_class(EBT).when("pre").is_type(dict).maps_to("pre", WorldState.kwargs)
        self.for_class(EBT).when("post").is_type(str).maps_to("post", WorldState.returns)
        
        # RBT Mappings
        self.for_class(RBT).when("test").is_type(str).maps_to("test", "criteria")

    def for_class(self, target_class: type) -> _ClassSelector:
        pass

```

### 1. Die Zuweisungskette: `for_class`, `when` und `is_type`

Diese Methoden bilden die kontextsensitiven Eintrittspunkte des verallgemeinerten Fluent Interfaces.

* **`for_class(Klasse)`:** Isoliert die darauffolgenden Regeln strikt auf die anfragende Test-Klasse (z. B. `EBT` oder `RBT`).
* **`when("parameter")`:** Definiert den Ziel-Parameter der jeweiligen Klasse (z. B. `"pre"` oder `"test"`), der evaluiert werden soll.
* **`is_type(Typ)`:** Der Trigger. Er friert den erwarteten primitiven Datentyp (wie `tuple` oder `str`) ein und übergibt die Meta-Informationen an die transiente Hilfsklasse `_Mapper`. *(Da `is` in Python ein reserviertes Schlüsselwort für Identitätsprüfungen ist, nutzen wir `is_type` als klaren, typsicheren Alias).*

### 2. `_Mapper` und `maps_to`: Der Zuweisungs-Knoten

Die intern verborgene `_Mapper`-Klasse fungiert als kurzlebiges Bindeglied, das ausschließlich dazu dient, die Signatur des Fluent Interfaces lesbar und sauber zu halten.

* **Die `maps_to`-Methode:** Dies ist der Endpunkt der Zuweisungskette, an dem die Typ-Inferenz deterministisch abgeschlossen wird. Sie verknüpft den Datentyp mit seinem finalen Bestimmungsort und teilt der Engine mit, ob das Objekt beispielsweise in ein `WorldState.args`-Attribut umgewandelt werden soll.

### 3. `__init__`: Die konkrete Map-Konfiguration

Der Konstruktor der `ConventionMap` fungiert als das "Out-of-the-box"-Fundament des Frameworks.

* **Standard-Konventionen:** Hier werden die fundamentalen Usage-Patterns in Code gegossen und als Standard-Registry für alle Test-Typen definiert.
* **Wahrung der Patterns:** Diese Vorab-Konfiguration garantiert, dass die Ausführungs-Engines (EBT, RBT, etc.) die Standard-Konventionen intern konsumieren können. Entwickler können somit ohne Boilerplate-Code testen, solange sie sich an die etablierten Shorthands halten.

### 4. `ConventionMap`: Der Ablauf im Ganzen

Zusammenfassend orchestriert die Klasse die intelligente Typ-Inferenz als zentrale Übersetzungsschicht, ohne die Kern-Mechanismen der Test-Ausführung zu modifizieren.

* **Der Inferenz-Zyklus:** Empfängt die Orchestrierungs-Engine (z. B. `EBT`) einen primitiven Datentyp als Shorthand, fragt sie die Registry der `ConventionMap` mit ihrer eigenen Klasse und dem Parameter-Namen ab. Die Map liefert das korrekte Ziel-Attribut, woraufhin die Engine das Shorthand implizit in das geforderte Objekt konvertiert.
* **Der Override-Mechanismus (Pluggability):** Möchte ein Nutzer dieses Standardverhalten modifizieren, definiert er in seiner lokalen `conftest.py` lediglich eine spezifische Pytest-Fixture (z. B. `cubie_convention`). Innerhalb dieser Fixture instanziiert er eine eigene `ConventionMap`, nutzt das Fluent Interface zur Rekonfiguration und gibt diese zurück. Das Framework fängt die Fixture dynamisch zur Laufzeit ab und überschreibt die internen Mapping-Regeln.

### **Die User-Experience in der `conftest.py`:**

```python
import pytest
from cubie.core import ConventionMap
from cubie.ebt import EBT, WorldState
from cubie.rbt import RBT

@pytest.fixture
def cubie_convention():
    config = ConventionMap()
    
    # Intuitiv, lesbar und völlig agnostisch über Test-Klassen hinweg
    config.for_class(EBT).when("post").is_type(str).maps_to("post", WorldState.fs)
    config.for_class(EBT).when("post").is_type(int).maps_to("post", WorldState.returns)
    config.for_class(RBT).when("check").is_type(str).maps_to("test", "review_directive")
    
    return config
```