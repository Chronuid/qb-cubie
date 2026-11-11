Use pytest test functions with assertions on actual results. Use parametrization
for related examples, fixtures for setup, tmp_path for file operations, and
pytest.raises for expected exceptions. Keep correlated input/output pairs in the
same case. Derive expected results from the issue, not from the current code.

```python
import pytest
from module_under_test import transform

@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4)])
def test_transform(value, expected):
    assert transform(value) == expected
```

Choose representative behavior, boundaries and relevant error cases. Assertions
belong inside test functions so behavioral failures do not break collection.

## Examples

### Pytest: Parameterized execution of value pairs

Using `@pytest.mark.parametrize` allows you to run the same test logic with multiple correlated input/output pairs. This keeps the test suite concise while clearly indicating which specific cases fail.

```python
import pytest
from module_under_test import double

@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4), (-1, -2)])
def test_double(value, expected):
    # Assertions belong directly inside the test function
    assert double(value) == expected

```

### Pytest: File transformation with `tmp_path`

Use the built-in `tmp_path` fixture to handle file system operations safely. Setup the required input files in the isolated temporary directory, execute the target function, and assert on the results.

```python
import json
from pathlib import Path
from module_under_test import create_report

def test_report(tmp_path: Path):
    # Setup: Create input file in the isolated tmp_path
    source_file = tmp_path / "source.json"
    source_file.write_text('{"sample": "data"}')
    
    report_file = tmp_path / "report.json"
    
    # Execute the target function
    create_report(source=source_file, destination=report_file)
    
    # Validation: Check file existence and contents using standard assertions
    assert report_file.is_file()
    
    report_data = json.loads(report_file.read_text())
    assert isinstance(report_data.get("duration"), float)

```

### Pytest: Validating Exceptions

Use `pytest.raises` as a context manager to assert that specific exceptions are thrown. The `match` argument accepts a regular expression to validate the exact error message.

```python
import pytest
from module_under_test import reject_order

def test_rejected_order():
    # Type and regex match for the expected exception
    with pytest.raises(ValueError, match=r"^invalid order: \d+$"):
        reject_order(order_id="123_invalid")

```