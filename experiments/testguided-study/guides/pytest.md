Use pytest functions to verify actual production behavior. Read nearby tests first.
Quote the issue requirement and select a concrete input and expected observation.
A test must call production code; never reimplement its calculation in the test.
Use the project's public observation API for objects or generators.

For correlated value pairs:
```python
import pytest
from module_under_test import transform

@pytest.mark.parametrize('value, expected', [(1, 2), (2, 4)])
def test_transform(value, expected):
    assert transform(value) == expected
```

For exceptions:
```python
import pytest
from module_under_test import reject_order

def test_rejected_order():
    with pytest.raises(ValueError, match=r'^invalid order$'):
        reject_order('invalid')
```

For files use tmp_path and assert actual contents:
```python
from module_under_test import create_report

def test_report(tmp_path):
    source = tmp_path / 'input.txt'
    source.write_text('example')
    output = tmp_path / 'report.txt'
    create_report(source, output)
    assert output.read_text() == 'EXAMPLE'
```
Expected observations must come from the issue. These examples illustrate syntax,
not requirements for an arbitrary repository. Keep assertions inside test functions.
Confirm the test is collected. Red must expose the reported behavior, not an
incorrect test API. If a new test is immediately green, check its relevance before
changing production code. Run focused tests and relevant regressions before submit.

Before adding a test, state the requirement, concrete input and expected observation
in the action note. Distinguish a literal string from a type or runtime value.
Check the failing assertion against that example before implementing. A failure
in an unrelated assertion is not reproduction. Keep the first regression small;
add boundary/control cases after the reported behavior is covered. A green
existing suite does not establish that the reported input is handled correctly.
