# Erfahrungsbericht: Sandbox-Inkompatibilitäten

**Datum:** 9. November 2026  
**Anlass:** Regressionstests und Implementierung des Rückgabe-Sentinels aus `GUTACHTEN.md`, Abschnitt 8, Priorität 1.1.

## Rahmenbedingungen

Die Arbeiten liefen unter Linux mit Python 3.13 in einer Agent-Sandbox. Schreibzugriffe waren auf das Projektverzeichnis und temporäre Verzeichnisse begrenzt; Netzwerkzugriffe waren eingeschränkt. Für `.git` bestand lediglich Lesezugriff. Eine Ausführung außerhalb der Sandbox erforderte eine Freigabe.

Diese Agent-Sandbox ist von Cubies Arenen `TempFS` und `PyVenv` zu unterscheiden: Die Arenen organisieren Arbeitsverzeichnisse und Python-Umgebungen, heben aber Einschränkungen der übergeordneten Ausführungsumgebung nicht auf.

Der Bericht beruht auf den während dieser Arbeit beobachteten Werkzeugausgaben. Die Sandbox-Konfiguration auf Kernel-Ebene wurde nicht untersucht. Die folgenden Hypothesen sind deshalb keine nachgewiesenen Ursachen.

## 1. Paketinstallation innerhalb eines Arena-Tests

**Betroffener Test:** `tests/tests_ebt/test_ebt_ignores.py::test_empty_arena_ignores_red`

Beim Lauf der EBT- und Reporter-Tests bestanden 109 Tests; dieser eine Test scheiterte. Sein Target installiert `cowsay` über `uv pip install` in einer temporären PyVenv-Arena. Beobachtet wurde ein `RuntimeError` mit einem eingebetteten `CalledProcessError` und Exitcode 2 des Installationsprozesses. Damit scheiterte die Ausführung vor dem vorgesehenen Zustandsvergleich. `expect=False` erwartet einen negativen Vertragsvergleich und fängt diesen Infrastrukturfehler nicht ab.

Die gezielte Wiederholung außerhalb der Sandbox bestand ohne Änderung am Test oder Produktionscode:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/tests_ebt/test_ebt_ignores.py::test_empty_arena_ignores_red -q --tb=short
```

**Ursachenhypothesen:**

- Die Netzwerkbeschränkung könnte einen erforderlichen Zugriff auf einen Paketindex oder Download verhindert haben.
- `uv` könnte einen Cache oder ein anderes Verzeichnis außerhalb der erlaubten Schreibbereiche benötigt haben.
- Lokale Cache-Zustände könnten beeinflussen, ob überhaupt ein Netzwerkzugriff erforderlich ist.

Der angezeigte Fehler enthielt keine ausreichende `uv`-Diagnose, um diese Möglichkeiten zu unterscheiden. Der erfolgreiche Wiederholungslauf spricht für eine Umgebungsabhängigkeit, beweist aber keine bestimmte Ursache: Zwischen zwei Läufen können sich auch Cache- oder Netzwerkzustände ändern.

## 2. Multiprocessing-Manager kann seinen Socket nicht initialisieren

**Betroffene Fälle:** `tests/tests_multiprocessors/test_mp_tempfs_isolation.py::test_overlapping_processes_isolate_relative_io_and_host_cwd`, jeweils für `pickle` und `loky`.

Der zusätzliche Lauf mit Rückgabe-, Multiprocessing-, Offline- und Codec-Tests ergab **262 bestanden, 2 fehlgeschlagen und 10 übersprungen**. Beide Fehler entstanden beim Start von `multiprocessing.get_context("spawn").Manager()`, bevor die eigentliche EBT-Ausführung begann.

Der Manager-Kindprozess scheiterte in `multiprocessing.connection.SocketListener` beim Aufruf:

```python
self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```

Die unmittelbare Ausnahme war `PermissionError: [Errno 1] Operation not permitted`. Im Elternprozess erschien anschließend `EOFError`, weil der gestartete Manager keine Adresse mehr über die Verbindung lieferte. Der `EOFError` ist hier ein Folgefehler; die aussagekräftige Diagnose stand in stderr des Kindprozesses.

Beide Fälle bestanden außerhalb der Sandbox ohne Codeänderung:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/tests_multiprocessors/test_mp_tempfs_isolation.py::test_overlapping_processes_isolate_relative_io_and_host_cwd \
  -q --tb=short
```

