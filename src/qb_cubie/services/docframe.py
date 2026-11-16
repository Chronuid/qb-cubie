"""Alias module re-exporting the prototype qb_cubie.services.doc_frame package (pending evaluation and hardening)."""

from .doc_frame import *  # noqa: F403
from .doc_frame import __all__ as __all__

if __name__ == "__main__":
    import sys

    from ..cli import main as _cli_main

    raise SystemExit(_cli_main(["docframe", *sys.argv[1:]]))
