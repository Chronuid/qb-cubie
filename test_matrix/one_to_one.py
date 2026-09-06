from pathlib import Path
from typing import List, Tuple
from protocols import WorldState
from test_matrix.protocols import EBTMatrixConfig

class OneToOne:
    matrix_type = "1:1"
    cache_folder = "one_to_one"

    def build(self, config: EBTMatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        target_cache_dir = cache_root / self.cache_folder
        target_cache_dir.mkdir(parents=True, exist_ok=True)

        # ... Generierung der Bausteine