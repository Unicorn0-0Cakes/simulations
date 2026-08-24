"""Sweep execution: parallel, resumable, and answerable afterwards.

Three things this adds over calling ``ExperimentRun`` in a loop.

**Parallelism.** Runs share no state, so the unit of parallelism is one run and
a process pool is enough. The pool is processes rather than threads because the
work is NumPy-bound inside the GIL for the array operations that dominate.

**Resume.** A run is identified by its directory, which encodes experiment name,
config hash and seed. A directory holding a complete manifest at the current
model version is treated as done and skipped. So a sweep interrupted at run 4,000
of 8,000 continues rather than restarting, and a sweep extended with new
conditions runs only the new ones.

Completeness is checked properly: a manifest must exist, parse, carry the current
model version, and be accompanied by a run-hash file. A half-written directory
from a killed process fails that test and is re-run. Resume never trusts a
directory just because it exists.

**An answerable result.** Every batch writes ``run_summary.csv``: one row per run
with the swept parameters and every final metric. That is the table an analysis
actually starts from, and building it at write time avoids re-opening thousands
of manifests later.

Determinism is unaffected by parallelism. Each run's randomness comes from
(seed, baseline key, condition key) alone; nothing depends on execution order, on
worker identity, or on how many workers there are. A sweep run on 1 worker and
the same sweep on 64 produce identical run hashes, which the test suite checks.
"""

from __future__ import annotations

import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..io.paths import run_directory
from ..io.writers import (
    aggregate_culture_rows,
    population_rows,
    resolve_format,
    write_json,
    write_table,
)
from ..version import MODEL_VERSION
from .config import ExperimentConfig
from .run import ExperimentRun
from .sweep import SweepSpec


@dataclass
class RunOutcome:
    """What happened to one run."""

    name: str
    seed: int
    config_hash: str
    directory: str
    status: str  # "completed" | "skipped" | "failed"
    run_hash: str = ""
    wall_seconds: float = 0.0
    error: str = ""
    final_metrics: dict[str, float] = field(default_factory=dict)
    axis_values: dict[str, Any] = field(default_factory=dict)


def is_complete(run_dir: Path) -> bool:
    """True only for a directory holding a finished run at the current version."""
    manifest = run_dir / "manifest.json"
    if not manifest.exists() or not (run_dir / "run_hash.txt").exists():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("model_version") == MODEL_VERSION and bool(data.get("run_hash"))


def write_run(result, out_dir: Path) -> dict[str, str]:
    """Write one run's outputs. Shared by the CLI and the executor."""
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
    # The hash file is written LAST, so its presence means the rest landed.
    (out_dir / "run_hash.txt").write_text(result.run_hash + "\n", encoding="utf-8")
    written["run_hash"] = str(out_dir / "run_hash.txt")
    return written


def _execute_one(task: dict) -> dict:
    """Worker entry point. Takes and returns plain dicts, so nothing that has to
    cross a process boundary needs to be picklable beyond JSON types."""
    out_dir = Path(task["directory"])
    try:
        cfg = ExperimentConfig.from_dict(task["config"])
        result = ExperimentRun(cfg, seed=task["seed"]).execute()
        write_run(result, out_dir)
        return {
            "status": "completed",
            "run_hash": result.run_hash,
            "wall_seconds": result.manifest["timing"]["wall_seconds"],
            "final_metrics": result.final_metrics,
        }
    except Exception as exc:  # noqa: BLE001 - a failed run must not kill the batch
        return {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=6),
        }


