## `class EBT`
Die `EBT`-Klasse ist die zentrale Orchestrierungs-Engine des Frameworks. 
Die Klasse selbst agiert dabei als direktes Interface für die Definition der Test-Fälle.

**Kern-Verantwortlichkeiten:**

* **Auto-Inferenz:**
Um die Entwickler-Erfahrung (DX) schlank zu halten und Boilerplate-Code zu minimieren, fungiert die Klasse als intelligenter Übersetzer. Sie nimmt Datentypen entgegen und konvertiert diese implizit in vollumfängliche, standardisierte `WorldState`-Objekte.

* **Erweiterte Formallogische Engine (Quantoren-Auflösung):**
Die Klasse steuert den iterativen Prüfprozess für komplexe Lösungsräume.

* Werden Vorbedingungen (`pre`) als WorldState-Listen übergeben, wendet die Klasse deterministisch das Prinzip des beschränkten Allquantors ($\forall$) an, führt jeden Zustand isoliert aus und verknüpft die Assertions mit einem logischen UND.

* Werden Nachbedingungen (`post`) als WorldState-Listen übergeben, schaltet die Engine auf das Prinzip des beschränkten Existenzquantors ($\exists$) um und bewertet den Test als bestanden (ODER-Verknüpfung), sobald der Output mit einem Element der Zielmenge übereinstimmt.

---

### `EBT.arena`

Das Attribut `arena` definiert den isolierten Ausführungsraum (die Sandbox), in dem das Programmsegment ($S$ bzw. das Target) operiert. 

**Kaskadierung und Override-Mechanismus:**

Die Arena kann sowohl global auf der `EBT`-Ebene (als Parameter der Klasse) als auch innerhalb der `WorldState`-Objekte von `pre` und `post` definiert werden. Hierbei greift eine klare Vererbungs- und Override-Logik:

1. **Globale Definition (Konstanter Raum):** Wird die Arena auf Ebene der `EBT`-Klasse definiert, dient sie als konstanter, unveränderlicher Ausführungsraum für die gesamte Transformation. Die Testausführung findet vollständig innerhalb dieser einen Welt statt.

2. **Lokaler Override (Umgebungs-Mutationen):** Die globale Arena kann auf `WorldState`-Ebene überschrieben werden. Dies sollte nicht genutzt werden, um bestimmte Eingaben (Edge-Cases) künstlich zu erleichtern, sondern ist für Szenarien gedacht, in denen das Target die explizite Aufgabe hat, die Umgebung selbst zu verändern.

3. **Lebenszyklus und Assertion:**
   * Definiert der `pre`-State lokal eine Arena, gilt diese **implizit** auch für den `post`-State, da der Raum während einer normalen Ausführung konstant bleiben muss.
   * Wird jedoch eine Arena in `pre` deklariert (z. B. `envs/pre_env`) und eine *abweichende* Arena explizit in `post` deklariert (z. B. `envs/post_env`), wechselt die Semantik der Arena von einem Ausführungsort zu einer Assertion. Das Framework validiert dann, ob die Umgebung durch die Ausführung des Targets korrekt in den neuen Ziel-Zustand mutiert wurde.

---

### `EBT.target`

Das Attribut `target` repräsentiert das auszuführende Programmsegment ($S$), welches die Transformation von der Vorbedingung ($P$) zur Nachbedingung ($Q$) vornimmt. Um maximale Flexibilität in der Testdefinition zu gewährleisten, unterstützt dieses Attribut ein polymorphes Interface und akzeptiert zwei unterschiedliche Deklarations-Wege:

1. **Direkte Callables:**
Python-Funktionen oder -Klassen können wie gewohnt in das Testmodul importiert und als direkte Referenz (z. B. `target=my_func`) übergeben werden.


#### Für die spätere Roadmap:
2. **String-Referenzen (Target-Grammatik):**
Alternativ kann das Target als String definiert werden, um Abhängigkeiten in den Test-Dateien zu reduzieren. Die Grammatik folgt hierbei dem Muster `"Dateiname:Funktionsname"` (z. B. `"main.py:my_func"` oder `"agent.py:refactor_repo"`).


