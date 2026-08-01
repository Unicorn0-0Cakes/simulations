"""Command-line entry points: single run, matched triad, batch, parameter export."""

from __future__ import annotations

import argparse
import json
import os
import time

from .kernel import MODEL_VERSION, RunConfig, Simulation
from .params import Params, registry_as_records


def _run(args) -> None:
    t0 = time.time()
    cfg = RunConfig(society=args.society, seed=args.seed, years=args.years,
                    capacity=args.population, logging_level=args.logging,
                    outdir=args.out, run_number=args.run_number, tag=args.tag,
                    panel_size=args.panel)
    res = Simulation(cfg).run()
    dt = time.time() - t0
    print(json.dumps({"experiment_id": res.experiment_id, "wall_seconds": round(dt, 2),
                      **res.summary}, indent=2))


def _triad(args) -> None:
    """Matched-seed A/B/C triad -- identical external shocks, different rules."""
    out = {}
    for soc in ("A", "B", "C"):
        cfg = RunConfig(society=soc, seed=args.seed, years=args.years,
                        capacity=args.population, logging_level=args.logging,
                        outdir=os.path.join(args.out, f"CCE-{soc}-{args.run_number:04d}")
                        if args.out else None,
                        run_number=args.run_number, tag=args.tag)
        res = Simulation(cfg).run()
        out[soc] = res.summary
    print(json.dumps(out, indent=2))


def _params(args) -> None:
    recs = registry_as_records()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"model_version": MODEL_VERSION,
                   "parameter_set_id": Params().fingerprint(),
                   "parameters": recs}, f, indent=2, default=str)
    print(f"wrote {len(recs)} parameters to {args.out}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="cce", description="Cognitive Civilization Experiment")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--seed", type=int, default=1)
    common.add_argument("--years", type=int, default=100)
    common.add_argument("--population", type=int, default=10_000)
    common.add_argument("--logging", default="standard",
                        choices=["minimal", "standard", "forensic"])
    common.add_argument("--out", default=None)
    common.add_argument("--run-number", dest="run_number", type=int, default=1)
    common.add_argument("--tag", default="exploratory",
                        choices=["main", "exploratory", "calibration", "debug", "sensitivity"])
    common.add_argument("--panel", type=int, default=None)

    r = sub.add_parser("run", parents=[common], help="single society run")
    r.add_argument("--society", choices=["A", "B", "C"], required=True)
    r.set_defaults(func=_run)

    t = sub.add_parser("triad", parents=[common], help="matched-seed A/B/C runs")
    t.set_defaults(func=_triad)

    p = sub.add_parser("params", help="export the parameter registry")
    p.add_argument("--out", default="params/baseline.json")
    p.set_defaults(func=_params)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
