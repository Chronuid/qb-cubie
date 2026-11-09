"""Internal script run by TempFS using the caller's Python interpreter."""

import multiprocessing
import pickle
import sys
import traceback
from pathlib import Path


def main():
    input_path, output_path = map(Path, sys.argv[1:])
    with input_path.open("rb") as stream:
        # Load the transport from caller paths before giving workspace modules
        # precedence for target imports (a fixture could itself be cloudpickle.py).
        import_paths, authkey = pickle.load(stream)
        sys.path[:] = import_paths
        multiprocessing.current_process().authkey = authkey
        import cloudpickle

        sys.path.insert(0, str(Path.cwd()))
        try:
            target, args, kwargs = cloudpickle.load(stream)
            result = (True, target(*args, **kwargs), None)
        except BaseException as error:  # noqa: BLE001 - the process boundary transports all target exceptions
            # KeyboardInterrupt/SystemExit must reach the caller as exceptions,
            # without terminating the runner before it writes its response.
            result = (False, error, traceback.format_exc())
    try:
        payload = cloudpickle.dumps(result)
    except Exception as error:  # noqa: BLE001 - user-defined reducers can raise arbitrary exceptions
        payload = cloudpickle.dumps((
            False,
            RuntimeError(f"TempFS could not serialize the target result or exception: {error}"),
            traceback.format_exc(),
        ))
    output_path.write_bytes(payload)


if __name__ == "__main__":
    main()
