from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Tuple, List, Any, Optional, Union
from protocols import Arena, WorldState, RunTrace

# ========== DATACLASSES ===============================================================================================

@dataclass
class Scenarios:
    one_to_one: int = 1
    n_to_one: int = 1
    one_to_n: int = 1
    n_to_n: int = 1

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
class MatrixConfig:
    scenarios: Scenarios
    aspects: Aspects
    overhead: Overhead
    arena: Optional[Arena] = None
    multiprocessing: bool = False


@dataclass
class MatrixReport:
    target_type: str      # Determined solution space (e.g., "N:1", "1:N", "1:1")
    target: str           # Matrix target used (the S in {P}S{Q})
    config: MatrixConfig  # All config data (scenarios, aspects, overhead, etc.)
    trace: RunTrace       # All engine run data (including run_id, duration, evaluation)

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

    def build(
            self,
            config: MatrixConfig,
            cache_root: Path
    ) -> Tuple[List[WorldState], List[WorldState]]:
        """
        Orchestrates the incremental assembly of assets
        and composes the fully declared pre- and post-states for the engine from them.
        """
        ...


class MatrixReporter(Protocol):
    """
    Protocol for EBT Matrix Benchmark result reporters.
    """
    def report(self, reports: Union[List[MatrixReport], MatrixReport]) -> None: ...