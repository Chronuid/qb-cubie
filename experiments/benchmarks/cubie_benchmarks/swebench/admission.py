"""Verify and copy reference evidence independently of immutable source packages."""

import json
import shutil
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v

from ._common import encode, sha
from .validation import check_response


def check_report(path, root, package):
    """Verify every reference admission against the current package."""
    path, report, manifest = _report(path, root, package)
    rows = _coverage(report, manifest, package)
    cases = {case['id']: case for case in package['scenarios']}
    _rows(rows, path, root, cases)
    return sha(path.read_bytes())


def copy_report(source, target):
    """Copy only the declared report, attempts and verified artifacts."""
    source, target = Path(source), Path(target)
    report = v.read_data(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    for row in report['scenarios']:
        _copy_row(source, target, row)


def _expected(base, reference, stage):
    """Describe the semantic inputs required for one admitted stage."""
    expected = {**reference['source'], 'stage': stage, 'harness_revision': reference['harness_revision'],
                'network': False, 'FAIL_TO_PASS': reference['FAIL_TO_PASS'], 'PASS_TO_PASS': reference['PASS_TO_PASS'],
                'patch': (base / reference['gold_patch']).read_text(encoding='utf-8') if stage == 'gold' else '',
                'test_patch': (base / reference['test_patch']).read_text(encoding='utf-8'),
                'record': v.read_data(base / reference['raw_record'])['record']}
    return expected


def _stage_binding(request, response, output, entry, expected):
    """Verify request content, response identity and stage evidence."""
    v.require(all(request.get(key) == value for key, value in expected.items()), 'reference_report.request', 'semantic inputs differ')
    checksum = sha(encode({key: value for key, value in request.items() if key not in {'run_id', 'output_dir', 'request_sha256'}}))
    v.require(checksum == request['request_sha256'], 'reference_report.request', 'request hash mismatch')
    actual = check_response(response, {**request, 'output_dir': str(output)})
    v.require(actual == {key: value for key, value in entry.items() if key != 'output_dir'},
              'reference_report.evidence', 'stage evidence differs')


def _stages(path, base, reference, evidence, attempts):
    """Verify both fresh stage attempts and their stored artifacts."""
    for entry in evidence:
        v.require(entry['run_id'] not in attempts, 'reference_report.run_id', 'attempt IDs must be unique')
        attempts.add(entry['run_id'])
        output = v.contained(path.parent, entry.get('output_dir'), 'evidence.output_dir', directory=True)
        request = json.loads(v.contained(output, 'request.json', 'request').read_bytes())
        response = json.loads(v.contained(output, 'response.json', 'response').read_bytes())
        expected = _expected(base, reference, entry['stage'])
        _stage_binding(request, response, output, entry, expected)


def _successful_stages(row):
    """Require successful baseline and gold stages with one image."""
    v.require(row.get('reference_passed') is True and row.get('validation_status') == 'author_checked',
              'reference_report', 'reference not successfully executed')
    evidence = row.get('evidence')
    v.require(type(evidence) is list and {entry.get('stage') for entry in evidence} == {'base', 'gold'} and len(evidence) == 2,
              'reference_report', 'both fresh stages required')
    v.require(len({entry['image_digest'] for entry in evidence}) == 1, 'reference_report', 'baseline and gold used different images')
    return evidence


def _coverage(report, manifest, package):
    """Check the import binding and exact scenario coverage."""
    for field in ('plan_sha256', 'harness_revision'):
        v.require(report.get(field) == manifest[field], 'reference_report.' + field, 'import binding differs')
    rows = report.get('scenarios')
    v.require(type(rows) is list and len(rows) == len(package['scenarios']), 'reference_report', 'scenario coverage differs')
    return rows


def _report(path, root, package):
    """Read a successful report bound to the current package."""
    from cubie_benchmarks.planning._planning import _identity
    path = Path(path).resolve()
    report = v.read_data(path)
    manifest = v.read_data(root / 'swebench-import.json')
    v.require(report.get('valid') is True and report.get('package') == _identity(root, package),
              'reference_report', 'missing successful report bound to this package hash')
    return (path, report, manifest)


def _rows(rows, path, root, cases):
    """Verify unique scenario identities and their private references."""
    seen: set[str] = set()
    attempts: set[str] = set()
    for row in rows:
        identifier = row.get('instance_id')
        v.require(identifier in cases and identifier not in seen, 'reference_report', 'unknown or duplicate instance')
        seen.add(identifier)
        evidence = _successful_stages(row)
        case = cases[identifier]
        v.require(row.get('scenario_id') == case['qualified_id'], 'reference_report.scenario_id', 'scenario binding differs')
        base = (root / case['manifest']).parent
        reference = v.read_data(base / case['evaluator']['reference'])
        _stages(path, base, reference, evidence, attempts)


def _copy_row(source, target, row):
    """Copy one scenario’s declared evidence files."""
    for entry in row['evidence']:
        output = v.contained(source.parent, entry['output_dir'], 'evidence', directory=True)
        relative = Path(entry['output_dir'])
        names = ['request.json', 'response.json', *[item['path'] for item in entry['artifacts']]]
        for name in names:
            original = v.contained(output, name, 'artifact')
            destination = target.parent / relative / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
