"""Herunterladen und Entpacken der Testguided-Study Benchmark-Runs.

Dieses Skript lädt das Archiv der vollständigen Experiment-Runs (ca. 918 MB komprimiert)
aus den GitHub Releases (oder einer alternativen URL) herunter und entpackt es nach
experiments/testguided-study/runs.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import urllib.request

DEFAULT_RELEASE_URL = (
    "https://github.com/Chronuid/qb-cubie/releases/download/v0.0.3/testguided-study-runs.tar.gz"
)
EXPECTED_SHA256 = "3234d440dd3d2df85299ccc98bfe42a2c34b9fa266b7be9d7918f51217277278"


def _format_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def _download_with_progress(url: str, dest_path: Path) -> None:
    print(f"Lade Runs-Archiv herunter von:\n  {url}")

    class ProgressHook:
        def __init__(self) -> None:
            self.total_size = 0
            self.downloaded = 0

        def __call__(self, block_num: int, block_size: int, total_size: int) -> None:
            self.total_size = total_size
            self.downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100.0, (self.downloaded / total_size) * 100)
                sys.stdout.write(
                    f"\rFortschritt: {percent:5.1f}% [{_format_size(self.downloaded)} / {_format_size(total_size)}]"
                )
            else:
                sys.stdout.write(f"\rHeruntergeladen: {_format_size(self.downloaded)}")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest_path, reporthook=ProgressHook())
    sys.stdout.write("\n")
    sys.stdout.flush()


def _verify_sha256(file_path: Path, expected_hash: str) -> bool:
    print("Verifiziere SHA-256 Prüfsumme...")
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha256.update(chunk)
    calculated = sha256.hexdigest()
    if calculated.lower() == expected_hash.lower():
        print("✓ Prüfsumme stimmt überein.")
        return True
    print(f"✗ Prüfsummenfehler!\n  Erwartet: {expected_hash}\n  Erhalten: {calculated}")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lädt die Testguided-Study Rohdaten/Runs herunter und entpackt sie."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("CUBIE_STUDY_RUNS_URL", DEFAULT_RELEASE_URL),
        help=f"Download-URL des .tar.gz-Archivs (Standard: {DEFAULT_RELEASE_URL})",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("experiments/testguided-study/runs"),
        help="Zielordner für die Runs (Standard: experiments/testguided-study/runs)",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        help="Optional: Lokales Archiv (.tar.gz) verwenden anstatt herunterzuladen.",
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Überspringt die SHA-256-Prüfung.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Überschreibt existierende Läufe im Zielordner ohne Nachfrage.",
    )

    args = parser.parse_args()
    target_dir: Path = args.target_dir.resolve()
    base_dir = target_dir.parent

    if target_dir.exists() and any(target_dir.iterdir()) and not args.force:
        print(f"Hinweis: Zielordner existiert bereits und ist nicht leer:\n  {target_dir}")
        answer = input("Möchtest du fortfahren und Inhalte ggf. überschreiben? [y/N]: ").strip().lower()
        if answer != "y":
            print("Abbruch durch Benutzer.")
            return 0

    base_dir.mkdir(parents=True, exist_ok=True)

    if args.from_file:
        archive_path = args.from_file.resolve()
        if not archive_path.is_file():
            print(f"Fehler: Datei nicht gefunden: {archive_path}", file=sys.stderr)
            return 1
        cleanup_archive = False
    else:
        temp_fd, temp_path = tempfile.mkstemp(suffix="_testguided_runs.tar.gz")
        os.close(temp_fd)
        archive_path = Path(temp_path)
        cleanup_archive = True
        try:
            _download_with_progress(args.url, archive_path)
        except Exception as exc:
            print(f"\nFehler beim Download: {exc}", file=sys.stderr)
            if cleanup_archive and archive_path.exists():
                archive_path.unlink()
            return 1

    try:
        if not args.no_check:
            if not _verify_sha256(archive_path, EXPECTED_SHA256):
                if not args.force:
                    print("Abbruch wegen abweichender Prüfsumme.", file=sys.stderr)
                    return 1

        print(f"Entpacke Archiv nach: {base_dir} ...")
        with tarfile.open(archive_path, "r:gz") as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(path=base_dir, filter="data")
            else:
                tar.extractall(path=base_dir)

        print(f"✓ Erfolgreich entpackt! Die Runs befinden sich in:\n  {target_dir}")
        return 0
    finally:
        if cleanup_archive and archive_path.exists():
            archive_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
