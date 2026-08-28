"""Reading and comparing stored run manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..version import MODEL_VERSION


class ManifestError(RuntimeError):
    pass


def load_manifest(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir) / "manifest.json"
    if not path.exists():
        raise ManifestError(f"no manifest.json in {run_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_replayable(manifest: dict[str, Any]) -> list[str]:
    """Reasons this manifest cannot be replayed by the current code, if any."""
    problems = []
    if manifest.get("model_version") != MODEL_VERSION:
        problems.append(
            f"model version differs: manifest {manifest.get('model_version')!r} vs "
            f"current {MODEL_VERSION!r}. Results across model versions are not "
            "comparable and replay is not attempted."
        )
    return problems
