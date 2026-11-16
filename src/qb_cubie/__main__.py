"""Module entrypoint for running qb-cubie via python -m qb_cubie."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
