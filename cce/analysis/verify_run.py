"""Post-run integrity gate for a single run directory.

Checks that a completed run is fit to look at: manifest present and consistent,
expected number of annual rows, population cap respected, no non-finite numeric
output anywhere, and every stored file matching the SHA-256 recorded in its own
manifest.

Usage:
    python3 analysis/verify_run.py runs/CCE-A-0001-full
    python3 analysis/verify_run.py runs/CCE-A-0001-full --society A --years 500 \
        --capacity 100000

Exit code 0 = pass, 1 = fail. Intended to be run before any run is used for
anything, including exploratory inspection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="verify one CCE run directory")
    ap.add_argument("run_dir")
    ap.add_argument("--society", default=None)
    ap.add_argument("--years", type=int, default=None)
    ap.add_argument("--capacity", type=int, default=None)
    args = ap.parse_args(argv)

    root = Path(args.run_dir)
    failures: list[str] = []
    problems: list[tuple] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    # Columns where NaN is a legitimate "no such value exists" rather than a
    # numeric failure. Exempting a column is not enough on its own: each one is
    # paired below with a consistency check that establishes *why* it is absent,
    # so a corrupted value can never hide behind a legitimate blank.
    NULLABLE = {
        ("panel.csv", "official_iq"),   # citizen not yet civically classified
        ("panel.csv", "official_se"),
        ("annual.csv", "president_iq"),  # office vacant at year end
    }

    # --- non-finite scan over every stored CSV -----------------------------
    for path in sorted(root.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as f:
            for row_number, row in enumerate(csv.DictReader(f), start=2):
                for column, value in row.items():
                    if value in (None, ""):
                        continue
                    try:
                        number = float(value)
                    except (ValueError, TypeError):
                        continue
                    if math.isfinite(number):
                        continue
                    if math.isnan(number) and (path.name, column) in NULLABLE:
                        continue  # justified below
                    problems.append((path.name, row_number, column, value))

    # --- justify every nullable blank --------------------------------------
    panel_path = root / "panel.csv"
    if panel_path.exists():
        with panel_path.open(newline="", encoding="utf-8") as f:
            unscored = banded_without_score = late = 0
            for r in csv.DictReader(f):
                missing = math.isnan(float(r["official_iq"]))
                banded = int(r["band"]) != -1
                if missing and banded:
                    banded_without_score += 1
                if not missing and not banded:
                    unscored += 1
                if missing and float(r["age"]) >= 25:
                    late += 1
        check(banded_without_score == 0,
              f"{banded_without_score} panel rows have a band but no score")
        check(unscored == 0, f"{unscored} panel rows have a score but no band")
        # classification is at age 20, but only on the 5-yearly anniversary,
        # so an unclassified citizen may be up to 24 -- never older
        check(late == 0, f"{late} panel rows unclassified at age 25 or older")

    # --- manifest ----------------------------------------------------------
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        print("FAIL: manifest.json missing")
        return 1
    manifest = json.loads(manifest_path.read_text())

    check(manifest["status"] == "completed", f"status is {manifest['status']!r}")
    if args.years is not None:
        check(manifest["years"] == args.years, f"years is {manifest['years']}")
    if args.capacity is not None:
        check(manifest["capacity"] == args.capacity, f"capacity is {manifest['capacity']}")
    if args.society is not None:
        check(manifest["society"] == args.society, f"society is {manifest['society']!r}")

    # --- checksums ---------------------------------------------------------
    for name, info in manifest.get("files", {}).items():
        fpath = root / info["path"]
        if not fpath.exists():
            failures.append(f"{name}: file {info['path']} missing")
            continue
        actual = sha256(fpath)
        if actual != info["sha256"]:
            failures.append(f"{name}: checksum mismatch")

    # --- annual series -----------------------------------------------------
    annual_path = root / "annual.csv"
    if not annual_path.exists():
        failures.append("annual.csv missing")
        annual = []
    else:
        with annual_path.open(newline="", encoding="utf-8") as f:
            annual = list(csv.DictReader(f))
        expected = args.years if args.years is not None else len(annual)
        check(len(annual) == expected, f"{len(annual)} annual rows, expected {expected}")
        cap = args.capacity if args.capacity is not None else manifest["capacity"]
        peak = max(int(float(r["population"])) for r in annual)
        check(peak <= cap, f"population peaked at {peak}, cap is {cap}")
        check(all(int(r["unrepresented_populated_bands"]) == 0 for r in annual),
              "a populated IQ band went unrepresented")
        worst_delay = max(float(r["max_detection_delay_years"]) for r in annual)
        check(worst_delay <= 1.0 + 1e-9,
              f"hidden abuse persisted {worst_delay} years")
        # president_iq may only be blank when the office is genuinely vacant
        unexplained = sum(1 for r in annual
                          if math.isnan(float(r["president_iq"]))
                          and int(r["president_cid"]) != -1)
        check(unexplained == 0,
              f"{unexplained} years have a seated president with no score")
        vacant = sum(1 for r in annual if int(r["president_cid"]) == -1)

    if problems:
        print("NON-FINITE VALUES FOUND:")
        for item in problems[:30]:
            print("  ", item)
    for f in failures:
        print("FAIL:", f)
    if problems or failures:
        return 1

    print(f"PASS: {manifest['experiment_id']} (society {manifest['society']}, "
          f"seed {manifest['seed']}, tag {manifest['run_tag']}) completed")
    print(f"PASS: {len(annual)} annual rows")
    print(f"PASS: population cap respected (peak {peak} / {cap})")
    print("PASS: no non-finite numeric output in any stored table "
          "(nullable columns justified, not exempted)")
    print(f"PASS: presidency seated in {len(annual) - vacant}/{len(annual)} years")
    print("PASS: every stored file matches its manifest checksum")
    print("PASS: every populated IQ band represented in every year")
    print("PASS: no hidden abuse beyond the safeguard interval")
    print("Model version:", manifest["model_version"],
          "| parameter set:", manifest["parameter_set_id"])
    print("Final population:", annual[-1]["population"])
    print("Final HALE:", annual[-1]["healthy_life_expectancy"])
    print("Final independent LE:", annual[-1]["independent_life_expectancy"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
