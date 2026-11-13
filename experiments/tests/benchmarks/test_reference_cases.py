"""Run new reference material against independent oracles and actual EBT verdicts."""

import json
import runpy
import sys
from types import ModuleType

import pytest

from qb_cubie import EBT, ExceptionExpectation, TempFS, WorldState

from .conftest import FIXTURES

SCENARIOS = FIXTURES / "scenarios"
REVIEW_ROWS = [([], 0), ([{"status": "paid", "cents": 101}, {"status": "unpaid", "cents": 125}], 101),
               ([{"status": "unpaid", "cents": 125}], 0),
               ([{"status": "paid", "cents": 10}, {"status": "paid", "cents": 20}], 30),
               ([{"status": "paid", "cents": 9007199254740993}], 9007199254740993)]
INPUTS = {
    "populated": {"docs/z.txt": b"last\n", "docs/a.txt": b"first\n",
                  "docs/sub/a.txt": b"nested\x00\xff", "docs/skip.csv": b"a,b\n"},
    "empty": {},
    "filtered": {"docs/sub/deep/keep.txt": b"deep", "docs/skip.csv": b"csv", "docs/LOUD.TXT": b"uppercase"},
}


def load_indexer(path):
    namespace = {"__name__": "indexer"}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)  # noqa: S102 - trusted local fixtures
    return namespace["build_index"]


def tree(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def expected_tree(inputs, episode):
    # The oracle uses the fixed input mapping, not the candidate's traversal or output.
    selected = {name.removeprefix("docs/"): content for name, content in inputs.items()
                if ("/" not in name.removeprefix("docs/") if episode == "initial" else name.endswith(".txt"))}
    expected = dict(inputs)
    expected.update({"out/" + name: content for name, content in selected.items()})
    expected["out/index.txt"] = "".join(name + "\n" for name in sorted(selected)).encode()
    return expected


def materialize(directory, files):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "docs").mkdir(exist_ok=True)
    for name, content in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


@pytest.mark.parametrize("faulty", [False, True], ids=["conforming", "cross-file-defect"])
@pytest.mark.parametrize("rows,expected", REVIEW_ROWS, ids=["empty", "mixed", "unpaid-only", "exact-cents", "beyond-float-precision"])
def test_review_reference_has_executable_counterexamples(monkeypatch, faulty, rows, expected):
    base = SCENARIOS / ("review-paid-faulty" if faulty else "review-paid-correct")
    policy = ModuleType("policy")
    policy.__dict__.update(runpy.run_path(str(base / "visible/policy.py")))
    with monkeypatch.context() as context:
        context.setitem(sys.modules, "policy", policy)
        balance = runpy.run_path(str(base / "visible/balance.py"))
    direct = balance["total"](rows)
    independently_expected = sum(row["cents"] for row in rows if row["status"] == "paid")
    assert independently_expected == expected
    result = EBT(target=balance["total"], pre=WorldState(args=(rows,)),
                 post=WorldState(returns=lambda actual: type(actual) is int and actual == expected),
                 reporter=None).run()
    conforms = not (faulty and any(row["status"] == "unpaid" for row in rows))
    assert (type(direct) is int and direct == expected) is conforms
    assert result.evaluation is conforms
    assert result.traces[0].evaluation is conforms


@pytest.mark.parametrize("name", ["review-paid-correct", "review-paid-faulty"])
def test_review_reference_covers_conforming_and_failing_criteria(name):
    base = SCENARIOS / name
    reference = json.loads((base / "evaluator/reference.json").read_text(encoding="utf-8"))
    manifest = json.loads((base / "scenario.json").read_text(encoding="utf-8"))
    assert set(reference["criterion_results"]) == set(manifest["criteria"])
    assert reference["criterion_results"]["exact_cents"] == "pass"
    failed = {key for key, value in reference["criterion_results"].items() if value == "fail"}
    assert {finding["criterion_id"] for finding in reference["findings"]} == failed
    assert failed == ({"paid_only"} if name.endswith("faulty") else set())
    for finding in reference["findings"]:
        assert (base / "visible" / finding["path"]).is_file()
        assert all(finding[field] for field in ["symbol", "mechanism", "impact", "allowed_alternatives"])
        example = finding["counterexample"]
        assert example["actual"] != example["expected"]


