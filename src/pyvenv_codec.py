from typing import Any
import textwrap


# ========== IPC-CODEC-IMPLEMENTATIONS =================================================================================

# ----- PICKLE-CODEC ---------------------------------------------------------------------------------------------------

class PickleCodec:
    file_suffix = ".pkl"

    @staticmethod
    def dump(obj: Any, path: str) -> None:
        import pickle
        with open(path, "wb") as f: pickle.dump(obj, f)

    @staticmethod
    def load(path: str) -> Any:
        import pickle
        with open(path, "rb") as f: return pickle.load(f)

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        return textwrap.dedent(f"""
            import pickle
            try:
                with open({repr(in_path)}, 'rb') as f: t, a, k = pickle.load(f)
                res = t(*a, **k)
                with open({repr(out_path)}, 'wb') as f: pickle.dump(("SUCCESS", res), f)
            except Exception as e:
                with open({repr(out_path)}, 'wb') as f: pickle.dump(("ERROR", e), f)
        """)


# ----- MSGspec-CODEC --------------------------------------------------------------------------------------------------

class MSGspecCodec:
    file_suffix = ".msgpack"
    requirements = ["msgspec"]

    @staticmethod
    def dump(obj: Any, path: str) -> None:
        import msgspec
        target, args, kwargs = obj
        target_info = {
            "module": target.__module__,
            "name": target.__name__
        }
        payload = {"target": target_info, "args": args, "kwargs": kwargs}
        with open(path, "wb") as f: f.write(msgspec.msgpack.encode(payload))

    @staticmethod
    def load(path: str) -> Any:
        import msgspec
        with open(path, "rb") as f: return msgspec.msgpack.decode(f.read())

    @staticmethod
    def get_runner_snippet(in_path: str, out_path: str) -> str:
        return textwrap.dedent(f"""
            import msgspec
            import importlib

            try:
                with open({repr(in_path)}, 'rb') as f: data = msgspec.msgpack.decode(f.read())

                # Modul dynamisch importieren und Funktion extrahieren
                module_name = data["target"]["module"]
                func_name = data["target"]["name"]
                mod = importlib.import_module(module_name)
                func = getattr(mod, func_name)

                # Funktion ausführen
                res = func(*data["args"], **data["kwargs"])
                with open({repr(out_path)}, 'wb') as f:
                    f.write(msgspec.msgpack.encode(["SUCCESS", res]))

            except Exception as e:
                # Exception in String umwandeln, da msgspec keine Objekte serialisiert
                error_msg = f"{{type(e).__name__}}: {{str(e)}}"
                with open({repr(out_path)}, 'wb') as f:
                    f.write(msgspec.msgpack.encode(["ERROR", error_msg]))
        """)