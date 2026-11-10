"""Retain provider, hardware and internal model-call evidence for a local study."""

import json
import platform
import shutil
import subprocess
import time
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting._files import digest, now, write_json
from qb_cubie.benchmarks.reporting.archives import read_archive
from qb_cubie.benchmarks.scaffolding.ollama import _observe

from ..client import OllamaClient


def environment(endpoint, model, expected):
    """Capture load state and competing GPU use without inventing unavailable metrics."""
    observed = _observe(endpoint, model)
    actual = [item for item in observed["tags"]["models"] if item["name"] == model]
    v.require(len(actual) == 1 and actual[0]["digest"] == expected["revision"], "model", "model digest changed")
    v.require(observed["version"]["version"] == expected["provider_version"], "provider", "version changed")
    return {"provider": observed, "gpu": _gpu(), "platform": platform.platform(),
            "python": platform.python_version(), "observed_at": now()}


def _gpu():
    """Report hardware observations when nvidia-smi is installed, preserving failures."""
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    result = subprocess.run([executable, "--query-gpu=name,uuid,memory.total,memory.used,utilization.gpu",
                             "--format=csv"], capture_output=True, text=True, timeout=10, check=False)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def warmup(path, endpoint, model):
    """Run a separately recorded unscored schema preflight at the selected context size."""
    schema = {"type": "object", "properties": {"ready": {"type": "string"}},
              "required": ["ready"], "additionalProperties": False}
    messages = [{"role": "user", "content": 'Unscored preflight. Return {"ready":"ready"} as JSON.'}]
    options = {**model["parameters"]}
    think = options.pop("think")
    client = OllamaClient(endpoint=endpoint, model=model["model_id"], options=options, think=think)
    started = time.monotonic()
    record = {"started_at": now(), "model": model, "messages": messages, "schema": schema}
    write_json(path, {**record, "status": "started"})
    try:
        result = client.chat(messages=messages, schema=schema, timeout=300)
    except ValueError as error:
        write_json(path, {**record, "status": "failed", "reason": str(error),
                          "raw": getattr(error, "raw", None), "duration_seconds": time.monotonic() - started})
        raise
    write_json(path, {**record, "status": "complete", "result": result,
                      "duration_seconds": time.monotonic() - started, "finished_at": now()})


def verify_evidence(archive):
    """Verify every sealed external adapter manifest bound through archived stderr."""
    read_archive(archive)
    records = []
    for stderr in archive.glob("episodes/*/transport/stderr.log"):
        for line in stderr.read_text(encoding="utf-8").splitlines():
            try:
                summary = json.loads(line)
            except ValueError:
                continue
            if isinstance(summary, dict) and "manifest_path" in summary:
                records.append(_evidence(summary))
    return records


def _evidence(summary):
    """Rehash recorded provider responses, tool observations and the manifest itself."""
    manifest = Path(summary["manifest_path"])
    v.require(digest(manifest) == summary["manifest_sha256"], "evidence", "adapter manifest hash mismatch")
    body = json.loads(manifest.read_bytes())
    calls, tools = 0, 0
    for name, checksum in body["artifact_hashes"].items():
        path = v.contained(manifest.parent, name, "evidence")
        v.require(digest(path) == checksum, "evidence", "adapter step hash mismatch")
        step = json.loads(path.read_bytes())
        calls += bool(step["request"])
        tools += step["tool_result"] is not None
    return {**summary, "model_calls": calls, "tool_results": tools}
