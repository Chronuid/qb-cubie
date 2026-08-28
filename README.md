> # Cubie
> Your Quality-Bench

---

Cubie ist ein kompromissloses Framework für strukturierte Qualitätssicherung. Es behandelt Code nicht als etwas, das geschrieben wird, sondern als etwas, das im unendlichen Suchraum aller Möglichkeiten ($\Sigma^*$) gefunden werden muss. Cubie liefert die Werkzeuge, um diesen Lösungsraum durch explizite Code-Verträge und orthogonale Datenpunkte so weit einzuengen, bis nur noch die korrekte Funktion überlebt.

---
## 🚀 Quickstart

Installiere das Framework via pip:

```bash
pip install cubie
```

In deinem Code nutzt du das etablierte, zweistellige Shorthand für maximalen Flow ohne Boilerplate:

```python
import cubie as qb
from my_module import calculate_tax

# Ein simpler EBT-Vertrag
def test_01(): qb.EBT(target=calculate_tax, pre=(100, 19), post=119).run
```

Lasse deinen Source-Code scannen und die Blaupausen der gesamten Testsuite vorbereiten!
Terminal: `qb build testsuite`

---

## 🧠 Core Concepts & API

Cubie verzichtet auf überladene Framework-Magie und erzwingt eine saubere, entkoppelte Architektur basierend auf fundamentaler Prädikatenlogik.

### 1. Review-Based Testing (RBT)

Für das Bootstrapping und Anforderungen, die sich harten mathematischen Assertions entziehen, bietet Cubie das RBT. Der Test-Lebenszyklus friert die Ausführung ein und delegiert die Verifikation an einen injizierten Reviewer.
Das kann der Entwickler am Terminal sein (Human-in-the-loop) oder ein vollautomatisierter Agent, der das resultierende `ReviewData`-Objekt befüllt.

```python
qb.RBT(
    target="auth_module.py",
    check="Wird das Passwort niemals im Klartext geloggt?"
    ).run

```

### 2. Example-Based Testing (EBT) & Der WorldState

Das Herzstück bildet das EBT, basierend auf dem klassischen Hoare-Tripel $\{P\}S\{Q\}$. Du definierst die Vorbedingung (`pre`) und die exakt geforderte Nachbedingung (`post`).
Egal ob du simple Integers, Dictionaries, ganze Dateisystem-Pfade oder Workspaces übergibst – Cubie inferiert diese Shorthands implizit in standardisierte `WorldState`-Objekte.


### 1.1. In-Memory ohne Ballast

Für reine Funktionen müssen wir überhaupt kein `WorldState`-Objekt definieren. Wenn `pre` ein `tuple` oder `dict` ist, interpretiert Cubie das konventionell automatisch als `args` bzw. `kwargs` eines WorldState-Objekts.

```python
# Shorthand für reine Funktionsaufrufe
def test_1(): EBT(target=my_func, pre=(1, 2), post=3).run()
def test_2(): EBT(target=my_func, pre={"x": 1, "y": 2}, post=3).run()
def test_3(): EBT(target=my_func, pre={"x": 6}, post=31, arena="envs/custom_env_1").run()
```

### 1.2. Datei-Transformationen & Seiteneffekte

Hier kommt die Definition von `WorldState` ins Spiel, um **Funktions-Inputs** von **Dateisystem-Zuständen** sauber zu trennen:

```python
def test_4(): 
    EBT(target="cleaner.py:my_func",
        
        # Vorbedingung (P)
        pre=WorldState(
            args=["kalkuel.md"], # Die Argumente für my_func("kalkuel.md")
            fs={"fixtures/pre/kalkuel.md"} # Welche Dateien werden in die Sandbox kopiert?
        ),
        
        # Nachbedingung (Q)
        post=WorldState(
            returns="Erfolgreich bereinigt", # Optional: Konsolenausgabe prüfen
            fs={"fixtures/post/kalkuel.md"} # Welchem Soll-Zustand muss die Sandbox danach entsprechen?
        ), 
        
        tags=["optional"]
    ).run()
```

---

---

