from pathlib import Path
from typing import List, Tuple, Any
from protocols import WorldState
from test_matrix.protocols import MatrixConfig


class One2One_Mock:
    matrix_type: str = "1:1"
    cache_dir: str = "one_to_one_mock"

    def target(self, mem_scale: int = 0, fs_scale: int = 0, env_scale: int = 0, **kwargs) -> Any:
        """Orchestrates the transformations based on the injected scalars."""
        returns_data = {}
        if mem_scale > 0: returns_data["mem"] = self._execute_memory(mem_scale)
        if fs_scale > 0: returns_data["fs"] = self._execute_fs(fs_scale)
        if env_scale > 0: returns_data["env"] = self._execute_env(env_scale)
        return returns_data

    @staticmethod
    def _execute_memory(scale: int) -> List[str]: return [f"{i} - mem" for i in range(scale)]
    @staticmethod
    def _execute_fs(scale: int) -> str:
        for i in range(scale): Path(f"mock_fs_{i}.txt").write_text(f"content_{i}")
        return f"Created {scale} files"
    @staticmethod
    def _execute_env(scale: int) -> str: return f"Mutated {scale} env vars"


    def build(self, config: MatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """Orchestrates the incremental assembly of the test vectors."""
        pre_states = self._build_pre(config)
        post_states = self._build_post(pre_states)
        return pre_states, post_states

    @staticmethod
    def _build_pre(config: MatrixConfig) -> List[WorldState]:
        pre_states = []
        scenario_scale = config.scenarios.one_to_one
        for _ in range(scenario_scale):
            pre = WorldState(kwargs={
                "mem_scale": config.aspects.memory,
                "fs_scale": config.aspects.filesystem,
                "env_scale": config.aspects.environment
            })
            pre_states.append(pre)
        return pre_states

    def _build_post(self, pre_states: List[WorldState]) -> List[WorldState]:
        post_states = []
        for pre in pre_states:
            mem = pre.kwargs.get("mem_scale", 0)
            fs = pre.kwargs.get("fs_scale", 0)
            env = pre.kwargs.get("env_scale", 0)
            expected_returns = {}
            expected_fs = {}
            if mem > 0: expected_returns["mem"] = self._execute_memory(mem)
            if fs > 0:
                expected_returns["fs"] = f"Created {fs} files"
                for i in range(fs): expected_fs[f"mock_fs_{i}.txt"] = lambda \
                            p, idx=i: p.exists() and p.read_text() == f"content_{idx}"
            if env > 0: expected_returns["env"] = self._execute_env(env)
            post = WorldState(returns=expected_returns)
            if fs > 0: post.fs = expected_fs
            post_states.append(post)
        return post_states



class One2One:
    matrix_type = "1:1"
    cache_dir = "one_to_one"

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