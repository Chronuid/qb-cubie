<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: Release-Vorbereitung und sauberer Release

![Cubie](../.assets/cubie-logo-written.png)

Dieser Leitfaden beschreibt den verbindlichen Ablauf vom Branch-Abgleich bis zum automatisierten GitHub- und PyPI-Release von `qb-cubie`.

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Überblick über die Release-Architektur

Das Release-Verfahren von `qb-cubie` ist so aufgebaut, dass Paketmetadaten, Lockfile, Dokumentation, Git-Tag und veröffentlichte Artefakte exakt zusammenpassen:

* **Single Source of Truth:** Die aktive Paketversion steht in [`pyproject.toml`](../../pyproject.toml) unter `[project].version`.
* **Automatisierte Pipeline:** Der Workflow [`.github/workflows/release.yml`](../../.github/workflows/release.yml) reagiert auf Tags der Form `v*` (oder manuell via `workflow_dispatch`) und bricht ab, falls das gepushte Tag nicht exakt `v<version>` entspricht.
* **Release-Notes aus dem Changelog:** Der Workflow extrahiert den Abschnitt `## [<version>]` aus [`CHANGELOG.md`](../../CHANGELOG.md) bis zur nächsten `## [`-Überschrift und ergänzt automatisch den Compare-Link zum vorherigen `v*`-Tag.
* **Sauberes Build-Gate vor Veröffentlichung:** Vor der Erstellung des GitHub-Releases und dem PyPI-Upload (`pypa/gh-action-pypi-publish` per Trusted Publishing) baut die CI sdist und Wheel mit `uv build` und prüft das Wheel über [`scripts/check_wheel.py`](../../scripts/check_wheel.py) in einer isolierten Umgebung außerhalb des Checkouts.

---

## 2. Phase 1: Lokale Branches prüfen und sauber mergen

Bevor eine Version angehoben wird, müssen Arbeitsverzeichnis und lokale Branches in einem eindeutigen Zustand sein. Typischerweise findet Entwicklung auf `experimental` (oder einem Feature-Branch) statt, während Releases auf `main` landen.

### 2.1 Unterschiede zwischen lokalen Branches sichtbar machen

Zuerst den Zustand von Arbeitsverzeichnis, Branches und abweichenden Commits prüfen:

```bash
git status
git branch -vv
git log --oneline --decorate --graph -n 20 main experimental
```

Um einseitige Commits in beide Richtungen gezielt aufzulisten:

```bash
# Commits, die auf experimental liegen, aber noch nicht in main enthalten sind:
git log --oneline experimental ^main

# Commits, die auf main liegen, aber auf experimental fehlen:
git log --oneline main ^experimental
```

### 2.2 Typische Merge-Szenarien sauber auflösen

* **Fall A – Entwicklung auf `experimental` soll in `main` integriert werden:**
  Auf `main` wechseln, aktuellen Remote-Stand prüfen und `experimental` mit einem expliziten Merge-Commit (`--no-ff`) übernehmen, damit die Release-Historie nachvollziehbar bleibt:

  ```bash
  git switch main
  git pull --ff-only origin main
  git merge --no-ff experimental -m "Merge branch 'experimental' for vX.Y.Z"
  ```

* **Fall B – Es treten Merge-Konflikte auf:**
  Betroffene Dateien über `git diff --name-only --diff-filter=U` identifizieren und inhaltlich auflösen. Bei Konflikten in `uv.lock` nicht manuell editieren, sondern zuerst `pyproject.toml` bereinigen und danach das Lockfile neu erzeugen:

  ```bash
  uv lock
  uv sync --locked --group dev
  git add pyproject.toml uv.lock
  git commit
  ```

* **Fall C – `main` ist `experimental` voraus (z. B. nach direktem Release-Commit auf `main`):**
  Wenn zuvor direkt auf `main` committed oder gemerged wurde, `experimental` nachziehen, damit der nächste Entwicklungszyklus nicht auf einem veralteten Stand startet:

  ```bash
  git switch experimental
  git merge --ff-only main
  # Falls experimental bereits eigene neue Commits hat:
  # git merge main
  git switch main
  ```

