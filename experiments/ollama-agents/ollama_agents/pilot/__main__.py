"""Freeze a calibrated pilot without starting a model or changing reference admission."""

import argparse
import json
import sys

from .freeze import freeze_pilot


def main(argv=None):
    """Expose the example gate from both the checkout and an installed wheel."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--calibration", action="append", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--exploratory", action="store_true", help="Mark the study as exploratory, independently of reference admission")
    args = parser.parse_args(argv)
    try:
        result = freeze_pilot(calibration_archives=args.calibration, suite_path=args.suite,
                              destination=args.destination, exploratory=args.exploratory)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(f"Pilot configuration error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
