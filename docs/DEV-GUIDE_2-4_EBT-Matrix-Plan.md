## 4. Entwicklungs-Phasen

Die Implementierung der Matrix erfolgt zielgerichtet anhand der definierten `Scenarios` und iteriert schrittweise durch die Skalierung der verschiedenen `Aspects`. Da die Komplexität innerhalb eines Steps nun direkt über die granularen Integer-Werte der Aspekte gesteuert wird, verschmilzt sie organisch mit den jeweiligen Sub-Phasen.

### Phase 1: Generierung und Prozessierung vom 1:1-Target
Entwicklung des grundlegenden Fundaments der automatisierten Szenarien-Generierung und des Wirings der EBTMatrix.

### Sub-Phase 1.1: Die EBTMatrix Engine (Lebenszyklus)

Die EBTMatrix adaptiert das Pipeline-Muster der regulären `EBT`-Klasse, operiert aber als Meta-Layer für Benchmarking.

* **`_arrange` (Generierung & Bereitstellung):**
  * Nimmt die `EBTMatrixConfig` entgegen.
  * Prüft, ob die für diese Konfiguration geforderten Testdaten (insbesondere Dateisystem-Topologien) bereits persistiert vorliegen.
  * Falls Daten fehlen, wird `build(config)` des Targets aufgerufen, um die physischen Artefakte und die `WorldState`-Listen zu generieren.
* **`_execute` (Testlauf via EBT-Delegation):**
  * Da die Matrix das Cubie-Framework validiert, baut sie intern eine native `EBT`-Instanz auf.
  * Sie injiziert das `MatrixTarget` in das `EBT.target` Attribut.
  * Sie reicht die generierten `WorldState`-Listen an `EBT.pre` und `EBT.post` weiter.
  * Parameter wie `EBT.MULTIPROCESSING` oder die isolierte Sandbox (`EBT.arena`) werden anhand der Matrix-Konfiguration deklariert.
  * Startet die Evaluation durch Aufruf von `ebt.run()`.
* **`_report` (Benchmarking & Konsolidierung):**
  * Konsumiert das retournierte, unveränderliche `RunTrace`-Objekt des `EBT`-Laufs.
  * Anstatt bloß `True` oder `False` auszuwerten, aggregiert die Matrix Metriken.
  * Formatiert diese Metriken mit dem MatrixReporter in einen standardisierten Benchmark-Report.

### Sub-Phase 1.2: Das 1:1-Target

Das 1:1-Target dient als Blaupause für die Datengenerierung. Es nimmt die `EBTMatrixConfig` entgegen und wandelt deren abstrakte Parameter (Aspects, Overhead) in physische Realität um.

* **Das Attribut `matrix_type`:** Wird strikt als `"1:1"` deklariert.
  * **Die `build()` Methode (Datengenerierung):**
  * Wertet die `Aspects` aus. Ist `memory=50`, generiert die Methode ein Dictionary oder eine Liste mit 50 komplexen Datenpunkten für die `args`/`kwargs`. Ist `filesystem=10`, werden 10 spezifische Zieldateien auf dem Host generiert.
  * Wertet den `Overhead` aus. Ist `fs=1000`, generiert der Builder zusätzlich 1.000 bedeutungslose Rausch-Dateien in der Sandbox.
  * Verpackt all dies abschließend in zwei Listen mit je exakt einem Element: `Tuple[[WorldState_Pre], [WorldState_Post]]`.
* **Die `target()` Methode (Transformation):**
  * Iteriert durch die erhaltenen Argumente, transformiert die Zieldateien präzise in den erwarteten Post-Zustand und ignoriert das künstlich generierte Overhead-Rauschen.

### Phase 2: Generierung und Prozessierung vom N:1-Target
Fokus auf den deterministischen Normalisierer (Allquantor). Deklaration über `Scenarios(n_to_one=X, one_to_n=1)`. Die `EBT`-Engine isoliert jeden der $X$ Ausführungs-Zustände. Das Target muss die Entropie eliminieren und am Ende immer exakt denselben Post-Zustand (Golden Master) generieren.
* **Sub-Phase 2.1: In-Memory-Transformation:** Auslastung über `Aspects(memory=X)`. Validierung, wie der Builder komplexe Datenstrukturen aufbaut und das Target diese Mengen iterativ über `args`/`kwargs` innerhalb eines Durchlaufs konsumiert.
* **Sub-Phase 2.2: FS-Transformation & Overhead:** Auslastung über `Aspects(filesystem=X)` und `Overhead(fs=Y)`. Der Builder generiert $X$ relevante Testdateien und injiziert zeitgleich $Y$ Rausch-Dateien in die Sandbox. Das Target muss die Ziel-Dateien präzise transformieren und das Rauschen ignorieren.
* **Sub-Phase 2.3: Arena-Transformation & Overhead:** Auslastung über `Aspects(environment=X)` und `Overhead(arena=Y)`. Manipulation von Abhängigkeiten unter messbarem Setup-Ballast durch den `ArenaBuilder`.
* **Sub-Phase 2.4: Kombinierte Aspekte:** Simultane Auslastung mehrerer Vektoren (z. B. Batch-Dateioperationen gesteuert durch überladene Argumenten-Ketten).

### Phase 3: Generierung und Prozessierung vom 1:N-Target

Fokus auf den deterministischen Generator (Existenzquantor). Deklaration über `Scenarios(n_to_one=1, one_to_n=X)`. Das Target generiert kontrollierte Entropie, und der Testlauf leuchtet grün, wenn das generierte Resultat mit einem der $X$ deklarierten Zielzustände übereinstimmt.
* **Sub-Phase 3.1: In-Memory-Transformation:** Konstante Eingaben, die zu einer von $X$ möglichen funktionalen Rückgaben (`returns`) führen.
* **Sub-Phase 3.2: FS-Transformation & Overhead:** Auslastung der Dateisystem-Validierung. Das Target generiert aus statischen Eingaben abweichende, aber valide Festplatten-Topologien, während das Framework diese gegen $X$ mögliche Post-Szenarien diffen muss.
* **Sub-Phase 3.3: Arena-Transformation & Overhead:** Generierung validierter, abweichender Umgebungszustände.
* **Sub-Phase 3.4: Kombinierte Aspekte:** Validierung komplexer, mehrdimensionaler Lösungsräume.

### Phase 4: Generierung und Prozessierung vom N:N-Target

Fokus auf den hybriden Prozessor. Entsteht implizit durch die Deklaration von `Scenarios(n_to_one=X, one_to_n=Y)`.
* **Sub-Phase 4.1 bis 4.4:** Analoger Durchstich durch die Aspekte. Das Target muss eine logische Iteration bewältigen: Die Normalisierung der $X$ Vorbedingungen paart sich mit einer kontrollierten Generierung in $Y$ erlaubte Nachbedingungen. Dies testet die iterative Kaskadierung der Engine, da für jedes Pre-Objekt eine Validierungs-Schleife gegen alle Post-Zustände laufen muss.