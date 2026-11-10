"""EBT contracts for GUTACHTEN.md, section 8, priority 3.2.

Public API: EBT(..., max_workers=None | positive int).
The effective pool size is min(cpu_count() or 1, len(pre), user limit),
where an omitted/None limit adds no further restriction. Post-states are
comparisons within a task, not additional pool tasks. The limit is local to
each EBT instance; it does not claim to coordinate separate xdist workers.

These desired contracts deliberately have no xfail markers. Recording
executors exercise the real EBT/manager/mapper pipeline without spawning
large pools. Independent assertions check resource requests and results.
The final cases also verify execution in real child processes.
"""

import os

import pytest

from qb_cubie import EBT, WorldState, multiprocessors


def echo(value):
    return value


def identify_worker(value):
    return value, os.getpid()


class RecordingExecutor:
    """Run tasks inline while recording the actual executor configuration."""

    def __init__(self, backend, max_workers):
        self.backend = backend
        self.max_workers = max_workers
        self.calls = []
        self.chunksizes = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)

    def shutdown(self, wait=True):
        self.closed = True

    def map(self, fn, *iterables, chunksize=1):
        self.chunksizes.append(chunksize)
        for args in zip(*iterables):
            self.calls.append(args[0])  # EBT's input-state index.
            yield fn(*args)


@pytest.fixture(params=["pickle", "loky"])
def backend(request):
    if request.param == "loky" and not multiprocessors.LOKY_AVAILABLE:
        pytest.skip("Loky is not installed")
    return request.param


@pytest.fixture
def executors(monkeypatch):
    created = []

    def create(backend, max_workers, **kwargs):
        executor = RecordingExecutor(backend, max_workers)
        created.append(executor)
        return executor

    monkeypatch.setattr(
        multiprocessors, "ProcessPoolExecutor",
        lambda max_workers, **kwargs: create("pickle", max_workers, **kwargs),
    )
    if multiprocessors.LOKY_AVAILABLE:
        monkeypatch.setattr(
            multiprocessors, "get_reusable_executor",
            lambda max_workers, **kwargs: create("loky", max_workers, **kwargs),
        )
    return created


def make_engine(backend, n_tasks, monkeypatch, **kwargs):
    engine = EBT(
        target=echo,
        pre=[WorldState(args=(value,)) for value in range(n_tasks)],
        post=WorldState(returns=int),
        multiprocessing=True,
        reporter=None,
        **kwargs,
    )
    processor_type = {
        "pickle": multiprocessors.PickleProcessor,
        "loky": multiprocessors.LokyProcessor,
    }[backend]
    processor = processor_type()
    # Force one backend so resolver heuristics/fallback cannot hide a violation.
    monkeypatch.setattr(processor, "check_condition", lambda pre, post: True)
    engine.MULTIPROCESSORS = [processor]
    return engine


def assert_run(result, n_tasks, n_posts=1):
    assert result.evaluation is True
    assert len(result.traces) == n_tasks * n_posts
    assert [trace.outcome.returns for trace in result.traces] == [
        value for value in range(n_tasks) for _ in range(n_posts)
    ]
    assert [trace.pre.args for trace in result.traces] == [
        (value,) for value in range(n_tasks) for _ in range(n_posts)
    ]
    assert all(trace.evaluation is True for trace in result.traces)
    assert len({trace.step_id for trace in result.traces}) == n_tasks


@pytest.mark.parametrize("cpu_count,n_tasks,expected", [
    (64, 1, 1),
    (64, 3, 3),
    (2, 7, 2),
    (None, 3, 1),
])
def test_default_pool_is_bounded_by_inputs_and_cpus(
    backend, executors, monkeypatch, cpu_count, n_tasks, expected,
):
    """The existing API must stop requesting idle workers for small inputs."""
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: cpu_count)
    engine = make_engine(backend, n_tasks, monkeypatch)

    assert_run(engine.run(), n_tasks)

    assert [(pool.backend, pool.max_workers) for pool in executors] == [(backend, expected)]
    assert executors[0].calls == list(range(n_tasks))
    assert all(chunk >= 1 for chunk in executors[0].chunksizes)
    assert executors[0].closed


@pytest.mark.parametrize("cpu_count,n_tasks,limit,expected", [
    (64, 7, 2, 2),
    (64, 7, 1, 1),
    (64, 2, 10, 2),
    (2, 7, 10, 2),
    (64, 3, None, 3),
    (None, 3, None, 1),
    (None, 3, 2, 1),
])
def test_public_limit_reaches_each_backend(
    backend, executors, monkeypatch, cpu_count, n_tasks, limit, expected,
):
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: cpu_count)
    engine = make_engine(backend, n_tasks, monkeypatch, max_workers=limit)

    assert_run(engine.run(), n_tasks)

    assert [(pool.backend, pool.max_workers) for pool in executors] == [(backend, expected)]
    assert executors[0].calls == list(range(n_tasks))
    assert all(chunk >= 1 for chunk in executors[0].chunksizes)
    assert executors[0].closed