Die drei Test-Paradigmen **Example-Based Testing (EBT)**, **Review-Based Testing (RBT)** und **Erweitertes Property-Based Testing (ePBT)** bilden das kompromisslose Spektrum der Qualitätssicherung im Cubie-Framework. Sie dienen dazu, den unendlichen Suchraum aller denkbaren Algorithmen (\\(\Sigma^*\\)) präzise zu filtern, unterscheiden sich jedoch grundlegend in ihrer logischen Ebene, ihrem Anwendungszweck und ihrer methodischen Ausführung.

---

### 1. Example-Based Testing (EBT): Die deterministische Basis

*   **Logische Fundierung:** Bewegt sich in der **Prädikatenlogik erster Stufe (First-Order Logic - FOL)**. Ein einzelner Testfall basiert quantorenfrei auf der reinen Aussagenlogik (sogenannte „Ground Terms“).
*   **Kernidee und Anwendung:** EBT ist das unbestechliche Fundament zur Definition von **„Golden Masters“ (deterministischen Realitäten)**. Es skaliert fraktal von simplen In-Memory-Funktionen (Ebene 1) über isolierte Dateitransformationen (Ebene 2, z. B. der „MD-Cleaner“) bis hin zur Prüfung ganzer Repository-Strukturen (Ebene 3).
*   **Funktionsweise:** Es basiert auf dem klassischen **Hoare-Tripel \\(\{P\} S \{Q\}\\)**. Hierbei werden die Zustände der Welt vor (\\(P\\)) und nach (\\(Q\\)) der Ausführung des Programms (\\(S\\)) als passive, eingefrorene `WorldState`-Objekte deklariert. Wie die interne Code-Logik im Detail abläuft, wird als Blackbox behandelt (es ist uns egal, „wie der Strom fließt“).
*   **Mengen-Mappings (Quantoren):** EBT nutzt Python-Listen, um logische Quantoren innerhalb einer Testinstanz abzubilden:
    *   **Der beschränkte Allquantor (\\(\forall\\)) (N:1-Mapping):** Mehrere chaotische oder unstrukturierte Eingangszustände werden deterministisch auf exakt denselben, normierten Zielzustand überführt (z. B. Datumsnormalisierung).
    *   **Der beschränkte Existenzquantor (\\(\exists\\)) (1:N-Mapping):** Ein diskreter Input mappt auf eine erlaubte Zielmenge. Der Test leuchtet grün, sobald das Ergebnis mit mindestens einem Element der Menge übereinstimmt (z. B. Zufallsgeneratoren oder stochastische Load-Balancer).
*   **Herausforderung:** Eine einzelne EBT-Instanz leidet unter **Unterspezifikation** – ein trivialer, fehlerhafter Code (z. B. `return 4` statt einer echten Verdopplung) kann den Test bestehen. Die Lösung liegt im Aufspannen des Raumes durch **orthogonale (unabhängige) EBT-Instanzen** in der Testsuite. Die gesamte Testsuite agiert dann als übergeordneter Allquantor, der über alle definierten Testfälle iteriert.

---

### 2. Review-Based Testing (RBT): Die qualitative Brücke

*   **Logische Fundierung:** Konzeptionell die Schnittmenge aus **allen Testverfahren (Any)** und den Fähigkeiten des jeweiligen **Reviewers**. RBT lässt sich nicht in ein rein formales System pressen.
*   **Kernidee und Anwendung:** Es dient als Brücke zwischen dem unendlichen Suchraum und dem automatisierten Testsystem. RBT ist das ideale Werkzeug für das **Bootstrapping** in frühen Projektphasen sowie für qualitative und subjektive Anforderungen (z. B. UI-Stil, Tonfall), die sich harten mathematischen Assertions entziehen.
*   **Funktionsweise:** BDas Framework pfuscht nicht im Capturing von Pytest herum. Wenn ein RBT-Knoten erreicht wird, ruft der Test den HumanReviewer auf und blockiert einfach (wartet synchron). Der „Reviewer“ erhält die Prüfregel („Check“) und das Zielobjekt („Target“) präsentiert und muss eine binäre Entscheidung (passed: y/n) sowie optional einen schriftlichen Bericht abgeben.
*   **Dependency Injection:** RBT arbeitet standardmäßig mit einem menschlichen Tester am Terminal (`HumanReviewer`). Über das Reviewer-Protokoll und den standardisierten `ReviewData`-Vertrag kann dieser jedoch mühelos gegen einen **automatisierten KI- bzw. LLM-Agenten** ausgetauscht werden, der komplexe Prüfungen vornimmt und strukturierte Metadaten im offenen Report-Dictionary ablegt.

