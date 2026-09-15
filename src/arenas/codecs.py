from typing import Any

# ========== IPC-CODEC-IMPLEMENTATIONS =================================================================================

# ===== PICKLE-CODEC ===================================================================================================

class PickleCodec:
    file_suffix = ".pkl"
    requirements = []

    @staticmethod
    def dump(obj: Any, path: str) -> None:
        import pickle
        target, args, kwargs, decontams = obj
        with open(path, "wb") as f:
            pickle.dump(decontams, f)
            pickle.dump((target, args, kwargs), f)

    @staticmethod
    def load(path: str) -> Any:
        import pickle
        with open(path, "rb") as f: return pickle.load(f)

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        import textwrap
        return textwrap.dedent(f"""
            import pickle
            import _cubie_phantom
            try:
                with open({repr(in_path)}, 'rb') as f:
                    decontams = pickle.load(f)
                    with _cubie_phantom.activate_hook(decontams):
                        t, a, k = pickle.load(f)
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
                        res = t(*a, **k)   
                with open({repr(out_path)}, 'wb') as f:
                    pickle.dump(("SUCCESS", res), f)
            except Exception as e:
                error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                with open({repr(out_path)}, 'wb') as f:
                    pickle.dump(("ERROR", error_msg), f)
        """)


# ===== MSGSPEC-CODEC ===================================================================================================

class MSGspecCodec:
    file_suffix = ".msgpack"
    requirements = ["msgspec"]

    # ----- Services (Orchestrators) -----------------------------------------------------------------------------------

    @classmethod
    def dump(cls, obj: Any, path: str) -> None:
        """Serializes the target, its parameters, and decontamination rules to the specified path."""
        import msgspec
        target, args, kwargs, decontams = obj
        target_info = cls._extract_target_info(target)
        payload = {"target": target_info, "args": args, "kwargs": kwargs, "decontams": decontams}
        with open(path, "wb") as f: f.write(msgspec.msgpack.encode(payload))

    @staticmethod
    def load(path: str) -> Any:
        """Reads and decodes the execution result from the specified path."""
        import msgspec
        with open(path, "rb") as f: return msgspec.msgpack.decode(f.read())

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        import textwrap
        return textwrap.dedent(f"""
                import msgspec
                import importlib
                import _cubie_phantom
                try:
                    # 1. Payload laden und splitten
                    with open({repr(in_path)}, 'rb') as f:
                        data = msgspec.msgpack.decode(f.read())
                    target_info = data["target"]
                    decontams = data.get("decontams", [])

                    with _cubie_phantom.activate_hook(decontams): # 2. Hook aktivieren und Target in den Kontext laden.
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

                    # 3. Target ausführen und erfolgreiches Ergebnis zurückmelden
                    res = func(*data["args"], **data["kwargs"])
                    with open({repr(out_path)}, 'wb') as f:
                        f.write(msgspec.msgpack.encode(["SUCCESS", res]))
                except Exception as e: # Exception abfangen und an den Host melden
                    error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                    with open({repr(out_path)}, 'wb') as f:
                        f.write(msgspec.msgpack.encode(["ERROR", error_msg]))
            """)


    # ----- Utilities (Workers) ----------------------------------------------------------------------------------------

    @classmethod
    def _extract_target_info(cls, target: Any) -> dict:
        """Routes the provided target to the appropriate extraction strategy."""
        if isinstance(target, str):
            return cls._extract_string(target)
        if hasattr(target, "__self__") and not isinstance(target.__self__, type):
            return cls._extract_instance(target)
        return cls._extract_callable(target)

    @staticmethod
    def _extract_string(target: str) -> dict:
        """Parses late-binding string targets into module and qualname components."""
        if ":" in target: module_name, qualname = target.split(":", 1)
        else:
            parts = target.split(".")
            module_name, qualname = ".".join(parts[:-1]), parts[-1]
        return {"type": "string", "module": module_name, "qualname": qualname}

    @staticmethod
    def _extract_instance(target: Any) -> dict:
        """Extracts the state of bound methods and warns about the experimental nature of IPC rehydration."""
        import warnings
        warnings.warn(
            "It is strongly recommended to use stateless static methods or classmethods. "
            "Instance rehydration via IPC is experimental and may fail for complex objects.",
            UserWarning, stacklevel=2
        )
        return {
            "type": "instance",
            "module": target.__module__,
            "qualname": target.__qualname__,
            "state": target.__self__.__dict__
        }

    @staticmethod
    def _extract_callable(target: Any) -> dict:
        """Extracts module and qualname references from standard functions and unbound methods."""
        return {
            "type": "callable",
            "module": target.__module__,
            "qualname": target.__qualname__
        }