from typing import Final
from pathlib import Path


class EBTMatrix:
    CACHE_ROOT: Final[Path] = Path(".matrix_cache")

    # ... innerhalb der _arrange oder _execute Phase:
    # target.build(self.config, cache_root=self.CACHE_ROOT)