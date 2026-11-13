"""Lazy Hugging Face/official GitHub acquisition with verified atomic caching."""

import json
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from importlib import import_module
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v

from ._common import (
    SOURCES,
    commit,
    encode,
    git_environment,
    license_text,
    normalize,
    publish,
    repository,
    sha,
    write,
)

GITHUB = 'https://github.com/'
TRANSFER_TIMEOUT = 120
MAX_BYTES = 256 * 1024 * 1024


def fetch(url):
    """Bound retries to transient errors and omit credential-bearing diagnostics."""
    for attempt in range(3):
        try:
            return _transfer(url)
        except urllib.error.HTTPError as error:
            if error.code not in {408, 429, 500, 502, 503, 504} or attempt == 2:
                raise ValueError(f'download {urllib.parse.urlsplit(url).hostname}: HTTP {error.code}') from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise ValueError(f'download {urllib.parse.urlsplit(url).hostname}: transport failed') from None
    raise ValueError('download: retries exhausted')


def fetch_git(repo, url, revision):
    """Fetch one immutable Git revision with bounded transient retries."""
    for attempt in range(3):
        try:
            if _git_attempt(repo, url, revision):
                return
        except subprocess.TimeoutExpired:
            pass
        if attempt == 2:
            raise ValueError(f'Git fetch {url}: transport failed')


def acquire(request):
    """Acquire a pinned snapshot without executing dataset or project scripts."""
    from .importer import cache_path, read_snapshot
    v.choice(request['dataset_name'], SOURCES, 'dataset_name')
    commit(request['revision'], 'revision')
    destination = cache_path(request)
    if destination.is_dir():
        read_snapshot(destination, request)
        return destination
    v.require(not request['offline'], 'offline', 'snapshot/cache missing')
    return _download(request, destination, _parquet())


def _transfer(url):
    """Read one bounded HTTP response."""
    started = time.monotonic()
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Cubie-SWEbench/1'}), timeout=30) as response:
        chunks, size = [], 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            v.require(size <= MAX_BYTES and time.monotonic() - started < TRANSFER_TIMEOUT,
                      'download', 'transfer size/time limit exceeded')
            chunks.append(chunk)
        return b''.join(chunks)


def _git_attempt(repo, url, revision):
    """Attempt one bounded fetch and classify permanent revision failures."""
    result = subprocess.run(['git', '-C', str(repo), '-c', 'credential.helper=',
                             '-c', 'http.connectTimeout=30', '-c', 'http.lowSpeedLimit=1024',
                             '-c', 'http.lowSpeedTime=30', 'fetch', '--no-tags', '--depth=1', url, revision],
                            capture_output=True, timeout=TRANSFER_TIMEOUT, env=git_environment(), check=False)
    if result.returncode == 0:
        return True
    diagnostic = result.stderr.lower()
    transient = any(word in diagnostic for word in (b'timed out', b'could not resolve', b'connection', b'http 5'))
    if not transient:
        raise ValueError(f'Git fetch {url}: revision unavailable')
    return False


def _parquet():
    """Load the optional parquet reader only for an actual download."""
    try:
        return import_module('pyarrow.parquet')
    except ImportError as error:
        raise ValueError('download: install qb-cubie[swebench] for parquet acquisition') from error


def _metadata(request):
    """Resolve licensed parquet files from the exact source revision."""
    name, revision = request['dataset_name'], request['revision']
    split = request['split']
    # Split is used only to match metadata, never as a filesystem or URL component.
    info = json.loads(fetch(f'https://huggingface.co/api/datasets/{name}/revision/{revision}'))
    v.require(info.get('sha') == revision, 'source.revision', 'Hugging Face revision differs')
    license_id = license_text(info.get('cardData', {}).get('license'), 'dataset_license')
    siblings = info.get('siblings', [])
    files = sorted(item['rfilename'] for item in siblings
                   if item['rfilename'].startswith(f'data/{split}-') and item['rfilename'].endswith('.parquet'))
    v.require(bool(files), 'split', 'no supported parquet files in pinned source split')
    return (name, revision, split, license_id, files)


def _parquet_rows(temporary, name, revision, files, parquet):
    """Download and normalize every row of the requested split."""
    rows: list[dict] = []
    downloads = Path(temporary) / 'parquet'
    downloads.mkdir()
    for index, filename in enumerate(files):
        v.relative(filename, 'source.file')
        raw = fetch(f'https://huggingface.co/datasets/{name}/resolve/{revision}/{urllib.parse.quote(filename)}')
        path = downloads / f'{index}.parquet'
        path.write_bytes(raw)
        rows.extend(normalize(row) for row in parquet.read_table(path).to_pylist())
    return rows


def _repository_license(storage, rows, repo):
    """Fetch required commits and require a consistent repository license."""
    revisions = sorted({row[key] for row in rows if row['repo'] == repo
                        for key in ('base_commit', 'environment_setup_commit') if row[key] is not None})
    observed = set()
    for revision_id in revisions:
        fetch_git(storage, GITHUB + repo + '.git', revision_id)
        license_info = json.loads(fetch(f'https://api.github.com/repos/{repo}/license?ref={revision_id}'))
        observed.add(license_text(license_info.get('license', {}).get('spdx_id'), f'{repo}.repository_license'))
    v.require(len(observed) == 1, 'repository_license', f'{repo}: inconsistent licenses across commits')
    return observed.pop()


def _git_repositories(root, rows):
    """Provision independent local Git object stores for the split."""
    repositories, licenses = {}, {}
    for repo in sorted({row['repo'] for row in rows}):
        repository(repo)
        relative = 'repos/' + repo.replace('/', '__')
        storage = root / relative
        storage.mkdir(parents=True)
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '--template=', '--bare', str(storage)],
                       check=True, capture_output=True, timeout=30, env=git_environment())
        licenses[repo] = _repository_license(storage, rows, repo)
        repositories[repo] = relative
    return (repositories, licenses)


def _snapshot_files(root, rows, request, license_id, repositories, licenses):
    """Write the complete verified source metadata and record bytes."""
    records = b''.join(encode(row) + b'\n' for row in rows)
    (root / 'records.jsonl').write_bytes(records)
    write(root / 'source.json', {'schema_version': 1, 'dataset_name': request['dataset_name'], 'revision': request['revision'], 'split': request['split'],
          'records_sha256': sha(records), 'dataset_license': license_id,
          'repositories': repositories, 'repository_licenses': licenses})


def _download(request, destination, parquet):
    """Create and atomically publish a fully verified source snapshot."""
    name, revision, _split, license_id, files = _metadata(request)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.download-', dir=destination.parent) as temporary:
        root = Path(temporary) / 'snapshot'
        root.mkdir()
        rows = _parquet_rows(temporary, name, revision, files, parquet)
        repositories, licenses = _git_repositories(root, rows)
        _snapshot_files(root, rows, request, license_id, repositories, licenses)
        _publish_cache(root, destination, request)
    return destination


def _publish_cache(root, destination, request):
    """Validate staging and any concurrently published cache entry."""
    from .importer import read_snapshot
    read_snapshot(root, request)
    if destination.exists():
        read_snapshot(destination, request)
    else:
        publish(root, destination)