**Ursachenhypothesen:**

- Eine Sandbox-Regel könnte Socket-Operationen oder konkret `setsockopt` einschränken. Ein Syscall-Filter wie Seccomp wäre ein möglicher Mechanismus, wurde aber nicht nachgewiesen.
- Die Beschränkung könnte auch lokale IPC betreffen. Aus dem Fehler folgt nicht, dass der Test eine externe Netzwerkverbindung herstellen wollte.
- Da beide Backends am selben Manager-Aufbau scheiterten, liegt eine gemeinsame Infrastrukturabhängigkeit näher als ein unabhängiger Defekt beider Backends.

Andere Multiprocessing-Tests bestanden in derselben Sandbox. Der Befund belegt daher keine generelle Unmöglichkeit von Unterprozessen oder paralleler Ausführung.

## 3. Git-Rücksetzung trotz beschreibbarem Arbeitsverzeichnis blockiert

Beim ersten Testlauf wurden bereits versionierte Python-Bytecode-Dateien verändert. Der Versuch, ausschließlich diese erzeugten Änderungen mit `git restore -- <Dateipfade>` zurückzusetzen, scheiterte mit:

```text
fatal: Unable to create '/home/symphonie/PycharmProjects/cubie/.git/index.lock': Read-only file system
```

Die gleiche Rücksetzung war nach Freigabe außerhalb der Sandbox erfolgreich.

**Einordnung:** Das beobachtete Verhalten passt zum expliziten Lesezugriff auf `.git`: Git benötigte eine Schreiboperation für seine Sperrdatei. Schreibrechte im Arbeitsverzeichnis allein reichten für diesen Befehl nicht aus. Hier ist die Erklärung durch die bekannte Berechtigungskonfiguration deutlich stärker abgesichert als bei der Paketinstallation.

Weitere Testläufe verwendeten `PYTHONDONTWRITEBYTECODE=1`, um neue Bytecode-Änderungen zu vermeiden. Das behebt weder die Socket- noch die Installationsbeschränkungen.

## Schlussfolgerungen und mögliche nächste Untersuchungen

**Nachprüfung nach Berechtigungsänderung am 9. November 2026:** Nach Deaktivierung der Agent-Sandbox und Freigabe des Netzwerkzugriffs wurden der oben genannte Installationstest und beide Manager-Fälle gemeinsam regulär, ohne zusätzliche Eskalation, ausgeführt. Ergebnis: **3 bestanden in 1,55 Sekunden**. Die vorherige Blockade trat mit den neuen Berechtigungen nicht mehr auf. Dies stützt die Einordnung als Berechtigungs-/Umgebungsproblem; die genaue Ursache des früheren Installer-Fehlers bleibt ungeklärt.

Die drei nach Freigabe wiederholten Testfälle bestanden. Es wurde kein vollständiger Testlauf außerhalb der Sandbox durchgeführt. Die ursprünglichen Fehlschläge sind durch diese Beobachtungen keine bestätigten Fehler der Sentinel-Implementierung; sie zeigen jedoch reale Voraussetzungen der betroffenen Testaufbauten.

Für die weitere Diagnose bieten sich folgende Schritte an:

- Bei Installationsfehlern stdout und stderr des Installers erhalten; mit einer vorbereiteten Umgebung und explizitem Cache-Verzeichnis prüfen, ob Netzwerk oder Schreibpfad ausschlaggebend ist.
- Den Manager-Start und den betroffenen Socket-Aufruf separat innerhalb und außerhalb der Sandbox reproduzieren; gegebenenfalls verfügbare Sandbox-Regeln oder Audit-Daten auswerten.
- Tests mit Paketinstallation von offline ausführbaren Kernprüfungen getrennt ausweisen. Die vorhandenen Offline-Tests bestanden im zusätzlichen Lauf.
- Bei Manager-Fehlern stets stderr des Kindprozesses berücksichtigen, statt allein den `EOFError` des Elternprozesses zu bewerten.
- Benötigte Berechtigungen für Installer, lokale IPC und Git-Metadaten ausdrücklich dokumentieren. Sandbox-Fehler sollten als Infrastrukturfehler sichtbar bleiben und nicht stillschweigend als erfolgreiche Fachprüfungen gelten.
