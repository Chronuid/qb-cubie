"""Workspace boundary shared by the local controller and container port."""

import difflib
import hashlib
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from .iteration import identity

PRIVATE = {'.git', 'evaluator', 'secret', 'evidence', 'private', 'reference', '.aws', '.codex', '.agents'}
IGNORED = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.venv', 'venv'}
TEST_KINDS = {'tests', 'fixture', 'test_configuration'}
KINDS = TEST_KINDS | {'production', 'environment', 'artifacts'}


def canonical_path(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('Use a canonical relative workspace path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in PRIVATE | {'..'} for part in path.parts):
        raise ValueError('Path is outside the public workspace')
    if path.as_posix() != name or name in {'.', ''}:
        raise ValueError('Path must be canonical')
    return path


def classify(name, manifest):
    canonical_path(name)
    matches = [(len(PurePosixPath(prefix).parts), kind) for prefix, kind in manifest.items()
               if name == prefix or name.startswith(prefix + '/')]
    if not matches:
        raise ValueError('Unclassified path; ask analysis to classify it')
    return max(matches)[1]


def versions(inventory, manifest):
    groups = {key: {} for key in ('production', 'tests', 'environment')}
    for name, digest in inventory.items():
        try:
            kind = classify(name, manifest)
        except ValueError:
            continue
        if kind != 'artifacts':
            groups['tests' if kind in TEST_KINDS else kind][name] = digest
    return {key: identity(value) for key, value in groups.items()}


class LocalWorkspace:
    def __init__(self, root, manifest):
        self.root = Path(root).resolve()
        self.manifest = dict(manifest)
        self.original = {name: self.read(name) for name in self.inventory()
                         if classify(name, self.manifest) == 'production'}

    def path(self, name):
        path = self.root / canonical_path(name)
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(self.root):
            raise ValueError('Symlinks and paths outside workspace are inaccessible')
        return path

    def inventory(self):
        result = {}
        for folder, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in PRIVATE | IGNORED
                             and not (Path(folder) / d).is_symlink())
            for name in sorted(names):
                path = Path(folder) / name
                if path.is_symlink() or not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                try:
                    classify(rel, self.manifest)
                except ValueError:
                    continue
                result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result

    def read(self, name):
        path = self.path(name)
        if path.stat().st_size > 2_000_000:
            raise ValueError('File exceeds the readable limit')
        return path.read_bytes()

    def check(self, name):
        self.path(name)

    def environment(self):
        import importlib.metadata
        import sys

        packages = {}
        for name in ('pytest', 'qb-cubie'):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                pass
        return {'python': sys.version.split()[0], 'packages': packages}

    def baseline(self):
        """Final tests, fixtures, configuration and environment; original production."""
        root = Path(tempfile.mkdtemp(prefix='v6-baseline-', dir=self.root.parent))
        for name in self.inventory():
            kind = classify(name, self.manifest)
            if kind not in TEST_KINDS | {'environment'}:
                continue
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.read(name))
        for name, content in self.original.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return str(root)

    def remove_baseline(self, root):
        shutil.rmtree(root)

    def patch(self):
        current = {name: self.read(name) for name in self.inventory()
                   if classify(name, self.manifest) == 'production'}
        result = []
        for name in sorted(self.original.keys() | current.keys()):
            old, new = self.original.get(name, b''), current.get(name, b'')
            if old == new:
                continue
            result.extend(difflib.unified_diff(old.decode('utf-8', 'replace').splitlines(True),
                                              new.decode('utf-8', 'replace').splitlines(True),
                                              fromfile='a/' + name if name in self.original else '/dev/null',
                                              tofile='b/' + name if name in current else '/dev/null'))
        return ''.join(result)


def inferred_manifest(names):
    """Classify public snapshot paths once; ambiguous new paths stay closed."""
    manifest = {}
    configs = {'pytest.ini', '.pytest.ini', 'tox.ini', 'setup.cfg', 'pyproject.toml'}
    for name in sorted(names):
        path = canonical_path(name)
        parts = path.parts
        if any(p in {'tests', 'test', 'fixtures'} or p.startswith('test_') for p in parts):
            kind = 'tests'
        elif path.name == 'conftest.py':
            kind = 'fixture'
        elif path.name in configs:
            kind = 'test_configuration'
        elif path.suffix == '.py' or parts[0] == 'src':
            kind = 'production'
        else:
            kind = 'environment'
        manifest[name] = kind
        if len(parts) > 1 and kind in {'tests', 'production'}:
            manifest.setdefault(parts[0], kind)
            if kind == 'production':
                manifest[parts[0]] = 'production'
        for index, part in enumerate(parts[:-1]):
            if part in {'tests', 'test', 'fixtures'}:
                manifest['/'.join(parts[:index+1])] = 'tests'
    manifest.setdefault('tests', 'tests')
    manifest.setdefault('src', 'production')
    return manifest


