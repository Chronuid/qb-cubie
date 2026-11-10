"""Internal script run by TempFS using the caller's Python interpreter."""

import multiprocessing
import pickle
import sys
import traceback
from pathlib import Path


def main():
    input_path, output_path = map(Path, sys.argv[1:])
    with input_path.open("rb") as stream:
        transport = _prepare_transport(stream)
        result = _call_target(stream, transport)
    output_path.write_bytes(_serialize_result(result, transport))


def _prepare_transport(stream):
    # Load transport from caller paths before giving workspace modules precedence.
    import_paths, authkey = pickle.load(stream)
    sys.path[:] = import_paths
    multiprocessing.current_process().authkey = authkey
    import cloudpickle  # type: ignore[import-untyped]

    sys.path.insert(0, str(Path.cwd()))
    return cloudpickle


def _call_target(stream, transport):
    try:
        target, args, kwargs = transport.load(stream)
        return True, target(*args, **kwargs), None
    except BaseException as error:  # noqa: BLE001 -- transport all target exceptions across the process boundary
        return False, error, traceback.format_exc()


def _serialize_result(result, transport) -> bytes:
    try:
        return transport.dumps(result)
    except Exception as error:  # noqa: BLE001 -- user-defined reducers may raise arbitrary exceptions
        return transport.dumps((
            False,
            RuntimeError(f"TempFS could not serialize the target result or exception: {error}"),
            traceback.format_exc(),
        ))


if __name__ == "__main__":
    main()
