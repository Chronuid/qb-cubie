"""Consumer contracts for truthful FS diagnostics.

Counts describe differences from post.fs, not writes performed since pre.fs.
Reference paths in reports must refer to the checked workspace, not host fixtures.
"""

import re
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

import pytest

from cubie import EBT, TempFS, WorldState
from cubie.reporter import PytestReporter


@dataclass
class Publication:
    expected: dict[str, bytes]
    actual: dict[str, bytes]
    changes: dict[str, set[str]] = field(default_factory=dict)
    scopes: tuple[str, ...] = (".",)
    initial: dict[str, bytes] = field(default_factory=dict)
    limit: int = 20


PUBLICATIONS = [
    pytest.param(Publication({"report.csv": b"A,250\n"}, {"report.csv": b"A,250\n"}), id="unchanged"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {"report.csv": b"A,250\n"},
        initial={"report.csv": b"A,250\n"},
    ), id="rewrite-identical-bytes"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {"report.csv": b"A,250\n"},
        initial={"report.csv": b"A,125\n"},
    ), id="intended-transformation-matches-post"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {"report.csv": b"A,999\n"},
        {"modified": {"report.csv"}},
    ), id="same-size-content-change"),
    pytest.param(Publication(
        {"report.csv": b""}, {"report.csv": b"A,250\n"}, {"modified": {"report.csv"}},
    ), id="empty-to-nonempty"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {"report.csv": b""}, {"modified": {"report.csv"}},
    ), id="nonempty-to-empty"),
    pytest.param(Publication(
        {"payload.bin": b"\x00\xff\x01"}, {"payload.bin": b"\x00\xfe\x01"},
        {"modified": {"payload.bin"}},
    ), id="same-size-binary-change"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {}, {"missing": {"report.csv"}},
    ), id="missing-file"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n"}, {"report.csv": b"A,250\n", "debug.txt": b"debug"},
        {"unexpected": {"debug.txt"}},
    ), id="unexpected-file"),
    pytest.param(Publication(
        {"report.csv": b"A,250\n", "receipt.txt": b"paid", "keep.txt": b"same"},
        {"report.csv": b"A,999\n", "debug.txt": b"debug", "keep.txt": b"same"},
        {"missing": {"receipt.txt"}, "unexpected": {"debug.txt"}, "modified": {"report.csv"}},
    ), id="mixed-categories"),
    pytest.param(Publication(
        {"out/2026/report.csv": b"250"}, {"out/2026/report.csv": b"999"},
        {"modified": {"out/2026/report.csv"}}, scopes=("out",),
    ), id="mapped-directory-with-nested-change"),
    pytest.param(Publication(
        {"shop/settings.json": b"EUR", "shipping/settings.json": b"EU"},
        {"shop/settings.json": b"USD", "shipping/settings.json": b"US"},
        {"modified": {"shop/settings.json", "shipping/settings.json"}},
        scopes=("shop", "shipping"),
    ), id="same-basename-in-separate-directories"),
    pytest.param(Publication(
        {"old.csv": b"250"}, {"new.csv": b"250"},
        {"missing": {"old.csv"}, "unexpected": {"new.csv"}},
    ), id="rename-is-missing-plus-unexpected"),
    pytest.param(Publication(
        {"out/report.csv": b"250"}, {"out/report.csv": b"999"},
        {"modified": {"out/report.csv"}}, scopes=("out/report.csv",),
    ), id="mapped-single-file"),
    pytest.param(Publication(
        {"out/report.csv": b"250"}, {"out/report.csv": b"250", "debug.txt": b"outside"},
        scopes=("out/report.csv",),
    ), id="outside-mapping-is-not-an-unexpected-file"),
    pytest.param(Publication(
        {"out/report.csv": b"250"}, {"out/report.csv": b"999"},
        {"modified": {"out/report.csv"}}, scopes=(".", "out"),
    ), id="overlapping-scopes-count-file-once"),
    pytest.param(Publication(
        {"missing-a": b"a", "missing-b": b"b", "changed-a": b"old", "changed-b": b"old"},
        {"added-a": b"a", "added-b": b"b", "changed-a": b"new", "changed-b": b"new"},
        {"missing": {"missing-a", "missing-b"}, "unexpected": {"added-a", "added-b"},
         "modified": {"changed-a", "changed-b"}}, limit=2,
    ), id="truncated-details-keep-complete-counts"),
]


