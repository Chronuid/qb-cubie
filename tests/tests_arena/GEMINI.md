# Reperatur von BUG-001

### [BUG-001] `PyVenv` verändert Testdaten durch eigene IPC-Dateien im Workspace

- **Status:** Offen *(Gutachten-Befund B1, P1)*
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/arenas/pyvenv.py` (`setup`, `_setup_ipc_files`, `_teardown_ipc_files`)
- **Umgebung / Version:** reproduziert ab `v0.0.3`, unverändert in `v0.0.9` (Linux, Python 3.13)

**Ist-Verhalten:**  
`PyVenv` legt seine Austauschdateien (`ipc_in<suffix>`, `ipc_out<suffix>`), das Hilfsmodul `_cubie_phantom.py` sowie `.venv/` direkt im geprüften `workspace_path` ab. Dadurch teilen sich Infrastruktur und Testdaten denselben Namensraum:
1. Eine über `pre.fs` bereitgestellte `ipc_in.<suffix>` wird vor dem Target-Aufruf still durch die IPC-Nutzlast überschrieben.
2. Eine über `pre.fs` bereitgestellte `ipc_out.<suffix>` wird nach der Ausführung durch `_teardown_ipc_files()` gelöscht.
3. Vollständige Workspace-Vergleiche (z. B. gegen ein leeres Referenzverzeichnis) schlagen durch `.venv/` und `_cubie_phantom.py` fehl.

**Soll-Verhalten:**  
Infrastrukturdateien (`ipc_in`, `ipc_out`, `_cubie_phantom.py`, `.venv`) liegen getrennt vom fachlichen Arbeitsbereich (analog zu den IPC-Dateien in `TempFS`). Bereitgestellte Testdaten werden weder überschrieben noch gelöscht.

**Reproduktion:**  
EBT-Vertrag mit `PyVenv` und `PickleCodec` ausführen, bei dem `pre.fs` eine Datei `ipc_in.pkl` (z. B. 3 Bytes) oder `ipc_out.pkl` bereitstellt: `os.path.getsize("ipc_in.pkl")` beobachtet die serialisierte IPC-Nutzlast statt 3 Bytes; `ipc_out.pkl` fehlt beim anschließenden Dateivergleich (`Path not found. Arena: False, Host: True`).

**Workaround:**  
In `PyVenv`-Tests keine Dateien namens `ipc_in.*`, `ipc_out.*` oder `_cubie_phantom.py` im Workspace-Root ablegen und Dateivergleiche auf fachliche Unterverzeichnisse eingrenzen.

**Hinweise / Ursache:**  
Quelle: [`GUTACHTEN.md` (§ 6.1, B1)](./GUTACHTEN.md#61-b1-pyvenv-verändert-testdaten-durch-eigene-ipc-dateien).  
Empfohlene Korrektur: IPC-Dateien, Hilfsmodule und `.venv` außerhalb des geprüften Workspace führen und Namenskollisionen sowie vollständige Verzeichnisvergleiche durch Regressionstests absichern.

## Weiteres

@docs/dev/README.md 

### **Dein Bericht**: 

@tests/tests_arena/ANALYSIS.md

### **Im Bericht**:
Halte dich grob an die Konvention mit dem Provenance-Kopf im Header des Dokuments:
```text
    <!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Neon" effort="High" -->
    # Analysis: Reperatur vom Cubie-Core
    
    **Dokument-Informationen & Herkunft:**
    - **Plattform / Umgebung:** Antigravity-CLI
    - **Modell:** Gemini-4-Neon
    - **Reasoning-Effort:** High
    - **Analysedatum:** 20. November 2026, ~ 10:30 (CET)
    - **Synthesebasis:** # Das hier musst du noch ausfüllen.
    - **Stand**: qb-cubie (v0.0.8) 
    - **Git-Log**: #`git log -n 1`
    ```text
    commit cf621be1e70df8fd4b248f084601af9ee99b2478 (HEAD -> main, origin/main)
    Author: Chronuid <Dominickwirzba@gmail.com>
    Date:   Fri Nov 20 09:19:54 2026 +0100
    
        Wrote down another bug.
    ``` 

--- # Trennlinie

--- # Trennlinie

<!-- /qb:frame -->

# Hier packst du deine Analyse rein.
```