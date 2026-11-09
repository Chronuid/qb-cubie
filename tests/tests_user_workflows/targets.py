"""Small consumer applications, deliberately independent of Cubie.

The named faults are application mutations, not patches to the test framework.
"""

import csv
import json
from pathlib import Path


def export_orders(fault=None):
    """Export paid orders; command API promises None, including empty exports."""
    with Path("orders.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    paid = [row for row in rows if row["status"] == "paid"]
    if fault == "include-unpaid":
        paid = rows
    lines = ["id,total_cents"]
    lines.extend(f"{row['id']},{int(row['quantity']) * int(row['unit_cents'])}"
                 for row in paid)
    if fault != "missing-file":
        Path("paid.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if fault == "extra-file":
        Path("debug.txt").write_text("internal", encoding="utf-8")
    if fault == "return-count":
        return len(paid)
    return None


class Stock:
    """A caller retains returned ledgers while running the same check again."""

    def __init__(self):
        self.ledger = {"remaining": [2]}

    def reserve(self):
        self.ledger["remaining"][0] -= 1
        return self.ledger


def availability(field, faulty=False):
    """An empty warehouse has several legitimate falsy API results."""
    empty = {"count": 0, "can_ship": False, "pending": [], "next_sku": ""}
    wrong = {"count": 1, "can_ship": True, "pending": ["SKU-1"], "next_sku": "SKU-1"}
    return (wrong if faulty else empty)[field]


def build_settings(fault=None):
    """Combine independently supplied shop and shipping settings."""
    shop = json.loads(Path("shop/settings.json").read_text(encoding="utf-8"))
    shipping = json.loads(Path("shipping/settings.json").read_text(encoding="utf-8"))
    if fault == "reuse-shop":
        shipping = shop
    settings = {"currency": shop["currency"], "region": shipping["region"]}
    Path("settings.json").write_text(
        json.dumps(settings, sort_keys=True) + "\n", encoding="utf-8",
    )
    return settings
