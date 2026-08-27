import os
import sys
from pathlib import Path

# conftest.py liegt in /tests, also ist das Parent-Directory dein Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent

# 1. Den IDE-Rechtsklick aushebeln: CWD hart auf das Projekt-Root zwingen
os.chdir(PROJECT_ROOT)

# 2. Den Pytest-Runner fixen: Das src/-Verzeichnis für Cubies Framework-Module bekanntmachen
sys.path.insert(0, str(PROJECT_ROOT / "src"))