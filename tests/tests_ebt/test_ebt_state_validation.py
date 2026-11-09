"""State validation contracts from GUTACHTEN.md, section 8, priority 1.3."""

# None supplies one default state; explicit empty lists raise ValueError.
# Invalid containers/entries raise TypeError before any target is executed.
# These desired contracts deliberately have no xfail markers.

from functools import partial

import pytest

from cubie import EBT, WorldState


def record_call(marker):
    with marker.open("a", encoding="utf-8") as stream:
        stream.write("executed")
    return 42


@pytest.fixture(params=[False, True], ids=["singleprocess", "multiprocess"])
def execution_mode(request, monkeypatch):
    monkeypatch.setattr("cubie.multiprocessors.os.cpu_count", lambda: 2)
    return request.param


@pytest.mark.parametrize("states", [{}, {"pre": None, "post": None},
                                    {"pre": WorldState(), "post": WorldState()},
                                    {"pre": [WorldState()], "post": [WorldState()]}],
                         ids=["omitted", "none", "single-state", "state-list"])
def test_valid_defaults_execute_once(tmp_path, execution_mode, states):
    marker = tmp_path / "called"
    result = EBT(target=partial(record_call, marker), reporter=None,
                 multiprocessing=execution_mode, **states).run()
    assert marker.read_text(encoding="utf-8") == "executed"
    assert result.evaluation is True
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == 42


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("expect", [True, False])
def test_empty_list_is_configuration_error(tmp_path, execution_mode, field, expect):
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match=field):
        EBT(target=partial(record_call, marker), **{field: []},
            expect=expect, reporter=None, multiprocessing=execution_mode).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
def test_default_reporter_rejects_empty_list(tmp_path, field):
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match=field):
        EBT(target=partial(record_call, marker), **{field: []}).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("invalid", [0, False, "", "state", {}, (), (WorldState(),)],
                         ids=["int", "bool", "empty-string", "string", "dict",
                              "empty-tuple", "state-tuple"])
def test_invalid_container_has_explicit_type_error(tmp_path, execution_mode, field, invalid):
    marker = tmp_path / "called"
    with pytest.raises(TypeError, match=field) as error:
        EBT(target=partial(record_call, marker), **{field: invalid},
            reporter=None, multiprocessing=execution_mode).run()
    assert "WorldState" in str(error.value)
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("invalid", [None, 42, "state", {}, [WorldState()]],
                         ids=["none-entry", "int-entry", "string-entry", "dict-entry", "nested-list"])
def test_invalid_list_entry_is_identified_before_execution(tmp_path, execution_mode, field, invalid):
    marker = tmp_path / "called"
    with pytest.raises(TypeError, match=field) as error:
        EBT(target=partial(record_call, marker), **{field: [WorldState(), invalid]},
            reporter=None, multiprocessing=execution_mode).run()
    assert "WorldState" in str(error.value)
    assert "1" in str(error.value)  # The invalid entry's zero-based index.
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("invalid, error_type", [([], ValueError), ([WorldState(), None], TypeError)])
def test_changed_lists_are_revalidated(tmp_path, execution_mode, field, invalid, error_type):
    marker = tmp_path / "called"
    case = EBT(target=partial(record_call, marker), reporter=None, multiprocessing=execution_mode)
    previous = case.run()
    marker.unlink()
    setattr(case, field, invalid)
    with pytest.raises(error_type, match=field):
        case.run()
    assert not marker.exists()
    assert case.run_trace is None
    assert previous.evaluation is True


@pytest.mark.parametrize("field", ["pre", "post"])
def test_in_place_mutation_is_revalidated(tmp_path, field):
    marker = tmp_path / "called"
    states = [WorldState()]
    case = EBT(target=partial(record_call, marker), reporter=None, **{field: states})
    getattr(case, field).append(None)
    with pytest.raises(TypeError, match=field):
        case.run()
    assert not marker.exists()
