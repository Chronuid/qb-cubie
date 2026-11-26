"""Module entrypoint for running DocEnsurance CLI via python -m qb_cubie.core.services.doc_ensurance."""

import sys

from ....cli import main

if __name__ == "__main__":
    raise SystemExit(main(["docensurance", *sys.argv[1:]]))
