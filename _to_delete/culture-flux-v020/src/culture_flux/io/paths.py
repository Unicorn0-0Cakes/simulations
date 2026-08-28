"""Run directory layout.

One directory per run, named so that a human scanning ``results/`` can tell what
is in it, and containing enough to reproduce the run without the original
command line:

    <experiment>__<config_hash8>__seed<NNNN>/
        manifest.json          provenance, configuration, realised geometry
        config.resolved.json   the configuration as run, canonically ordered
        timeseries.parquet     one row per measurement
        final_population.*     one row per agent (optional)
        culture_distribution.* one row per distinct cultural profile
        metrics_final.json     the last measurement, for quick reading
        run_hash.txt           the reproducibility digest
"""

from __future__ import annotations

import re
from pathlib import Path


def slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    return s[:80] or "run"


def run_directory(root: str | Path, experiment_name: str, config_hash: str, seed: int) -> Path:
    return Path(root) / f"{slugify(experiment_name)}__{config_hash[:8]}__seed{seed:04d}"
