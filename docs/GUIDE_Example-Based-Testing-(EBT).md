# Example-Based-Testing (EBT)

Willkommen in der greifbarsten und gleichzeitig kompromisslosesten Disziplin der Qualitätssicherung.  
Hier geht es nicht um theoretische Beweise, sondern um absolute, in Stein gemeißelte Realitäten: Konkrete Werte, handfeste Argumente und exakte Systemzustände.  
Wir definieren klare Realitäten und machen sie zu unserem "Golden Master" → dem unbestechlichen Standard, an dem sich jeder Code messen lassen kann.

### 1. Die Philosophie: Zustände definieren

Die Kernidee von EBT basiert auf dem klassischen Hoare-Tripel, das wir für unsere Zwecke aus der akademischen Welt direkt in die Praxis übersetzen. Anstatt mit Variablen zu jonglieren, definieren wir Welten:

* **P (Pre-Condition / Input):** Wie sieht die Welt *vor* der Ausführung aus?
* **Q (Post-Condition / Output):** Wie muss die exakte Welt *nach* der Ausführung aussehen?
* **S (Das Programmsegment):** Der Code (oder der KI-Agent), der den Weg von *P* nach *Q* bauen muss.

**Das Lichtschalter-Beispiel:**
Machen wir es greifbar. Stell dir vor, du betrittst ein Zimmer.
Wenn der Raum dunkel ist (**P**), und ich den Lichtschalter betätige (**S**), dann ist der Raum danach hell (**Q**).
Beim EBT testen wir nicht, *wie* der Strom durch die Kabel fließt (die abstrakte Logik). Wir prüfen lediglich: War es vorher dunkel? Ja. Wurde der Schalter gedrückt? Ja. Ist es jetzt hell? Ja. Test bestanden.

EBT ist unser "Ground Truth"-Protokoll. Es stellt sicher, dass bei aller maschinellen Kreativität und komplexen Architekturen das deterministische Endresultat exakt unseren Erwartungen entspricht. Es ist das Fundament, auf dem wir Vertrauen in unseren Code aufbauen.

---

### 2. Die Dynamiken: Skalierbarkeit von der Funktion zum Repo

Das Schöne am EBT ist, dass es nicht auf primitive Datentypen beschränkt bleibt. Das Prinzip der eingefrorenen Vor- und Nachbedingungen skaliert fraktal durch alle Architekturebenen deines Projekts:

* **Micro-Dynamik (Die Funktions-Ebene):** Hier bewegen wir uns direkt im Arbeitsspeicher. Ein simples I/O-Paar. Ein Input ($P$) geht in die Funktion ($S$) hinein, ein Output ($Q$) kommt heraus.
* **Meso-Dynamik (Die Service-Ebene):** Hier agiert unser Vorzeige-Beispiel, der *MD-Cleaner*. Wir testen isolierte Dateitransformationen in einer geschützten Arena (dem Pytest-Gym). Ein rohes Wikipedia-Markdown-Dokument wird in den Workspace geladen ($P$); das Skript bereinigt es; die Validierung prüft am Ende Byte-für-Byte gegen dein handverlesenes Ziel-Dokument ($Q$).
* **Macro-Dynamik (Die Repo-Ebene):** Das absolute Endgegner-Level. Hier vergleichen wir ganze Projektbäume. $P$ ist der unaufgeräumte Legacy-Ordner, $Q$ ist die perfekt strukturierte Refactoring-Vision. Der Test vergleicht nicht nur Codezeilen, sondern Ordnerstrukturen, Abhängigkeiten und die Existenz ganzer Module.

**Die goldene Regel der Kohärenz:**
Gerade, wenn wir uns in Richtung Meso- und Macro-Dynamik bewegen, müssen wir das Systemverhalten genau verstehen. EBT gleicht *lediglich* statisch $P$ und $Q$ ab. Das bedeutet: **Die Qualität deiner Funktion ($S$) ist nur exakt so gut wie die Kohärenz deiner Testdaten.**

