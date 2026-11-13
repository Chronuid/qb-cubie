"""Export the versioned public development dataset from installed resources."""

from importlib.resources import as_file, files
from pathlib import Path

from cubie_benchmarks.contracts.packages import load_package
from cubie_benchmarks.reporting._files import copy_tree
from cubie_benchmarks.scaffolding.custom import _available
from cubie_benchmarks.scaffolding.templates import _review_sources


def init_base_package(path: str | Path) -> dict:
    """Create a relocatable base-v1 package without running scenario programs."""
    path = Path(path).resolve()
    _available(path)
    with as_file(files("cubie_benchmarks").joinpath("data/base")) as source:
        copy_tree(source, path)
    _review_sources(path)
    load_package(path)
    return {"package": str(path)}
