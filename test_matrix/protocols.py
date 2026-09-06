from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Tuple, List, Any, Optional
from protocols import Arena, WorldState

# ========== DATACLASSES ===============================================================================================

@dataclass
class Scenarios:
    # 1:1 → arises implicitly when both values are 1.
    n_to_one: int = 1  # N:1 → Scales the list of pre-states
    one_to_n: int = 1  # 1:N → Scales the list of post-states
    # N:N → arises implicitly when both values are greater than 1.

@dataclass
class Aspects:
    memory: int = 0       # 0 = inactiv, > 0 = step_complexity for args/kwargs
    filesystem: int = 0   # 0 = inactiv, > 0 = step_complexity for fs
    environment: int = 0  # 0 = inactiv, > 0 = step_complexity for arena

@dataclass
class Overhead:
    fs: int = 0
    arena: int = 0

@dataclass
class EBTMatrixConfig:
    scenarios: Scenarios
    aspects: Aspects
    overhead: Overhead
    arena: Optional[Arena] = None
    multiprocessing: bool = False


# ========== PROTOCOLS =================================================================================================

class MatrixTarget(Protocol):
    matrix_type: str  # "1:1" | "N:1" | "1:N" | "N:N"
    cache_dir: str  # The name of the dedicated directory within .matrix_cache

    def target(self, *args, **kwargs) -> Any:
        """
        The actual implementation that performs the transformation.
        It must be equipped to handle the iterative processing of batch inputs (step_complexity)
        and navigate through noisy data.
        """
        ...
    def _execute_memory(self, *args, **kwargs) -> Any: ...
    def _execute_fs(self, *args, **kwargs) -> Any: ...
    def _execute_env(self, *args, **kwargs) -> Any: ...


    def build(self, config: EBTMatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """
        Orchestrates the incremental assembly of assets
        and composes the fully declared pre- and post-states for the engine from them.
        """
        ...
    def _build_pre(self): ...
    def _build_post(self): ...

    ...