Es ist elementar, dass die Menge deiner Beispiele denselben, widerspruchsfreien Regeln folgt. Wenn sich in einem großen Datensatz auch nur wenige Beispiele gegenseitig widersprechen oder fehlerhafte Zielzustände fordern, passiert etwas Fatales: Die Komplexität des generierten Codes explodiert. Die Maschine versucht verzweifelt, eine Funktion zu schreiben, die allen (auch den falschen) Regeln gerecht wird. Der Code wird unleserlich, unzuverlässig oder lässt sich schlichtweg gar nicht erst finden.

Ein sauberes, kohärentes "Golden Dataset" bewirkt exakt das Gegenteil: Es schnürt das Korsett der Anforderungen so präzise, dass die Entwicklung der Funktionalität ($S$) wesentlich schlanker, schneller und zuverlässiger stattfinden kann.

*(Hinweis für Architekten: Genau hier, an der Grenze, wo statische Beispiele nicht mehr ausreichen, um alle Verhaltensweisen abzusichern, bereiten wir den Weg für ein Upcasting zu Property-Based-Testing (PBT) oder formaler Verifikation (FVT) – doch dazu später mehr.)*

---

### 3. Das Vorzeige-Beispiel: Der MD-Cleaner im RL-Gym

Um die Meso-Dynamik (Service-Ebene) in der Praxis zu verstehen, betrachten wir ein reales Transformations-Szenario: Die Bereinigung von Wikipedia-Artikeln.

Unser Ziel ist ein Skript ($S$), das rohes, von Web-Clippern generiertes HTML-Markdown in perfektes, lesbares LaTeX-Markdown überführt.

**Das Setup (Die Goldenen Datensätze):**
Wir verzichten auf abstrakte Beschreibungen und definieren stattdessen harte Fakten in unserem Dateisystem:

* **Der Input ($P$):** Eine Datei `kalkuel_raw.md` (voll mit störenden HTML-Tags und fehlerhaften Bild-Links).
* **Der Output ($Q$):** Eine Datei `kalkuel_normalized.md` (von uns handverlesen und perfekt formatiert).

**Die Arena (Das Test-Gym):**
QA-Bench führt solche Tests nicht blind im Projektordner aus, sondern etabliert eine strikte, flüchtige Arena (vergleichbar mit einem Environment-Reset im Reinforcement Learning).

1. **Reset:** Das Framework erstellt einen sterilen, isolierten Workspace im Arbeitsspeicher.
2. **Setup:** Die `_raw.md` Datei ($P$) wird in diese Arena kopiert.
3. **Action:** Das Skript (oder der KI-Agent) wird exklusiv auf diese Arena losgelassen und mutiert die Datei.
4. **Reward:** Das Framework friert die Zeit ein und vergleicht das Resultat Byte-für-Byte mit der `_normalized.md` ($Q$).
* Gibt es auch nur ein übersehenes Leerzeichen, schlägt der Test fehl und der Agent erhält ein detailliertes Diff (Reward = 0).
* Sind die Dateien absolut identisch, ist die Funktion verifiziert (Reward = 1).



Dieses Setup zwingt den Code (oder die KI), exakt die Transformation durchzuführen, die wir als Architekten vorgegeben haben – ohne dass wir ihr erklären müssen, *wie* sie das tun soll.

---

### 4. Die Gefahr der Underspezifikation (Das "Lazy Agent" Syndrom)

EBT ist kompromisslos, hat aber eine gewaltige konzeptionelle Schwäche, die besonders in der KI-gestützten Entwicklung (Test-Driven Generation) gefährlich wird: **Die Maschine wählt immer den Weg des geringsten Widerstands.**

**Die Illusion der Abdeckung:**
Nehmen wir ein simples Beispiel: Wir definieren als Input ($P$) die Zahl `2` und als Output ($Q$) die Zahl `4`.
Unser Ziel ist es, dass der Agent eine Funktion schreibt, die den Input verdoppelt (`x * 2`). Der Agent könnte aber genauso gut einfach `return 4` oder `return x + 2` schreiben. Beide Wege bestehen den Test mit Bravour.

