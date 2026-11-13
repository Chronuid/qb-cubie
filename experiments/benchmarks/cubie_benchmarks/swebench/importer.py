"""Pinned, deterministic, transactional SWE-bench scenario imports."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v

from ._common import (
    CONTRACT,
    SOURCES,
    commit,
    encode,
    git_environment,
    inventory,
    license_text,
    normalize,
    publish,
    repository,
    sha,
    write,
)


def configuration(config):
    """Validate an independent copy of the complete import configuration."""
    config = v.snapshot(config)
    v.version(config)
    _config_fields(config)
    _config_selection(config)
    _config_rules(config)
    return config


def cache_path(config):
    """Locate the cache partition for one source revision and split."""
    return Path(config['cache_dir']) / config['dataset_name'].replace('/', '__') / config['revision'] / sha(config['split'].encode())


def read_snapshot(root, config):
    """Validate a complete local source snapshot without executing project code."""
    root = Path(root).resolve()
    source = v.read_data(v.contained(root, 'source.json', 'snapshot.source'))
    for field in ('dataset_name', 'revision', 'split'):
        v.require(source.get(field) == config[field], 'source.' + field, 'snapshot identity differs')
    raw = v.contained(root, 'records.jsonl', 'snapshot.records').read_bytes()
    v.require(sha(raw) == source.get('records_sha256'), 'records_sha256', 'source integrity hash mismatch')
    license_text(source.get('dataset_license'), 'dataset_license')
    _repositories(root, source)
    rows, originals = _records(raw, source)
    return root, source, rows, originals


def prepare(config, source):
    """Compose a verified snapshot and deterministic import plan."""
    config = configuration(config)
    root, metadata, rows, originals = read_snapshot(_snapshot_path(config, source), config)
    candidates, excluded = _selection(config, rows)
    return config, _plan(config, metadata, candidates, excluded), root, metadata, originals


def plan_swebench_import(config: dict, *, source=None) -> dict:
    """Check the entire source and return a reproducible import plan."""
    return prepare(config, source)[1]


class MaterializationError(ValueError):
    """A record-specific missing Git object, eligible for explicit skip."""


def git(repo, *args):
    """Read local Git objects with hooks and remote transports disabled."""
    try:
        return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                              capture_output=True, check=True, timeout=120,
                              env={**git_environment(), 'GIT_NO_LAZY_FETCH': '1', 'GIT_ALLOW_PROTOCOL': ''}).stdout
    except (subprocess.SubprocessError, OSError) as error:
        raise MaterializationError('commit checkout: Git object unavailable') from error


def checkout(repo, row, visible):
    """Export the exact supported base tree without altering the source checkout."""
    for revision in {row['base_commit'], row['environment_setup_commit']} - {None}:
        git(repo, 'cat-file', '-e', revision + '^{commit}')
    files = _tree_files(repo, row)
    visible.mkdir(parents=True)
    # Validate all names first; symlinks are created last so writes never traverse them.
    links = {path for path, mode, _ in files if mode == '120000'}
    for name, _, _ in files:
        v.require(not any(parent.as_posix() in links for parent in Path(name).parents), 'git.path', 'symlink ancestor')
    _write_tree(visible, files)
    for path in visible.rglob('*'):
        v.require(path.resolve().is_relative_to(visible.resolve()), 'symlink', 'target escapes visible tree')


def materialize(staging, row, config, plan, metadata, root, original):
    """Create one independent scenario with private reference material."""
    identifier, repo = row['instance_id'], row['repo']
    base = staging / 'scenarios' / identifier
    checkout(v.contained(root, metadata['repositories'][repo], 'repository.path', directory=True), row, base / 'visible')
    provenance = _provenance(row, plan, metadata, original)
    scenario = _scenario(identifier, repo, row, provenance)
    task = _task(row, config)
    (base / 'task.md').write_text(task, encoding='utf-8')
    write(base / 'scenario.json', scenario)
    _private(base, row, config, provenance, original)
    return _catalog_case(repo, scenario, provenance)


def import_swebench(config: dict, destination, *, source=None) -> dict:
    """Publish a new portable package without changing its source checkout."""
    destination = Path(os.path.abspath(destination))
    _new_destination(destination)
    prepared = prepare(config, source)
    v.require(not destination.resolve().is_relative_to(prepared[2]), 'destination', 'must stay outside source snapshot')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.swebench-', dir=destination.parent) as temporary:
        staging = Path(temporary) / 'package'
        result = _build(staging, prepared)
        _new_destination(destination)
        publish(staging, destination)
    return {'package': str(destination), **result}


def _config_fields(config):
    """Validate the source and package identity fields."""
    allowed = {'schema_version', 'dataset_name', 'revision', 'split', 'snapshot', 'cache_dir', 'offline',
               'namespace', 'version', 'instance_ids', 'repositories', 'limit', 'seed', 'include_hints',
               'on_error', 'process_profile', 'harness_revision'}
    v.require(not set(config) - allowed, 'config', f'unknown fields: {sorted(set(config) - allowed)}')
    v.choice(config.get('dataset_name'), SOURCES, 'dataset_name')
    for field in ('revision', 'harness_revision'):
        commit(config.get(field), field)
    for field in ('split', 'version', 'cache_dir'):
        v.text(config.get(field), field)
    v.identifier(config.get('namespace'), 'namespace')


def _config_selection(config):
    """Validate selection filters and boolean defaults."""
    for field, default in (('offline', True), ('include_hints', False)):
        config.setdefault(field, default)
        v.require(type(config[field]) is bool, field, 'expected boolean')
    for field in ('instance_ids', 'repositories'):
        config.setdefault(field, [])
        v.strings(config[field], field)
    for repo in config['repositories']:
        repository(repo)
    for identifier in config['instance_ids']:
        v.identifier(identifier, 'instance_ids')


def _config_rules(config):
    """Validate deterministic sampling and failure policy."""
    config.setdefault('seed', 0)
    v.require(type(config['seed']) is int, 'seed', 'expected integer')
    if 'limit' in config:
        v.number(config['limit'], 'limit', positive=True, integer=True)
    config.setdefault('on_error', 'fail')
    config.setdefault('process_profile', 'issue_resolution')
    v.choice(config['on_error'], {'fail', 'skip'}, 'on_error')
    v.choice(config['process_profile'], {'issue_resolution'}, 'process_profile')


def _repositories(root, source):
    """Verify every declared repository object store."""
    v.mapping(source.get('repository_licenses'), 'repository_licenses')
    for repo, path in v.mapping(source.get('repositories'), 'repositories').items():
        repository(repo)
        storage = v.contained(root, path, 'repositories.path', directory=True)
        try:
            _git_storage(root, storage)
            git(storage, 'fsck', '--full', '--no-reflogs')
        except MaterializationError as error:
            raise ValueError(f'source integrity: invalid Git object store for {repo}') from error


def _git_storage(root, storage):
    """Reject Git storage paths outside the source snapshot."""
    gitdir = Path(git(storage, 'rev-parse', '--absolute-git-dir').decode().strip()).resolve()
    common = (storage / Path(git(storage, 'rev-parse', '--git-common-dir').decode().strip())).resolve()
    v.require(gitdir.is_relative_to(root) and common.is_relative_to(root), 'repositories.path', 'Git storage escapes snapshot')
    objects = common / 'objects'
    v.require(objects.resolve().is_relative_to(root) and all(path.resolve().is_relative_to(root) for path in objects.rglob('*') if path.is_symlink()),
              'repositories.path', 'Git objects escape snapshot')
    v.require(not (common / 'objects/info/alternates').exists(), 'repositories.path', 'external Git alternates are unsupported')


def _records(raw, source):
    """Preserve raw records while rejecting duplicate instance identities."""
    rows, originals = [], {}
    for line in raw.splitlines():
        row = _source_row(line, source)
        identifier = row['instance_id']
        v.require(identifier not in originals, 'instance_id', f'duplicate instance: {identifier}')
        rows.append(row)
        originals[identifier] = line
    return rows, originals


def _source_row(line, source):
    """Normalize one licensed source row with a declared repository."""
    try:
        row = normalize(json.loads(line, object_pairs_hook=v.unique_keys))
    except (ValueError, UnicodeError) as error:
        raise ValueError(f'records.jsonl: {error}') from error
    repo = row['repo']
    license_text(source['repository_licenses'].get(repo), f'{repo}.repository_license')
    v.require(repo in source['repositories'], 'repositories', f'missing repository {repo}')
    return row


def _snapshot_path(config, source):
    """Locate an explicit snapshot or an already available cache entry."""
    root = Path(config.get('snapshot', cache_path(config)))
    if root.is_dir():
        return root
    cached = cache_path(config)
    if cached.is_dir():
        return cached
    v.require(not config['offline'], 'offline', 'snapshot/cache missing; acquisition disabled')
    return _acquire(config, source)


def _acquire(config, source):
    """Invoke the acquisition boundary once with sanitized diagnostics."""
    default_source = source is None
    if source is None:
        from .source import acquire
        source = acquire
    try:
        return source({key: config[key] for key in ('dataset_name', 'revision', 'split', 'cache_dir', 'offline')})
    except Exception as error:
        raise _source_error(config, error, default_source) from error


def _source_error(config, error, default_source):
    """Report acquisition failure without exposing remote credentials."""
    if default_source and isinstance(error, ValueError):
        return ValueError(f'source download {config["dataset_name"]}: {error}')
    return ValueError(f'source download {config["dataset_name"]}: {type(error).__name__}')


def _selection(config, rows):
    """Select the configured intersection before deterministic limiting."""
    known = {row['instance_id'] for row in rows}
    v.require(set(config['instance_ids']) <= known, 'instance_ids', f'unknown instances: {sorted(set(config["instance_ids"]) - known)}')
    candidates, excluded = [], []
    for row in sorted(rows, key=lambda row: row['instance_id']):
        reason = _exclusion(config, row)
        if reason:
            excluded.append({'instance_id': row['instance_id'], 'reason': reason})
        else:
            candidates.append(row)
    candidates = _limited(config, candidates, excluded)
    v.require(bool(candidates), 'selection', 'empty selection')
    return candidates, excluded


def _exclusion(config, row):
    """Return the first applicable selection exclusion."""
    if config['instance_ids'] and row['instance_id'] not in config['instance_ids']:
        return 'id_filter'
    if config['repositories'] and row['repo'] not in config['repositories']:
        return 'repository_filter'
    return None


def _limited(config, candidates, excluded):
    """Apply the published hash ranking while preserving final ID order."""
    if 'limit' not in config:
        return candidates
    ranked = sorted(candidates, key=lambda row: (sha(f'{config["seed"]}\n{row["instance_id"]}'.encode()), row['instance_id']))
    selected = {row['instance_id'] for row in ranked[:config['limit']]}
    excluded.extend({'instance_id': row['instance_id'], 'reason': 'limit'} for row in candidates if row['instance_id'] not in selected)
    return [row for row in candidates if row['instance_id'] in selected]


def _plan(config, metadata, candidates, excluded):
    """Bind normalized records and import rules to their immutable source."""
    provenance = {key: metadata[key] for key in ('dataset_name', 'revision', 'split', 'records_sha256', 'dataset_license', 'repository_licenses')}
    rules = {key: value for key, value in config.items() if key not in {'snapshot', 'cache_dir', 'offline'}}
    plan = {'schema_version': 1, 'loader_contract': CONTRACT, 'source': provenance, 'rules': rules,
            'selection': candidates, 'excluded': sorted(excluded, key=lambda row: row['instance_id'])}
    plan['plan_sha256'] = sha(encode(plan))
    return plan


def _tree_files(repo, row):
    """Read supported versioned blobs from the exact base tree."""
    entries = git(repo, 'ls-tree', '-rz', '--full-tree', row['base_commit']).split(b'\0')
    files = []
    for entry in filter(None, entries):
        header, name = entry.split(b'\t', 1)
        mode, kind, object_id = header.decode().split()
        path = name.decode('utf-8')
        v.relative(path, 'git.path')
        v.require('.git' not in {part.lower() for part in path.split('/')}, 'git.path', 'Git metadata forbidden')
        v.require(mode != '160000' and kind == 'blob', 'submodule', 'gitlinks/submodules unsupported')
        v.require(mode in {'100644', '100755', '120000'}, 'git.mode', 'unsupported file mode')
        files.append((path, mode, git(repo, 'cat-file', 'blob', object_id)))
    return files


def _write_tree(visible, files):
    """Publish regular blobs before their internal symlinks."""
    for name, mode, data in sorted(files, key=lambda item: item[1] == '120000'):
        path = visible / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == '120000':
            _tree_link(visible, path, data)
        else:
            path.write_bytes(data)
            path.chmod(int(mode, 8) & 0o777)


def _tree_link(visible, path, data):
    """Create one symlink confined to the visible tree."""
    target = data.decode('utf-8')
    v.require(not Path(target).is_absolute() and (path.parent / target).resolve().is_relative_to(visible.resolve()),
              'symlink', 'target escapes visible tree')
    path.symlink_to(target)


def _provenance(row, plan, metadata, original):
    """Build portable dataset and repository provenance."""
    repo = row['repo']
    provenance = {**{key: plan['source'][key] for key in ('dataset_name', 'revision', 'split', 'dataset_license')},
                  **{key: row[key] for key in ('instance_id', 'repo', 'base_commit', 'environment_setup_commit')},
                  'repository_license': metadata['repository_licenses'][repo], 'raw_sha256': sha(original)}
    return provenance


def _scenario(identifier, repo, row, provenance):
    """Declare one independent issue-resolution episode."""
    scenario = {'schema_version': 1, 'id': identifier, 'group_id': repo.replace('/', '__'),
                'title': identifier, 'benchmark': 'developer_agent', 'process_profile': 'issue_resolution',
                'requires': [], 'split': 'development', 'criteria': ['repair', 'regression'],
                'task': 'task.md', 'visible': 'visible', 'types': ['correctness'], 'tags': ['swebench'],
                'evaluator': {'kind': 'external.swebench_v1', 'reference': 'evaluator/reference.json'},
                'source': provenance, 'regression_coverage': bool(row['PASS_TO_PASS'])}
    return scenario


def _task(row, config):
    """Compose the issue and explicitly enabled hints."""
    task = row['problem_statement'] + '\n\nSubmit all project changes as a unified Git patch.\n'
    if config['include_hints'] and row.get('hints_text'):
        task += '\nHints:\n' + v.text(row['hints_text'], 'hints_text') + '\n'
    return task


def _reference(row, config, provenance):
    """Declare the initial unvalidated external patch reference."""
    reference = {'schema_version': 1, 'validation_status': 'unvalidated', 'human_reviews': [],
                 'gold_patch': 'evaluator/gold.patch', 'test_patch': 'evaluator/tests.patch',
                 'FAIL_TO_PASS': row['FAIL_TO_PASS'], 'PASS_TO_PASS': row['PASS_TO_PASS'],
                 'source': provenance, 'harness_revision': config['harness_revision'], 'raw_record': 'evaluator/record.json'}
    return reference


def _private(base, row, config, provenance, original):
    """Write private patches and source records."""
    write(base / 'evaluator/reference.json', _reference(row, config, provenance))
    (base / 'evaluator/gold.patch').write_text(row['patch'], encoding='utf-8')
    (base / 'evaluator/tests.patch').write_text(row['test_patch'], encoding='utf-8')
    (base / 'evaluator/raw.jsonl').write_bytes(original + b'\n')
    write(base / 'evaluator/record.json', {'schema_version': 1, 'record': row})


def _catalog_case(repo, scenario, provenance):
    """Describe one public executable dataset case."""
    return {'origin': f'https://github.com/{repo}', 'license': provenance['repository_license'],
            'design_id': scenario['group_id'], 'domain': 'python', 'assessment': 'executable',
            'potentially_known': True, 'source': provenance, 'regression_coverage': scenario['regression_coverage']}


def _new_destination(destination):
    """Reject existing targets including dangling symlinks."""
    v.require(not os.path.lexists(destination), 'destination', 'already exists; refusing overwrite')


def _build(staging, prepared):
    """Create and structurally validate one complete staged package."""
    from cubie_benchmarks.contracts.packages import load_package
    config, plan, _root, metadata, _originals = prepared
    staging.mkdir()
    cases, skipped = _cases(staging, prepared)
    imported = list(cases)
    v.require(bool(imported), 'selection', 'all scenarios failed; empty package')
    status = 'partial' if skipped else 'complete'
    _package_files(staging, config, plan, metadata, cases, skipped, status)
    load_package(staging)
    return {'plan_sha256': plan['plan_sha256'], 'imported': imported, 'skipped': skipped, 'status': status}


def _cases(staging, prepared):
    """Materialize selected cases with an explicit per-record failure balance."""
    config, plan, root, metadata, originals = prepared
    cases = {}
    skipped: list[dict] = []
    for row in plan['selection']:
        identifier = row['instance_id']
        try:
            cases[identifier] = materialize(staging, row, config, plan, metadata, root, originals[identifier])
        except MaterializationError as error:
            _skip(staging, config, identifier, error, skipped)
    return cases, skipped


def _skip(staging, config, identifier, error, skipped):
    """Apply the explicit skip policy to a materialization failure."""
    if config['on_error'] != 'skip':
        raise ValueError(f'{identifier}: {error}') from error
    shutil.rmtree(staging / 'scenarios' / identifier, ignore_errors=True)
    skipped.append({'instance_id': identifier, 'stage': 'checkout', 'reason': str(error)})


def _package_files(staging, config, plan, metadata, cases, skipped, status):
    """Write the package identity, public catalog and private import inventory."""
    write(staging / 'package.json', _package(config, metadata, cases))
    write(staging / 'dataset.json', {'schema_version': 1, 'publication_status': 'public', 'cases': cases})
    write(staging / 'swebench-import.json', {'schema_version': 1, 'loader_contract': CONTRACT,
          'plan': plan, 'plan_sha256': plan['plan_sha256'], 'harness_revision': config['harness_revision'],
          'imported': list(cases), 'skipped': skipped, 'status': status, 'inventory': inventory(staging)})


def _package(config, metadata, cases):
    """Declare a portable package containing exactly the successful cases."""
    return {'schema_version': 1, 'namespace': config['namespace'], 'version': config['version'],
            'license': metadata['dataset_license'], 'provenance': config['dataset_name'] + '@' + config['revision'],
            'dataset': 'dataset.json', 'swebench_import': 'swebench-import.json',
            'scenarios': [f'scenarios/{identifier}/scenario.json' for identifier in cases]}
