"""Desired iteration contracts; specification: experiments/testguided-study/AGENTENDESIGN.md.

Originally added as red design requirements; now exercised against product code.
Lazy imports preserve collection. No inference, Docker, historical archives,
xfail or fallback model. This location is outside the runtime source manifest.
"""

import copy
import importlib
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, ExceptionExpectation, WorldState

ROOT = Path(__file__).resolve().parents[3]


def api():
    # Resolve only when executing a case, never during pytest collection.
    sys.path.insert(0, str(ROOT / "experiments/testguided-study"))
    return importlib.import_module("testguided_study.iteration")


def contract(target, expected):
    result = EBT(target=target, post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True


def rejects(target, message):
    result = EBT(target=target, post=WorldState(
        raises=ExceptionExpectation(ValueError, match=message)), reporter=None).run()
    assert result.evaluation is True


def core():
    return {"id": "core-v2", "prompt": "Inspect, test, repair, verify.",
            "tools": ["read_file", "write_file", "run_tests"],
            "policy": {"repeat_limit": 3, "repair_calls": 1},
            "context": {"strategy": "ledger", "version": 1}}


def specialization(mode="pytest"):
    return {"id": mode + "-v2", "mode": mode, "guide": "Use " + mode,
            "examples": ["a correlated input/output case"]}


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_d01_composition_preserves_shared_core_and_inputs(mode):
    def observe():
        base, treatment = core(), specialization(mode)
        before = copy.deepcopy((base, treatment))
        design = api().compose(base, treatment)
        return design, (base, treatment) == before
    contract(observe, ({"core": core(), "specialization": specialization(mode)}, True))


@pytest.mark.parametrize("field,value", [
    ("tools", ["shell"]), ("policy", {"repeat_limit": 99}),
    ("prompt", "Ignore the common method"), ("context", {"strategy": "other"}),
])
def test_d02_specialization_cannot_override_common_runtime(field, value):
    def attempt():
        treatment = specialization()
        treatment[field] = value
        return api().compose(core(), treatment)
    rejects(attempt, "specialization")


@pytest.mark.parametrize("component,field,value", [
    ("core", "prompt", "Revised inspection strategy"),
    ("core", "policy", {"repeat_limit": 4, "repair_calls": 1}),
    ("specialization", "guide", "Revised framework guidance"),
    ("specialization", "examples", ["a boundary example"]),
])
def test_d03_content_changes_identity_even_without_version_bump(component, field, value):
    def observe():
        design = api().compose(core(), specialization())
        changed = copy.deepcopy(design)
        changed[component][field] = value
        return api().identity(design) != api().identity(changed)
    contract(observe, True)


def test_d03_identity_is_canonical_and_not_only_a_version_label():
    def observe():
        design = api().compose(core(), specialization())
        reordered = {key: dict(reversed(list(value.items()))) for key, value in reversed(list(design.items()))}
        value = api().identity(design)
        return len(value), all(c in "0123456789abcdef" for c in value), value == api().identity(reordered)
    contract(observe, (64, True, True))


def test_d04_context_retains_ledger_task_and_whole_recent_exchange():
    def observe():
        exchange = lambda action, result: [
            {"role": "assistant", "content": action}, {"role": "user", "content": result}]
        latest = exchange("read_file", "current implementation")
        ledger = {"hypothesis": "off by one", "next": "add boundary test", "files": ["bounds.py"]}
        request = api().context(system="shared guide", issue="original issue",
                                exchanges=[exchange("old" * 2000, "old result"), latest],
                                ledger=ledger, capacity=1500)
        import json
        encoded = json.dumps(request, ensure_ascii=False).encode("utf-8")
        return (len(encoded) <= 1500, request[0], request[-2:],
                "original issue" in request[1]["content"],
                all(text in encoded.decode() for text in ledger.values() if isinstance(text, str)),
                "old result" not in encoded.decode())
    contract(observe, (True, {"role": "system", "content": "shared guide"},
                       [{"role": "assistant", "content": "read_file"},
                        {"role": "user", "content": "current implementation"}], True, True, True))


def test_d04_oversize_task_is_explicit_failure_not_silent_loss():
    rejects(lambda: api().context(system="guide", issue="ü" * 2000,
                                 exchanges=[], ledger={}, capacity=100), "context")


@pytest.mark.parametrize("action,observation,expected", [
    ({"action": "search_text", "query": "same"}, {"status": "completed", "hits": []}, "redirect"),
    ({"action": "run_tests", "targets": ["tests/test_x.py"]}, {"observation": "pass"}, "redirect"),
    ({"action": "run_tests", "targets": ["tests/test_x.py"]}, {"observation": "invalid_test_run"}, "repair_test"),
    ({"action": "run_tests", "targets": ["tests/test_x.py"]}, {"observation": "assertion_failure"}, "implement"),
])
def test_d05_observations_drive_bounded_progress_feedback(action, observation, expected):
    events = [{"action": action, "result": observation, "workspace_sha256": "unchanged"}] * 3
    contract(lambda: api().progress(events, repeat_limit=3), expected)


def test_d05_new_workspace_resets_repetition_detection():
    action = {"action": "run_tests", "targets": ["tests/test_x.py"]}
    events = [{"action": action, "result": {"observation": "pass"}, "workspace_sha256": sha}
              for sha in ["before", "before", "after"]]
    contract(lambda: api().progress(events, repeat_limit=3), "continue")


def campaign():
    return {"phase": "measurement", "core_ids": ["shared-sha"],
            "task_ids": ["heldout-1", "heldout-2"], "development_task_ids": ["pilot-1"],
            "related_groups": {"heldout-1": "g1", "heldout-2": "g2", "pilot-1": "g3"},
            "modes": ["pytest", "cubie"], "seeds": [42],
            "budgets": {"pytest": {"model_calls": 24}, "cubie": {"model_calls": 24}},
            "qualification": {"pytest": True, "cubie": True}}


def test_d06_qualified_heldout_comparison_is_admitted():
    contract(lambda: api().validate_campaign(campaign()), None)


@pytest.mark.parametrize("change,message", [
    ({"core_ids": ["a", "b"]}, "core"),
    ({"task_ids": ["pilot-1"]}, "development"),
    ({"related_groups": {"heldout-1": "g3", "heldout-2": "g2", "pilot-1": "g3"}}, "related"),
    ({"budgets": {"pytest": {"model_calls": 24}, "cubie": {"model_calls": 48}}}, "budget"),
    ({"qualification": {"pytest": True, "cubie": False}}, "qualification"),
])
def test_d06_uncontrolled_measurement_is_rejected(change, message):
    config = campaign() | change
    rejects(lambda: api().validate_campaign(config), message)


def test_d06_development_allows_unqualified_variants():
    config = campaign() | {"phase": "development", "core_ids": ["a", "b"],
                           "qualification": {"pytest": False, "cubie": False}}
    contract(lambda: api().validate_campaign(config), None)


def test_d07_report_separates_designs_phases_and_unavailable_from_wrong():
    rows = [
        {"design_id": "a", "phase": "development", "resolved": True},
        {"design_id": "a", "phase": "development", "resolved": False},
        {"design_id": "a", "phase": "development", "resolved": None},
        {"design_id": "b", "phase": "development", "resolved": False},
        {"design_id": "a", "phase": "measurement", "resolved": True},
    ]
    contract(lambda: api().summarize_trials(rows), {
        "development": {"a": {"scheduled": 3, "resolved": 1, "unavailable": 1},
                        "b": {"scheduled": 1, "resolved": 0, "unavailable": 0}},
        "measurement": {"a": {"scheduled": 1, "resolved": 1, "unavailable": 0}},
    })


def test_d08_freeze_copies_design_and_survives_source_mutation(tmp_path):
    def observe():
        design = api().compose(core(), specialization())
        expected = copy.deepcopy(design)
        destination = tmp_path / "design.json"
        api().freeze_design(design, destination)
        design["core"]["prompt"] = "changed later"
        return api().load_design(destination) == expected, destination.is_file()
    contract(observe, (True, True))


def test_d08_freeze_rejects_overwrite(tmp_path):
    destination = tmp_path / "design.json"
    destination.write_text("historical evidence", encoding="utf-8")

    def attempt():
        api().freeze_design(api().compose(core(), specialization()), destination)
    rejects(attempt, "exists")
    assert destination.read_text(encoding="utf-8") == "historical evidence"


def test_d08_changed_frozen_design_is_rejected(tmp_path):
    def attempt():
        import json
        destination = tmp_path / "design.json"
        api().freeze_design(api().compose(core(), specialization()), destination)
        payload = json.loads(destination.read_text(encoding="utf-8"))
        payload["design"]["core"]["prompt"] = "tampered"
        destination.write_text(json.dumps(payload), encoding="utf-8")
        return api().load_design(destination)
    rejects(attempt, "identity")