Das ist das Problem der **Underspezifikation**. Ein Golden Dataset beweist *nicht*, dass der Code universell korrekt ist. Es beweist lediglich, dass der Code *für dieses spezifische Beispiel* nicht falsch ist. Es können extrem komplexe, völlig fehlerhafte Programme entstehen, die den Lösungsraum schlichtweg überanpassen (Overfitting), um die Tests auszutricksen.

---

### 5. Die Lösungs-Matrix: Orthogonalität und Upcasting

Wie bauen wir eine EBT-Suite, die diese Fallstricke umgeht und den Code in die Enge treibt?

**A. Orthogonale Beispiele (Den Raum aufspannen)**
Ein einzelnes I/O-Paar reicht niemals aus. Ein gutes Golden Dataset muss die Koordinaten der Domäne abstecken. Wir fügen ein zweites Beispiel hinzu: Input `3`, Output `6`. Plötzlich schlägt der trickreiche `return 4`-Code fehl. Der Agent wird gezwungen, die zugrundeliegende Struktur (`x * 2`) zu abstrahieren. Je orthogonaler (vielfältiger) die Datensätze sind (Happy Path, Randfälle, Null-Werte), desto schmaler wird der Korridor für fehlerhaften Code.

**B. Der Tipping Point (Das Upcasting zu PBT & FVT)**
Irgendwann erreicht jedes Projekt den Punkt, an dem statische Beispiele nicht mehr skalieren. Wenn du 50 verschiedene Markdown-Dateien handverlesen musst, um alle Regex-Kombinationen abzudecken, wird EBT vom Werkzeug zur Belastung. Das ist der "Tipping Point".

Hier offenbart die QA-Bench ihre wahre architektonische Stärke: **Wir nutzen EBT, um unsere Tests zu testen.**
Anstatt weitere statische Datensätze anzulegen, werfen wir unsere handverlesenen, verifizierten EBT-Beispiele nicht weg. Wir nutzen sie als Fundament (Ground Truth), um höhergradige Test-Regeln zu induzieren:

* Wir schreiben einen stochastischen Generator (Property-Based Testing - **PBT**), der zehntausende wilde Markdown-Dateien erzeugt. Ob dieser Generator richtig funktioniert, beweisen wir, indem wir prüfen, ob er unsere alten EBT-Beispiele korrekt reproduzieren kann.
* Wir definieren formale mathematische Gesetze für einen SMT-Solver (**FVT**). Ob diese Gesetze lückenlos sind, validieren wir gegen unsere hartcodierten EBT-Beispiele.

**Fazit:** EBT ist der Funke, der das Feuer entfacht. Es ist das Bootstrapping-Protokoll, mit dem wir die initiale Wahrheit des Systems empirisch festnageln, um von dort aus sicher in die unendlichen Möglichkeitsräume der stochastischen und formalen Verifikation aufzusteigen.

---

---

> **Hinweise:**
> * Die folgenden Skizzen sind ein erster Entwurf zur Realisierung der definierten Aussagen und könnten sich noch anpassen oder ausgetauscht werden.

---

### 1. Micro-Dynamik (In-Memory ohne Ballast)

Für reine Funktionen brauchen wir überhaupt kein `State`-Objekt. Wenn `pre` ein `tuple` oder `dict` ist, interpretiert QA-Bench das automatisch als `args` bzw. `kwargs`.

```python
# Shorthand für reine Funktionsaufrufe
EBT(target=my_func, pre=(1, 2), post=3)
EBT(target=my_func, pre={"x": 1, "y": 2}, post=3)
```

---

### 2. Meso-Dynamik (Datei-Transformationen & Seiteneffekte)

Hier kommt `State` ins Spiel, um **Funktions-Inputs** von **Dateisystem-Zuständen** sauber zu trennen:

