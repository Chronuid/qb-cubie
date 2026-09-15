from pathlib import Path
from typing import Tuple, List, Any
from test_matrix.protocols import WorldState, MatrixConfig


class N2One_Mock:
    matrix_type: str = "N:1"
    cache_dir: str = "n_to_one_mock"

    def target(
            self,
            input_variant: int = 0,
            mem_scale: int = 0,
            fs_scale: int = 0,
            env_scale: int = 0,
            **kwargs
    ) -> Any:
        """
        Transforms a noisy or deviating input into the normalized target state.
        """
        returns_data = {}
        if mem_scale > 0: returns_data["mem"] = self._execute_memory(mem_scale)
        if fs_scale > 0: returns_data["fs"] = self._execute_fs(fs_scale)
        if env_scale > 0: returns_data["env"] = self._execute_env(env_scale)
        return returns_data

    @staticmethod
    def _execute_memory(scale: int) -> List[str]:
        return [f"Normalized | {i} - mem" for i in range(scale)]
    @staticmethod
    def _execute_fs(scale: int) -> str:
        for i in range(scale):
            Path(f"normalized_fs_{i}.txt").write_text(f"normalized_content_{i}")
        return f"Created {scale} normalized files"
    @staticmethod
    def _execute_env(scale: int) -> str:
        return f"Mutated {scale} env vars to normalized state"


    def build(self, config: MatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """Orchestrates the N:1 assembly of the test vectors."""
        pre_states = self._build_pre(config)
        post_states = self._build_post(config)
        return pre_states, post_states

    @staticmethod
    def _build_pre(config: MatrixConfig) -> List[WorldState]:
        """Constructs the set of noisy input states (N)."""
        pre_states = []
        n_scale = config.scenarios.n_to_one
        mem = config.aspects.memory
        fs = config.aspects.filesystem
        env = config.aspects.environment
        for variant_idx in range(n_scale):
            pre = WorldState(kwargs={
                "input_variant": variant_idx,
                "mem_scale": mem,
                "fs_scale": fs,
                "env_scale": env
            })
            pre_states.append(pre)
        return pre_states

    @staticmethod
    def _build_post(config: MatrixConfig) -> List[WorldState]:
        """Builds exactly one standardized target state (1)."""
        mem = config.aspects.memory
        fs = config.aspects.filesystem
        env = config.aspects.environment
        expected_returns = {}
        expected_fs = {}
        if mem > 0: expected_returns["mem"] = N2One_Mock._execute_memory(mem)
        if fs > 0:
            expected_returns["fs"] = f"Created {fs} normalized files"
            for i in range(fs):
                expected_fs[f"normalized_fs_{i}.txt"] = lambda \
                        p, idx=i: (
                            p.exists() and p.read_text() == f"normalized_content_{idx}"
                        )
        if env > 0: expected_returns["env"] = N2One_Mock._execute_env(env)
        post = WorldState(returns=expected_returns)
        if fs > 0:  post.fs = expected_fs
        return [post]


class N2One:
    matrix_type = "N:1"
    cache_dir = "n_to_one"

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