# Only these internal operations are sent to the container. They are never
# exposed in a model schema and never accept a command or arbitrary Python.
REMOTE_SCRIPT = r'''
import base64, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile
root = pathlib.Path('/workspace')
a = json.loads(sys.argv[1])
private = {'.git', 'evaluator', 'secret', 'evidence', 'private', 'reference', '.aws', '.codex', '.agents'}
ignored = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.venv', 'venv'}
def target(name):
    p = pathlib.PurePosixPath(name)
    if not name or p.is_absolute() or any(x in private | {'..'} for x in p.parts) or p.as_posix() != name:
        raise ValueError('Invalid public workspace path')
    path = root / p
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root):
        raise ValueError('Symlinks are inaccessible')
    return path
def inventory():
    result = {}
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in private | ignored and not (pathlib.Path(folder)/d).is_symlink())
        for n in sorted(names):
            p = pathlib.Path(folder) / n
            if not p.is_symlink() and p.is_file():
                result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result
op = a['op']
if op == 'inventory':
    result = inventory()
elif op == 'environment':
    import importlib.metadata
    packages = {}
    for name in ('pytest', 'qb-cubie'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    result = {'python': sys.version.split()[0], 'packages': packages}
elif op == 'read':
    p = target(a['path'])
    if p.stat().st_size > 2_000_000:
        raise ValueError('File exceeds readable limit')
    result = base64.b64encode(p.read_bytes()).decode()
elif op == 'check':
    target(a['path'])
    result = True
elif op == 'baseline':
    dest = pathlib.Path(tempfile.mkdtemp(prefix='v6-baseline-'))
    archive = subprocess.run(['git', '-C', str(root), 'archive', '_swegemma_baseline'], capture_output=True, check=True)
    subprocess.run(['tar', '-x', '-C', str(dest)], input=archive.stdout, check=True)
    manifest = a['manifest']
    def kind(name):
        matches = [(len(pathlib.PurePosixPath(p).parts), k) for p, k in manifest.items()
                   if name == p or name.startswith(p + '/')]
        return max(matches)[1] if matches else 'environment'
    for folder, dirs, names in os.walk(dest, topdown=False):
        for name in names:
            p = pathlib.Path(folder)/name
            if kind(p.relative_to(dest).as_posix()) != 'production':
                p.unlink()
    for name in inventory():
        if kind(name) in {'tests', 'fixture', 'test_configuration', 'environment'}:
            p = dest/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(target(name).read_bytes())
    production = {}
    for folder, dirs, names in os.walk(dest, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in private | ignored)
        for name in names:
            p = pathlib.Path(folder)/name
            relative = p.relative_to(dest).as_posix()
            if kind(relative) == 'production' and p.is_file() and not p.is_symlink():
                production[relative] = hashlib.sha256(p.read_bytes()).hexdigest()
    fingerprint = hashlib.sha256(json.dumps(production, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    result = {'path': str(dest), 'production': fingerprint}
elif op == 'cleanup_baseline':
    p = pathlib.Path(a['path'])
    if p.parent != pathlib.Path('/tmp') or not p.name.startswith('v6-baseline-') or p.is_symlink():
        raise ValueError('Invalid baseline cleanup')
    shutil.rmtree(p)
    result = True
elif op == 'production_patch':
    for name in a['paths']:
        target(name)
    result = subprocess.run(['git', '-C', str(root), 'diff', '--binary', '_swegemma_baseline', '--',
                             *a['paths']], capture_output=True, text=True, check=True).stdout if a['paths'] else ''
else:
    raise ValueError('Unknown workspace operation')
print(json.dumps(result))
'''


class RemoteWorkspace:
    """Read public workspace state through the existing isolated container manager."""
    def __init__(self, manager, sandbox, timeout=10):
        self.manager, self.sandbox, self.timeout = manager, sandbox, timeout
        original = self._call(op='inventory')
        self.original_names = set(original)
        self.manifest = inferred_manifest(self.original_names)
        self.original_production = versions(original, self.manifest)['production']

    def _call(self, **payload):
        import json

        from .workspace import command
        result = self.manager.exec(self.sandbox, command(REMOTE_SCRIPT, json.dumps(payload)), timeout=self.timeout)
        if result.exit_code or result.timed_out:
            raise OSError('Container workspace operation failed: ' + result.stderr[-500:])
        return json.loads(result.stdout)

    def inventory(self):
        return {p: h for p, h in self._call(op='inventory').items()
                if any(p == key or p.startswith(key + '/') for key in self.manifest)}

    def read(self, name):
        import base64
        canonical_path(name)
        return base64.b64decode(self._call(op='read', path=name))

    def check(self, name):
        canonical_path(name)
        self._call(op='check', path=name)

    def environment(self):
        return self._call(op='environment')

    def baseline(self):
        result = self._call(op='baseline', manifest=self.manifest)
        if result['production'] != self.original_production:
            self.remove_baseline(result['path'])
            raise OSError('Baseline production differs from the original workspace snapshot')
        return result['path']

    def remove_baseline(self, root):
        self._call(op='cleanup_baseline', path=root)

    def patch(self):
        from .workspace import patch
        return patch(self.manager, self.sandbox)

    def production_patch(self):
        paths = sorted(p for p in self.original_names | self.inventory().keys()
                       if classify(p, self.manifest) == 'production')
        return self._call(op='production_patch', paths=paths)