* **Fall D – Abweichende Sicherungs-Branches (z. B. `backup-*`):**
  Vor dem Löschen oder Mergen alter lokaler Branches mit `git log --oneline <branch> ^main` prüfen, ob es sich um bewusste historische Snapshots handelt; diese bleiben bei Bedarf unangetastet.

### 2.3 Alte lokale Tags vorab gegen das Remote prüfen

Weicht ein bereits existierender lokaler Tag (z. B. durch Re-Tagging) vom Remote-Tag ab, führt ein pauschales `git push --tags` später zum Fehler `![rejected] ... (already exists)`. Falls lokale Alt-Tags vom Remote abweichen, lassen sie sich bei Bedarf sauber mit dem Remote-Stand überschreiben:

```bash
git ls-remote --tags origin
git fetch --tags --force
```

---

## 3. Phase 2: Versions-Sprung (`X.Y.Z`) und Dokumentation aktualisieren

### 3.1 Paketversion und Lockfile anheben

1. In [`pyproject.toml`](../../pyproject.toml) unter `[project]` den Wert `version = "X.Y.Z"` setzen.
2. Lockfile und lokale `.venv`-Metadaten synchronisieren:

   ```bash
   uv lock
   uv sync --locked --group dev
   ```

### 3.2 Aktive Versions- und Wheel-Referenzen aktualisieren

Alle Vorkommen der bisherigen Version (z. B. `0.0.4`) im Repository suchen:

```bash
git grep -n "0\.0\.4"
```

Folgende **aktiven** Referenzen werden bei einem Release auf `X.Y.Z` aktualisiert:

| Datei | Zu aktualisierende Stelle |
| :--- | :--- |
| [`README.md`](../../README.md) | Wheel-Installationsbeispiel (`dist/qb_cubie-X.Y.Z-py3-none-any.whl[linters]`) |
| [`docs/core/GUIDE_Contract-Semantics.md`](../core/GUIDE_Contract-Semantics.md) | Aktuell beschriebene Implementierungsversion (`Cubie X.Y.Z`) |
| [`experiments/benchmarks/cubie_benchmarks/data/GUIDE_Ollama-Agents.md`](../../experiments/benchmarks/cubie_benchmarks/data/GUIDE_Ollama-Agents.md) | Wheel-Installationspfad (`qb_cubie-X.Y.Z-py3-none-any.whl[benchmarks]`) |
| [`experiments/ollama-agents/README.md`](../../experiments/ollama-agents/README.md) | Wheel-Installationspfad (`qb_cubie-X.Y.Z-py3-none-any.whl[benchmarks]`) |
| [`experiments/ollama-agents/swebench/Dockerfile`](../../experiments/ollama-agents/swebench/Dockerfile) | `ARG CUBIE_WHEEL=dist/qb_cubie-X.Y.Z-py3-none-any.whl` |

**Nicht ändern:** Historische Verweise auf frühere Stände in älteren `CHANGELOG.md`-Abschnitten, in [`docs/dev/DEV-GUIDE_Next-Steps.md`](./DEV-GUIDE_Next-Steps.md), in [`GUTACHTEN.md`](../../GUTACHTEN.md), in eingefrorenen Studienartefakten (`experiments/testguided-study/`) sowie Versionspins fremder Pakete (z. B. `annotated-doc`).

### 3.3 `CHANGELOG.md` pflegen

Am Anfang von [`CHANGELOG.md`](../../CHANGELOG.md) einen neuen Abschnitt mit exaktem Datums- und Versionsformat einfügen:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Neu
- ...

### Geändert
- ...
```

Der Release-Workflow sucht exakt nach dem Muster `^## \[X\.Y\.Z\](?:\s|$)`. Stimmt die Überschrift nicht mit `[project].version` überein, fällt GitHub auf automatisch generierte Notes zurück.

---

## 4. Phase 3: Lokale Vollprüfung und isolierter Wheel-Check

Vor dem Release-Commit müssen die vollständige Testsuite (inklusive `slow`-Tests, `DocEnsurance`, Styleguide und Lintern) sowie der isolierte Wheel-Test lokal grün sein.

