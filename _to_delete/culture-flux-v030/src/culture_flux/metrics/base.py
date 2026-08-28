"""Metric interface and registry.

A metric is a named, described, versioned callable over a ``MetricContext``.
Registering rather than hard-coding buys three things the project needs:

* metrics can be listed (``culture-flux metrics --list``) and their status
  audited without reading the engine;
* a metric that is planned but not yet computable is registered with status
  ``placeholder``, returns NaN, and is reported as NaN -- never silently absent
  and never quietly replaced by a proxy;
* the metric set used by a run is recorded in its manifest, so a stored result
  can be interpreted years later without guessing which definition was in force.

Metrics return plain floats. Metrics that are naturally vector-valued (per
feature, per source) register one scalar summary each and write the vector to the
run's detail output, so that the time series stays a rectangular table.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..agents.population import Population
from ..culture.features import CultureSchema
from ..influence.base import InfluenceModel

METRIC_STATUSES = ("implemented", "placeholder")


@dataclass
class MetricContext:
    """Everything a metric is allowed to see."""

    population: Population
    schema: CultureSchema
    step: int
    year: float
    generation: float
    initial_resident_profile: np.ndarray
    initial_culture: np.ndarray
    influence: InfluenceModel
    rng: np.random.Generator
    #: (1+K, F) -- the resident founding profile stacked with every incoming
    #: source profile. The reference set for "has anything genuinely new
    #: appeared", which only becomes a meaningful question once traits can move.
    founding_profiles: np.ndarray | None = None
    distance_metric: str = "hamming"
    source_labels: dict[int, str] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    #: Per-measurement memo. Several metrics need the same expensive derived
    #: quantity (the profile grouping, the distance-to-founding-culture vector);
    #: recomputing it once per metric dominated profiling. The memo is scoped to
    #: one MetricContext, so it can never leak a stale value across measurements.
    _cache: dict[str, Any] = field(default_factory=dict, repr=False)

    def cached(self, key: str, compute: Callable[[], Any]) -> Any:
        """Return a derived quantity, computing it at most once per measurement."""
        if key not in self._cache:
            self._cache[key] = compute()
        return self._cache[key]


MetricFn = Callable[[MetricContext], float]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    fn: MetricFn
    description: str
    category: str
    status: str
    #: What must exist before a placeholder can become implemented.
    blocked_on: str = ""

    def __post_init__(self) -> None:
        if self.status not in METRIC_STATUSES:
            raise ValueError(f"metric {self.name!r}: unknown status {self.status!r}")


_REGISTRY: dict[str, MetricSpec] = {}


def register_metric(
    name: str,
    *,
    description: str,
    category: str,
    status: str = "implemented",
    blocked_on: str = "",
) -> Callable[[MetricFn], MetricFn]:
    def deco(fn: MetricFn) -> MetricFn:
        if name in _REGISTRY:
            raise ValueError(f"metric {name!r} already registered")
        _REGISTRY[name] = MetricSpec(
            name=name,
            fn=fn,
            description=description,
            category=category,
            status=status,
            blocked_on=blocked_on,
        )
        return fn

    return deco


def get_metric(name: str) -> MetricSpec:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown metric {name!r}; registered: {sorted(_REGISTRY)}") from None


def available_metrics(status: str | None = None) -> dict[str, MetricSpec]:
    if status is None:
        return dict(_REGISTRY)
    return {k: v for k, v in _REGISTRY.items() if v.status == status}


def default_metric_names() -> tuple[str, ...]:
    """Every implemented metric, in registration order."""
    return tuple(k for k, v in _REGISTRY.items() if v.status == "implemented")


def compute_metrics(
    ctx: MetricContext, names: tuple[str, ...] | None = None
) -> dict[str, float]:
    """Evaluate the named metrics. Placeholders return NaN by design."""
    selected = names if names is not None else default_metric_names()
    out: dict[str, float] = {}
    for name in selected:
        spec = get_metric(name)
        value = spec.fn(ctx)
        out[name] = float(value)
    return out


def metric_table() -> list[dict[str, str]]:
    """Machine-readable description of every registered metric."""
    return [
        {
            "name": s.name,
            "category": s.category,
            "status": s.status,
            "description": s.description,
            "blocked_on": s.blocked_on,
        }
        for s in _REGISTRY.values()
    ]
