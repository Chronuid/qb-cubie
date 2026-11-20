"""Safe Windows .exe launcher relocation for uv PE-resource trampolines and distlib wrappers."""

import ctypes
import ntpath
import os
import posixpath
import re
import struct
from pathlib import Path
from typing import Any

_LOAD_LIBRARY_AS_DATAFILE = 0x2
_RT_RCDATA = 10
_PYTHON_EXE_RE = re.compile(r"(?:python|[π𝜋]thon)w?(?:\d+(?:\.\d+)*t?)?(?:_d)?(?:\.exe)?", re.IGNORECASE)
_RESOURCE_SPECS: tuple[tuple[str, list[Any], Any], ...] = (
    ("LoadLibraryExW", [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_uint32], ctypes.c_void_p),
    ("FindResourceW", [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_void_p], ctypes.c_void_p),
    ("SizeofResource", [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_uint32),
    ("LoadResource", [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_void_p),
    ("LockResource", [ctypes.c_void_p], ctypes.c_void_p),
    ("FreeLibrary", [ctypes.c_void_p], ctypes.c_int),
    ("BeginUpdateResourceW", [ctypes.c_wchar_p, ctypes.c_int], ctypes.c_void_p),
    (
        "UpdateResourceW",
        [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint16, ctypes.c_char_p, ctypes.c_uint32],
        ctypes.c_int,
    ),
    ("EndUpdateResourceW", [ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
)


def relocate_windows_launcher(script: Path, base: Path, clone: Path) -> bool:
    """Relocate verified uv PE-resource or distlib ZIP .exe launchers, rejecting all others."""
    if _relocate_uv_trampoline(script, base, clone):
        return True
    return _relocate_distlib_launcher(script, base, clone)


def _resource_kernel32() -> Any:
    """Return configured ctypes windll.kernel32 interface on Windows, or None."""
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return None
    return _configure_resource_lib(windll.kernel32)


def _configure_resource_lib(lib: Any) -> Any:
    """Bind explicit Win32 PE resource loader and updater signatures."""
    for name, argtypes, restype in _RESOURCE_SPECS:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = argtypes, restype
    return lib


def _relocate_uv_trampoline(script: Path, base: Path, clone: Path) -> bool:
    """Inspect and rewrite UV_PYTHON_PATH in verified uv Script trampolines."""
    lib = _resource_kernel32()
    resources = _read_uv_resources(lib, script) if lib is not None else None
    if resources is None or resources[0] != b"\x01":
        return False
    try:
        target = resources[1].decode("utf-8")
    except UnicodeDecodeError:
        return False
    if _is_safe_relative_python(target):
        return True
    new_target = _match_base_python(target, base, clone)
    return bool(new_target and _write_uv_python_path(lib, script, new_target.encode("utf-8")))


def _read_uv_resources(lib: Any, script: Path) -> tuple[bytes, bytes] | None:
    """Load uv trampoline metadata read-only and free the module handle before updating."""
    module = lib.LoadLibraryExW(str(script), None, _LOAD_LIBRARY_AS_DATAFILE)
    if not module:
        return None
    try:
        kind = _read_pe_resource(lib, module, "UV_TRAMPOLINE_KIND")
        py_path = _read_pe_resource(lib, module, "UV_PYTHON_PATH")
        return None if kind is None or py_path is None else (kind, py_path)
    finally:
        lib.FreeLibrary(module)


def _read_pe_resource(lib: Any, module: Any, name: str) -> bytes | None:
    """Read one RT_RCDATA resource buffer from a PE image loaded as datafile."""
    res = lib.FindResourceW(module, name, _RT_RCDATA)
    if not res:
        return None
    size = lib.SizeofResource(module, res)
    mem = lib.LoadResource(module, res) if size else 0
    ptr = lib.LockResource(mem) if mem else 0
    return ctypes.string_at(ptr, size) if ptr else None


def _write_uv_python_path(lib: Any, script: Path, new_bytes: bytes) -> bool:
    """Write the relocated UTF-8 interpreter path into the trampoline RT_RCDATA table."""
    handle = lib.BeginUpdateResourceW(str(script), 0)
    if not handle:
        return False
    ok = bool(lib.UpdateResourceW(handle, _RT_RCDATA, "UV_PYTHON_PATH", 0, new_bytes, len(new_bytes)))
    committed = bool(lib.EndUpdateResourceW(handle, 0 if ok else 1))
    return ok and committed


def _is_safe_relative_python(target: str) -> bool:
    """Accept safe relative Python interpreter targets without parent-directory traversal."""
    normalized = target.replace("\\", "/")
    if not target or target.startswith("/") or ntpath.splitdrive(target)[0]:
        return False
    clean = posixpath.normpath(normalized)
    return not clean.startswith("..") and bool(_PYTHON_EXE_RE.fullmatch(posixpath.basename(clean)))


def _match_base_python(target: str, base: Path, clone: Path) -> str | None:
    """Verify target points to a base Python executable and map it into clone."""
    norm_target = target.replace("\\", "/").rstrip("/")
    cmp_target = norm_target.casefold() if os.name == "nt" else norm_target
    for root in dict.fromkeys((base, base.resolve())):
        root_str = str(root).replace("\\", "/").rstrip("/")
        cmp_root = root_str.casefold() if os.name == "nt" else root_str
        if cmp_target.startswith(cmp_root + "/"):
            rel = norm_target[len(cmp_root) + 1 :]
            parts = rel.split("/")
            if ".." not in parts and _PYTHON_EXE_RE.fullmatch(parts[-1]):
                return str(clone / Path(*parts))
    return None


def _relocate_distlib_launcher(script: Path, base: Path, clone: Path) -> bool:
    """Relocate MZ + #!shebang + ZIP distlib/pip console executables cleanly."""
    updated = _rewrite_distlib_bytes(script.read_bytes(), base, clone)
    if updated is None:
        return False
    script.write_bytes(updated)
    return True


def _rewrite_distlib_bytes(data: bytes, base: Path, clone: Path) -> bytes | None:
    """Rewrite the interpreter path inside a verified distlib launcher payload."""
    span = _locate_distlib_span(data)
    parsed = _parse_shebang_command(data[span[0] : span[1]]) if span else None
    new_exe = _match_base_python(parsed[0], base, clone) if parsed else None
    if span is None or parsed is None or new_exe is None:
        return None
    quoted = f'"{new_exe}"' if " " in new_exe else new_exe
    header = f"#!{quoted}{parsed[1]}".encode("utf-8") + parsed[2]
    return data[: span[0]] + header + data[span[1] :]


def _locate_distlib_span(data: bytes) -> tuple[int, int] | None:
    """Validate PE header, trailing ZIP structure, and immediately preceding shebang line."""
    if not data.startswith(b"MZ"):
        return None
    zip_start = _find_zip_start(data)
    if zip_start is None:
        return None
    shebang_start = data.rfind(b"#!", 0, zip_start)
    if shebang_start < 0 or not data[:zip_start].endswith(b"\n"):
        return None
    return shebang_start, zip_start


def _find_zip_start(data: bytes) -> int | None:
    """Compute and verify ZIP local header start offset from the trailing EOCD record."""
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0 or eocd + 22 > len(data):
        return None
    comment_len = struct.unpack_from("<H", data, eocd + 20)[0]
    if eocd + 22 + comment_len != len(data):
        return None
    cd_size, cd_offset = struct.unpack_from("<II", data, eocd + 12)
    zip_start = eocd - cd_size - cd_offset
    if zip_start < 0 or data[zip_start : zip_start + 4] != b"PK\x03\x04":
        return None
    return zip_start


def _parse_shebang_command(raw: bytes) -> tuple[str, str, bytes] | None:
    """Decode and split a quoted or unquoted distlib shebang line."""
    ending = b"\r\n" if raw.endswith(b"\r\n") else b"\n"
    try:
        line = raw[2 : len(raw) - len(ending)].decode("utf-8")
    except UnicodeDecodeError:
        return None
    if "\n" in line or not line:
        return None
    if line.startswith('"'):
        end_quote = line.find('"', 1)
        return None if end_quote < 0 else (line[1:end_quote], line[end_quote + 1 :], ending)
    exe_str, *tail = line.split(maxsplit=1)
    return exe_str, (f" {tail[0]}" if tail else ""), ending
