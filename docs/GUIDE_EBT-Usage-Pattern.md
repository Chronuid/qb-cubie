# EBT Usage-Patterns

---

## 1. Einfache Nutzungs-Muster und eindeutige Beispiele

### 1.1. In-Memory ohne Ballast

Für reine Funktionen müssen wir überhaupt kein `WorldState`-Objekt definieren. Wenn `pre` ein `tuple` oder `dict` ist, interpretiert Cubie das konventionell automatisch als `args` bzw. `kwargs` eines WorldState-Objekts.

```python
# Shorthand für reine Funktionsaufrufe
def test_1(): EBT(target=my_func, pre=(1, 2), post=3).run()
def test_2(): EBT(target=my_func, pre={"x": 1, "y": 2}, post=3).run()
def test_2_red(): EBT(target=my_func, pre={"x": 1, "y": 2}, post=4, expect=False).run()
def test_3(): EBT(target=my_func, pre={"x": 6}, post=31, arena="envs/custom_env_1").run()
```


```python
# Vollständige Deklaration
def test_1(): 
    EBT(
        target=my_func, 
        pre=WorldState(args=(1, 2)), 
        post=WorldState(returns=3)
    ).run()
    
def test_2(): 
    EBT(
        target=my_func, 
        pre=WorldState(kwargs={"x": 1, "y": 2}), 
        post=WorldState(returns=3)
    ).run()
    
def test_2_red(): 
    EBT(
        target=my_func, 
        pre=WorldState(kwargs={"x": 1, "y": 2}), 
        post=WorldState(returns=4),
        expect=False
    ).run()

def test_3(): 
    EBT(
        arena=PyVenv("envs/custom_env_1"),
        target=my_func, 
        pre=WorldState(kwargs={"x": 6}), 
        post=WorldState(returns=31), 
    ).run()
```

### 1.2. Datei-Transformationen & Seiteneffekte

Hier kommt die Definition von `WorldState` ins Spiel, um **Funktions-Inputs** von **Dateisystem-Zuständen** sauber zu trennen:

```python
def test_4(): 
    EBT(
        target=my_func,
        pre=WorldState( # VORBEDINGUNG (P)
            args=["kalkuel.md"], # Die Argumente für my_func("kalkuel.md")
            fs={"fixtures/pre/kalkuel.md"} # Welche Dateien werden in die Sandbox kopiert?
        ),
        post=WorldState( # NACHBEDINGUNG (Q)
            returns="Erfolgreich bereinigt", # Für die Roadmap - Optional: Konsolenausgabe prüfen
            fs={"fixtures/post/kalkuel.md"} # Welchem Soll-Zustand muss die Sandbox danach entsprechen?
        ), 
        tags=["optional"]
    ).run()
```

#### 1.3. Ganze Ordner / Repositories

Wenn wir ganze Verzeichnisse oder Refactorings prüfen, zeigt das `WorldState`-Muster seine volle Stärke, bleibt aber schlank:

```python
def test_5(): 
    EBT(
        target=Agent.refactor_repo(),
        arena="envs/qa_env", # Wo wird ausgeführt? (Arena, optional deklarierbar)
        pre=WorldState(fs="fixtures/pre/project_x/"), # Copied in als Workspace-Root
        post=WorldState(
            fs="fixtures/post/project_x/", # Byte-Vergleich des gesamten Ordners
            returns=True # Erwarteter Return-Wert des Agents
        ),
        tags=["optional"]
    ).run()
```

#### 1.4. Das Dictionary-Pattern

Der bisher veranschaulichte Ansatz mit den `pre`- und `post`-Ordnern ist ein reiner Konventions-Ansatz (*Convention over Configuration*). Das ist extrem schlank, entwicklerfreundlich und reduziert Boilerplate-Code enorm.

Das Dictionary-Pattern hingegen ist ein reiner Konfigurations-Ansatz (IoC) und gibt dir die absolute Kontrolle über die Dateisystem-Topologie.

