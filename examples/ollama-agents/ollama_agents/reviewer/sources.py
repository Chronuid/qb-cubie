"""Inventory originals, enforce immutable review context and validate findings."""

import ast
import os
import re
from pathlib import Path

from ..context import ContextBuilder
from ..errors import AdapterError, invalid
from ..jsonio import encode
from ..paths import directory
from ..workspace import WorkspacePolicy


class SourceChanged(AdapterError):
    """Mark a fatal context change that cannot be repaired by rewording output."""

    def __init__(self, message):
        super().__init__("invalid_output", message)


def inventory(root):
    """Reject links and special files while collecting every exported original."""
    result: list[str] = []
    for folder, children, files in os.walk(root, followlinks=False):
        for name in children + files:
            path = Path(folder) / name
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise invalid(f'Invalid source path or symlink: {path.name}')
        result.extend((Path(folder) / name).relative_to(root).as_posix()
                      for name in files if (Path(folder) / name).relative_to(root).as_posix() != 'review.json')
    return sorted(result)


class ReviewSources:
    """Bind one complete decoded source snapshot to the original file bytes."""

    def __init__(self, root, *, max_bytes, prompt_bytes, output_reserve_bytes):
        self.root = directory(root)
        names = inventory(self.root)
        self.policy = WorkspacePolicy(root=self.root, readable=names, writable=['review.json'])
        self.context = ContextBuilder(policy=self.policy).build(
            paths=names, max_bytes=max_bytes, prompt_bytes=prompt_bytes,
            output_reserve_bytes=output_reserve_bytes)
        self.hashes = {block['path']: block['sha256'] for block in self.context['files']}
        self.contents = {block['path']: block['content'] for block in self.context['files']}
        if not names or 'task.md' not in names or (self.root / 'review.json').exists():
            raise invalid('Review requires task.md, originals and a fresh review.json destination')

    def unchanged(self):
        """Detect additions, deletions and modifications before accepting further work."""
        try:
            if inventory(self.root) != sorted(self.hashes):
                raise invalid('Review source inventory changed')
            if self.policy.artifact_hashes(list(self.hashes)) != self.hashes:
                raise invalid('Review source hashes changed')
        except AdapterError as error:
            raise SourceChanged(str(error)) from error

    def validate(self, report, criteria):
        """Require complete decisions, genuine source bindings and consistent findings."""
        decisions = decisions_for(report, criteria)
        sources = report['sources']
        if len(sources) != len(set(sources)) or set(sources) != set(self.hashes):
            raise invalid('Review sources must contain the complete original inventory once')
        for finding in report['findings']:
            self._finding(finding, decisions)
        failed = {key for key, value in decisions.items() if value == 'fail'}
        if failed != {finding['criterion_id'] for finding in report['findings']}:
            raise invalid('Every fail criterion requires a concrete finding')

    def _finding(self, finding, decisions):
        """Check source symbol existence without executing submitted production code."""
        if any(not value.strip() for value in finding.values()):
            raise invalid('Finding fields require meaningful nonempty text')
        if decisions.get(finding['criterion_id']) != 'fail':
            raise invalid('Finding criterion must name a requested fail decision')
        explanation(finding)
        path = finding['path']
        if path not in self.contents or finding['symbol'] not in symbols(self.contents[path]):
            raise invalid(f'Finding path or symbol does not exist: {path}:{finding["symbol"]}')

    def publish(self, report):
        """Recheck originals immediately before publishing the validated review."""
        self.unchanged()
        return self.policy.write_files({'review.json': encode(report).decode('utf-8')})


def symbols(content):
    """Collect Python functions, classes and assigned module symbols statically."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()
    return _symbols(tree)


def _symbols(tree, prefix=''):
    """Include qualified class members as well as their local names."""
    result: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.update((node.name, prefix + node.name))
            result.update(_symbols(node, prefix + node.name + '.'))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            result.add(node.id)
        else:
            result.update(_symbols(node, prefix))
    return result


def decisions_for(report, criteria):
    """Require the strict report version and exactly the requested decisions."""
    if type(report['schema_version']) is not int:
        raise invalid('Review schema_version must be integer 1')
    decisions = report['criterion_results']
    if set(decisions) != set(criteria):
        raise invalid('Review criterion_results must cover exactly the requested criteria')
    return decisions


def explanation(finding):
    """Reject known non-explanations without pretending to judge arbitrary semantics."""
    labels = r'(?:severity|priority|schweregrad|priorität)?\s*[:=-]?\s*'
    labels += r'(?:high|medium|low|critical|major|minor|hoch|mittel|niedrig|kritisch|n/?a|none|unknown|tbd)'
    for field in ('mechanism', 'impact'):
        value = finding[field].strip().strip('.!')
        if re.fullmatch(labels, value, re.IGNORECASE):
            raise invalid(f'Finding {field} must explain the concrete cause or consequence, '
                          'including actual and expected behavior; a severity or placeholder is insufficient')
