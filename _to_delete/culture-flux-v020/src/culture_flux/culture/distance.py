"""Cultural distance.

Distance is a *registry*, not a single function, because the right metric is an
open scientific question (assumption A-003) and because different features may
eventually demand different treatment. Every registered metric returns values in
[0, 1] where 0 means identical, so that metrics are comparable across schemas
with different numbers of features and traits.

Implemented in v0.1
-------------------
``hamming``
    Fraction of features on which two profiles differ. The complement of
    Axelrod's cultural overlap. Unweighted; a true metric.

``weighted_hamming``
    The same, weighted by feature salience. Reduces to ``hamming`` when all
    saliences are equal. A metric whenever all saliences are non-negative and
    at least one is positive.

Both ignore trait *identity* beyond equality: for categorical features, "trait 3
vs trait 4" is exactly as distant as "trait 3 vs trait 0". That is correct for
unordered features and wrong for ordinal ones, which is why ordinal features are
not yet implemented rather than being run through this code.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from .features import CultureSchema

DistanceFn = Callable[[np.ndarray, np.ndarray, CultureSchema], np.ndarray]

_REGISTRY: dict[str, dict[str, Any]] = {}


def register_distance(name: str, *, description: str, is_metric: bool) -> Callable[[DistanceFn], DistanceFn]:
    """Decorator registering a distance function under ``name``."""

    def deco(fn: DistanceFn) -> DistanceFn:
        if name in _REGISTRY:
            raise ValueError(f"distance metric {name!r} already registered")
        _REGISTRY[name] = {"fn": fn, "description": description, "is_metric": is_metric}
        return fn

    return deco


def available_distances() -> dict[str, dict[str, Any]]:
    """Registered metric names -> {description, is_metric}."""
    return {k: {"description": v["description"], "is_metric": v["is_metric"]} for k, v in _REGISTRY.items()}


def get_distance(name: str) -> DistanceFn:
    try:
        return _REGISTRY[name]["fn"]
    except KeyError:
        raise KeyError(
            f"unknown cultural distance metric {name!r}; registered: {sorted(_REGISTRY)}"
        ) from None


def _as_2d(a: np.ndarray) -> np.ndarray:
    arr = np.asarray(a)
    return arr[None, :] if arr.ndim == 1 else arr


@register_distance(
    "hamming",
    description="Fraction of features on which two profiles differ (1 - Axelrod overlap).",
    is_metric=True,
)
def hamming(a: np.ndarray, b: np.ndarray, schema: CultureSchema) -> np.ndarray:
    """Row-wise normalised Hamming distance. Broadcasts (N,F) against (M,F) when M==1."""
    A, B = _as_2d(a), _as_2d(b)
    if A.shape[1] != schema.n_features or B.shape[1] != schema.n_features:
        raise ValueError("profile width does not match the culture schema")
    return np.asarray((A != B).sum(axis=1) / schema.n_features, dtype=np.float64)


@register_distance(
    "weighted_hamming",
    description="Salience-weighted fraction of differing features; equals hamming when saliences are equal.",
    is_metric=True,
)
def weighted_hamming(a: np.ndarray, b: np.ndarray, schema: CultureSchema) -> np.ndarray:
    A, B = _as_2d(a), _as_2d(b)
    if A.shape[1] != schema.n_features or B.shape[1] != schema.n_features:
        raise ValueError("profile width does not match the culture schema")
    w = schema.salience
    total = float(w.sum())
    if total <= 0:
        raise ValueError("weighted_hamming requires a positive total salience")
    return np.asarray(((A != B) * w[None, :]).sum(axis=1) / total, dtype=np.float64)


def distance_to_profile(
    matrix: np.ndarray, profile: np.ndarray, schema: CultureSchema, metric: str = "hamming"
) -> np.ndarray:
    """Distance from every row of ``matrix`` to a single ``profile``. Shape (N,)."""
    fn = get_distance(metric)
    prof = np.asarray(profile).reshape(1, -1)
    return fn(matrix, np.broadcast_to(prof, (matrix.shape[0], prof.shape[1])), schema)


def mean_pairwise_distance(
    matrix: np.ndarray,
    schema: CultureSchema,
    metric: str = "hamming",
    *,
    max_pairs: int = 200_000,
    sample_pairs: int = 20_000,
    rng: np.random.Generator | None = None,
) -> float:
    """Mean distance over agent pairs, sampled when the population is large.

    Exact when N(N-1)/2 <= ``max_pairs``. Above that, ``sample_pairs`` pairs are
    drawn from a supplied generator; the estimator is unbiased, and the sampling
    is recorded rather than hidden -- callers needing exactness must lower N or
    raise ``max_pairs``.

    ``sample_pairs = 20_000`` is chosen from the estimator's own error: the
    quantity is bounded in [0, 1], so its standard error is at most
    0.5/sqrt(20000) ~ 0.0035 -- an order of magnitude finer than any effect the
    design is powered to detect, at a hundredth of the cost of an exact
    computation at N = 10^4.
    """
    n = matrix.shape[0]
    if n < 2:
        return float("nan")
    fn = get_distance(metric)
    n_pairs = n * (n - 1) // 2
    if n_pairs <= max_pairs:
        i, j = np.triu_indices(n, k=1)
        return float(fn(matrix[i], matrix[j], schema).mean())
    if rng is None:
        raise ValueError(
            f"mean_pairwise_distance needs an explicit rng to sample "
            f"{sample_pairs} of {n_pairs} pairs; refusing to use global randomness"
        )
    i = rng.integers(0, n, size=sample_pairs)
    j = rng.integers(0, n - 1, size=sample_pairs)
    j = j + (j >= i)  # avoid self-pairs without rejection sampling
    return float(fn(matrix[i], matrix[j], schema).mean())