def write_publication(files):
    """A simple publishing command; no Cubie or comparison logic in the target."""
    for name, content in files.items():
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def materialize(root, files):
    root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


@pytest.fixture(params=PUBLICATIONS)
def publication_run(request, tmp_path, monkeypatch):
    publication = request.param
    reference, initial, direct = (tmp_path / name for name in ("reference", "initial", "direct"))
    materialize(reference, publication.expected)
    materialize(initial, publication.initial)
    materialize(direct, publication.initial)
    # Observe the application independently before asking Cubie to evaluate it.
    with monkeypatch.context() as context:
        context.chdir(direct)
        assert write_publication(publication.actual) is None
    observed = {str(path.relative_to(direct)): path.read_bytes()
                for path in direct.rglob("*") if path.is_file()}
    assert observed == publication.actual
    case = EBT(
        target=partial(write_publication, publication.actual), arena=TempFS(),
        pre=WorldState(fs={".": str(initial)}),
        post=WorldState(returns=None, fs={scope: str(reference / scope) for scope in publication.scopes}),
        reporter=None,
    )
    return publication, case.run()


def test_fs_verdict_and_recorded_changes_agree_with_reference(publication_run):
    publication, result = publication_run
    assert result.evaluation is (not publication.changes)
    assert len(result.traces) == 1
    trace = result.traces[0]
    assert trace.evaluation is result.evaluation
    assert trace.outcome.returns is None
    # Decode public diff records; the expected categories/paths above are literals.
    recorded = {category: set() for category in ("missing", "unexpected", "modified")}
    for scope, diff in (trace.diffs or {}).get("fs", {}).items():
        assert "error" not in diff, diff
        for category, names in diff.items():
            assert category in recorded
            for name in names:
                path = scope if scope in publication.expected else str(Path(scope) / name)
                recorded[category].add(path)
    assert recorded == {category: publication.changes.get(category, set()) for category in recorded}


@pytest.fixture
def publication_report(publication_run):
    publication, result = publication_run
    reporter = PytestReporter(verbosity=1, max_diff_items=publication.limit)
    if not publication.changes:
        reporter.report(result)
        return publication, None
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        reporter.report(result)
    return publication, str(error.value)


def test_report_counts_agree_with_reference(publication_report):
    publication, message = publication_report
    if message is None:
        return
    expected_counts = tuple(len(publication.changes.get(category, set()))
                            for category in ("missing", "unexpected", "modified"))
    summaries = re.findall(r"Details: -(\d+) Missing \| \+(\d+) Unexpected \| ~(\d+) Modified", message)
    assert summaries == [tuple(map(str, expected_counts))], message


def test_report_paths_and_truncation_agree_with_reference(publication_report):
    publication, message = publication_report
    if message is None:
        return
    listed = re.findall(r"^        ([+~\-]) (.+)$", message, re.MULTILINE)
    wanted = {(symbol, name) for category, symbol in (("missing", "-"), ("unexpected", "+"), ("modified", "~"))
              for name in publication.changes.get(category, set())}
    assert len(listed) == min(len(wanted), publication.limit), message
    assert len(set(listed)) == len(listed), message
    assert set(listed) <= wanted, message
    if len(wanted) <= publication.limit:
        assert set(listed) == wanted, message
        assert "more." not in message
    else:
        assert f"... and {len(wanted) - publication.limit} more." in message


def test_modified_path_names_workspace_target_instead_of_reference_fixture(tmp_path):
    reference = tmp_path / "golden-result.dat"
    reference.write_bytes(b"250")
    result = EBT(target=partial(write_publication, {"out/report.csv": b"999"}), arena=TempFS(),
                 post=WorldState(fs={"out/report.csv": str(reference)}), reporter=None).run()
    assert result.evaluation is False
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter().report(result)
    listed = re.findall(r"^        ([+~\-]) (.+)$", str(error.value), re.MULTILINE)
    assert listed == [("~", "out/report.csv")], str(error.value)


