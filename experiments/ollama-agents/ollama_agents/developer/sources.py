"""Explicit phase grants and snapshots of a small developer workspace."""

import ast
import os
from pathlib import Path

from ..context import ContextBuilder
from ..errors import invalid
from ..paths import directory, relative
from ..workspace import WorkspacePolicy


def inventory(root):
    """Reject symlinks and special files without hiding any workspace entries."""
    result: list[str] = []
    for folder, children, files in os.walk(directory(root), followlinks=False):
        for name in children + files:
            path = Path(folder) / name
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise invalid(f'Forbidden workspace source: {path}')
        result.extend((Path(folder) / name).relative_to(root).as_posix() for name in files)
    return sorted(result)


def is_test(name):
    """Recognize only Python tests within the explicit tests directory."""
    path = Path(name)
    return name.startswith('tests/') and path.suffix == '.py'


class DeveloperSources:
    """Bind accepted snapshots and separate original code from submitted tests."""

    def __init__(self, root):
        self.root = directory(root)
        self.originals = inventory(self.root)
        self.production = {name for name in self.originals if name.endswith('.py') and not is_test(name)}
        self.docs = {documentation_name(self.originals)}
        self.expected = self.hashes()
        self.frozen = None

    def policy(self, writable=()):
        """Grant reads to the current inventory and writes to a specific proposal set."""
        return WorkspacePolicy(root=self.root, readable=inventory(self.root), writable=list(writable))

    def hashes(self):
        """Hash all actual files independently of model claims."""
        policy = self.policy()
        return policy.artifact_hashes(list(policy.readable))

    def unchanged(self):
        """Reject external edits, additions and deletions before any further action."""
        if self.hashes() != self.expected:
            raise invalid('Developer workspace changed outside accepted proposals; frozen tests are immutable')

    def context(self, capacity):
        """Read the complete small visible project, with bound file hashes."""
        policy = self.policy()
        return ContextBuilder(policy=policy).build(paths=list(policy.readable), max_bytes=capacity,
                                                   prompt_bytes=0, output_reserve_bytes=0)

    def write(self, files, phase):
        """Check every permission and Python syntax before atomically publishing."""
        allowed = self._allowed(files, phase)
        for name, content in files.items():
            if name.endswith('.py'):
                try:
                    ast.parse(content, filename=name)
                except (SyntaxError, ValueError) as error:
                    raise invalid(f'Python syntax error in test/code {name}: {error}') from error
        result = self.policy(allowed).write_files(files)
        self.expected = self.hashes()
        return result

    def _allowed(self, files, phase):
        """No proposal can grant itself access to original files or frozen tests."""
        for name in files:
            relative(name)
            permitted = (is_test(name) and name not in self.originals if phase == 'test_design'
                         else name in self.production or name in self.docs)
            if not permitted:
                detail = ' Create new Python tests below tests/, e.g. tests/test_contract.py; preserve originals.' if phase == 'test_design' else ''
                raise invalid(f'File not allowed in phase {phase}: {name}.{detail}')
        return list(files)

    def freeze(self):
        """Retain exact test hashes for external auditing and all later phases."""
        self.frozen = {name: value for name, value in self.expected.items() if is_test(name)}
        if not self.frozen:
            raise invalid('Test design requires submitted tests')


def documentation_name(originals):
    """Choose a fresh documentation destination without overwriting existing usage."""
    candidate, index = 'USAGE.md', 0
    while candidate in originals:
        index += 1
        candidate = f'USAGE.agent-{index}.md'
    return candidate
