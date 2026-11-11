"""Prepare cached study images and retain their build provenance."""

import hashlib
import json
import shutil
import subprocess

from .artifacts import ROOT, digest, read, write
from .telemetry import emit

REPOSITORY = ROOT.parent.parent
LABEL = "cubie.study.inputs"


def signature(paths):
    return hashlib.sha256(json.dumps({str(path.relative_to(REPOSITORY)): digest(path)
                                     for path in sorted(paths)}).encode()).hexdigest()


def execute(arguments, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n" + repr(arguments) + "\n")
        stream.flush()
        result = subprocess.run(arguments, cwd=REPOSITORY, stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f"Build failed ({result.returncode}); see {log}")


def identity(image):
    result = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True, check=False)
    return json.loads(result.stdout)[0] if result.returncode == 0 else None


def wheel(observer, log):
    cache = ROOT / "local/build"
    paths = [REPOSITORY / "pyproject.toml", *REPOSITORY.joinpath("src/qb_cubie").rglob("*.py")]
    paths = [p for p in paths if "arena_envs" not in p.parts]
    fingerprint = signature(paths)
    receipt = cache / "wheel.json"
    if receipt.exists():
        previous = read(receipt)
        path = REPOSITORY / previous["path"]
        if previous["signature"] == fingerprint and path.exists() and digest(path) == previous["sha256"]:
            return path
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to build the Cubie wheel; install uv or provide prepared images with --no-build-images")
    emit(observer, "wheel_build", "Cubie-Wheel vorbereiten", phase="preparation", state="building")
    execute(["uv", "build", "--wheel", "--out-dir", str(cache / "wheels")], log)
    paths = list((cache / "wheels").glob("qb_cubie-*.whl"))
    if len(paths) != 1:
        raise ValueError("Expected one cached Cubie wheel")
    write(receipt, {"signature": fingerprint, "path": paths[0].relative_to(REPOSITORY).as_posix(), "sha256": digest(paths[0])})
    return paths[0]


def ensure(config, directory, observer=None, *, build=True):
    images = config["images"]
    if not build:
        if any(identity(image) is None for image in images.values()):
            raise ValueError("Required images missing; remove --no-build-images to prepare them")
        return
    if images != {"pytest": "cubie-study-pytest:local", "cubie": "cubie-study-cubie:local", "evaluator": "cubie-study-pytest:local"}:
        raise ValueError("Custom image tags require --no-build-images and explicit provisioning")
    log = directory / "build.log"
    base_signature = signature([ROOT / "Dockerfile.pytest", ROOT / "task-requirements.txt"])
    base = identity(images["pytest"])
    if base is None or (base["Config"].get("Labels") or {}).get(LABEL) != base_signature:
        emit(observer, "image_build", "Gemeinsames Aufgabenimage mit lokalen Testabhängigkeiten aufbauen", phase="preparation", state="building")
        execute(["docker", "build", "-f", str(ROOT / "Dockerfile.pytest"), "--label", f"{LABEL}={base_signature}",
                 "-t", images["pytest"], "."], log)
        base = identity(images["pytest"])
    artifact = wheel(observer, log)
    cubie_signature = hashlib.sha256((base["Id"] + digest(artifact) + digest(ROOT / "Dockerfile.cubie")).encode()).hexdigest()
    cubie = identity(images["cubie"])
    if cubie is None or (cubie["Config"].get("Labels") or {}).get(LABEL) != cubie_signature:
        emit(observer, "image_build", "Cubie-Variante desselben Aufgabenimages aufbauen", state="building")
        base_tag = "cubie-study-base:" + base["Id"].split(":", 1)[1]
        execute(["docker", "tag", base["Id"], base_tag], log)
        execute(["docker", "build", "-f", str(ROOT / "Dockerfile.cubie"), "--label", f"{LABEL}={cubie_signature}",
                 "--build-arg", f"BASE_IMAGE={base_tag}", "--build-arg", f"CUBIE_WHEEL={artifact.relative_to(REPOSITORY)}",
                 "-t", images["cubie"], "."], log)
    write(directory / "images.json", {mode: identity(image)["Id"] for mode, image in images.items()})