def test_fs_match_is_reported_when_only_the_return_is_wrong(tmp_path):
    reference = tmp_path / "report.csv"
    reference.write_bytes(b"250")
    case = EBT(target=partial(write_publication, {"report.csv": b"250"}), arena=TempFS(),
               post=WorldState(returns="done", fs={"report.csv": str(reference)}))
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        case.run()
    assert "    - FS: Match" in str(error.value)
    assert "Details:" not in str(error.value)
    assert "returns" in case.run_trace.traces[0].diffs
    assert "fs" not in case.run_trace.traces[0].diffs


@pytest.mark.parametrize("kind", ["missing-target", "file-replaced-by-directory"])
def test_comparison_errors_are_explained_instead_of_reporting_zero_changes(tmp_path, kind):
    reference = tmp_path / "report.csv"
    reference.write_bytes(b"250")
    actual = {} if kind == "missing-target" else {"report.csv/child.txt": b"250"}
    result = EBT(target=partial(write_publication, actual), arena=TempFS(),
                 post=WorldState(fs={"report.csv": str(reference)}), reporter=None).run()
    assert result.evaluation is False
    detail = result.traces[0].diffs["fs"]["report.csv"]
    assert detail["error"]
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter().report(result)
    message = str(error.value)
    assert "Error:" in message, message
    assert "report.csv" in message, message
    assert "Details: -0 Missing | +0 Unexpected | ~0 Modified" not in message, message


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_delayed_report_preserves_paths_after_reference_removal(tmp_path, kind):
    reference = tmp_path / "same"
    if kind == "file":
        reference.write_bytes(b"old")
        actual = {"out": b"new"}
        expected_path = "out"
    else:
        reference.mkdir()
        (reference / "same").write_bytes(b"old")
        actual = {"out/same": b"new"}
        expected_path = "out/same"
    result = EBT(target=partial(write_publication, actual), arena=TempFS(),
                 post=WorldState(fs={"out": str(reference)}), reporter=None).run()
    assert result.evaluation is False
    if kind == "directory":
        (reference / "same").unlink()
        reference.rmdir()
    else:
        reference.unlink()
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter().report(result)
    message = str(error.value)
    assert "Details: -0 Missing | +0 Unexpected | ~1 Modified" in message
    assert f"        ~ {expected_path}" in message


@pytest.mark.parametrize("verbosity", [0, 1])
@pytest.mark.parametrize("limit", [0, 1])
def test_comparison_error_remains_visible_alongside_counted_changes(tmp_path, verbosity, limit):
    reference = tmp_path / "reference"
    reference.mkdir()
    (reference / "report.csv").write_bytes(b"old")
    result = EBT(
        target=partial(write_publication, {"out/report.csv": b"new", "bad/child.txt": b"data"}),
        arena=TempFS(),
        post=WorldState(fs={"out": str(reference), "bad": str(reference / "report.csv")}),
        reporter=None,
    ).run()
    assert result.evaluation is False
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter(verbosity=verbosity, max_diff_items=limit).report(result)
    message = str(error.value)
    assert "Error: bad: Topology mismatch (file vs dir)." in message
    if verbosity == 0:
        assert "Details:" not in message
        assert "        ~ out/report.csv" not in message
    else:
        assert "Details: -0 Missing | +0 Unexpected | ~1 Modified" in message
        if limit == 0:
            assert "... and 1 more." in message
            assert "        ~ out/report.csv" not in message
        else:
            assert "        ~ out/report.csv" in message
            assert "more." not in message


@pytest.mark.parametrize("name", ["error", "missing", "modified"])
def test_mapping_names_are_not_interpreted_as_diff_fields(tmp_path, name):
    reference = tmp_path / "reference.dat"
    reference.write_bytes(b"old")
    result = EBT(target=partial(write_publication, {name: b"new"}), arena=TempFS(),
                 post=WorldState(fs={name: str(reference)}), reporter=None).run()
    assert result.evaluation is False
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter().report(result)
    message = str(error.value)
    assert "Error:" not in message
    assert "Details: -0 Missing | +0 Unexpected | ~1 Modified" in message
    assert f"        ~ {name}" in message
