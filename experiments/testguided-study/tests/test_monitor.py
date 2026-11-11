"""Check live observation, archived steps and read-only HTTP isolation."""

import io
import json
import tarfile
import urllib.error
import urllib.request
from types import SimpleNamespace

import pytest
from testguided_study import agent
from testguided_study.admission import control_file
from testguided_study.artifacts import ROOT, load_config, read, write
from testguided_study.corpus import sanitize
from testguided_study.monitor import MonitorServer, run_view
from testguided_study.telemetry import Observer, snapshot


def row():
    return {"run_id": "0001", "pair_id": "0001", "task_id": "visible-task", "mode": "pytest", "seed": 42}


def test_model_wait_is_visible_before_call_and_matches_actual_context(tmp_path, monkeypatch):
    observer = Observer(tmp_path)
    config = load_config(ROOT / "study.toml")
    observer.bind(tmp_path, config, [row()])
    observer.begin(row(), config)
    captured = []

    class Client:
        def chat(self, **kwargs):
            state = snapshot(tmp_path)
            assert state["state"] == "model_wait"
            assert state["agent"]["context"] == kwargs["messages"]
            captured.append(kwargs["messages"])
            return {"action": {"action": "submit", "stage": "finish", "reason": "complete"},
                    "raw": {}, "usage": {"input_tokens": 5, "output_tokens": 2}}

    monkeypatch.setattr(agent, "patch", lambda *args: "")
    task = SimpleNamespace(problem_statement="Visible issue", test_patch="PRIVATE_REFERENCE_NEVER_SENT")
    directory = tmp_path / "runs/0001"
    result = agent.develop(None, None, task, row(), config, {"pytest": "Visible guide"}, directory,
                           client=Client(), observer=observer)
    assert result["status"] == "submitted"
    state = snapshot(tmp_path)
    assert state["agent"]["context"] == captured[0]
    assert state["active"]["agent_finished_at"] >= state["active"]["agent_started_at"]
    assert "PRIVATE_REFERENCE" not in json.dumps(state)
    assert state["agent"]["action"]["action"] == "submit"


def test_monitor_serves_live_state_and_archived_steps_without_private_files(tmp_path):
    observer = Observer(tmp_path)
    config = {"study_id": "read-only-test"}
    observer.bind(tmp_path, config, [row()])
    write(tmp_path / "schedule.json", [row()])
    private = tmp_path / "inputs/record.json"
    write(private, {"patch": "SECRET_GOLD_PATCH"})
    write(tmp_path / "runs/0001/steps/0000-request.json", [{"role": "user", "content": "source </script>"}])
    write(tmp_path / "runs/0001/steps/0000-tool.json", {"result": {"stdout": "public", "junit_xml": "own xml"}})
    server = MonitorServer(tmp_path)
    url = server.start()
    try:
        with urllib.request.urlopen(url + "/") as response:
            assert "Kontext" in response.read().decode()
        observer.emit("model_request", "Waiting", state="model_wait", agent={"context": [{"content": "actual input"}]})
        with urllib.request.urlopen(url + "/api/state") as response:
            assert json.load(response)["agent"]["context"] == [{"content": "actual input"}]
        with urllib.request.urlopen(url + "/api/run?run_id=0001&step=0") as response:
            data = json.load(response)
            assert data["agent"]["context"][0]["content"] == "source </script>"
            assert data["agent"]["result"] == {"stdout": "public"}
        for path, code in (("/inputs/record.json", 404), ("/api/run?run_id=../inputs", 400),
                           ("/api/run?run_id=0001&step=999", 400)):
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(url + path)
            assert error.value.code == code
        request = urllib.request.Request(url + "/api/state", b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        assert error.value.code == 501
        assert read(private)["patch"] == "SECRET_GOLD_PATCH"
    finally:
        server.close()


def test_archived_monitor_rejects_study_path_escape(tmp_path):
    write(tmp_path / "monitor/state.json", {"study_path": "../outside"})
    with pytest.raises(ValueError, match="outside"):
        run_view(tmp_path, "0001")


def test_progress_counts_pending_failed_and_unavailable_separately(tmp_path):
    observer = Observer(tmp_path)
    rows = [{**row(), "run_id": f"{i:04d}"} for i in range(1, 5)]
    observer.bind(tmp_path, {"study_id": "test"}, rows)
    for record, resolved in zip(rows, (True, False, None), strict=False):
        observer.finish({**record, "resolved": resolved, "total_seconds": 1,
                         "agent": {"status": "submitted"}})
    state = snapshot(tmp_path)
    assert (state["completed_runs"], state["resolved_runs"], state["failed_runs"], state["unavailable_runs"]) == (3, 1, 1, 1)
    assert state["runs"][-1]["status"] == "pending"


def test_snapshot_materializes_file_links_and_removes_git_history(tmp_path):
    source = tmp_path / "original.tgz"
    with tarfile.open(source, "w:gz") as archive:
        for name, content in (("./module.py", b"pass\n"), ("./.git/objects/secret", b"GOLD_HISTORY")):
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            archive.addfile(entry, io.BytesIO(content))
        link = tarfile.TarInfo("./alias.py")
        link.type, link.linkname = tarfile.SYMTYPE, "module.py"
        archive.addfile(link)
    clean = tmp_path / "clean.tgz"
    receipt = sanitize(source, clean)
    with tarfile.open(clean) as archive:
        assert set(archive.getnames()) == {"module.py", "alias.py"}
        assert archive.getmember("alias.py").isfile()
        assert archive.extractfile("alias.py").read() == b"pass\n"
    assert receipt["removed_git_entries"] == 1
    assert receipt["materialized_links"] == 1


@pytest.mark.parametrize("name,link", [("../escape", None), ("link.py", "../host.py"),
                                      ("link.py", "/etc/passwd")])
def test_snapshot_preparation_rejects_paths_outside_archive(tmp_path, name, link):
    source = tmp_path / "unsafe.tgz"
    with tarfile.open(source, "w:gz") as archive:
        entry = tarfile.TarInfo(name)
        if link:
            entry.type, entry.linkname = tarfile.SYMTYPE, link
        archive.addfile(entry, None if link else io.BytesIO())
    with pytest.raises(ValueError):
        sanitize(source, tmp_path / "output.tgz")
    assert not (tmp_path / "output.tgz").exists()


def test_new_test_files_choose_related_existing_regression_file():
    paths = ["tests/test_unrelated.py", "tests/test_response_model_as_return_annotation.py",
             "tests/test_return_none_stringified_annotations.py"]
    assert control_file(paths, [paths[-1]]) == paths[1]
    assert control_file([paths[-1]], [paths[-1]]) is None