```python
def test_6(): 
    EBT(
        target=my_func,
        arena="envs/qa_env",
        pre=WorldState(
            args=["--process"], # Das Argument, das die Funktion bekommt
            fs={
                "/etc/app/config.yaml": "tests/pre/1_config.yaml",
                "./data/pre.csv": "tests/pre/1_input.csv"
            } # Mirror: Arena-Pfad ← Host-Dataset (Echte Kopie)
        ),
        post=WorldState(
            fs={
                "/etc/app/config.yaml": "tests/post/1_config.yaml", 
                "./data/pre.csv":     "tests/post/1_input.csv"
            } # Assert: Erwarteter Endzustand in der Arena ← Post-Dataset
        )
    ).run()

```

Das Dictionary-Mapping `{"Pfad_in_der_Arena": "Pfad_auf_dem_Host"}` wird genau dann zur Pflicht, wenn die Struktur deiner Testdaten auf der Festplatte (Host) **nicht** mit der Struktur übereinstimmt, die der Code (Target) während der Ausführung in der Sandbox (Arena) zwingend erwartet.

---

## 2. Erweiterte EBT Usage-Patterns

### 2.1. Das Fundament: 1:1 Mapping (Absolute Zuordnung)

Die klassische EBT-Definition, abgeleitet aus dem Hoare-Tripel {P}S{Q}, mappt exakt einen definierten Input auf exakt einen definierten Output.
Logik: S: P → Q
Bedeutung: Das Programmsegment transformiert ein isoliertes P-Objekt präzise in ein Q-Objekt.

### 2.2. Die Q-Menge: 1:N Mapping (Der beschränkte Existenzquantor)

In Systemen mit nicht-diskreten, aber validen Lösungsräumen (z.B. definierte Zufallsgeneratoren) mappt ein P-Objekt auf eine Menge von erlaubten Zielzuständen. Der Test leuchtet grün, sobald das Ergebnis von S(P) irgendeinem Element der definierten Menge Q entspricht.
Logik: ∃ q ∈ Qset : S(P) = q
Bedeutung: Es existiert mindestens ein Element in der erlaubten Ziel-Menge, das mit dem Output identisch ist.
Praxis-Beispiel (Datei-Zustände):

#### Cubie Konfiguration für eine Q-Menge

```python
def test_7():  
    EBT(
        target=my_func,
        pre=WorldState(fs="data/input/1_prompt.md"),
        post=[
            WorldState(fs="data/output/1_valid_response_a.md"),
            WorldState(fs="data/output/1_valid_response_b.md"),
            WorldState(fs="data/output/1_valid_response_c.md")
        ]
    ).run()
```

Der Testrunner vergleicht den Output gegen alle definierten Elemente der Post-Condition-Liste. Ein einzelner Byte-für-Byte-Match reicht für eine erfolgreiche Verifikation.

### 2.3. Die P-Menge: N:1 Mapping (Der beschränkte Allquantor)
Häufig müssen unterschiedliche Eingangs-Zustände auf ein und denselben, normierten Ziel-Zustand transformiert werden.
Logik: ∀ p ∈ Pset : S(p) = Q
Bedeutung: Für alle definierten Elemente der Eingabe-Menge muss die Funktion exakt denselben Ziel-Zustand Q generieren.
Praxis-Beispiel (Datums-Format-Normalisierung, Datei-Zustände):

#### Cubie Konfiguration für eine P-Menge

```python
def test_8():  
    EBT(
        target=my_func,
        pre=[
            WorldState(fs="data/input/1_date_format_us.txt"),
            WorldState(fs="data/input/1_date_format_eu.txt"),
            WorldState(fs="data/input/1_date_format_iso.txt")
        ],
        post=WorldState(fs="data/output/1_date_format_normalized.txt")
    ).run()
```
Das Framework iteriert deterministisch durch die Menge der Pre-Conditions und isoliert jede Ausführung in einer Arena. Jede Mutation muss in dem exakt gleichen Q-Dokument enden.