---

### 3. Erweitertes Property-Based Testing (ePBT): Das universelle Gesetz

*   **Logische Fundierung:** Bewegt sich in der **Logik höherer Stufe (Higher-Order Logic - HOL)**, da über Eigenschaften und Quantoren selbst quantifiziert wird.
*   **Kernidee und Anwendung:** ePBT löst sich von der historisch engen Verbindung zum reinen „Fuzzing“. Es ist die ebenenübergreifende Deklaration und automatisierte Verifikation allgemeingültiger Segment-Eigenschaften (Invarianten).
*   **Die 4 Säulen des ePBT:** Es vereint ehemals isolierte Werkzeuge als integrierte Kette von Ausführungs-Engines für dieselbe formale Aufgabe:
    1.  **Strukturelles PBT (Typing-Protokolle):** Formuliert statische Verträge vor der Laufzeit (z. B. Duck-Typing-Interfaces via Mypy), bei denen der Type-Checker als Beweismaschine den abstrakten Syntaxbaum (AST) verifiziert.
    2.  **Meta-PBT (Linter & AST-Queries):** Prüft architektonische Invarianten wie Namespace-Grenzen oder maximale Komplexität.
    3.  **Laufzeit-PBT (Design by Contract - DbC):** Erzwingt Vor- und Nachbedingungen direkt live in der Produktionsumgebung bei jedem realen Funktionsaufruf.
    4.  **Grenzbereich-PBT (Data Generation / Fuzzing):** Flutet das System stochastisch mit extremen Randwerten, um das dynamische Verhalten der Geschäftslogik gegen die deklarierte Invariante zu prüfen. ePBT stellt klar: Fuzzing ist nicht PBT selbst, sondern nur dessen stochastische Ausführungs-Engine.
*   **Erkenntnistheoretischer Status (Karl Popper):** ePBT-Definitionen deklarieren universelle Gesetze auf einer Meta-Ebene, die in deterministische EBT-Fakten herunterkompiliert werden (HOL \\(\to\\) EBT). Ein PBT-Generator ist jedoch selbst nur eine **Hypothese**. Schlägt ein PBT-Test fehl, kann auch die PBT-Definition fehlerhaft oder zu scharf gestellt sein. Daher besitzt ePBT eine **niedrigere Autorität** als das auf harten Fakten basierende EBT. Das Framework empfiehlt, PBT-Funde stets als Vorschläge für neue deterministische EBT-Edge-Cases zu interpretieren.

---

### Zusammenfassung der Unterschiede im Überblick

| Kriterium | Example-Based Testing (EBT) | Review-Based Testing (RBT)                                                   | Erweitertes Property-Based Testing (ePBT) |
| :--- | :--- |:-----------------------------------------------------------------------------| :--- |
| **Logische Ebene** | Prädikatenlogik 1. Stufe (FOL) & Aussagenlogik | Schnittmenge aus allen Testarten und dem Prüfverfahren                       | Logik höherer Stufe (HOL) |
| **Primärer Fokus** | Deterministische Transformationen, „Golden Masters“ | Qualitative, subjektive Kriterien & Bootstrapping                            | Deklaration universeller Gesetze & Systeminvarianten |
| **Zustandserfassung** | Passive, eingefrorene `WorldState`-Objekte | Dynamische Übergabe des Ergebnisses an den Testlauf via `ReviewData`-Vertrag | Statische & dynamische Kette aus 4 integrierten Säulen |
| **Verifikations-Art** | Exakter Byte-für-Byte-Abgleich oder logisches Mengen-Mapping | Menschliches y/n-Urteil oder semantische KI-Evaluation                       | Statische Syntaxbaum-Beweise & stochastische Flutung (Fuzzing) |
| **Autoritätsstufe** | Absolute Fakten-Autorität (Ground Truth) | Explorative / subjektive Brücke                                              | Hypothese (muss durch EBT verifiziert werden) |