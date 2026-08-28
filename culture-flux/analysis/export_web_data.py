#!/usr/bin/env python3
"""Build the embedded data block for culture-flux.html from stored run output.

The atlas page carries no second implementation of the model and makes no
network requests. Everything it displays is computed here, from run directories
on disk, and embedded at build time -- so a figure on that page can always be
traced to a run hash, and the page cannot drift away from the engine by being
edited.

    python3 analysis/export_web_data.py --batch results/rq2

Writes ``culture-flux.data.js`` next to the page. Regenerating after a new batch
is the only supported way to change the numbers the page shows.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Metrics the page reports. Ordered as they appear.
REPORTED = [
    ("resident_trait_retention", "Resident cultural retention", "share of features"),
    ("cultural_richness", "Distinct cultures present", "count"),
    ("dominant_profile_share", "Largest culture's share", "share of population"),
    ("cultural_effective_number", "Effective number of cultures", "count"),
    ("spatial_segregation", "Spatial segregation", "Theil's H"),
    ("mean_distance_to_nearest_founding_culture", "Distance from any founding culture", "0–1"),
]

RULE_LABEL = {
    "null": "No transmission (control)",
    "axelrod_homophily": "Homophilous copying",
    "conformist": "Conformist transmission",
}


def read_rows(batch: Path) -> list[dict]:
    path = batch / "run_summary.csv"
    if not path.exists():
        raise SystemExit(f"no run_summary.csv in {batch} -- run the sweep first")
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def summarise(values: list[float]) -> dict:
    """Mean, sd, standard error and the full sorted sample.

    The sample is kept, not just its summary: the homophily arm looked bimodal
    in the pilot, and a mean is the wrong description of a bimodal outcome. The
    page plots the individual runs for exactly that reason.
    """
    clean = [v for v in values if v == v]
    if not clean:
        return {"n": 0, "mean": None, "sd": None, "se": None, "values": []}
    n = len(clean)
    mean = statistics.fmean(clean)
    sd = statistics.stdev(clean) if n > 1 else 0.0
    return {
        "n": n,
        "mean": round(mean, 6),
        "sd": round(sd, 6),
        "se": round(sd / (n**0.5), 6) if n > 1 else 0.0,
        "values": [round(v, 6) for v in sorted(clean)],
    }


def build(batch: Path) -> dict:
    rows = read_rows(batch)
    manifest = json.loads((batch / "batch_manifest.json").read_text(encoding="utf-8"))

    rules, ks = [], []
    for r in rows:
        if r["dynamics.transmission_rule"] not in rules:
            rules.append(r["dynamics.transmission_rule"])
        k = int(r["migration.source_count"])
        if k not in ks:
            ks.append(k)
    rules.sort(key=lambda x: ("null", "axelrod_homophily", "conformist").index(x))
    ks.sort()

    cells: dict[str, dict] = {}
    for rule in rules:
        for k in ks:
            sel = [
                r
                for r in rows
                if r["dynamics.transmission_rule"] == rule
                and int(r["migration.source_count"]) == k
            ]
            cell = {"n_runs": len(sel), "seeds": sorted(int(r["seed"]) for r in sel)}
            for metric, _, _ in REPORTED:
                cell[metric] = summarise([num(r.get(metric, "nan")) for r in sel])
            cells[f"{rule}|{k}"] = cell

    # The K contrast, per rule: highest K against lowest, with a standard error
    # on the difference. Reported as a z, and deliberately not as a p-value --
    # this is one comparison from an exploratory design, and dressing it as a
    # test would imply a pre-registration that does not exist.
    contrasts = {}
    for rule in rules:
        lo = cells[f"{rule}|{ks[0]}"]["resident_trait_retention"]
        hi = cells[f"{rule}|{ks[-1]}"]["resident_trait_retention"]
        if not lo["n"] or not hi["n"]:
            continue
        se = ((lo["se"] or 0) ** 2 + (hi["se"] or 0) ** 2) ** 0.5
        diff = hi["mean"] - lo["mean"]
        contrasts[rule] = {
            "k_low": ks[0],
            "k_high": ks[-1],
            "diff": round(diff, 6),
            "se": round(se, 6),
            "z": round(diff / se, 3) if se > 0 else None,
        }

    sample = json.loads(
        (batch / sorted(p.name for p in batch.iterdir() if p.is_dir())[0] / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    cfg = sample["config"]

    return {
        "generated_from": str(batch.relative_to(ROOT)) if batch.is_relative_to(ROOT) else str(batch),
        "model_version": manifest["model_version"],
        "batch": {
            "n_runs": manifest["total_runs"],
            "counts": manifest["counts"],
            "failures": len(manifest["failures"]),
            "compute_seconds": manifest["wall_seconds_total"],
            "finished_utc": manifest["finished_utc"],
        },
        "design": {
            "rules": rules,
            "rule_labels": {r: RULE_LABEL.get(r, r) for r in rules},
            "source_counts": ks,
            "replicates": manifest["sweep"]["replicates"],
            "migration_share": cfg["migration"]["total_share"],
            "cultural_distance": cfg["migration"]["cultural_distance"],
            "population": cfg["population"]["initial_size"],
            "features": cfg["culture"]["features"],
            "traits": cfg["culture"]["traits_per_feature"],
            "years": cfg["runtime"]["total_years"],
            "network": cfg["network"]["layers"],
            "drift": cfg["dynamics"]["rule_params"]
            .get("axelrod_homophily", {})
            .get("drift_rate"),
            "conformity": cfg["dynamics"]["rule_params"].get("conformist", {}).get("conformity"),
        },
        "metrics": [{"key": k, "label": lab, "units": u} for k, lab, u in REPORTED],
        "cells": cells,
        "contrasts": contrasts,
        # The compositional prediction, computed rather than asserted: under no
        # transmission, retention is exactly 1 - M*D.
        "compositional_baseline": round(
            1.0 - cfg["migration"]["total_share"] * _distance(cfg["migration"]["cultural_distance"]),
            6,
        ),
        "provenance": [
            {
                "rule": r["dynamics.transmission_rule"],
                "k": int(r["migration.source_count"]),
                "seed": int(r["seed"]),
                "config_hash": r["config_hash"],
                "run_hash": r["run_hash"],
            }
            for r in rows
        ],
    }


def _distance(value) -> float:
    presets = {"near": 0.25, "medium": 0.50, "far": 0.75, "maximal": 1.00}
    return presets[value] if isinstance(value, str) else float(value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", default="results/rq2")
    ap.add_argument("--out", default="culture-flux.data.js")
    args = ap.parse_args()

    batch = Path(args.batch)
    if not batch.is_absolute():
        batch = ROOT / batch
    data = build(batch)
    out = ROOT / args.out
    out.write_text(
        "/* Generated by analysis/export_web_data.py -- do not edit by hand.\n"
        f"   Source: {data['generated_from']} · model {data['model_version']}\n"
        f"   {data['batch']['n_runs']} runs, {data['batch']['failures']} failures. */\n"
        "const DATA = " + json.dumps(data, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {out.name}: {out.stat().st_size / 1024:.0f} KB from {data['batch']['n_runs']} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