def execute_sweep(
    spec: SweepSpec,
    out_root: str | Path,
    *,
    workers: int = 1,
    resume: bool = True,
    on_progress: Callable[[int, int, RunOutcome], None] | None = None,
) -> dict:
    """Run every (config, seed) in the sweep. Returns the batch manifest."""
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    pairs = spec.expand()
    axis_paths = list(spec.axes)

    tasks: list[dict] = []
    outcomes: list[RunOutcome] = []
    for cfg, seed in pairs:
        out_dir = run_directory(root, cfg.name, cfg.config_hash, seed)
        axis_values = {p: _read_path(cfg, p) for p in axis_paths}
        if resume and is_complete(out_dir):
            outcomes.append(
                RunOutcome(
                    name=cfg.name,
                    seed=seed,
                    config_hash=cfg.config_hash,
                    directory=str(out_dir),
                    status="skipped",
                    run_hash=(out_dir / "run_hash.txt").read_text(encoding="utf-8").strip(),
                    final_metrics=_read_metrics(out_dir),
                    axis_values=axis_values,
                )
            )
            continue
        tasks.append(
            {
                "config": cfg.to_dict(),
                "seed": seed,
                "directory": str(out_dir),
                "name": cfg.name,
                "config_hash": cfg.config_hash,
                "axis_values": axis_values,
            }
        )

    started = datetime.now(timezone.utc).isoformat()
    total = len(pairs)
    done = len(outcomes)

    def record(task: dict, payload: dict) -> RunOutcome:
        return RunOutcome(
            name=task["name"],
            seed=task["seed"],
            config_hash=task["config_hash"],
            directory=task["directory"],
            status=payload["status"],
            run_hash=payload.get("run_hash", ""),
            wall_seconds=payload.get("wall_seconds", 0.0),
            error=payload.get("error", ""),
            final_metrics=payload.get("final_metrics", {}),
            axis_values=task["axis_values"],
        )

    if workers <= 1 or len(tasks) <= 1:
        for task in tasks:
            outcome = record(task, _execute_one(task))
            outcomes.append(outcome)
            done += 1
            if on_progress:
                on_progress(done, total, outcome)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_execute_one, t): t for t in tasks}
            for future in as_completed(futures):
                task = futures[future]
                outcome = record(task, future.result())
                outcomes.append(outcome)
                done += 1
                if on_progress:
                    on_progress(done, total, outcome)

    manifest = _batch_manifest(spec, root, outcomes, started, workers, resume)
    write_json(root / "batch_manifest.json", manifest)
    _write_summary(root, outcomes, axis_paths)
    return manifest


def _batch_manifest(
    spec: SweepSpec,
    root: Path,
    outcomes: list[RunOutcome],
    started: str,
    workers: int,
    resume: bool,
) -> dict:
    by_status: dict[str, int] = {}
    for o in outcomes:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    failures = [
        {"name": o.name, "seed": o.seed, "directory": o.directory, "error": o.error}
        for o in outcomes
        if o.status == "failed"
    ]
    return {
        "model_version": MODEL_VERSION,
        "sweep": spec.summary(),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "workers": workers,
        "resume": resume,
        "counts": by_status,
        "total_runs": len(outcomes),
        "wall_seconds_total": round(sum(o.wall_seconds for o in outcomes), 3),
        # Failures are listed, not just counted. A batch that quietly dropped
        # 3% of its runs would still look complete in an aggregate table.
        "failures": failures,
        "output_root": str(root),
        "environment": {"cpu_count": os.cpu_count()},
    }


def _write_summary(root: Path, outcomes: list[RunOutcome], axis_paths: list[str]) -> None:
    """One row per run: swept parameters plus every final metric."""
    completed = [o for o in outcomes if o.status in ("completed", "skipped") and o.final_metrics]
    if not completed:
        return
    metric_names = sorted({k for o in completed for k in o.final_metrics})
    rows = []
    for o in completed:
        row: dict[str, Any] = {
            "name": o.name,
            "seed": o.seed,
            "config_hash": o.config_hash,
            "run_hash": o.run_hash,
            "status": o.status,
        }
        for p in axis_paths:
            row[p] = _stringify(o.axis_values.get(p))
        for m in metric_names:
            row[m] = o.final_metrics.get(m, float("nan"))
        rows.append(row)
    rows.sort(key=lambda r: (str(r.get(axis_paths[0], "")) if axis_paths else "", r["seed"]))
    write_table(root / "run_summary", rows, "csv")


def _stringify(value: Any) -> Any:
    """Axis values may be dicts (a whole network specification). Flatten them to
    a stable string so the summary table stays rectangular and diffable."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _read_path(cfg: ExperimentConfig, path: str) -> Any:
    node: Any = cfg
    for part in path.split("."):
        node = getattr(node, part)
    return node


def _read_metrics(run_dir: Path) -> dict[str, float]:
    try:
        return json.loads((run_dir / "metrics_final.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
