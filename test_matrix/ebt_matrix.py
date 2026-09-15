from typing import List, Optional, Union, Tuple
from pathlib import Path
from ebt import EBT
from protocols import WorldState, RunTrace
from test_matrix.protocols import MatrixConfig, MatrixTarget, MatrixReporter, MatrixReport
from test_matrix.one_to_one import One2One
from test_matrix.one_to_n import One2N
from test_matrix.n_to_one import N2One
from test_matrix.n_to_n import N2N

class EBTMatrix:
    def __init__(
            self,
            configs: Union[List[MatrixConfig], MatrixConfig],
            reporter: Optional[MatrixReporter] = None,
            _one_to_one: MatrixTarget = One2One(),
            _one_to_n: MatrixTarget = One2N(),
            _n_to_one: MatrixTarget = N2One(),
            _n_to_n: MatrixTarget = N2N(),
    ):
        self.CACHE_ROOT = Path(".ebt_matrix")
        self.CONFIGS: List[MatrixConfig] = configs if isinstance(configs, list) else [configs]
        self.reporter: Optional[MatrixReporter] = reporter
        self._one_to_one: MatrixTarget = _one_to_one
        self._one_to_n: MatrixTarget = _one_to_n
        self._n_to_one: MatrixTarget = _n_to_one
        self._n_to_n: MatrixTarget = _n_to_n

    def run(self) -> Union[List[MatrixReport], MatrixReport]:
        """Orchestrates the lifecycle of all passed configurations."""
        all_reports: List[MatrixReport] = []
        for config in self.CONFIGS:
            active_targets = []
            if config.scenarios.one_to_one > 0: active_targets.append(self._one_to_one)
            if config.scenarios.one_to_n > 0: active_targets.append(self._one_to_n)
            if config.scenarios.n_to_one > 0: active_targets.append(self._n_to_one)
            if config.scenarios.n_to_n > 0: active_targets.append(self._n_to_n)
            for target in active_targets:
                pre_states, post_states = self._arrange(target, config)
                trace = self._execute(target, config, pre_states, post_states)
                if not trace: raise RuntimeError("STATE-GUARD: No trace found.")
                report = self._report(target, config, trace)
                all_reports.append(report)
        if self.reporter: self.reporter.report(all_reports)
        if not all_reports: return []
        return all_reports if len(all_reports) > 1 else all_reports[0]

    def _arrange(self, target: MatrixTarget, config: MatrixConfig) -> Tuple[List[WorldState], List[WorldState]]:
        """Delegates the generation and assembly to the target's build() method."""
        return target.build(config, cache_root=self.CACHE_ROOT)

    @staticmethod
    def _execute(
            target: MatrixTarget,
            config: MatrixConfig,
            pre: List[WorldState],
            post: List[WorldState]
    ) -> RunTrace | None:
        """Proxies the generated states natively into the Cubie framework."""
        engine = EBT(
            target=target.target,
            pre=pre,
            post=post,
            arena=config.arena,
            multiprocessing=config.multiprocessing,
            reporter=None
        )
        return engine.run()

    @staticmethod
    def _report(target: MatrixTarget, config: MatrixConfig, trace: RunTrace) -> MatrixReport:
        """Encapsulates the EBT trace within a MatrixReport DTO in terms of formal logic."""
        return MatrixReport(
            target_type=target.matrix_type,
            target=target.__class__.__name__,
            config=config,
            trace=trace
        )