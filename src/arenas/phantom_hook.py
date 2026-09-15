import sys, types
from contextlib import contextmanager
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from typing import List, Generator, Any


class PhantomObject:
    """Silently absorbs all attribute accesses and function calls."""
    def __init__(self, name: str = ""): self._name = name
    def __getattr__(self, name: str) -> 'PhantomObject': return PhantomObject(f"{self._name}.{name}")
    def __call__(self, *args, **kwargs) -> 'PhantomObject': return PhantomObject(self._name)
    def __enter__(self) -> 'PhantomObject': return self
    def __exit__(self, *args) -> None: pass


class PhantomModule(types.ModuleType):
    """Simulates a successfully loaded Python module."""
    def __getattr__(self, name: str) -> PhantomObject: return PhantomObject(name)


class PhantomLoader(Loader):
    """Handles the loading process for modules to be intercepted."""
    def create_module(self, spec: ModuleSpec) -> PhantomModule: return PhantomModule(spec.name)
    def exec_module(self, module: types.ModuleType) -> None:  pass


class PhantomFinder(MetaPathFinder):
    """Intercepts imports defined in the decontams list."""
    def __init__(self, decontams: List[str]): self.decontams = decontams
    def find_spec(self, fullname: str, path: Any, target: Any = None) -> ModuleSpec | None:
        for blocked in self.decontams:
            if fullname == blocked or fullname.startswith(blocked + "."):
                return ModuleSpec(fullname, PhantomLoader())
        return None


@contextmanager
def activate_hook(decontams: List[str]) -> Generator[None, None, None]:
    """
    Encapsulates the injection of MetaPathFinders and inserts the hook (at position 0) to ensure priority during import.
    """
    finder = PhantomFinder(decontams)
    sys.meta_path.insert(0, finder)
    try: yield
    finally:
        if finder in sys.meta_path: sys.meta_path.remove(finder)