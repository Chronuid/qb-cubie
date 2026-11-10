"""Priority 3.5: versioned JSON evidence survives teardown and a fresh process.

This specifies the proposed JsonReporter, not a test-local persistence adapter.
See CONTRACT_CASES_3_5.md for the minimal interchange schema.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, TempFS, WorldState


def json_reporter(path):
    from qb_cubie.reporter import JsonReporter

    return JsonReporter(path)


def echo(value):
    return value


@pytest.mark.parametrize("value, type_name", [
    (None, "NoneType"), (False, "bool"), (0, "int"), ("", "str"),
    ([], "list"), ({}, "dict"), ((), "tuple"),
])
def test_json_keeps_falsy_values_and_their_types(tmp_path, value, type_name):
    path = tmp_path / "report.json"
    result = EBT(target=echo, pre=WorldState(args=(value,)),
                 post=WorldState(returns=value), reporter=json_reporter(path)).run()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["run_id"] == result.run_id
    assert document["evaluation"] is True
    assert len(document["traces"]) == 1
    trace = document["traces"][0]
    assert trace["step_id"] == result.traces[0].step_id
    encoded = {"kind": "value", "type": f"builtins.{type_name}",
               "value": [] if isinstance(value, tuple) else value}
    assert trace["post"]["returns"] == encoded
    assert trace["outcome"]["returns"] == encoded
    assert trace["evaluation"] is True


@pytest.mark.parametrize("post", [WorldState(), WorldState(returns=None)], ids=["unspecified", "none"])
def test_json_distinguishes_no_return_check_from_expected_none(tmp_path, post):
    path = tmp_path / "report.json"
    result = EBT(target=lambda: 42, post=post, reporter=json_reporter(path)).run()
    document = json.loads(path.read_text(encoding="utf-8"))
    encoded = document["traces"][0]["post"]["returns"]
    if post.returns is None:
        assert encoded == {"kind": "value", "type": "builtins.NoneType", "value": None}
        assert document["evaluation"] is False
    else:
        assert encoded == {"kind": "unspecified"}
        assert document["evaluation"] is True
    assert document["evaluation"] is result.evaluation


def publish():
    Path("out").mkdir()
    Path("out/report.csv").write_bytes(b"new")


def test_delayed_json_report_is_self_contained_after_workspace_and_reference_removal(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    (reference / "report.csv").write_bytes(b"old")
    arena = TempFS()
    result = EBT(target=publish, arena=arena,
                 post=WorldState(returns=None, fs={"out": str(reference)}), reporter=None).run()
    assert result.evaluation is False
    assert arena.workspace_path is None
    assert not Path(result.traces[0].outcome.fs).exists()
    shutil.rmtree(reference)
    path = tmp_path / "report.json"
    json_reporter(path).report(result)
    # A stdlib-only reader needs neither Cubie nor the original files/objects.
    reader = subprocess.run(
        [sys.executable, "-I", "-c",
         ("import json, pathlib, sys; "
         "d = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')); "
         "assert d['schema_version'] == 1; "
         "assert d['evaluation'] is False; "
         "assert d['traces'][0]['diffs']['fs'] == {'out': {'modified': ['report.csv']}}; "
         "assert d['traces'][0]['outcome']['returns']['value'] is None; "
         "print(d['run_id'])"), str(path)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert reader.returncode == 0, reader.stderr
    assert reader.stdout.strip() == result.run_id


@pytest.mark.parametrize("pattern, kind", [
    (int, "type"), (re.compile("^ord-"), "re.Pattern"),
    (lambda value: value.startswith("ord-"), "function"),
])
def test_return_patterns_have_descriptions_without_executable_serialization(tmp_path, pattern, kind):
    path = tmp_path / "report.json"
    result = EBT(target=lambda: "ord-17", post=WorldState(returns=pattern),
                 reporter=json_reporter(path)).run()
    document = json.loads(path.read_text(encoding="utf-8"))
    encoded = document["traces"][0]["post"]["returns"]
    assert encoded["kind"] == "pattern"
    assert encoded["type"].endswith(kind)
    assert isinstance(encoded["description"], str)
    assert encoded["description"]
    assert "pickle" not in encoded
    assert document["evaluation"] is result.evaluation


def reject_order():
    raise ValueError("invalid order: 17")


def test_json_records_expected_exception_and_observed_exception_separately(tmp_path):
    from qb_cubie.protocols import ExceptionExpectation

    path = tmp_path / "report.json"
    result = EBT(target=reject_order,
                 post=WorldState(raises=ExceptionExpectation(ValueError, match="^invalid order:")),
                 reporter=json_reporter(path)).run()
    assert result.evaluation is True
    trace = json.loads(path.read_text(encoding="utf-8"))["traces"][0]
    assert trace["post"]["raises"] == {"type": "builtins.ValueError", "match": "^invalid order:"}
    assert trace["outcome"]["exception"] == {"type": "builtins.ValueError", "message": "invalid order: 17"}
    assert trace["outcome"]["returns"] == {"kind": "unspecified"}


def test_json_retains_every_input_and_post_match_including_negative_states(tmp_path):
    path = tmp_path / "report.json"
    result = EBT(target=echo,
                 pre=[WorldState(args=(1,)), WorldState(args=(2,))],
                 post=[WorldState(returns=int), WorldState(returns=2, expect=False)],
                 reporter=json_reporter(path)).run()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["expect"] is True
    assert document["evaluation"] is False
    assert len(document["traces"]) == 4
    assert len({trace["step_id"] for trace in document["traces"]}) == 2
    assert [trace["evaluation"] for trace in document["traces"]] == [True, False, True, True]
    assert [trace["post"]["expect"] for trace in document["traces"]] == [True, False, True, False]
    assert document["run_id"] == result.run_id


def test_separate_reports_remain_stable_when_case_is_reused(tmp_path):
    first_path, second_path = tmp_path / "first.json", tmp_path / "second.json"
    case = EBT(target=echo, pre=WorldState(args=(1,)), post=WorldState(returns=1),
               reporter=json_reporter(first_path))
    first = case.run()
    first_bytes = first_path.read_bytes()
    case.pre = [WorldState(args=(2,))]
    case.reporter = json_reporter(second_path)
    second = case.run()
    assert first_path.read_bytes() == first_bytes
    first_document, second_document = (json.loads(path.read_text(encoding="utf-8"))
                                       for path in (first_path, second_path))
    assert first_document["run_id"] == first.run_id
    assert second_document["run_id"] == second.run_id
    assert first.run_id != second.run_id
    assert first_document["evaluation"] is True
    assert second_document["evaluation"] is False


def test_report_write_error_is_not_converted_into_success(tmp_path):
    path = tmp_path / "directory"
    path.mkdir()
    with pytest.raises(OSError):
        EBT(target=lambda: None, reporter=json_reporter(path)).run()


def test_nested_values_keep_type_information_and_cycles_are_described(tmp_path):
    from typing import Any

    value = {"nested": [(0, False)], "nonstring": {1: "one"}}
    value["cycle"] = value
    path = tmp_path / "report.json"
    EBT(target=echo, pre=WorldState(args=(value,)), post=WorldState(returns=Any),
        reporter=json_reporter(path)).run()
    encoded = json.loads(path.read_text())["traces"][0]["outcome"]["returns"]["value"]
    pair = encoded["nested"]["value"][0]
    assert pair["type"] == "builtins.tuple"
    assert [item["type"] for item in pair["value"]] == ["builtins.int", "builtins.bool"]
    key, item = encoded["nonstring"]["value"][0]
    assert key == {"kind": "value", "type": "builtins.int", "value": 1}
    assert item["value"] == "one"
    assert encoded["cycle"] == {"kind": "cycle", "type": "builtins.dict"}


def test_atomic_report_replacement_preserves_previous_file_on_failure(tmp_path, monkeypatch):
    import qb_cubie.reporter

    path = tmp_path / "report.json"
    reporter = json_reporter(path)
    result = EBT(target=lambda: None, reporter=reporter).run()
    previous = path.read_bytes()

    def fail_replace(*args):
        raise OSError("replacement failed")

    monkeypatch.setattr(qb_cubie.reporter.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement failed"):
        reporter.report(result)
    assert path.read_bytes() == previous
    assert sorted(p.name for p in tmp_path.iterdir()) == ["report.json"]


def test_observed_callable_is_a_return_value_and_reporting_does_not_reexecute_predicate(tmp_path):
    calls = []

    def expected(value):
        calls.append(value)
        return value is int

    path = tmp_path / "report.json"
    result = EBT(target=lambda: int, post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True
    assert calls == [int]
    json_reporter(path).report(result)
    assert calls == [int]
    trace = json.loads(path.read_text())["traces"][0]
    assert trace["post"]["returns"]["kind"] == "pattern"
    assert trace["outcome"]["returns"]["kind"] == "description"
    assert trace["outcome"]["returns"]["type"] == "builtins.type"
