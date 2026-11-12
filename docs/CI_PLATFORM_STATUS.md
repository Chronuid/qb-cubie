# CI Plattform- und Kompatibilitätsstatus

Dieses Dokument erfasst den aktuellen Plattformsupport in der Continuous Integration (GitHub Actions) von `qb-cubie` sowie den Hintergrund zu vorübergehend eingefrorenen Plattform-Checks.

---

## 1. Übersicht der CI-Matrix

| Plattform / Runner | Python 3.13 | Python 3.14 | Status | Scope |
| :--- | :---: | :---: | :---: | :--- |
| **Linux** (`ubuntu-24.04`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv)** | Wheel-Prüfung + Vollständige Repository-Testsuite + provisionierte Test-Arenen |
| **macOS** (`macos-15`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv)** | Wheel-Prüfung in isolierter Testumgebung (Core + Linter) |
| **Windows** (`windows-2022`) | ⏸️ Eingefroren | ⏸️ Eingefroren | **Vorübergehend eingefroren** | Aus CI-Matrix ausgeklammert (Details siehe unten) |

---

## 2. Dokumentation der Windows-CI-Befunde (`windows-2022`)

Die GitHub Actions Checks für Windows (`CI / Wheel / windows-2022 / Python 3.13` und `3.14`) schlugen nach ca. 1 Minute fehl.

### Ursachenanalyse:
1. **Verzeichnisstruktur und native Launcher (`.exe`):**
   - Auf Windows liegen Interpreter und Skripte unter `Scripts/` statt `bin/`.
   - Venvs auf Windows verwenden kompilierte Wrapper-Binärdateien (`.exe`) anstelle von POSIX-Shebang-Skripten.
   - Gemäß [Arena-Handbuch](GUIDE_Arena-Management.md#pyvenv-kopierte-virtuelle-umgebung) (Zeile 56) sind *native Windows-Konsolenlauncher derzeit nicht unterstützt*. `PyVenv.setup()` ist primär auf POSIX-Skripte und Trampoline ausgelegt.
2. **Subprozess-Umgebung und `PATH`-Isolation:**
   - [check_wheel.py](../scripts/check_wheel.py) und `PyVenv` isolieren Kindprozess-Umgebungen streng (`PATH` wird auf den Interpreter-Pfad begrenzt).
   - Unter Windows erfordert die C-Laufzeitumgebung und Netzwerk-I/O zwingend Zugriff auf Systembibliotheken in `C:\Windows\System32` (z. B. `vcruntime140.dll`, `kernel32.dll`, `ws2_32.dll`). Ein strikt bereinigter `PATH` führt unter Windows zu Ausführungsfehlern oder Deadlocks im Testtreiber.
3. **POSIX-Prozessgrenzen:**
   - Prozessgruppen, Signalweiterleitung und Ressourcenlimits (`resource`-Modul) basieren auf POSIX-Standards. Windows erfordert stattdessen Win32-Job-Objects.

---

## 3. Temporäre Einfrierung

Um einen stabilen, 100 % grünen CI-Zustand für das Release **v0.0.3** sicherzustellen, wurde `windows-2022` vorübergehend aus der aktiven Matrix in `.github/workflows/ci.yml` entfernt:

- **Linux und macOS** decken POSIX-Umgebungen unter Python 3.13 und Python 3.14 vollständig ab.
- Die Python 3.14-Kompatibilität (einschließlich des neuen `𝜋thon`-Launchers) wurde erfolgreich verifiziert.

---

## 4. Roadmap zur Reaktivierung von Windows

Für ein zukünftiges Release sind folgende Schritte für nativen Windows-Support geplant:
1. Anpassung der `PATH`-Bereinigung in `check_wheel.py` und `qb_cubie.arenas._env`, sodass `System32` und `%SystemRoot%` auf Windows-Systemen erhalten bleiben.
2. Erkennung der Windows-Venv-Struktur (`Scripts/python.exe`) bei Arena-Kopien.
3. Fallback auf `sys.executable -m ...` anstelle von nativer Launcher-Relokation für Konsolenskripte unter Windows.
4. Reaktivierung von `windows-2022` in der GitHub Actions Matrix.