3. **Implizite Root-Auflösung:**
Wenn das Target als String-Referenz übergeben wird, benötigt das Framework einen deterministischen Ausgangspunkt, um die referenzierte Datei zu finden und den Code dynamisch aufzulösen. Hierbei greift folgende Konvention zur Bestimmung des Root-Verzeichnisses:
   * **Standard-Verhalten:** Das Root-Verzeichnis des gesamten Repositories fungiert als Basis für die Target-Suche.
   * **`src`-Override:** Existiert innerhalb des Repositories ein direkt auffindbarer `src`-Ordner, überschreibt dieser die Standard-Konvention. In diesem Fall gilt ausschließlich der `src`-Ordner als Root-Verzeichnis, von dem aus die Pfade der String-Definitionen evaluiert werden.

---

### EBT-Zustandsattribute: `EBT.pre` und `EBT.post`

* **Zustands-Attribute (Gemeinsamkeiten & Mechanik):**
Die Attribute `pre` und `post` bilden das Fundament des Hoare-Tripels $\{P\}S\{Q\}$ und definieren die exakten Welten vor und nach der Ausführung. Beide Attribute sind polymorph aufgebaut und setzen die Shorthand-Muster um, um reine Funktionen völlig ohne Ballast testen zu können. Werden Listen übergeben, spannen sie erweiterte Mengen-Mappings (Quantoren) auf. Für komplexe Anforderungen, die über reine I/O-Werte hinausgehen, verweisen beide Attribute konzeptionell auf die `WorldState`-Klasse, in welche alle Shorthands unter der Haube ohnehin implizit gecastet werden.


  * **`EBT.pre` (Die Vorbedingung / $P$):**
  Dieses Attribut definiert den geforderten Eingangs-Zustand *vor* der Ausführung.
      * **Shorthand-Inferenz:** Wird `pre` direkt als primitiver Datentyp übergeben, greift das automatische Casting. Ein `tuple` wird konventionell als `args` interpretiert, ein `dict` automatisch als `kwargs`. 
        * Da pre den Funktionsaufruf vorbereitet, mappt die Engine jeden primitiven Datentyp auf die Eingangsparameter. Wird ein einzelner Parameter (z.B. pre=5 oder pre="input.txt") übergeben, wird dieser implizit als Argument (args) deklariert. Ein übergebenes tuple mappt direkt auf args, ein dict auf kwargs.
      * **Die $P$-Menge (Der beschränkte Allquantor $\forall$):** Wird `pre` als WorldState-Liste übergeben, iteriert das System deterministisch über diese Menge ($N:1$ Mapping).
      * **WorldState-Referenz:** Für alles, was über primitive Argumente hinausgeht – insbesondere wenn Dateien (`fs`) in die Sandbox kopiert werden müssen –, wird ein explizites `WorldState`-Objekt an `pre` übergeben.


  * **`EBT.post` (Die Nachbedingung / $Q$):**
  Dieses Attribut definiert wie die Welt *nach* der Ausführung exakt aussehen muss.
    * **Shorthand-Inferenz:** Wird `post` als primitiver Datentyp (z. B. `int` oder `str`) übergeben, wird dies vom System implizit als erwarteter funktionaler Rückgabewert (`returns`) ausgewertet.
      * Da post das Resultat auswertet, mappt die Engine primitive Datentypen nicht auf Argumente, sondern auf Rückgabewerte. Wird ein einzelner Parameter (z.B. post=5 oder post=True) übergeben, wird dieser pauschal in das returns-Attribut des WorldState-Objekts konvertiert.
    * **Die $Q$-Menge (Der beschränkte Existenzquantor $\exists$):** Wird `post` als WorldState-Liste übergeben, definiert es einen validen Lösungsraum ($1:N$ Mapping). Der Test leuchtet grün, wenn das Ergebnis mit mindestens einem Element der Menge übereinstimmt.
    * **WorldState-Referenz:** Für topologische Assertions, bei denen beispielsweise mutierte Dateisystem-Strukturen (`fs`) oder Konsolen-Ausgaben validiert werden müssen, wird ein explizites `WorldState`-Objekt an `post` übergeben.