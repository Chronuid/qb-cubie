import sys
import types
from contextlib import contextmanager
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec, PathFinder
from typing import List, Generator, Any


class PhantomObject:
    """Represents an import placeholder whose runtime use fails explicitly."""

    def __init__(self, name: str = ""):
        self._name = name

    def __getattr__(self, name: str) -> "PhantomObject":
        return PhantomObject(f"{self._name}.{name}")

    def __call__(self, *args, **kwargs) -> "PhantomObject":
        raise TypeError(f"PhantomObject {self._name!r} cannot be called; install the real dependency.")

    def __enter__(self) -> "PhantomObject":
        raise TypeError(f"PhantomObject {self._name!r} cannot be used as a context manager.")

    def __exit__(self, *args) -> None:
        raise TypeError(f"PhantomObject {self._name!r} cannot finish a context manager.")

    def __bool__(self) -> bool:
        raise TypeError(f"PhantomObject {self._name!r} has no runtime truth value.")


class _ImportDecorator(PhantomObject):
    """Allows pytest declarations only while executing a module body."""

    def __getattr__(self, name: str) -> "_ImportDecorator":
        return _ImportDecorator(f"{self._name}.{name}")

    def __call__(self, *args, **kwargs):
        if sys._getframe(1).f_code.co_name != "<module>":
            return super().__call__(*args, **kwargs)
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return self


class _PytestImports(types.ModuleType):
    """Provides narrowly scoped declarations for test modules without pytest."""

    def __getattr__(self, name: str) -> PhantomObject:
        if name in {"fixture", "mark", "param"}:
            return _ImportDecorator(f"pytest.{name}")
        if name.startswith("__"):
            raise AttributeError(name)
        return PhantomObject(f"pytest.{name}")


class PhantomModule(types.ModuleType):
    """Simulates a successfully loaded Python module."""

    def __getattr__(self, name: str) -> PhantomObject:
        if name.startswith("__"):
            raise AttributeError(name)
        return PhantomObject(f"{self.__name__}.{name}")


class PhantomLoader(Loader):
    """Handles the loading process for modules to be intercepted."""

    def create_module(self, spec: ModuleSpec) -> PhantomModule:
        module = PhantomModule(spec.name)
        module.__path__ = []
        return module

    def exec_module(self, module: types.ModuleType) -> None:
        pass


class _PytestLoader(Loader):
    def create_module(self, spec: ModuleSpec) -> _PytestImports:
        return _PytestImports(spec.name)

    def exec_module(self, module: types.ModuleType) -> None:
        pass


class PhantomFinder(MetaPathFinder):
    """Intercepts imports defined in the decontams list."""

    def __init__(self, decontams: List[str]):
        self.decontams = decontams
        self.importing = True

    def find_spec(self, fullname: str, path: Any, target: Any = None) -> ModuleSpec | None:
        for blocked in self.decontams:
            if fullname == blocked or fullname.startswith(blocked + "."):
                return ModuleSpec(fullname, PhantomLoader())
        if self.importing and fullname == "pytest" and PathFinder.find_spec(fullname, path) is None:
            return ModuleSpec(fullname, _PytestLoader())
        return None

    def finish(self) -> None:
        """End declaration support before invoking the target."""
        self.importing = False
        if isinstance(sys.modules.get("pytest"), _PytestImports):
            del sys.modules["pytest"]


@contextmanager
def activate_hook(decontams: List[str]) -> Generator[PhantomFinder, None, None]:
    """Encapsulates the injection of MetaPathFinders and inserts the hook (at position 0) to ensure priority during import."""
    finder = PhantomFinder(decontams)
    sys.meta_path.insert(0, finder)
    try:
        yield finder
    finally:
        finder.finish()
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