#### Architektur-Hinweis: Abgrenzung zur Stochastik (PBT)
Obwohl hier Mengen (Sets) verwendet werden, befinden wir uns weiterhin an der absoluten Grenze des EBT und tief im Territorium der deterministischen Prädikatenlogik erster Stufe (FOL). Die Mengen P und Q sind manuell definiert, endlich und deterministisch (Ground Truth). Es findet keine stochastische Flutung (wie bei der Logik höherer Stufe, HOL) statt. Wir nutzen lediglich endliche Mengen, um die Orthogonalität des Raumes präziser abzustecken, ohne den Rahmen der harten, falsifizierbaren Fakten zu verlassen.

### 2.4 Die Anatomie des `WorldState`-Objekts

Schauen wir uns genau an, wie das `WorldState`-Objekt die Brücke zwischen der formalen Logik und der Sandbox-Realität schlägt und wie es sich nahtlos auf deine mathematischen Mengen-Mappings übertragen lässt.

Das `WorldState`-Objekt fungiert in Meso- und Macro-Szenarien als **Zustands-Deklarator**. Es trennt die funktionale Ausführungsebene (`args`, `returns`, `stdout`) strikt von der topologischen Dateisystem-Ebene (`fs`).

Hier sind die drei Kernmechanismen, wie das `WorldState`-Objekt arbeitet:

#### **Die Auswertung von `fs` (Hydration & Assert):**

* **In `pre`:** Wenn `fs` ein Set aus Pfaden oder ein Dictionary ist, triggert Cubie die **physische Hydration**. Die Dateien werden vom Host gelesen und in den Workspace projiziert.


* **In `post`:** Hier wechselt die Semantik von *Aktion* zu *Assertion*. Das Framework führt ein Byte-für-Byte Diff gegen die dort definierten Soll-Strukturen aus.


#### **Pfad-Personalisierung über String-Mappings:**
Durch das Dictionary-Pattern `{"Pfad_in_der_Arena": "Pfad_auf_dem_Host"}` entkoppelt das `WorldState`-Objekt den Code von deiner physischen Testordner-Struktur. Das erlaubt es, für alle möglichen Szenarien personalisierten Code zu schreiben, um die Testordner-Strukturen ganz nach den eigenen Bedürfnissen anlegen zu lassen.

#### **Typ-Flexibilität für funktionale Rückgaben:**
Neben dem Dateisystem verwaltet es funktionale Schnittstellen wie `stdout` (für CLI-Streams) oder `returns` (für Rückgabewerte von Funktionen).


### 2.5 Anwendung auf diskrete Mengen-Mappings

Da wir nun wissen, wie das `WorldState`-Objekt aufgebaut ist, können wir die erweiterten Patterns für Quantoren (1:N und N:1) verstehen.

#### Das 1:N Mapping (Der beschränkte Existenzquantor $\exists$)

In Systemen mit nicht-diskreten, aber validen Lösungsräumen (z. B. Zufallsgeneratoren) mappt ein fixer P-Input auf eine endliche Menge von erlaubten Zielzuständen. Der Test leuchtet grün, sobald das Ergebnis von $S(P)$ irgendeinem Element der definierten Menge $Q$ entspricht.

* **Logik:** $\exists q \in Q_{\text{set}} : S(P) = q$ 

* **Bedeutung:** Es existiert mindestens ein Element in der erlaubten Ziel-Menge, das mit dem aktuellen Output identisch ist.

#### Praxis-Beispiel (Datei-Zustände):

Um den Raum orthogonal aufzuspannen und das System zur Abstraktion zu zwingen, definieren wir zwei EBT-Cases mit unterschiedlichen Wertebereichen:

```python
# Generator beschränkt auf Werte von 1 bis 5
def test_9():  
    EBT(
        target=my_func,
        pre=WorldState(args=("--min", "1", "--max", "5")),
        post=[
            WorldState(returns=0, expect=False),
            WorldState(returns=1),
            WorldState(returns=2),
            WorldState(returns=3),
            WorldState(returns=4),
            WorldState(returns=5),
            WorldState(returns=6, expect=False)
        ]
    ).run()
# Orthogonale Erweiterung – Generator beschränkt auf 3 bis 7
def test_10():  
    EBT(
        target=my_func,
        pre=WorldState(args=("--min", "3", "--max", "7")),
        post=[
            WorldState(returns=2, expect=False),
            WorldState(returns=3),
            WorldState(returns=4),
            WorldState(returns=5),
            WorldState(returns=6),
            WorldState(returns=7),
            WorldState(returns=8, expect=False)
        ]
    ).run()
```

#### Das N:1 Mapping (Der beschränkte Allquantor $\forall$)

Müssen verschiedene unstrukturierte Eingänge (z. B. Datums-Format-Normaliserung oder polymorphe Interfaces) in dasselbe standardisierte Ziel-Format gepresst werden, übergeben wir eine **Liste von `WorldState`-Objekten** an den `pre`-Parameter. Cubie isoliert jeden Lauf isoliert in der Arena, verifiziert jedoch jedes Mal gegen denselben `post`-Zustand.

```python
def test_11():  
    EBT(
        target=my_func,
        pre=[ # Vorbedingung (P-Menge): Verschiedene verrauschte Eingangsquellen
            WorldState(args=["raw_us.md"], fs={"/app/input.md": "fixtures/pre/raw_us.md"}),
            WorldState(args=["raw_eu.md"], fs={"/app/input.md": "fixtures/pre/raw_eu.md"}),
            WorldState(args=["raw_iso.md"], fs={"/app/input.md": "fixtures/pre/raw_iso.md"})
        ],
        post=WorldState( # Nachbedingung (Q): Exakt ein kohärenter Ziel-Zustand
            fs={"/app/output.md": "fixtures/post/normalized.md"}
        ),
        tags=["universal"]
    ).run()
```

---

# Arenen und Umgebungs-Mutationen

Das Attribut **`arena`** definiert den isolierten Ausführungsraum (die Sandbox), in dem das Target ($S$) operiert.

Die wichtigste Grundregel für den Lebenszyklus einer Arena lautet: **Der Raum bleibt konstant.** Wenn im `WorldState` der `pre`-Condition eine Arena definiert wird, gilt diese implizit und zwingend auch für die `post`-Condition. Das Framework testet schließlich die Mutation *innerhalb* dieser einen Welt ($P \to Q$).

* *Wann definiert man die Arena im `WorldState`?:* Man überschreibt die Arena auf lokaler State-Ebene **nicht**, um es bestimmten Eingaben (Edge-Cases) leichter zu machen. Das würde den Test verfälschen.
Die lokale Arena-Definition wird ausschließlich dann genutzt, wenn das Target ($S$) die explizite Aufgabe hat, mit der Umgebung selbst zu interagieren – beispielsweise bei System-Skripten, Installationen oder dem Bootstrapping von Projekten.

### Validierung einer aktiven Umgebungs-Mutation

In diesem Szenario testen wir eine Funktion, deren einziger Zweck es ist, ein Paket in eine virtuelle Umgebung zu installieren. Wir definieren eine leere Arena als Vorbedingung und prüfen, ob die Funktionalität die Umgebung korrekt mutiert hat.

```python
def test_12():
    EBT(
        target=EnvManager.install_package(),
        pre=WorldState(args="requests", arena=PyVenv("envs/pre_env")),
        post=WorldState(arena=PyVenv("envs/post_env"))
    ).run()
```

```python
def test_13():
    EBT(
        target=md_to_json_converter(),
        pre=WorldState(
            args="why-cats-like-to-cuddle.json", 
            arena=TempFS("envs/pre_env/why-cats-like-to-cuddle.md")
        ),
        post=WorldState(
            returns="'why-cats-like-to-cuddle.md' succesfully converted to json.",
            arena=TempFS("envs/post_env/why-cats-like-to-cuddle.json")
        )
    ).run()
```