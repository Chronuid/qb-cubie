"""Capture isolated pytest observations and criterion-level JUnit outcomes."""

import sys
import xml.etree.ElementTree as ET

from qb_cubie.benchmarks.execution._process import ExecutionError, invoke


def observe(context, directory, tests, record):
    """Capture pytest output and classify its JUnit observations."""
    config = directory / "pytest.ini"
    config.write_text("[pytest]\npythonpath = .\n", encoding="utf-8")
    junit = record.with_suffix(".xml")
    command = [sys.executable, "-I", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--import-mode=importlib", "--confcutdir=" + str(directory), "-c", str(config),
               "--junitxml=" + str(junit), str(tests)]
    result = invoke(context, command, directory, record)
    result["cases"] = _cases(junit)
    result["test_outcome"] = _outcome(result)
    return result


def _cases(path):
    """Read per-test outcomes from a JUnit report."""
    try:
        return [{"name": case.attrib["name"], "failures": [_failure(child) for child in case
                 if child.tag in {"failure", "error", "skipped"}]}
                for case in ET.parse(path).iter("testcase")]
    except (OSError, ET.ParseError, KeyError) as error:
        raise ExecutionError("infrastructure_error", f"Missing or invalid pytest JUnit report: {error}") from error


def _failure(element):
    """Preserve a JUnit failure, error or skip observation."""
    return {"kind": element.tag, "message": element.get("message", ""), "text": element.text or ""}


def _outcome(result):
    """Classify observed pytest success, assertion failure or execution error."""
    if result["returncode"] == 0 and result["cases"]:
        return "passed"
    if result["returncode"] == 2:
        return "import_error"
    failures = [item for case in result["cases"] for item in case["failures"]]
    if result["returncode"] == 1 and failures and all(_business_failure(f) for f in failures):
        return "assertion_failure"
    return "test_error"


def _business_failure(failure):
    """Recognize pytest assertion and missing-exception summaries, excluding setup errors."""
    terminal = failure["text"].rstrip().rsplit("\n", 1)[-1]
    return failure["kind"] == "failure" and (
        terminal.endswith(": AssertionError")
        or (terminal.endswith(": Failed") and failure["message"].startswith("Failed: DID NOT RAISE ")))


def criteria(observation, identifiers):
    """Aggregate independent test outcomes for every required criterion."""
    decisions = {}
    for identifier in identifiers:
        cases = [case for case in observation["cases"] if case["name"].split("[")[0] == "test_" + identifier]
        if not cases:
            raise ExecutionError("infrastructure_error", f"Evaluator did not cover criterion {identifier}")
        decisions[identifier] = "pass" if all(not c["failures"] for c in cases) else "fail"
    return decisions
