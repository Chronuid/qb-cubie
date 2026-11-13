"""Data-only primitives shared by SWE-bench import and evaluation."""

import ctypes
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v

CONTRACT = "swebench-v1"
SOURCES = {"SWE-bench/SWE-bench", "SWE-bench/SWE-bench_Lite", "SWE-bench/SWE-bench_Verified"}


def git_environment():
    """Keep caller Git overrides and global hooks/configuration out of object reads."""
    return {**{key: value for key, value in os.environ.items() if not key.startswith('GIT_')},
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_NO_REPLACE_OBJECTS': '1',
            'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0'}


def encode(value):
    """Encode canonical finite UTF-8 JSON data."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(value):
    """Return the SHA-256 digest of exact bytes."""
    return hashlib.sha256(value).hexdigest()


def write(path, value):
    """Write a deterministic JSON document and its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode(value) + b"\n")


def commit(value, field):
    """Validate a full immutable Git commit identifier."""
    v.require(type(value) is str and re.fullmatch(r"[a-fA-F0-9]{40}", value), field, "expected full immutable commit")
    return value


def repository(value):
    """Validate a safe repository owner and name."""
    v.require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", value),
              "repo", "expected owner/name repository")
    return value


def license_text(value, field):
    """Require an explicit resolved license declaration."""
    v.text(value, field)
    v.require(value.strip().lower() not in {"unknown", "none", "noassertion", "unlicensed", "other"}, field, "unresolved license")
    return value


def normalize(row):
    """Normalize one complete source record without dropping private metadata."""
    row = v.snapshot(v.mapping(row, "record"))
    identifier = v.identifier(row.get("instance_id"), "instance_id")
    _record_fields(row, identifier)
    row['environment_setup_commit'] = _setup_commit(row.get('environment_setup_commit'), identifier)
    for field in ('FAIL_TO_PASS', 'PASS_TO_PASS'):
        row[field] = _test_ids(row.get(field), identifier, field)
    v.require(not set(row['FAIL_TO_PASS']) & set(row['PASS_TO_PASS']), identifier, 'FAIL_TO_PASS/PASS_TO_PASS overlap')
    return row


def inventory(root):
    """Inventory package files, modes and symlink identities."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path == root / "swebench-import.json" or (path.is_dir() and not path.is_symlink()):
            continue
        v.require(path.resolve().is_relative_to(root.resolve()), "path", "symlink escapes package")
        result[path.relative_to(root).as_posix()] = {
            "mode": path.lstat().st_mode & 0o777,
            "symlink": str(path.readlink()) if path.is_symlink() else None,
            "sha256": sha(str(path.readlink()).encode() if path.is_symlink() else path.read_bytes()),
        }
    return result


def verify_inventory(root):
    """Verify package material and its bound import plan."""
    manifest = v.read_data(Path(root) / "swebench-import.json")
    v.require(inventory(root) == manifest.get("inventory"), "swebench.integrity", "inventory hash, mode or file coverage differs")
    plan = v.mapping(manifest.get('plan'), 'swebench.plan')
    checksum = sha(encode({key: value for key, value in plan.items() if key != 'plan_sha256'}))
    v.require(checksum == plan.get('plan_sha256') == manifest.get('plan_sha256'), 'swebench.plan_sha256', 'plan integrity mismatch')
    v.require(manifest.get('loader_contract') == CONTRACT == plan.get('loader_contract'), 'swebench.loader_contract', 'unsupported loader contract')
    v.require(manifest.get('harness_revision') == plan['rules']['harness_revision'], 'swebench.harness_revision', 'plan differs')
    return manifest


def publish(staging, destination):
    """Atomically publish a directory without replacing an existing target."""
    if os.name == 'nt':
        staging.rename(destination)
        return
    rename = _rename()
    if rename(-100, os.fsencode(staging), -100, os.fsencode(destination), 1) != 0:
        _publication_error()


def _record_fields(row, identifier):
    """Check required textual fields and repository identity."""
    for field in ('repo', 'base_commit', 'version', 'problem_statement', 'patch', 'test_patch'):
        v.text(row.get(field), f'{identifier}.{field}')
    repository(row['repo'])
    commit(row['base_commit'], f'{identifier}.base_commit')


def _setup_commit(value, identifier):
    """Normalize the optional provisioning commit."""
    if value == '' or value is None:
        return None
    return commit(value, f'{identifier}.environment_setup_commit')


def _test_ids(value, identifier, field):
    """Normalize a distinct list of required test identifiers."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as error:
            raise ValueError(f'{identifier}.{field}: invalid JSON') from error
    return v.strings(value, f'{identifier}.{field}', nonempty=field == 'FAIL_TO_PASS')


def _rename():
    """Resolve the platform's atomic directory publication primitive."""
    library = ctypes.CDLL(None, use_errno=True)
    rename = getattr(library, 'renameat2', None)
    if rename is None:
        raise ValueError('destination: atomic no-replace publication unsupported on this platform')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    return rename


def docker(field, detail) -> str:
    """Resolve the required container executable or report its absence."""
    binary = shutil.which('docker')
    if binary is None:
        raise ValueError(f'{field}: {detail}')
    return binary


def _publication_error():
    """Classify failed atomic publication without overwriting the target."""
    import errno
    number = ctypes.get_errno()
    if number == errno.EEXIST:
        raise ValueError('destination: already exists; refusing overwrite')
    raise OSError(number, 'atomic package publication failed')
