from pathlib import Path
from typing import Tuple, List, Any
from test_matrix.protocols import WorldState, MatrixConfig


class N2N_Mock:
    matrix_type: str = "N:N"
    cache_dir: str = "n_to_n_mock"

    def target(self, variant_idx: int = 0, mem_scale: int = 0, fs_scale: int = 0, env_scale: int = 0, **kwargs) -> Any:
        """
        Accepts a specific input variant and generates a corresponding target variant from it.
        """
        returns_data = {}
        if mem_scale > 0: returns_data["mem"] = self._execute_memory(variant_idx, mem_scale)
        if fs_scale > 0: returns_data["fs"] = self._execute_fs(variant_idx, fs_scale)
        if env_scale > 0: returns_data["env"] = self._execute_env(variant_idx, env_scale)
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
        """Orchestrates the N:N assembly of the synchronous test vectors."""
        pre_states = self._build_pre(config)
        post_states = self._build_post(pre_states)
        return pre_states, post_states

    @staticmethod
    def _build_pre(config: MatrixConfig) -> List[WorldState]:
        """Construct the set of N specific input states."""
        pre_states = []
        n_scale = config.scenarios.n_to_n
        mem = config.aspects.memory
        fs = config.aspects.filesystem
        env = config.aspects.environment
        for variant_idx in range(n_scale):
            pre = WorldState(kwargs={
                "variant_idx": variant_idx,
                "mem_scale": mem,
                "fs_scale": fs,
                "env_scale": env
            })
            pre_states.append(pre)
        return pre_states

    @staticmethod
    def _build_post(pre_states: List[WorldState]) -> List[WorldState]:
        """
        Derives the exact corresponding Q-state for each specific P-state.
        """
        post_states = []
        for pre in pre_states:
            variant_idx = pre.kwargs.get("variant_idx", 0)
            mem = pre.kwargs.get("mem_scale", 0)
            fs = pre.kwargs.get("fs_scale", 0)
            env = pre.kwargs.get("env_scale", 0)
            expected_returns = {}
            expected_fs = {}
            if mem > 0: expected_returns["mem"] = N2N_Mock._execute_memory(variant_idx, mem)
            if fs > 0:
                expected_returns["fs"] = f"Created {fs} files for variant {variant_idx}"
                for i in range(fs):
                    expected_fs[f"mock_fs_v{variant_idx}_{i}.txt"] = lambda \
                            p, v=variant_idx, idx=i: (
                                p.exists() and p.read_text() == f"content_v{v}_{idx}"
                            )
            if env > 0: expected_returns["env"] = N2N_Mock._execute_env(variant_idx, env)
            post = WorldState(returns=expected_returns)
            if fs > 0: post.fs = expected_fs
            post_states.append(post)
        return post_states


class N2N:
    matrix_type = "N:N"
    cache_dir = "n_to_n"

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