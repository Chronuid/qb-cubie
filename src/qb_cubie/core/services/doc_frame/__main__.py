"""Module entrypoint for running DocFrame CLI via python -m qb_cubie.services.doc_frame."""

import sys

from ....cli import main

if __name__ == "__main__":
    raise SystemExit(main(["docframe", *sys.argv[1:]]))
