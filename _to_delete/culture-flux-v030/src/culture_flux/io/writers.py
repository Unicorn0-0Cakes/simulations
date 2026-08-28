"""Output writers.

Formats, in order of preference:

``parquet``  columnar, typed, compressed. Read directly by pandas/polars/duckdb.
             Requires pyarrow.
``csv``      the fallback, written by the standard library so that a run never
             fails for want of an optional dependency.

``format: auto`` picks parquet when pyarrow imports and CSV otherwise, and the
choice is recorded in the manifest -- a stored result always says how it was
stored.

Size discipline: the time series is one row per measurement (not per step, and
never per agent). The final population is one row per agent and is the only
output that scales with N, which is why it can be switched off for large sweeps
where only trajectories matter.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


def parquet_available() -> bool:
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        return False
    return True


def resolve_format(requested: str) -> str:
    if requested == "auto":
        return "parquet" if parquet_available() else "csv"
    if requested == "parquet" and not parquet_available():
        raise RuntimeError(
            "output.format is 'parquet' but pyarrow is not installed. Install "
            "pyarrow, or set output.format to 'csv' or 'auto'."
        )
    return requested


def write_json(path: Path, obj: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_default) + "\n", encoding="utf-8")
    return path


def _default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"cannot serialise {type(o).__name__}")


def write_table(path_stem: Path, rows: list[dict[str, Any]], fmt: str) -> Path:
    """Write a list of uniform dicts as parquet or CSV. Returns the path written."""
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out = path_stem.with_suffix(".csv")
        out.write_text("", encoding="utf-8")
        return out
    columns = list(rows[0])
    for r in rows:
        if list(r) != columns:
            raise ValueError("table rows must all share the same columns in the same order")
    if fmt == "parquet":
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.table({c: [r[c] for r in rows] for c in columns})
        out = path_stem.with_suffix(".parquet")
        pq.write_table(table, out, compression="zstd")
        return out
    out = path_stem.with_suffix(".csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return out


def population_rows(population: Any) -> list[dict[str, Any]]:
    """Final population, one row per agent, culture flattened to one column per feature."""
    n = population.size
    names = population.schema.names
    rows: list[dict[str, Any]] = []
    culture = population.culture
    for i in range(n):
        row: dict[str, Any] = {
            "agent_id": int(population.agent_id[i]),
            "source_id": int(population.source_id[i]),
            "source_label": population.source_labels.get(int(population.source_id[i]), "?"),
            "arrival_step": int(population.arrival_step[i]),
            "migration_generation": int(population.migration_generation[i]),
        }
        for j, name in enumerate(names):
            row[f"trait_{name}"] = int(culture[i, j])
        rows.append(row)
    return rows


def aggregate_culture_rows(population: Any) -> list[dict[str, Any]]:
    """Distribution over distinct cultural profiles: one row per profile.

    Kept alongside the per-agent table because it is orders of magnitude smaller
    and is what most analyses actually need.
    """
    if population.size == 0:
        return []
    profiles, counts = np.unique(population.culture, axis=0, return_counts=True)
    names = population.schema.names
    rows = []
    for p, c in zip(profiles, counts):
        row: dict[str, Any] = {"count": int(c), "share": float(c) / population.size}
        for j, name in enumerate(names):
            row[f"trait_{name}"] = int(p[j])
        rows.append(row)
    rows.sort(key=lambda r: -r["count"])
    return rows
