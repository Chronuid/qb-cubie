"""Reproduces random findings and edge-case regressions in arena execution."""

import tempfile
from pathlib import Path
from typing import Any

from qb_cubie import (
    CloudpickleCodec,
    EBT,
    ExceptionExpectation,
    MSGspecCodec,
    PickleCodec,
    WorldState,
)
from qb_cubie.arenas.pyvenv import ArenaBuilder


def _runtime_decontam_import() -> float:
    """Imports a decontaminated stdlib module lazily at target execution time."""
    import statistics

    return float(statistics.mean([1, 2, 3]))


def _execute_in_decontaminated_pyvenv(codec: Any) -> float:
    """Provisions an isolated PyVenv with the given codec and runs the lazy-import target."""
    with tempfile.TemporaryDirectory(prefix="cubie_finding_") as tmp_dir:
        env_path = str(Path(tmp_dir) / ".venv")
        builder = ArenaBuilder(env_path).with_packages(["cloudpickle", "msgspec"])
        arena = builder.build(codec=codec)
        arena._decontams = ["statistics"]
        return arena.run(_runtime_decontam_import, (), {})


def test_ebt_pyvenv_codecs_enforce_decontams_during_runtime_imports() -> None:
    """Verifies that all PyVenv IPC codecs block decontaminated runtime imports equally."""
    EBT(
        target=_execute_in_decontaminated_pyvenv,
        pre=[
            WorldState(args=(PickleCodec(),)),
            WorldState(args=(CloudpickleCodec(),)),
            WorldState(args=(MSGspecCodec(),)),
        ],
        post=WorldState(
            raises=ExceptionExpectation(
                TypeError,
                match=r"PhantomObject 'statistics\.mean' cannot be called",
            )
        ),
        custom_id="finding_msgspec_runtime_decontam_bypass",
    ).run()