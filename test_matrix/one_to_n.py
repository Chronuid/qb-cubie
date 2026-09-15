import random
from pathlib import Path
from typing import Tuple, List, Any
from test_matrix.protocols import WorldState, MatrixConfig


class One2N_Mock:
    matrix_type: str = "1:N"
    cache_dir: str = "one_to_n_mock"

    def target(self, n_scale: int = 1, mem_scale: int = 0, fs_scale: int = 0, env_scale: int = 0, **kwargs) -> Any:
        """
        Randomly selects a variant from the solution space (n_scale) and constructs the required aspects based on it.
        """
        returns_data = {}
        rand_variant = random.randint(0, max(0, n_scale - 1))
        if mem_scale > 0: returns_data["mem"] = self._execute_memory(rand_variant, mem_scale)
        if fs_scale > 0: returns_data["fs"] = self._execute_fs(rand_variant, fs_scale)
        if env_scale > 0: returns_data["env"] = self._execute_env(rand_variant, env_scale)
        return returns_data

    @staticmethod
    def _execute_memory(variant: int, scale: int) -> List[str]:
        return [f"Variant {variant} | {i} - mem" for i in range(scale)]
    @staticmethod
    def _execute_fs(variant: int, scale: int) -> str:
        for i in range(scale):
            Path(f"mock_fs_v{variant}_{i}.txt").write_text(f"content_v{variant}_{i}")
        return f"Created {scale} files for variant {variant}"
    @staticmethod
    def _execute_env(variant: int, scale: int) -> str:
        return f"Mutated {scale} env vars for variant {variant}"


    def build(self, config: MatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """Orchestrates the 1:N assembly of the test vectors."""
        pre_states = self._build_pre(config)
        post_states = self._build_post(config)
        return pre_states, post_states

    @staticmethod
    def _build_pre(config: MatrixConfig) -> List[WorldState]:
        """Set up the fixed initial state (1)."""
        pre = WorldState(kwargs={
            "n_scale": config.scenarios.one_to_n,
            "mem_scale": config.aspects.memory,
            "fs_scale": config.aspects.filesystem,
            "env_scale": config.aspects.environment
        })
        return [pre]

    @staticmethod
    def _build_post(config: MatrixConfig) -> List[WorldState]:
        """Construct the set of allowed target states (N)."""
        post_states = []
        n_scale = config.scenarios.one_to_n
        mem = config.aspects.memory
        fs = config.aspects.filesystem
        env = config.aspects.environment
        for variant_idx in range(n_scale):
            expected_returns = {}
            expected_fs = {}
            if mem > 0: expected_returns["mem"] = One2N_Mock._execute_memory(variant_idx, mem)
            if fs > 0:
                expected_returns["fs"] = f"Created {fs} files for variant {variant_idx}"
                for i in range(fs):
                    expected_fs[f"mock_fs_v{variant_idx}_{i}.txt"] = lambda \
                            p, v=variant_idx, idx=i: (
                            p.exists() and p.read_text() == f"content_v{v}_{idx}"
                    )
            if env > 0: expected_returns["env"] = One2N_Mock._execute_env(variant_idx, env)
            post = WorldState(returns=expected_returns)
            if fs > 0: post.fs = expected_fs
            post_states.append(post)
        return post_states


class One2N:
    matrix_type = "1:N"
    cache_dir = "one_to_n"

    def target(self, *args, **kwargs) -> Any:
        ...
    def _execute_memory(self, *args, **kwargs) -> Any: pass
    def _execute_fs(self, *args, **kwargs) -> Any: pass
    def _execute_env(self, *args, **kwargs) -> Any: pass

    def build(self, config: MatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        target_cache_dir = cache_root / self.cache_dir
        target_cache_dir.mkdir(parents=True, exist_ok=True)
        return (
            [WorldState(args="Hello")],
            [WorldState(returns="World")]
        )
    def _build_pre(self): pass
    def _build_post(self): pass