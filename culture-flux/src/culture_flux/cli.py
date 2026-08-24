"""Command-line interface.

The model runs headless. The GUI does not exist and, when it does, will read
stored output rather than driving the engine.

    python -m culture_flux.cli status
    python -m culture_flux.cli metrics --list
    python -m culture_flux.cli validate configs/smoke.json
    python -m culture_flux.cli run configs/smoke.json --seed 1
    python -m culture_flux.cli verify results/<run-dir>
    python -m culture_flux.cli sweep configs/sweeps/example_sweep.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agents.attributes import implemented_attributes, unimplemented_attributes
from .culture.distance import available_distances
from .dynamics.base import DECLARED_RULES, IMPLEMENTED_RULES
from .experiment.config import ConfigError, ExperimentConfig
from .experiment.run import ExperimentRun, RunResult
from .experiment.sweep import SweepSpec
from .influence.base import available_influence_models
from .io.manifest import check_replayable, load_manifest
from .io.paths import run_directory
from .io.writers import (
    aggregate_culture_rows,
    parquet_available,
    population_rows,
    resolve_format,
    write_json,
    write_table,
)
from .metrics.base import metric_table
from .networks.base import DECLARED_LAYERS, IMPLEMENTED_LAYERS
from .version import MODEL_VERSION, OUTPUT_SCHEMA_VERSION, RNG_LAYOUT_VERSION


def _emit_warnings(cfg: ExperimentConfig) -> None:
    for w in cfg.warnings:
        print(f"  warning: {w}", file=sys.stderr)


def cmd_status(args: argparse.Namespace) -> int:
    unimplemented = unimplemented_attributes()
    placeholders = [m for m in metric_table() if m["status"] == "placeholder"]
    print(f"culture-flux model version {MODEL_VERSION}")
    print(f"  rng layout v{RNG_LAYOUT_VERSION}   output schema v{OUTPUT_SCHEMA_VERSION}")
    print(f"  parquet available: {parquet_available()}")
    print()
    print("IMPLEMENTED")
    print(f"  distance metrics    : {', '.join(sorted(available_distances()))}")
    print(f"  influence models    : {', '.join(available_influence_models())}")
    print(f"  transmission rules  : {', '.join(IMPLEMENTED_RULES)}")
    print(f"  network layers      : {', '.join(IMPLEMENTED_LAYERS)}")
    print(f"  agent attributes    : {len(implemented_attributes())}")
    print(f"  metrics             : {len(metric_table()) - len(placeholders)}")
    print()
    print("DECLARED BUT NOT IMPLEMENTED")
    print(f"  transmission rules  : {', '.join(r for r in DECLARED_RULES if r not in IMPLEMENTED_RULES)}")
    missing_layers = [l for l in DECLARED_LAYERS if l not in IMPLEMENTED_LAYERS]
    print(f"  network layers      : {', '.join(missing_layers) if missing_layers else '(none)'}")
    print(f"  agent attributes    : {', '.join(a.name for a in unimplemented)}")
    print(f"  metrics             : {', '.join(m['name'] for m in placeholders)}")
    print()
    print("The null rule remains the mandatory control arm: under it all metric")
    print("movement is compositional. Under the well-mixed citywide-only network,")
    print("every configuration tested converged to a single culture -- see")
    print("docs/research/pilot_notes.md and docs/model/ROADMAP.md.")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    rows = metric_table()
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    width = max(len(r["name"]) for r in rows)
    for r in rows:
        flag = " " if r["status"] == "implemented" else "*"
        print(f"{flag} {r['name']:<{width}}  {r['category']:<20} {r['description']}")
        if r["blocked_on"]:
            print(f"  {'':<{width}}  blocked on: {r['blocked_on']}")
    print("\n* = placeholder: registered, returns NaN, not yet computable.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        cfg = ExperimentConfig.load(args.config)
    except ConfigError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(f"VALID   {args.config}")
    print(f"  config_hash  {cfg.config_hash}")
    print(f"  baseline_key {cfg.baseline_key}")
    print(f"  condition_key {cfg.condition_key}")
    _emit_warnings(cfg)
    return 0


def _write_run(result: RunResult, out_dir: Path) -> dict[str, str]:
    fmt = resolve_format(result.config.output.format)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    manifest = dict(result.manifest)
    manifest["output"] = {"format": fmt, "directory": str(out_dir)}
    written["manifest"] = str(write_json(out_dir / "manifest.json", manifest))
    written["config"] = str(write_json(out_dir / "config.resolved.json", result.config.to_dict()))
    written["metrics_final"] = str(write_json(out_dir / "metrics_final.json", result.final_metrics))
    if result.config.output.write_timeseries:
        written["timeseries"] = str(write_table(out_dir / "timeseries", result.timeseries, fmt))
    written["culture_distribution"] = str(
        write_table(out_dir / "culture_distribution", aggregate_culture_rows(result.population), fmt)
    )
    if result.config.output.write_final_population:
        written["final_population"] = str(
            write_table(out_dir / "final_population", population_rows(result.population), fmt)
        )
    (out_dir / "run_hash.txt").write_text(result.run_hash + "\n", encoding="utf-8")
    written["run_hash"] = str(out_dir / "run_hash.txt")
    return written


def cmd_run(args: argparse.Namespace) -> int:
    try:
        cfg = ExperimentConfig.load(args.config)
    except ConfigError as exc:
        print(f"INVALID CONFIG: {exc}", file=sys.stderr)
        return 2
    seed = args.seed if args.seed is not None else cfg.seed
    _emit_warnings(cfg)
    result = ExperimentRun(cfg, seed=seed).execute()

    root = args.out or cfg.output.directory
    out_dir = Path(args.out_dir) if args.out_dir else run_directory(root, cfg.name, cfg.config_hash, seed)
    written = _write_run(result, out_dir)

    acct = result.manifest["accounting"]
    print(f"run      {cfg.name}  seed {seed}")
    print(f"  model  {MODEL_VERSION}   config {cfg.config_hash[:8]}   run_hash {result.run_hash}")
    print(f"  people {acct['n_initial']} -> {acct['n_final']}  "
          f"(+{acct['arrivals_total']} arrivals, -{acct['displaced_total']} displaced)")
    print(f"  migrant share requested {acct['requested_migrant_share']:.4f}  "
          f"realised {acct['final_migrant_share']:.4f}")
    ss = result.manifest["source_set"]
    print(f"  sources K={len(ss['labels'])}  evenness {ss['evenness']:.4f}  "
          f"mean distance to resident "
          f"{sum(ss['realised_distance_to_resident']) / len(ss['labels']):.4f}")
    if not result.manifest["dynamics"]["changes_culture"]:
        print("  dynamics NULL -- no agent changed culture; movement is compositional only")
    print(f"  output {out_dir}")
    for k in sorted(written):
        print(f"    {k}: {Path(written[k]).name}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = load_manifest(run_dir)
    problems = check_replayable(manifest)
    if problems:
        for p in problems:
            print(f"CANNOT VERIFY: {p}", file=sys.stderr)
        return 3
    cfg = ExperimentConfig.from_dict(manifest["config"])
    if cfg.config_hash != manifest["config_hash"]:
        print(
            f"CONFIG HASH MISMATCH: stored {manifest['config_hash']} vs "
            f"recomputed {cfg.config_hash}",
            file=sys.stderr,
        )
        return 4
    result = ExperimentRun(cfg, seed=manifest["seed"]).execute()
    stored = manifest["run_hash"]
    if result.run_hash == stored:
        print(f"REPRODUCED  {run_dir.name}")
        print(f"  run_hash {stored}")
        return 0
    print(f"MISMATCH    {run_dir.name}", file=sys.stderr)
    print(f"  stored     {stored}", file=sys.stderr)
    print(f"  recomputed {result.run_hash}", file=sys.stderr)
    return 5


def cmd_sweep(args: argparse.Namespace) -> int:
    spec = SweepSpec.load(args.spec)
    summary = spec.summary()
    print(f"sweep    {summary['name']}")
    print(f"  conditions {summary['n_conditions']}  replicates {summary['replicates']}  "
          f"runs {summary['n_runs']}")
    for axis, values in summary["axes"].items():
        print(f"    {axis}: {values}")
    if args.dry_run:
        pairs = spec.expand()
        print(f"  expanded to {len(pairs)} (config, seed) pairs")
        seen = {cfg.config_hash for cfg, _ in pairs}
        print(f"  distinct condition hashes: {len(seen)}")
        if len(seen) != summary["n_conditions"]:
            print(
                "  WARNING: distinct hashes != condition count; an axis may not affect "
                "the scientific configuration",
                file=sys.stderr,
            )
        return 0
    root = args.out or spec.base.output.directory
    for i, (cfg, seed) in enumerate(spec.expand(), start=1):
        result = ExperimentRun(cfg, seed=seed).execute()
        out_dir = run_directory(root, cfg.name, cfg.config_hash, seed)
        _write_run(result, out_dir)
        print(f"  [{i}/{spec.n_runs}] {cfg.name} seed={seed} -> {out_dir.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="culture-flux",
        description="Cultural dynamics under migration: an experimental instrument. "
        f"Model version {MODEL_VERSION}. No transmission mechanism is implemented yet.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("status", help="what is implemented and what is not")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("metrics", help="list registered metrics")
    s.add_argument("--list", action="store_true", help="(default behaviour)")
    s.add_argument("--json", action="store_true", help="machine-readable output")
    s.set_defaults(func=cmd_metrics)

    s = sub.add_parser("validate", help="validate a configuration without running it")
    s.add_argument("config")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("run", help="execute one run")
    s.add_argument("config")
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--out", default=None, help="results root directory")
    s.add_argument("--out-dir", default=None, help="exact output directory")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("verify", help="re-run a stored run and compare its hash")
    s.add_argument("run_dir")
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("sweep", help="expand or execute a parameter sweep")
    s.add_argument("spec")
    s.add_argument("--dry-run", action="store_true", help="expand and report, run nothing")
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_sweep)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
