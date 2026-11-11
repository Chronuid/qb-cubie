Use qb_cubie's EBT and WorldState in pytest functions to verify production behavior.
Read nearby tests first. Quote the issue requirement and select a concrete input
and expected observation. Execute the EBT contract and explicitly check evaluation.
Use reporter=None consistently. Importing or constructing EBT is not execution.

For correlated value pairs, execute one contract per pair:
```python
import pytest
from qb_cubie import EBT, WorldState
from module_under_test import transform

@pytest.mark.parametrize('value, expected', [(1, 2), (2, 4)])
def test_transform(value, expected):
    result = EBT(target=transform, pre=WorldState(args=(value,)),
                 post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True
```

For exceptions:
```python
from qb_cubie import EBT, WorldState, ExceptionExpectation
from module_under_test import reject_order

def test_rejected_order():
    result = EBT(target=reject_order, pre=WorldState(args=('invalid',)),
                 post=WorldState(raises=ExceptionExpectation(ValueError, match=r'^invalid order$')),
                 reporter=None).run()
    assert result.evaluation is True
```

For files use tmp_path and a small observation adapter:
```python
from qb_cubie import EBT, WorldState
from module_under_test import create_report

def test_report(tmp_path):
    source = tmp_path / 'input.txt'
    source.write_text('example')
    output = tmp_path / 'report.txt'
    def observe():
        create_report(source, output)
        return output.read_text()
    result = EBT(target=observe, post=WorldState(returns='EXAMPLE'), reporter=None).run()
    assert result.evaluation is True
```
An adapter delegates to production code; never reimplement its calculation.
Expected observations come from the issue; examples illustrate syntax only.
args is a tuple; kwargs is a dictionary. returns and raises cannot share a post.
Use concrete returns when possible; type patterns are weaker. Independent pre/post
lists do not pair inputs and outputs. For required filesystem isolation, TempFS
supports WorldState(fs={'relative/path': 'fixture/source'}); file expectations use
separate expected fixtures. Ordinary assertions remain available for supplementary
checks. Finite examples do not prove universal correctness.
Confirm collection and behavioral red, then implement and verify regressions.
If a new test is immediately green, check that it reproduces the issue.