def test_post_states_do_not_increase_the_task_count(backend, executors, monkeypatch):
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 64)
    engine = make_engine(backend, 2, monkeypatch)
    engine.post = [WorldState(returns=int) for _ in range(9)]

    assert_run(engine.run(), 2, n_posts=9)

    assert [pool.max_workers for pool in executors] == [2]
    assert executors[0].calls == [0, 1]


def test_repeated_run_recalculates_capacity(backend, executors, monkeypatch):
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 64)
    engine = make_engine(backend, 6, monkeypatch, max_workers=4)
    assert_run(engine.run(), 6)
    engine.pre = [WorldState(args=(0,))]
    assert_run(engine.run(), 1)
    engine.pre = [WorldState(args=(value,)) for value in range(3)]
    assert_run(engine.run(), 3)

    assert [pool.max_workers for pool in executors] == [4, 1, 3]
    assert all(pool.closed for pool in executors)


def test_limits_are_independent_between_ebt_instances(backend, executors, monkeypatch):
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 64)
    limited = make_engine(backend, 5, monkeypatch, max_workers=2)
    default = make_engine(backend, 5, monkeypatch)

    assert_run(limited.run(), 5)
    assert_run(default.run(), 5)
    assert_run(limited.run(), 5)

    assert [pool.max_workers for pool in executors] == [2, 5, 2]


@pytest.mark.parametrize("multiprocessing", [False, True], ids=["serial", "parallel"])
@pytest.mark.parametrize("invalid,error_type", [
    (0, ValueError),
    (-1, ValueError),
    (True, TypeError),
    (False, TypeError),
    (1.5, TypeError),
    ("2", TypeError),
])
def test_invalid_limit_fails_before_resources_or_target(
    executors, multiprocessing, invalid, error_type,
):
    calls = []
    with pytest.raises(error_type, match="max_workers") as error:
        EBT(
            target=lambda: calls.append("executed"),
            multiprocessing=multiprocessing,
            max_workers=invalid,
            reporter=None,
        ).run()
    # A missing public parameter must not masquerade as successful validation.
    assert "unexpected keyword argument" not in str(error.value)
    assert calls == []
    assert executors == []


def test_serial_execution_accepts_limit_without_creating_pool(executors):
    result = EBT(
        target=echo,
        pre=[WorldState(args=(value,)) for value in range(3)],
        post=WorldState(returns=int),
        multiprocessing=False,
        max_workers=2,
        reporter=None,
    ).run()

    assert_run(result, 3)
    assert executors == []


@pytest.mark.parametrize("multiprocessing", [False, True], ids=["serial", "parallel"])
def test_changed_limit_is_validated_before_next_execution(executors, multiprocessing):
    calls = []
    engine = EBT(target=lambda: calls.append("executed"), reporter=None,
                 multiprocessing=multiprocessing, max_workers=2)
    engine.max_workers = 0

    with pytest.raises(ValueError, match="max_workers"):
        engine.run()

    assert calls == []
    assert executors == []
    assert engine.run_trace is None


def test_backend_fallback_preserves_the_worker_limit(executors, monkeypatch):
    if not multiprocessors.LOKY_AVAILABLE:
        pytest.skip("Loky is not installed")
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 64)
    engine = make_engine("pickle", 5, monkeypatch, max_workers=2)
    failed_requests = []

    def fail_setup(max_workers):
        failed_requests.append(max_workers)
        raise OSError("executor unavailable")

    monkeypatch.setattr(multiprocessors, "ProcessPoolExecutor", fail_setup)
    fallback = multiprocessors.LokyProcessor()
    monkeypatch.setattr(fallback, "check_condition", lambda pre, post: True)
    engine.MULTIPROCESSORS.append(fallback)

    with pytest.warns(UserWarning, match="executor unavailable"):
        assert_run(engine.run(), 5)

    assert failed_requests == [2]
    assert [(pool.backend, pool.max_workers) for pool in executors] == [("loky", 2)]
    assert executors[0].calls == list(range(5))
    assert executors[0].closed


def test_explicit_limit_is_not_silently_ignored_by_legacy_processor(executors):
    class LegacyProcessor:
        priority = 100

        def check_condition(self, pre_states, post_states):
            return True

        def create_handler(self, n_tasks):
            pytest.fail("A legacy factory cannot enforce an explicit worker limit")

    engine = EBT(target=echo, pre=WorldState(args=(0,)), reporter=None,
                 multiprocessing=True, max_workers=2)
    engine.MULTIPROCESSORS = [LegacyProcessor()]

    with pytest.raises(TypeError, match="max_workers"):
        engine.run()

    assert executors == []
    assert engine.run_trace is None


def test_real_backend_with_one_worker_still_uses_child_process(backend, monkeypatch):
    """A limit of one keeps process isolation and executes every input once."""
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 8)
    engine = make_engine(backend, 3, monkeypatch, max_workers=1)
    engine.target = identify_worker
    engine.post = [WorldState(returns=tuple)]

    result = engine.run()

    assert result.evaluation is True
    assert len(result.traces) == 3
    outcomes = [trace.outcome.returns for trace in result.traces]
    assert [value for value, _ in outcomes] == [0, 1, 2]
    pids = {pid for _, pid in outcomes}
    assert len(pids) == 1
    assert os.getpid() not in pids
