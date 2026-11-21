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

---

Ich bin kein Experte hier. Ich habe den Bug selbst noch garnicht erlebt. Es wäre gut, wenn wir dafür sorgen könnten, dass unsere Entscheidungen es uns später leichter machen die CI-Matrix für Windows reaktivieren zu können. Bitte treffe auf Basis der @tests/tests_arena/ANALYSIS.md selber eine möglichst gute Entscheidung, welche es uns auch in der Zukunft einfacher macht das Projekt zu pflegen.

## Weiteres
@docs/dev/README.md
@docs/GUIDE_Quality-Assurance.md
@tests/tests_arena/ANALYSIS.md

## Auftrag

Lass uns das neue TGD-Muster mal in einem Komplett-Durchlauf austesten. Bitte orchestriere alle Schritte und dokumentiere am Ende den Verlauf unter @tests/tests_arena/TGD_1.md mit dem Provenance-Header aus CUBIE_DOC_FRAME_2.