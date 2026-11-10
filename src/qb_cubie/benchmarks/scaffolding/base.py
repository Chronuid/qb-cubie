"""Export the versioned public development dataset from installed resources."""

from importlib.resources import as_file, files
from pathlib import Path

from qb_cubie.benchmarks.contracts.packages import load_package
from qb_cubie.benchmarks.reporting._files import copy_tree
from qb_cubie.benchmarks.scaffolding.custom import _available
from qb_cubie.benchmarks.scaffolding.templates import _review_sources


def init_base_package(path: str | Path) -> dict:
    """Create a relocatable base-v1 package without running scenario programs."""
    path = Path(path).resolve()
    _available(path)
    with as_file(files("qb_cubie.benchmarks").joinpath("data/base")) as source:
        copy_tree(source, path)
    _review_sources(path)
    load_package(path)
    return {"package": str(path)}