VARIANTS = [(episode, path) for episode in ["initial", "maintenance", "diagnosis"]
            for path in [SCENARIOS / f"index-{episode}/evaluator/solution.py.txt",
                         *sorted((SCENARIOS / f"index-{episode}/evaluator/mutants").glob("*.txt"))]]


@pytest.mark.parametrize("episode,path", VARIANTS, ids=[f"{ep}-{p.stem}" for ep, p in VARIANTS])
@pytest.mark.parametrize("dataset", INPUTS)
def test_project_references_and_mutants_against_independent_tree(tmp_path, monkeypatch, episode, path, dataset):
    inputs = INPUTS[dataset]
    expected = expected_tree(inputs, episode)
    direct_dir, input_dir, expected_dir = [tmp_path / name for name in ["direct", "input", "expected"]]
    materialize(direct_dir, inputs)
    materialize(input_dir, inputs)
    materialize(expected_dir, expected)
    target = load_indexer(path)
    with monkeypatch.context() as context:
        context.chdir(direct_dir)
        direct_return = target("docs", "out")
    conforms = direct_return is None and tree(direct_dir) == expected
    result = EBT(target=target, arena=TempFS(), pre=WorldState(
        args=("docs", "out"), fs={".": str(input_dir)}),
        post=WorldState(returns=None, fs={".": str(expected_dir)}), reporter=None).run()
    assert result.evaluation is conforms
    assert result.traces[0].evaluation is conforms
    if path.name == "solution.py.txt":
        assert conforms is True
    # Every mutant must fail the populated dataset; empty input may mask a defect.
    elif dataset == "populated":
        assert conforms is False, f"Surviving mutant: {path}"


@pytest.mark.parametrize("episode", ["initial", "maintenance", "diagnosis"])
def test_starting_project_exposes_missing_episode_behavior(tmp_path, monkeypatch, episode):
    inputs = INPUTS["populated"]
    materialize(tmp_path / "workspace", inputs)
    target = load_indexer(SCENARIOS / f"index-{episode}/visible/indexer.py.txt")
    with monkeypatch.context() as context:
        context.chdir(tmp_path / "workspace")
        if episode == "initial":
            result = EBT(target=target, pre=WorldState(args=("docs", "out")), post=WorldState(
                raises=ExceptionExpectation(NotImplementedError, match="document index")), reporter=None).run()
            assert result.evaluation is True
        else:
            assert target("docs", "out") is None
            assert tree(tmp_path / "workspace") != expected_tree(inputs, episode)


@pytest.mark.parametrize("episode", ["initial", "maintenance", "diagnosis"])
def test_each_mutant_has_a_declared_visible_criterion_and_real_material(episode):
    base = SCENARIOS / f"index-{episode}"
    reference = json.loads((base / "evaluator/reference.json").read_text(encoding="utf-8"))
    manifest = json.loads((base / "scenario.json").read_text(encoding="utf-8"))
    assert set(reference["criterion_results"]) == set(manifest["criteria"])
    assert set(reference["mutant_criteria"]) == set(reference["mutants"])
    assert {path.name for path in (base / "evaluator/mutants").glob("*.txt")} == {
        path.rsplit("/", 1)[-1] for path in reference["mutants"].values()}
    for name, criteria in reference["mutant_criteria"].items():
        assert criteria and set(criteria) <= set(manifest["criteria"])
        assert (base / reference["mutants"][name]).is_file()


def test_review_counterexample_record_matches_actual_public_code(monkeypatch):
    base = SCENARIOS / "review-paid-faulty"
    reference = json.loads((base / "evaluator/reference.json").read_text(encoding="utf-8"))
    example = reference["findings"][0]["counterexample"]
    policy = ModuleType("policy")
    policy.__dict__.update(runpy.run_path(str(base / "visible/policy.py")))
    with monkeypatch.context() as context:
        context.setitem(sys.modules, "policy", policy)
        target = runpy.run_path(str(base / "visible/balance.py"))["total"]
        assert target(example["rows"]) == example["actual"]
    assert sum(row["cents"] for row in example["rows"] if row["status"] == "paid") == example["expected"]
