"""Generate a tiny synthetic plumbing task outside the measurement sample."""

import shutil
import subprocess
import tarfile
from pathlib import Path

from .artifacts import ROOT, write

BASE = "def bounded(value, lower, upper):\n    return value\n"
FIX = "def bounded(value, lower, upper):\n    return max(lower, min(value, upper))\n"
VISIBLE = "from bounds import bounded\n\ndef test_inside():\n    assert bounded(3, 0, 5) == 3\n"
PRIVATE = VISIBLE + "\ndef test_outside():\n    assert bounded(-2, 0, 5) == 0\n    assert bounded(9, 0, 5) == 5\n"


def generate(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    project = destination / "project"
    project.mkdir()
    (project / "tests").mkdir()
    (project / "bounds.py").write_text(BASE)
    (project / "tests/test_bounds.py").write_text(VISIBLE)

    def git(*args):
        return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, check=True).stdout

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Study", "-c", "user.email=study@localhost", "commit", "-qm", "base")
    with tarfile.open(destination / "snapshot.tar.gz", "w:gz") as archive:
        for name in ("bounds.py", "tests/test_bounds.py"):
            archive.add(project / name, arcname=name)
    (project / "bounds.py").write_text(FIX)
    gold = git("diff", "--", "bounds.py")
    (project / "tests/test_bounds.py").write_text(PRIVATE)
    tests = git("diff", "--", "tests/test_bounds.py")
    write(destination / "record.json", {
        "instance_id": "study-smoke-bounds", "repo": "local/study-smoke", "base_commit": git("rev-parse", "HEAD").strip(),
        "problem_statement": "Fix bounds.bounded(value, lower, upper): return lower when value is below lower, "
                             "upper when it is above upper, and value otherwise. Inputs are integers and lower <= upper. "
                             "Inspect and maintain the visible tests while using test-guided development.",
        "patch": gold, "test_patch": tests, "FAIL_TO_PASS": ["tests/test_bounds.py::test_outside"],
        "PASS_TO_PASS": ["tests/test_bounds.py::test_inside"],
    })
    write(destination / "tasks.json", [{"id": "study-smoke-bounds", "split": "pilot",
                                        "task_type": "infrastructure_smoke", "change_kind": "bugfix",
                                        "test_scope": "unit", "repo": "local/study-smoke",
                                        "related_group": "study_smoke_bounds",
                                        "record": "record.json", "snapshot": "snapshot.tar.gz"}])
    shutil.copytree(ROOT / "guides", destination / "guides")
    template = (ROOT / "study.toml").read_text()
    template = template.replace('"cubie-testguided-pilot-v1"', '"plumbing-smoke-not-evidence"')
    template = template.replace("seeds = [42, 137]", "seeds = [42]")
    (destination / "study.toml").write_text(template)
    shutil.rmtree(project)
    return {"config": str(destination / "study.toml"), "purpose": "Synthetic infrastructure smoke, never study evidence"}