```python
EBT(
    target="cleaner.py:my_func",
    venv="envs/qa_env", # Wo wird ausgeführt? (Arena, optional deklarierbar)
    
    # Vorbedingung (P)
    pre=State(
        args=["kalkuel.md"], # Die Argumente für my_func("kalkuel.md")
        fs={"fixtures/pre/kalkuel.md"} # Welche Dateien werden in die Sandbox kopiert?
    ),
    
    # Nachbedingung (Q)
    post=State(
        stdout="Erfolgreich bereinigt", # Optional: Konsolenausgabe prüfen
        fs={"fixtures/post/kalkuel.md"} # Welchem Soll-Zustand muss die Sandbox danach entsprechen?
    ), 
    
    tags=["optional"]
)
```

---

### 3. Macro-Dynamik (Ganze Ordner / Repositories)

Wenn wir ganze Verzeichnisse oder Refactorings prüfen, zeigt das `State`-Muster seine volle Stärke, bleibt aber schlank:

```python
EBT(
    target="agent.py:refactor_repo",
    
    pre=State(fs="fixtures/pre/project_x/"), # Copied in als Workspace-Root

    post=State(
        fs="fixtures/post/project_x/", # Byte-Vergleich des gesamten Ordners
        returns=True # Erwarteter Return-Wert des Agents
    ),
    
    tags=["optional"]
)

```

---

### 4. Convention vs. Configuration (Das Dictionary-Pattern)

Der bisher veranschaulichte Ansatz mit den `pre`- und `post`-Ordnern ist ein reiner Konventions-Ansatz (*Convention over Configuration*). Das ist extrem schlank, entwicklerfreundlich und reduziert Boilerplate-Code enorm.

Das Dictionary-Pattern hingegen ist ein reiner Konfigurations-Ansatz. Es beruht auf dem Paradigma der **Inversion of Control (IoC)** und gibt dir die absolute Kontrolle über die Dateisystem-Topologie.

> **💡 Wichtig: Hydration statt Symlinks** > Das Dictionary agiert hierbei *nicht* als intelligenter Symlink zum Host-System. QA-Bench nutzt diese Pfade für eine echte **Hydration**: Die Original-Datensätze (Ground-Truth) werden ausgelesen und physisch in die sterile Arena kopiert. Die Quelldateien bleiben stets unantastbar. Das erspart uns fehleranfällige Rollback-Zirkusse und garantiert, dass kein Testlauf jemals aus Versehen deine echten Testdaten manipuliert oder korrumpiert.

```python
EBT(
    target="main.py:my_func",
    venv="envs/qa_env",
    
    pre=State(
        args=["--process"], # Das Argument, das die Funktion bekommt
        fs={
            "/etc/app/config.yaml": "tests/pre/1_config.yaml",
            "./data/pre.csv":     "tests/pre/1_input.csv"
        } # Mirror: Arena-Pfad ← Host-Dataset (Echte Kopie)
    ),
    
    post=State(
        fs={
            "/etc/app/config.yaml": "tests/post/1_config.yaml", 
            "./data/pre.csv":     "tests/post/1_input.csv"
        } # Assert: Erwarteter Endzustand in der Arena ← Post-Dataset
    )
)

```

Das Dictionary-Mapping `{"Pfad_in_der_Arena": "Pfad_auf_dem_Host"}` wird genau dann zur Pflicht, wenn die Struktur deiner Testdaten auf der Festplatte (Host) **nicht** mit der Struktur übereinstimmt, die der Code (Target) während der Ausführung in der Sandbox (Arena) zwingend erwartet.

* **Topologische Entkopplung (Hardcodes im Code):**
Stell dir vor, du testest einen Legacy-Service, der hartcodiert erwartet, dass eine Konfigurationsdatei exakt unter `/etc/app/config.yaml` oder relativ im Pfad `./data/input.csv` liegt.
Mit einer simplen Namenskonvention (wie `1_config.yaml` im Root-Verzeichnis) würde der Test scheitern, weil der Code am falschen Ort sucht. Das Dictionary löst das elegant: Die Datei heißt auf deinem Rechner anders und liegt bequem und sortiert in deinem Test-Ordner, wird aber zur Laufzeit exakt unter ihrem vom Code erwarteten Pfad in die Arena projiziert.