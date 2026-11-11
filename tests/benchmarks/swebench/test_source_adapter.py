"""Specify the acquisition boundary with a local stand-in for remote downloads."""

from ..contracts import accepted, rejected
from .conftest import read_json


def online(config):
    return {key: value for key, value in {**config, "offline": False}.items() if key != "snapshot"}


def test_remote_acquisition_receives_exact_revision_and_uses_returned_snapshot(config, snapshot, public_api):
    requests = []

    def source(request):
        requests.append(request)
        return snapshot["root"]

    result = accepted(lambda: public_api("plan_swebench_import")(online(config), source=source),
                      expected=lambda value: len(value["selection"]) == 2)
    assert len(requests) == 1
    assert all(requests[0][field] == config[field] for field in ("dataset_name", "revision", "split", "cache_dir"))
    assert requests[0]["offline"] is False
    assert result["source"]["revision"] == config["revision"]


def test_automated_acquisition_feeds_the_same_package_contract(config, snapshot, public_api, tmp_path):
    calls = []

    def source(request):
        calls.append(request)
        return snapshot["root"]

    root = tmp_path / "online via synthetic source"
    accepted(lambda: public_api("import_swebench")(online(config), root, source=source),
             expected=lambda value: value["status"] == "complete")
    assert len(calls) == 1
    assert len(read_json(root / "package.json")["scenarios"]) == 2


def test_offline_missing_snapshot_does_not_invoke_remote_source(config, public_api, tmp_path):
    calls = []

    def source(request):
        calls.append(request)
        raise AssertionError("Offline mode must reject before acquisition")

    config["snapshot"] = str(tmp_path / "missing")
    rejected(lambda: public_api("plan_swebench_import")(config, source=source), match="offline|snapshot|cache")
    assert calls == []


def test_transfer_failure_is_diagnostic_and_does_not_publish_a_package(config, public_api, tmp_path):
    def source(request):
        raise TimeoutError("synthetic transfer interrupted")

    root = tmp_path / "failed transfer"
    rejected(lambda: public_api("import_swebench")(online(config), root, source=source),
             match="source|download|transfer|timeout")
    assert not root.exists()


def test_invalid_source_identity_is_rejected_after_acquisition(config, snapshot, public_api):
    changed = online(config)
    changed["revision"] = "f" * 40
    rejected(lambda: public_api("plan_swebench_import")(changed, source=lambda request: snapshot["root"]),
             match="revision|source")
