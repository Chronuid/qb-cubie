"""Offline phase-one contracts; missing public APIs fail tests, not collection."""

import importlib
import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "phase1"


@pytest.fixture
def package(tmp_path):
    destination = tmp_path / "package"
    shutil.copytree(FIXTURES, destination)
    return destination


@pytest.fixture
def public_api():
    def resolve(name):
        try:
            module = importlib.import_module("qb_cubie.benchmarks")
        except ModuleNotFoundError as error:
            if error.name != "qb_cubie.benchmarks":
                raise
            pytest.fail("Phase 10.1: public qb_cubie.benchmarks API is not implemented", pytrace=False)
        target = getattr(module, name, None)
        assert callable(target), f"Missing public benchmark function: {name}"
        return target
    return resolve
