"""Symmetric QA templates; oracles are supplied by QA, never inferred here."""

import ast
import keyword
from textwrap import indent

REQUIRED = ('case_id', 'requirement_id', 'reason_ref', 'target', 'expected', 'pytest_node')


def validate(case):
    if not isinstance(case, dict) or any(key not in case for key in REQUIRED):
        raise ValueError('Case requires ' + ', '.join(REQUIRED))
    for key in REQUIRED[:-2]:
        if not isinstance(case[key], str) or not case[key].strip():
            raise ValueError(f'Invalid case {key}')
    if not isinstance(case['pytest_node'], str) or '::test_' not in case['pytest_node']:
        raise ValueError('A concrete pytest node is required')
    if not isinstance(case['expected'], dict) or len(case['expected']) != 1 or not (
            {'returns', 'raises'} & case['expected'].keys()):
        raise ValueError('Expected observation must contain exactly returns or raises')
    if not isinstance(case.get('args', []), list) or not isinstance(case.get('kwargs', {}), dict):
        raise TypeError('Use concrete args and kwargs')
    if not isinstance(case.get('setup', {}), dict):
        raise TypeError('setup must be an object')


def render(case, mode):
    """Render function/keyword/exception cases and real observation adapters.

    Adapters in setup.code may observe fixture state, HTTP, streams or files.
    They are ordinary reviewed test source and receive the same QA write checks.
    """
    validate(case)
    if mode not in {'pytest', 'cubie'}:
        raise ValueError('Unknown test condition')
    node = case['pytest_node'].split('::')
    name = node[-1]
    if len(node) != 2 or not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError('Generated cases need a module-level test function')
    setup = case.get('setup', {})
    target = case['target']
    tree = ast.parse(target, mode='eval')
    if not isinstance(tree.body, (ast.Name, ast.Attribute)) or any(
            not part.isidentifier() or keyword.iskeyword(part) for part in target.split('.')):
        raise TypeError('Target must be a callable name or dotted public symbol')
    imports = 'import pytest\n'
    if '.' in target and not setup.get('code') and target.split('.')[0] not in setup.get('fixtures', []):
        imports += f'import {target.rsplit(".", 1)[0]}\n'
    fixtures = setup.get('fixtures', [])
    if not isinstance(fixtures, list) or any(not f.isidentifier() or keyword.iskeyword(f) for f in fixtures):
        raise ValueError('Invalid fixture arguments')
    args, kwargs = repr(tuple(case.get('args', []))), repr(case.get('kwargs', {}))
    expected = case['expected']
    if 'raises' in expected:
        exc = expected['raises']
        if not isinstance(exc, dict) or not isinstance(exc.get('type'), str) or any(
                not p.isidentifier() or keyword.iskeyword(p) for p in exc['type'].split('.')):
            raise ValueError('Exception observation requires a type name')
        exception = exc['type']
        if '.' in exception:
            imports += f'import {exception.rsplit(".", 1)[0]}\n'
        match = f", match={exc['match']!r}" if 'match' in exc else ''
        post = f'raises=ExceptionExpectation({exception}{match})'
        check = f'    with pytest.raises({exception}{match}):\n        {target}(*{args}, **{kwargs})\n'
    else:
        post = f'returns={expected["returns"]!r}'
        check = f'    assert {target}(*{args}, **{kwargs}) == {expected["returns"]!r}\n'
    if mode == 'cubie':
        imports += 'from qb_cubie import EBT, ExceptionExpectation, WorldState\n'
        check = (f'    result = EBT(target={target}, pre=WorldState(args={args}, kwargs={kwargs}), '
                 f'post=WorldState({post}), reporter=None).run()\n'
                 '    assert result.evaluation is True\n')
    body = indent(setup.get('body', ''), '    ')
    if body and not body.endswith('\n'):
        body += '\n'
    if case.get('cleanup'):
        cleanup = indent(case['cleanup'], '        ')
        check = '    try:\n' + indent(check, '    ') + '    finally:\n' + cleanup + '\n'
    result = imports + '\n' + setup.get('code', '') + f'\n\ndef {name}({", ".join(fixtures)}):\n' + body + check
    compile(result, node[0], 'exec')
    return result