### 4.1 Arena-Basen und vollständige Testsuite

```bash
.venv/bin/python scripts/provision_test_arenas.py
make test-all
```

`make test-all` führt `.venv/bin/python -m pytest -m "" --hypothesis-profile=ci -q` aus und deckt damit auch die in der Standard-Entwicklung übersprungenen `slow`-Tests, `tests/test_styleguide.py` (inklusive `test_module_size` und `test_docs_code_examples` via `DocEnsurance`) sowie `tests/test_lint.py` (`ruff`, `pylint`, `mypy`) ab.

### 4.2 Build-Artefakte bauen und isoliert verifizieren

[`scripts/check_wheel.py`](../../scripts/check_wheel.py) erwartet **genau ein** `qb_cubie-*.whl` in `dist/`. Alte Build-Artefakte deshalb vor dem Neubau gezielt entfernen, ohne `dist/.gitignore` oder eventuelle Studien-Archive (wie `testguided-study-runs.tar.gz`) zu löschen:

```bash
rm -f dist/qb_cubie-*.whl dist/qb_cubie-*.tar.gz
uv build --python .venv/bin/python
.venv/bin/python scripts/check_wheel.py dist
```

Der Check installiert das gebaute Wheel nacheinander in einem frischen `venv` außerhalb des Checkouts für die Profile `core`, `linters` und `benchmarks` und prüft alle Smoke- und Installationsverträge.

---

## 5. Phase 4: Sauberer Commit, Tag und Push

### 5.1 Änderungen prüfen und committen

Alle geänderten und neu hinzugekommenen Dateien (insbesondere neue Testdateien) mit `git status` und `git diff` kontrollieren und gesammelt auf `main` committen:

```bash
git status -s
git add -A
git commit -m "chore(release): prepare vX.Y.Z"
```

### 5.2 Release-Tag anlegen und gezielt pushen

Das Tag muss exakt `vX.Y.Z` lauten (empfohlen als annotiertes Tag):

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

> **Wichtig – niemals pauschal `git push origin main --tags` verwenden:**
> `--tags` versucht, *sämtliche* lokalen Tags zum Remote zu senden. Weicht auch nur ein älteres lokales Tag (z. B. `v0.0.3`) vom Remote ab, bricht `git push` mit `error: Fehler beim Versenden einiger Referenzen` und `![rejected] ... (already exists)` ab, selbst wenn `main` und das neue Tag bereits übertragen wurden.

Stattdessen immer **gezielt und atomar** nur den Ziel-Branch und das konkrete neue Release-Tag pushen:

```bash
git push --atomic origin main vX.Y.Z
```

Mit `--atomic` wird sichergestellt, dass `main` und `vX.Y.Z` auf dem Server nur gemeinsam angenommen werden; alte Tags werden nicht angefasst.

---

## 6. Phase 5: Automatisierter Release-Ablauf und Nachlauf

1. **GitHub Actions prüfen:** Durch den Push von `vX.Y.Z` startet [`.github/workflows/release.yml`](../../.github/workflows/release.yml):
   * Der Job **`release`** validiert Tag gegen `pyproject.toml`, extrahiert die Notes aus `CHANGELOG.md`, baut sdist/Wheel, führt `scripts/check_wheel.py dist` aus und erstellt das GitHub-Release mit angehängten `.whl`- und `.tar.gz`-Dateien.
   * Der Job **`pypi-publish`** lädt die verifizierten Distributionen herunter und veröffentlicht sie über Trusted Publishing (`id-token: write`) auf PyPI.
2. **Manuelles Re-Release (falls nötig):** Über `workflow_dispatch` in GitHub Actions lässt sich der Workflow erneut anstoßen; der Schalter `publish_pypi` steuert dabei, ob auch nach PyPI hochgeladen wird.
3. **Entwicklungs-Branch nachziehen:** Falls der Release-Commit direkt auf `main` entstanden ist, anschließend `experimental` wieder mit `main` synchronisieren:

   ```bash
   git switch experimental
   git merge --ff-only main
   git switch main
   ```

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
