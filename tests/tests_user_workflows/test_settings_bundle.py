"""A shop bundles same-named configuration inputs and validates case tables."""

import json
from functools import partial

import pytest

from qb_cubie import EBT, TempFS, WorldState

from .targets import build_settings


@pytest.fixture
def settings_files(tmp_path):
    paths = []
    for name, data in [("shop", {"currency": "EUR", "region": "DE"}),
                       ("shipping", {"currency": "USD", "region": "EU"})]:
        path = tmp_path / name / "settings.json"
        path.parent.mkdir()
        path.write_text(json.dumps(data), encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.parametrize("fault", [None, "reuse-shop"], ids=["correct", "wrong-source"])
def test_explicit_destinations_preserve_both_settings(tmp_path, monkeypatch, settings_files, check_case, fault):
    shop, shipping = settings_files
    direct = tmp_path / "direct"
    for name, source in [("shop", shop), ("shipping", shipping)]:
        destination = direct / name / "settings.json"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(source.read_bytes())
    with monkeypatch.context() as context:
        context.chdir(direct)
        actual = build_settings(fault)
    expected = {"currency": "EUR", "region": "EU"}
    assert actual == {"currency": "EUR", "region": "DE" if fault else "EU"}
    expected_file = tmp_path / "expected.json"
    expected_file.write_text('{"currency": "EUR", "region": "EU"}\n', encoding="utf-8")
    assert (direct / "settings.json").read_bytes() == (
        b'{"currency": "EUR", "region": "DE"}\n' if fault else expected_file.read_bytes()
    )
    case = EBT(
        target=partial(build_settings, fault), arena=TempFS(),
        pre=WorldState(fs={"shop/settings.json": str(shop), "shipping/settings.json": str(shipping)}),
        post=WorldState(returns=expected, fs={"settings.json": str(expected_file)}),
    )
    result, message = check_case(case, accepted=fault is None)
    assert result.traces[0].outcome.returns == actual
    if message:
        assert "Returns:" in message and "FS: Mismatch" in message


@pytest.mark.parametrize("field", ["pre", "post"])
def test_ambiguous_settings_are_rejected_before_target_execution(settings_files, field):
    calls = []
    with pytest.raises(ValueError, match="settings.json") as error:
        EBT(target=lambda: calls.append("executed"), arena=TempFS(),
            **{field: WorldState(fs=settings_files)}).run()
    assert calls == []
    assert all(str(path) in str(error.value) for path in settings_files)


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("invalid, error_type", [([], ValueError), (["not-a-state"], TypeError)],
                         ids=["empty-case-table", "unconverted-row"])
def test_bad_generated_case_tables_do_not_run_the_application(field, invalid, error_type):
    calls = []
    with pytest.raises(error_type, match=field):
        EBT(target=lambda: calls.append("executed"), **{field: invalid}).run()
    assert calls == []


def test_empty_next_batch_does_not_reuse_previous_success():
    calls = []
    case = EBT(target=lambda: calls.append("executed"), post=WorldState(returns=None))
    first = case.run()
    case.pre = []
    with pytest.raises(ValueError, match="pre"):
        case.run()
    assert calls == ["executed"]
    assert case.run_trace is None
    assert first.evaluation is True
    assert len(first.traces) == 1
