"""Independently establish the new fixtures and the existing exact-match/RBT limits."""

import copy
import json
import runpy
import sys
import types

import pytest

from qb_cubie.benchmarks.execution import _review, evaluators

from ...benchmarks.contracts import accepted, rejected
from .conftest import FIXTURES
from .support import hashes, paraphrased_report, report, request

PAIRS = [("", "<span></span>"), ("A&B", "<span>A&amp;B</span>"),
         ("<&>", "<span>&lt;&amp;&gt;</span>"), ("&amp;", "<span>&amp;amp;</span>"),
         (' Grüße 🌍\n" ', '<span> Grüße 🌍\n" </span>')]


def renderer(root, monkeypatch):
    module = types.ModuleType("escaping")
    module.escape_text = runpy.run_path(str(root / "escaping.py"))["escape_text"]
    monkeypatch.setitem(sys.modules, "escaping", module)
    return runpy.run_path(str(root / "renderer.py"))["render"]


@pytest.mark.parametrize("text,expected", PAIRS)
def test_conform_fixture_against_explicit_input_output_pairs(review_workspace, monkeypatch, text, expected):
    render = renderer(review_workspace(), monkeypatch)
    accepted(render, text, expected=expected)


@pytest.mark.parametrize("text,expected", [("A&B", "<span>A&B</span>"), ("&amp;", "<span>&amp;</span>")])
def test_faulty_fixture_really_violates_ampersand_requirement(review_workspace, monkeypatch, text, expected):
    render = renderer(review_workspace("faulty"), monkeypatch)
    accepted(render, text, expected=expected)
    assert expected != dict(PAIRS)[text]


@pytest.mark.parametrize("variant", ["conform", "faulty"])
def test_existing_visible_examples_are_green_for_both_variants(review_workspace, monkeypatch, variant):
    root = review_workspace(variant)
    module = types.ModuleType("renderer")
    module.render = renderer(root, monkeypatch)
    monkeypatch.setitem(sys.modules, "renderer", module)
    examples = runpy.run_path(str(root / "tests/test_renderer.py"))
    accepted(examples["test_plain_unicode"], expected=None)
    accepted(examples["test_angle_brackets"], expected=None)


def evaluation_context(root, tmp_path, variant):
    incoming = request(root)
    directory = tmp_path / "runner-results"
    directory.mkdir()
    reference = json.loads((FIXTURES / "reference.json").read_bytes())[variant]
    return {"root": tmp_path, "directory": directory, "workspace": root, "base": FIXTURES,
            "run": {"run_id": incoming["run_id"], "scenario_id": incoming["scenario_id"], "condition": "cubie"},
            "scenario": {"criteria": incoming["criteria"], "evaluator": {"kind": "review_reference"}},
            "source_files": hashes(root), "reference": reference}


def evaluate(context, payload):
    root = context["workspace"]
    (root / "review.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    incoming = request(root)
    event = {"run_id": incoming["run_id"], "artifacts": ["review.json"],
             "artifact_hashes": {"review.json": hashes(root)["review.json"]}}
    return evaluators.review(context, event)


@pytest.mark.parametrize("variant,decision", [("conform", "pass"), ("faulty", "fail")])
def test_new_reference_decisions_are_accepted_by_independent_runner(review_workspace, tmp_path, variant, decision):
    context = evaluation_context(review_workspace(variant), tmp_path, variant)
    accepted(lambda: evaluate(context, report(decision)), expected=lambda value: value["quality_passed"] is True)


def test_semantic_paraphrase_keeps_correct_decisions_but_exact_match_scores_zero(review_workspace, tmp_path):
    context = evaluation_context(review_workspace("faulty"), tmp_path, "faulty")
    payload = paraphrased_report()
    result = accepted(lambda: evaluate(context, payload), expected=lambda value: value["quality_passed"] is False)
    assert result["criterion_results"] == context["reference"]["criterion_results"]
    assert {metric["name"]: metric["value"] for metric in result["metrics"]} == {"precision": 0.0, "recall": 0.0}
    assert json.loads((context["workspace"] / "review.json").read_bytes()) == payload


@pytest.mark.parametrize("name", ["escaping.py", "task.md"])
def test_runner_itself_rejects_changed_review_sources(review_workspace, tmp_path, name):
    root = review_workspace()
    context = evaluation_context(root, tmp_path, "conform")
    (root / name).write_bytes(b"changed after initial inventory")
    rejected(lambda: evaluate(context, report()), match="review context changed")


@pytest.mark.parametrize("decision,passed", [("pass", True), ("fail", False), ("abstain", False)])
def test_rbt_only_approves_all_pass_and_retains_distinct_decisions(review_workspace, tmp_path, decision, passed):
    context = evaluation_context(review_workspace(), tmp_path, "conform")
    payload = report(decision)
    accepted(lambda: _review.submit(context, copy.deepcopy(payload)), expected=payload)
    archived = json.loads((context["directory"] / "rbt.json").read_bytes())
    assert archived == {"passed": passed, "report": payload}
