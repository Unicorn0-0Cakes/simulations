"""Parameter sweeps.

A sweep is a declarative product over configuration paths, expanded into
concrete ``ExperimentConfig`` objects with their seeds. Expansion is separated
from execution so that:

* the size and shape of a design can be inspected before any compute is spent
  (``--dry-run`` prints the condition count and the per-condition parameters);
* conditions are addressable by ``config_hash``, so a partially completed sweep
  can be resumed without re-running what already finished;
* the same expansion feeds a single process now and a job array later, without
  the model knowing which.

Replication is explicit: ``replicates`` seeds per condition, generated as
``seed_start + i``, so a replicate is identified by a number a human can type
rather than by position in an output file.

Nothing here parallelises yet. The unit of parallelism is one run and runs share
no state, so this is embarrassingly parallel whenever it needs to be; the
decision about *how* (processes, job array, cluster) is deferred until the sweep
sizes are known, because it is easy to change and hard to change back.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import ConfigError, ExperimentConfig, canonical_json


@dataclass
class SweepSpec:
    """A base configuration plus axes to vary over it."""

    name: str
    base: ExperimentConfig
    #: dotted path -> list of values, e.g. "migration.total_share": [0.0, 0.1, 0.2]
    axes: dict[str, list[Any]] = field(default_factory=dict)
    replicates: int = 1
    seed_start: int = 1
    description: str = ""

    def __post_init__(self) -> None:
        if self.replicates < 1:
            raise ConfigError("a sweep needs at least one replicate per condition")
        if self.seed_start < 0:
            raise ConfigError("seed_start must be non-negative")
        for path, values in self.axes.items():
            if not isinstance(values, list) or not values:
                raise ConfigError(f"sweep axis {path!r} must be a non-empty list")
            _resolve_path(self.base, path)  # raises if the path does not exist

    @property
    def n_conditions(self) -> int:
        n = 1
        for values in self.axes.values():
            n *= len(values)
        return n

    @property
    def n_runs(self) -> int:
        return self.n_conditions * self.replicates

    def expand(self) -> list[tuple[ExperimentConfig, int]]:
        """Every (config, seed) pair this sweep describes."""
        paths = list(self.axes)
        out: list[tuple[ExperimentConfig, int]] = []
        for combo in itertools.product(*(self.axes[p] for p in paths)):
            data = self.base.to_dict()
            label_bits = []
            for path, value in zip(paths, combo):
                _assign_path(data, path, value)
                label_bits.append(f"{path.split('.')[-1]}={value}")
            data["name"] = f"{self.name}[{','.join(label_bits)}]"
            try:
                cfg = ExperimentConfig.from_dict(data)
            except ConfigError as exc:
                # A sweep that produces an invalid combination must say WHICH
                # combination, not fail somewhere deep in validation. Large
                # designs make an unlabelled failure very expensive to diagnose.
                raise ConfigError(
                    f"sweep {self.name!r} produced an invalid condition "
                    f"({', '.join(label_bits)}): {exc}"
                ) from exc
            for r in range(self.replicates):
                out.append((cfg, self.seed_start + r))
        return out

    def summary(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "axes": {k: list(v) for k, v in self.axes.items()},
            "n_conditions": self.n_conditions,
            "replicates": self.replicates,
            "n_runs": self.n_runs,
            "seed_start": self.seed_start,
            "base_config_hash": self.base.config_hash,
        }

    @classmethod
    def load(cls, path: str | Path) -> "SweepSpec":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in (".yaml", ".yml"):
            import yaml  # type: ignore

            data = yaml.safe_load(text)
        else:
            import json

            data = json.loads(text)
        if "base" not in data:
            raise ConfigError("a sweep file needs a 'base' configuration section")
        base_field = data["base"]
        if isinstance(base_field, str):
            base = ExperimentConfig.load(p.parent / base_field)
        else:
            base = ExperimentConfig.from_dict(base_field)
        return cls(
            name=data.get("name", p.stem),
            base=base,
            axes=data.get("axes", {}),
            replicates=int(data.get("replicates", 1)),
            seed_start=int(data.get("seed_start", 1)),
            description=data.get("description", ""),
        )

    def manifest(self) -> str:
        return canonical_json(self.summary())


def _resolve_path(cfg: ExperimentConfig, path: str) -> None:
    parts = path.split(".")
    obj: Any = cfg
    for part in parts:
        if not hasattr(obj, part):
            raise ConfigError(
                f"sweep axis {path!r}: configuration has no field {part!r}. "
                "Axes must name existing fields so that a typo cannot silently "
                "produce a sweep over nothing."
            )
        obj = getattr(obj, part)


def _assign_path(data: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value
