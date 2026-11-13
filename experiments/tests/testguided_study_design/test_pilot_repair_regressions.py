"""Additional boundaries exposed while implementing the 180702 contracts."""

import json

import pytest
from test_pilot_technical_ebt import LocalSandbox, contract
from test_session_integration import action
from test_workspace_iteration import execute as local_execute
from testguided_study import workspace
from testguided_study.backend import patch_import_failure


@pytest.mark.parametrize("operation", ["replace_text", "write_file"])
@pytest.mark.parametrize("invalid", ["return 2\n", "def value(x, x): return x\n"])
def test_compiler_scope_errors_are_rejected_without_changing_python(tmp_path, operation, invalid):
    source = tmp_path / "module.py"
    original = "VALUE = 1\n"
    source.write_text(original)
    selected = (action("replace_text", path="module.py", old=original, new=invalid)
                if operation == "replace_text" else action("write_file", path="module.py", content=invalid))

    def observe():
        response = local_execute(tmp_path, selected)
        result = json.loads(response.stdout)
        return response.returncode != 0, result.get("status"), source.read_text()

    contract(observe, (True, "tool_error", original))


@pytest.mark.parametrize("path", ["docs_src/settings/test_main.py", "test.with.dots.py"])
def test_collection_paths_come_from_pytest_even_when_junit_flattens_them(tmp_path, path):
    manager = LocalSandbox(tmp_path, False)
    source = manager.tree / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("import missing_repair_dependency\n")

    def observe():
        result = workspace.run_tests(manager, object(), [path], 20, 12000)
        return result["observation"], result["diagnostics"]["errors"][0]["id"]

    contract(observe, ("invalid_test_run", path))


@pytest.mark.parametrize("modified,traceback,expected", [
    ("src/pkg/utils.py", ('ImportError while loading conftest "/workspace/tests/conftest.py".\n'
     'E     File "/workspace/src/pkg/utils.py", line 4\nE   IndentationError: unexpected indent\n'), True),
    ("src/pkg/utils.py", ('ImportError while loading conftest "/workspace/tests/conftest.py".\n'
     '/usr/local/lib/python3.13/site-packages/utils.py:1: in <module>\n'
     'E   ModuleNotFoundError: No module named "dependency"\n'), False),
    ("src/pkg/utils.py", 'ERROR: unrecognized arguments: --bad-option\n', False),
    ("other.py", ('ImportError while loading conftest "/workspace/tests/conftest.py".\n'
     'src/pkg/utils.py:1: in <module>\nE   ModuleNotFoundError: No module named "dependency"\n'), False),
], ids=["changed-workspace", "unrelated-site-package", "pytest-cli", "unchanged-workspace"])
def test_import_attribution_requires_a_traceback_in_the_effective_patch(modified, traceback, expected):
    patch = f"--- a/{modified}\n+++ b/{modified}\n@@ -1 +1 @@\n-old\n+new\n"
    contract(lambda: patch_import_failure(patch, traceback), expected)
