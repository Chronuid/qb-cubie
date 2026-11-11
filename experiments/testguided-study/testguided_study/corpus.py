"""Materialize selected source records and sanitize visible snapshot archives."""

import copy
import json
import posixpath
import tarfile
from pathlib import Path, PurePosixPath

from .artifacts import digest, write
from .selection import metadata
from .telemetry import emit


def name_of(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive path: {name}")
    return path.as_posix()


def sanitize(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    counts = {"files": 0, "removed_git_entries": 0, "materialized_links": 0}
    try:
        with tarfile.open(source, "r:*") as archive, tarfile.open(destination, "w:gz", compresslevel=1) as output:
            entries = {name_of(entry.name): entry for entry in archive.getmembers()}
            for name, entry in entries.items():
                if ".git" in PurePosixPath(name).parts:
                    counts["removed_git_entries"] += 1
                    continue
                if name == ".":
                    continue
                target = entry
                seen = set()
                while target.issym() or target.islnk():
                    if target.name in seen:
                        raise ValueError(f"Cyclic snapshot link: {name}")
                    seen.add(target.name)
                    link = target.linkname if target.islnk() else posixpath.join(posixpath.dirname(target.name), target.linkname)
                    resolved = name_of(posixpath.normpath(link))
                    if ".git" in PurePosixPath(resolved).parts or resolved not in entries:
                        raise ValueError(f"Snapshot link escapes visible files: {name}")
                    target = entries[resolved]
                    counts["materialized_links"] += 1
                if not target.isfile() and not target.isdir():
                    raise ValueError(f"Special snapshot entry: {name}")
                if target.isdir() and target is not entry:
                    raise ValueError(f"Directory link needs manual materialization: {name}")
                info = copy.copy(target)
                info.name, info.uid, info.gid, info.uname, info.gname = name, 0, 0, "", ""
                info.mode &= 0o777
                output.addfile(info, archive.extractfile(target) if target.isfile() else None)
                counts["files"] += int(target.isfile())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {"source_sha256": digest(source), "snapshot_sha256": digest(destination), **counts}


def prepare(catalog, selected, source, snapshots, destination, observer=None):
    source, snapshots, destination = Path(source), Path(snapshots), Path(destination)
    if digest(source) != catalog["source_sha256"]:
        raise ValueError("Source task pool differs from the reviewed catalog")
    records = {row["instance_id"]: row for row in map(json.loads, source.read_text().splitlines()) if row}
    tasks = []
    for index, selected_task in enumerate(selected):
        task_id = selected_task["id"]
        row = records[task_id]
        folder = destination / "inputs" / f"{index:04d}"
        folder.mkdir(parents=True, exist_ok=False)
        emit(observer, "snapshot_started", f"Sichtbaren Snapshot bereinigen: {task_id}",
             phase="preparation", state="snapshot")
        receipt = sanitize(snapshots / f"{task_id}.tgz", folder / "snapshot.tar.gz")
        write(folder / "snapshot-receipt.json", receipt)
        write(folder / "record.json", row)
        (folder / "issue.md").write_text(row["problem_statement"], encoding="utf-8")
        tasks.append({"id": task_id, "split": selected_task["split"], **metadata(selected_task),
                      "snapshot": (folder / "snapshot.tar.gz").relative_to(destination).as_posix(),
                      "record": (folder / "record.json").relative_to(destination).as_posix()})
    write(destination / "tasks.json", tasks)
    return tasks
