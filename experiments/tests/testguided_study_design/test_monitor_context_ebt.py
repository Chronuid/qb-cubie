"""The Studienwarte exposes only context; live and archive controls still work."""

import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest
from test_pilot_technical_ebt import contract
from testguided_study.artifacts import ROOT


def example(scenario):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the actual monitor JavaScript")
    result = subprocess.run([
        node, str(Path(__file__).parent / "fixtures/monitor_context.cjs"),
        str(ROOT / "testguided_study/monitor.html"), scenario,
    ], check=True, capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout)


def test_context_is_the_only_tab_and_owns_the_accessible_panel():
    class Page(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tabs, self.ids = [], {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get("role") == "tab":
                self.tabs.append(attrs)
            if "id" in attrs:
                self.ids[attrs["id"]] = attrs

    def observe():
        page = Page()
        page.feed((ROOT / "testguided_study/monitor.html").read_text())
        return ([tab.get("id") for tab in page.tabs],
                page.ids["tab-context"].get("aria-selected"),
                page.ids["tab-context"].get("aria-controls"),
                page.ids["payload-panel"].get("aria-labelledby"),
                "raw-payload" in page.ids)

    contract(observe, (["tab-context"], "true", "payload-panel", "tab-context", False))


def test_live_context_updates_without_showing_unsent_action_tool_or_response():
    def observe():
        data = example("live")
        return ("CONTEXT_0" in data["initial"], "CONTEXT_1" in data["payload"],
                "ACTION_ALREADY_SENT_IN_CONTEXT" in data["payload"],
                "UNSENT_" in data["payload"], data["stateCalls"])

    contract(observe, (True, True, True, False, 2))


@pytest.mark.parametrize("scenario", ["missing", "empty", "malformed"])
def test_context_absent_keeps_empty_state_and_never_copies_other_evidence(scenario):
    def observe():
        data = example(scenario)
        return (data["payload"].startswith("Noch kein Kontext übermittelt."), data["empty"],
                data["copyDisabled"], data["copied"], "UNSENT_" in data["payload"])

    contract(observe, (True, True, True, [], False))


def test_paused_context_stays_fixed_and_resumes_with_the_latest_input():
    def observe():
        data = example("pause")
        return data["paused"] == data["initial"], "CONTEXT_1" in data["resumed"], data["stateCalls"]

    contract(observe, (True, True, 2))


def test_pinned_archive_can_return_to_current_live_context():
    def observe():
        data = example("archive")
        return ("CONTEXT_ARCHIVE_0" in data["archived"], "CONTEXT_1" in data["payload"],
                data["archiveQueries"], data["stateCalls"])

    contract(observe, (True, True, [None, "0"], 2))


@pytest.mark.parametrize("scenario,index", [("copy-live", "0"), ("copy-archive", "ARCHIVE_0")])
def test_copy_contains_only_the_selected_sent_messages(scenario, index):
    def observe():
        data = example(scenario)
        messages = json.loads(data["copied"][0])
        return messages, data["copyLabel"], data["copyDisabled"]

    contract(observe, ([{"role": "system", "content": "FRAMEWORK_GUIDE"},
                       {"role": "user", "content": f"CONTEXT_{index} · café </script>"},
                       {"role": "assistant", "content": "ACTION_ALREADY_SENT_IN_CONTEXT"}],
                      "Kontext kopieren", False))


def test_live_updates_keep_context_scroll_position_and_wrap_choice():
    def observe():
        data = example("wrap")
        return data["scrollTop"], data["scrollLeft"], data["noWrap"], "CONTEXT_1" in data["payload"]

    contract(observe, (123, 17, True, True))


def test_error_summary_has_no_pointer_to_deleted_views_or_raw_response():
    def observe():
        data = example("error")
        return ("Invalid JSON action" in data["errorNote"], "Schritt 2" in data["errorNote"],
                "Rohdaten unter Antwort" in data["errorNote"], "UNSENT_" in data["payload"],
                "Ungültige Modellantwort" in data["stopNote"])

    contract(observe, (True, True, False, False, True))
