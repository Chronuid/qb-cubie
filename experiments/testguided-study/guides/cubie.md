Use qb-cubie's EBT and WorldState inside pytest test functions. Use parametrization
for related examples and one correlated input/output pair per EBT execution.
Derive expected results from the issue, not from the current code.

```python
import pytest
from qb_cubie import EBT, WorldState
from module_under_test import transform

@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4)])
def test_transform(value, expected):
    result = EBT(target=transform, pre=WorldState(args=(value,)),
                 post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True
```

WorldState args is a tuple of positional arguments; kwargs is a dictionary.
returns may be a concrete value, type, or nested pattern. Dictionary keys must
match exactly. Independent pre/post lists do not pair inputs with outputs.
Use pytest.raises for required exceptions or WorldState(raises=ExceptionExpectation(
ValueError, match="pattern")); returns and raises cannot share a post-state.
For file operations use pytest's tmp_path or EBT with TempFS and WorldState(fs=
{"relative/path": "fixture/source"}). File expectations refer to fixture sources;
use separate input and expected fixtures. Do not use absolute destination paths.
EBT's finite examples do not prove universal correctness. Check evaluation, not
just successful construction. Assertions belong inside test functions.
Ordinary pytest assertions remain available when useful.

## Examples

### EBT: Parameterized execution of value pairs

Using a separate EBT contract for each test case prevents underspecification; this approach integrates ideally with `pytest`.

```python
import pytest
from qb_cubie import EBT, WorldState

@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4), (-1, -2)])
def test_double(value, expected):
    EBT(
        target=lambda x: x * 2, # 'target' receives the callable
        pre=WorldState(args=(value,)), # Positional argument passed as a tuple
        post=WorldState(returns=expected), # Exact check of the return value
    ).run()

```

### EBT: File transformation in TempFS with limits and a predicate

Hydrating host files and evaluating generated files.

```python
import json
from pathlib import Path
from qb_cubie import EBT, TempFS, WorldState

def valid_report(path: Path) -> bool:
    # The predicate receives a path pointer to the currently active workspace
    return path.is_file() and isinstance(json.loads(path.read_text()).get("duration"), float)

def test_report(tmp_path):
    EBT(
        target=create_report,
        arena=TempFS(timeout=5, max_output_bytes=65536), # Limits for execution time and streams
        pre=WorldState(fs={"input.json": str(tmp_path / "source.json")}), # Relative target: absolute host source
        post=WorldState(fs={"report.json": valid_report}), # Validation via a predicate function
    ).run()

```
### EBT: Validating Exceptions

Regular expressions are used to validate the error message.

```python
from qb_cubie import EBT, ExceptionExpectation, WorldState

def test_rejected_order():
    EBT(
        target=reject_order,
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"^invalid order: \d+$") # Type and regex match
        ),
    ).run()

```