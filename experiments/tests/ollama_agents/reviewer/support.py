"""Data builders for reviewer replays; no adapter decisions or validation."""

import copy
import hashlib
import json
from pathlib import Path

from ..conftest import ReplayTransport, client, tree_bytes

CRITERIA = ["markup_escaping", "unicode_preserved"]
SOURCES = ["escaping.py", "renderer.py", "task.md", "tests/test_renderer.py"]
FINDING = {
    "criterion_id": "markup_escaping", "path": "escaping.py", "symbol": "escape_text",
    "mechanism": "Ampersands are copied without escaping before the markup replacements.",
    "impact": "Rendering A&B produces <span>A&B</span> instead of <span>A&amp;B</span>.",
}


def report(decision="pass"):
    return {"schema_version": 1,
            "criterion_results": {"markup_escaping": decision, "unicode_preserved": "pass"},
            "findings": [copy.deepcopy(FINDING)] if decision == "fail" else [],
            "sources": list(SOURCES)}


def submit(payload):
    return {"action": "submit_review", "review": copy.deepcopy(payload)}


def paraphrased_report():
    return json.loads((Path(__file__).parent / "fixtures/semantic_paraphrase.json").read_bytes())


def response(action, **changes):
    return {"model": "gemma4:12b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(action, ensure_ascii=False)},
            "prompt_eval_count": 13, "eval_count": 7, **changes}


def request(root, **changes):
    return {"schema_version": 1, "type": "request", "run_id": "reviewer-5-2",
            "scenario_id": "markup/escaping", "benchmark": "review_agent", "phase": "review",
            "task": (root / "task.md").read_text(encoding="utf-8"), "workspace": str(root),
            "criteria": list(CRITERIA), "output_format": "review_v1",
            "budgets": {"wall_time_seconds": 300, "tool_calls": 20}, **changes}


def hashes(root):
    return {name: hashlib.sha256(body).hexdigest() for name, body in tree_bytes(root).items()}


def setup_session(api, reviewer_api, root, tmp_path, responses, **options):
    transport = ReplayTransport(*responses)
    budget = api("BudgetLedger")(wall_time_seconds=300,
                               max_model_calls=options.pop("max_model_calls", 6),
                               max_tool_calls=options.pop("max_tool_calls", 12),
                               reserve_seconds=5, clock=options.pop("clock", lambda: 100.0))
    evidence = api("EvidenceWriter")(archive_root=tmp_path / "archives", workspace=root)
    adapter = reviewer_api(client=client(api, transport), budget=budget, evidence=evidence,
                           context_max_bytes=65536, **options)
    return adapter, transport, evidence


def written_report(root):
    return json.loads((root / "review.json").read_bytes())
