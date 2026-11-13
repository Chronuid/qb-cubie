from typing import Any

from .._execution import CaptureTarget

########################################################################################################################
# ========== IPC-CODEC-IMPLEMENTATIONS =================================================================================
########################################################################################################################


# ===== PICKLE-CODEC ===================================================================================================


class PickleCodec:
    file_suffix = ".pkl"
    requirements: list[str] = []

    @staticmethod
    def dump(obj: Any, path: str) -> None:
        import pickle

        target, args, kwargs, decontams = obj
        capture = isinstance(target, CaptureTarget)
        if capture:
            target = target.target
        with open(path, "wb") as f:
            pickle.dump(decontams, f)
            pickle.dump((target, args, kwargs, capture), f)

    @staticmethod
    def load(path: str) -> Any:
        import pickle

        with open(path, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        """Render the child runner with its input and output paths."""
        import textwrap
        return textwrap.dedent(_PICKLE_RUNNER.format(in_path=repr(in_path), out_path=repr(out_path)))


# ===== MSGSPEC-CODEC ===================================================================================================


class MSGspecCodec:
    file_suffix = ".msgpack"
    requirements = ["msgspec"]

    # ----- Services (Orchestrators) -----------------------------------------------------------------------------------

    @classmethod
    def dump(cls, obj: Any, path: str) -> None:
        """Serialize the target, arguments and decontamination rules."""
        import msgspec
        target, args, kwargs, decontams = obj
        target_info = cls._extract_target_info(target)
        payload = {"target": target_info, "args": args, "kwargs": kwargs, "decontams": decontams}
        try:
            with open(path, "wb") as stream:
                stream.write(msgspec.msgpack.encode(payload))
        except TypeError as error:
            raise cls._serialization_error(error) from None

    @staticmethod
    def load(path: str) -> Any:
        """Reads and decodes the execution result from the specified path."""
        import msgspec

        with open(path, "rb") as f:
            return msgspec.msgpack.decode(f.read())

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        """Render the child runner with its input and output paths."""
        import textwrap
        return textwrap.dedent(_MSGSPEC_RUNNER.format(in_path=repr(in_path), out_path=repr(out_path)))

    # ----- Utilities (Workers) ----------------------------------------------------------------------------------------

    @staticmethod
    def _serialization_error(error: TypeError) -> TypeError:
        return TypeError(
            "**It is strongly recommended to use stateless static methods or classmethods.**\n"
            "Instance rehydration via IPC is experimental and may fail for complex objects.\n\n",
            f"IPC Serialization Error: {str(error)}\n\n"
            "By default, the MSGspecCodec supports only primitive data types.\n"
            "Since the payload contains complex objects (e.g., in the target instance's __dict__ or as an argument),\n"
            "**simplify the payload** or explicitly assign a more capable codec to the arena for complex support:\n"
            "> `PyVenv(codec=qb_cubie.CloudpickleCodec()`\n"
            "> Note: CloudpickleCodec cant isolate the host dependencies from the arena yet.)"
        )

    @classmethod
    def _extract_target_info(cls, target: Any) -> dict:
        """Routes the provided target to the appropriate extraction strategy."""
        if isinstance(target, CaptureTarget):
            return {**cls._extract_target_info(target.target), "capture_exception": True}
        if isinstance(target, str):
            return cls._extract_string(target)
        if hasattr(target, "__self__") and not isinstance(target.__self__, type):
            return cls._extract_instance(target)
        return cls._extract_callable(target)

    @staticmethod
    def _extract_string(target: str) -> dict:
        """Parses late-binding string targets into module and qualname components."""
        if ":" in target:
            module_name, qualname = target.split(":", 1)
        else:
            parts = target.split(".")
            module_name, qualname = ".".join(parts[:-1]), parts[-1]
        return {"type": "string", "module": module_name, "qualname": qualname}

    @staticmethod
    def _extract_instance(target: Any) -> dict:
        """Describe a bound method and warn about experimental state rehydration."""
        import warnings
        warnings.warn(
            "It is strongly recommended to use stateless static methods or classmethods. "
            "Instance rehydration via IPC is experimental and may fail for complex objects.",
            UserWarning, stacklevel=2,
        )
        return {"type": "instance", "module": target.__module__,
                "qualname": target.__qualname__, "state": target.__self__.__dict__}

    @staticmethod
    def _extract_callable(target: Any) -> dict:
        """Extracts module and qualname references from standard functions and unbound methods."""
        return {"type": "callable", "module": target.__module__, "qualname": target.__qualname__}


# ===== CLOUDPICKLE-CODEC ==============================================================================================


class CloudpickleCodec:
    file_suffix = ".cpkl"
    requirements = ["cloudpickle"]

    def __init__(self, isolation: int = 1):
        """Configure serialization with an experimental dependency-isolation setting."""
        # The isolation hook is currently a placeholder for both supported levels.
        self.isolation = isolation

    # ----- Services ---------------------------------------------------------------------------------------------------

    def dump(self, obj: Any, path: str) -> None:
        """Serialize the target, arguments and decontamination rules by value."""
        target, args, kwargs, decontams = obj
        capture = isinstance(target, CaptureTarget)
        if capture:
            target = target.target
        modules = self._register_modules((target, *args, *kwargs.values()))
        try:
            self._serialize_payload(target, args, kwargs, decontams, capture, path)
        finally:
            self._unregister_modules(modules)

    @staticmethod
    def load(path: str) -> Any:
        """Reads and decodes the execution result from the specified path."""
        import cloudpickle  # type: ignore[import-untyped]

        with open(path, "rb") as f:
            return cloudpickle.load(f)

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        """Render the child runner with its input and output paths."""
        import textwrap
        return textwrap.dedent(_CLOUDPICKLE_RUNNER.format(in_path=repr(in_path), out_path=repr(out_path)))

    # ----- Utilities (Workers) ----------------------------------------------------------------------------------------

    def _serialize_payload(self, target, args, kwargs, decontams, capture, path) -> None:
        import cloudpickle  # type: ignore[import-untyped]

        if self.isolation >= 1:
            self._apply_dependency_isolation()
        payload = {"target": target, "args": args, "kwargs": kwargs,
                   "decontams": decontams, "capture_exception": capture}
        with open(path, "wb") as stream:
            cloudpickle.dump(payload, stream)

    @classmethod
    def _register_modules(cls, items):
        import cloudpickle  # type: ignore[import-untyped]

        modules = set()
        for item in items:
            module = cls._value_module(item)
            if module is not None:
                cloudpickle.register_pickle_by_value(module)
                modules.add(module)
        return modules

    @staticmethod
    def _value_module(item):
        import sys

        name = getattr(item, "__module__", None)
        if not name or name not in sys.modules:
            return None
        # Preserve canonical stdlib class identities in the receiving interpreter.
        if name.partition(".")[0] in sys.stdlib_module_names:
            return None
        if name.startswith(("builtins", "_", "cloudpickle")):
            return None
        return sys.modules[str(name)]

    @staticmethod
    def _unregister_modules(modules) -> None:
        import cloudpickle  # type: ignore[import-untyped]

        for module in modules:
            cloudpickle.unregister_pickle_by_value(module)

    def _apply_dependency_isolation(self):
        """Reserve the hook for future dependency isolation."""
        pass


_PICKLE_RUNNER = """
            import pickle
            import _cubie_phantom
            try:
                with open({in_path}, 'rb') as f:
                    decontams = pickle.load(f)
                    with _cubie_phantom.activate_hook(decontams) as imports:
                        t, a, k, capture = pickle.load(f)
                        if isinstance(t, str):
                            import importlib
                            if ":" in t: module_name, qualname = t.split(":", 1)
                            else:
                                parts = t.split(".")
                                module_name = ".".join(parts[:-1])
                                qualname = parts[-1]
                            mod = importlib.import_module(module_name)
                            t = mod
                            for part in qualname.split('.'): t = getattr(t, part)
                        imports.finish()
                        status = "CAPTURED_SUCCESS" if capture else "SUCCESS"
                        try:
                            res = t(*a, **k)
                        except Exception as error:
                            if not capture: raise
                            status = "TARGET_EXCEPTION"
                            res = {{"type": type(error).__module__ + "." + type(error).__qualname__,
                                   "message": str(error),
                                   "mro": [cls.__module__ + "." + cls.__qualname__ for cls in type(error).__mro__]}}
                with open({out_path}, 'wb') as f: pickle.dump((status, res), f)
            except Exception as e:
                error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                with open({out_path}, 'wb') as f: pickle.dump(("ERROR", error_msg), f)
        """


_MSGSPEC_RUNNER = """
                import msgspec
                import importlib
                import _cubie_phantom
                try:
                    # ----- 1. Load and split payload -----
                    with open({in_path}, 'rb') as f: data = msgspec.msgpack.decode(f.read())
                    target_info = data["target"]
                    decontams = data.get("decontams", [])
                    # ----- 2. Activate the hook and load the target into the context. -----
                    with _cubie_phantom.activate_hook(decontams) as imports:
                        mod = importlib.import_module(target_info["module"])
                        parts = target_info["qualname"].split('.')
                        if target_info["type"] == "instance":
                            cls_obj = mod
                            for part in parts[:-1]: cls_obj = getattr(cls_obj, part)
                            inst = cls_obj.__new__(cls_obj)
                            inst.__dict__.update(target_info.get("state", {{}}))
                            func = getattr(inst, parts[-1])
                        else:
                            func = mod
                            for part in parts: func = getattr(func, part)
                        imports.finish()
                        # ----- 3. Execute target and report successful result -----
                        capture = target_info.get("capture_exception", False)
                        status = "CAPTURED_SUCCESS" if capture else "SUCCESS"
                        try:
                            res = func(*data["args"], **data["kwargs"])
                        except Exception as error:
                            if not capture: raise
                            status = "TARGET_EXCEPTION"
                            res = {{"type": type(error).__module__ + "." + type(error).__qualname__,
                                   "message": str(error),
                                   "mro": [cls.__module__ + "." + cls.__qualname__ for cls in type(error).__mro__]}}
                    with open({out_path}, 'wb') as f: f.write(msgspec.msgpack.encode([status, res]))
                except Exception as e: # Exception abfangen und an den Host melden
                    error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                    with open({out_path}, 'wb') as f: f.write(msgspec.msgpack.encode(["ERROR", error_msg]))
            """


_CLOUDPICKLE_RUNNER = """
            import cloudpickle, importlib, _cubie_phantom
            try:
                # ----- 1. Fully rehydrate the payload from the byte stream -----
                with open({in_path}, 'rb') as f: data = cloudpickle.load(f)
                target = data["target"]
                decontams = data.get("decontams", [])
                args = data.get("args", ())
                kwargs = data.get("kwargs", {{}})
                # ----- 2. Activate hook and prepare target in the arena vacuum -----
                with _cubie_phantom.activate_hook(decontams) as imports:
                    # --- Resolve late-binding string targets ---
                    if isinstance(target, str):
                        if ":" in target: module_name, qualname = target.split(":", 1)
                        else:
                            parts = target.split(".")
                            module_name = ".".join(parts[:-1])
                            qualname = parts[-1]
                        target = importlib.import_module(module_name)
                        for part in qualname.split('.'): target = getattr(target, part)
                    imports.finish()
                    # ----- 3. Execute -----
                    capture = data.get("capture_exception", False)
                    status = "CAPTURED_SUCCESS" if capture else "SUCCESS"
                    try:
                        res = target(*args, **kwargs)
                    except Exception as error:
                        if not capture: raise
                        status = "TARGET_EXCEPTION"
                        res = {{"type": type(error).__module__ + "." + type(error).__qualname__,
                               "message": str(error),
                               "mro": [cls.__module__ + "." + cls.__qualname__ for cls in type(error).__mro__]}}
                # ----- 4. Serialize successful result -----
                with open({out_path}, 'wb') as f: cloudpickle.dump([status, res], f)
            except Exception as e:
                error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                with open({out_path}, 'wb') as f: cloudpickle.dump(["ERROR", error_msg], f)
        """
