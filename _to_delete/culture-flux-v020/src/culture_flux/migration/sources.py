"""Incoming source populations: how many, how large, how culturally distant.

This module is where the project's central experimental contrast lives. Holding
total incoming share M fixed, it must be possible to vary independently:

``K``  the number of distinct source populations
``H``  the evenness of their relative sizes
``D``  their cultural distance from the resident culture
       and, separately, from each other

Two design commitments
----------------------
1. **Targets are requested; realised values are measured.** ``D`` is a target
   distance. The generator aims at it, and the realised pairwise distance matrix
   is computed and written into the run manifest. Analysis uses the realised
   values. Nothing downstream may assume the target was achieved exactly --
   with F features, only multiples of 1/F are achievable at all.

2. **Arrangement is explicit.** Two source cultures each at distance 0.5 from the
   resident culture may be identical to each other or maximally different. That
   difference is the whole of hypotheses H2-H4, so it is a named parameter
   (``arrangement``), never an accident of the random draw. See assumption A-006.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..culture.distance import get_distance
from ..culture.features import CultureSchema
from ..culture.profile import TRAIT_DTYPE

SHARE_DISTRIBUTIONS = ("single", "even", "geometric", "dirichlet", "explicit")
ARRANGEMENTS = ("independent", "disjoint", "nested")

#: Named cultural-distance presets. Values are PROVISIONAL placeholders chosen to
#: span the achievable range, not estimates from data (assumption A-007).
DISTANCE_PRESETS = {"near": 0.25, "medium": 0.50, "far": 0.75, "maximal": 1.00}


def resolve_distance(value: float | str) -> float:
    """Accept either a float in [0, 1] or a named preset."""
    if isinstance(value, str):
        try:
            return DISTANCE_PRESETS[value]
        except KeyError:
            raise KeyError(
                f"unknown cultural-distance preset {value!r}; "
                f"known: {sorted(DISTANCE_PRESETS)}"
            ) from None
    v = float(value)
    if not 0.0 <= v <= 1.0:
        raise ValueError(f"cultural distance must lie in [0, 1], got {v}")
    return v


# ---------------------------------------------------------------------------
# Relative sizes of the incoming populations
# ---------------------------------------------------------------------------

def source_shares(
    k: int,
    distribution: str,
    rng: np.random.Generator | None = None,
    *,
    decay: float = 0.5,
    concentration: float = 1.0,
    explicit: list[float] | None = None,
) -> np.ndarray:
    """Relative sizes of the K incoming populations. Sums to 1.

    ``single``      K must be 1.
    ``even``        all equal -- maximum evenness for a given K.
    ``geometric``   p_i proportional to decay**i; ``decay`` in (0, 1].
                    Deterministic, so evenness can be targeted exactly.
    ``dirichlet``   drawn from Dirichlet(concentration); stochastic, so evenness
                    varies across replicates and must be measured per run.
    ``explicit``    a supplied list, renormalised.
    """
    if k < 1:
        raise ValueError("source count K must be >= 1")
    if distribution not in SHARE_DISTRIBUTIONS:
        raise ValueError(
            f"unknown source distribution {distribution!r}; known: {SHARE_DISTRIBUTIONS}"
        )
    if distribution == "single":
        if k != 1:
            raise ValueError("distribution 'single' requires K == 1")
        return np.array([1.0])
    if distribution == "even":
        return np.full(k, 1.0 / k)
    if distribution == "geometric":
        if not 0.0 < decay <= 1.0:
            raise ValueError("geometric decay must lie in (0, 1]")
        w = decay ** np.arange(k, dtype=np.float64)
        return w / w.sum()
    if distribution == "dirichlet":
        if concentration <= 0:
            raise ValueError("dirichlet concentration must be > 0")
        if rng is None:
            raise ValueError("dirichlet source shares require an explicit rng")
        return np.asarray(rng.dirichlet(np.full(k, concentration)), dtype=np.float64)
    # explicit
    if explicit is None or len(explicit) != k:
        raise ValueError(f"distribution 'explicit' needs a list of exactly K={k} weights")
    arr = np.asarray(explicit, dtype=np.float64)
    if (arr < 0).any():
        raise ValueError("explicit source weights must be non-negative")
    total = arr.sum()
    if total <= 0:
        raise ValueError("explicit source weights must not sum to zero")
    return arr / total


def evenness(shares: np.ndarray) -> float:
    """Pielou evenness of a share vector: Shannon entropy over log K.

    1.0 when all sources are equal; approaches 0 as one dominates. Defined as
    1.0 for K == 1 by convention (a single source is trivially even), which is
    recorded here rather than left to whichever caller hits it first.
    """
    p = np.asarray(shares, dtype=np.float64)
    p = p[p > 0]
    k = p.size
    if k <= 1:
        return 1.0
    h = float(-(p * np.log(p)).sum())
    return h / float(np.log(k))


def shares_for_target_evenness(
    k: int, target: float, *, tol: float = 1e-9, max_iter: int = 200
) -> np.ndarray:
    """Geometric shares whose Pielou evenness equals ``target``.

    Lets H be manipulated as an independent variable at fixed K, which RQ3
    requires. Bisects on the geometric decay parameter; evenness is monotone
    increasing in decay, so the solution is unique.
    """
    if k < 1:
        raise ValueError("K must be >= 1")
    if not 0.0 < target <= 1.0:
        raise ValueError("target evenness must lie in (0, 1]")
    if k == 1:
        return np.array([1.0])
    lo, hi = 1e-6, 1.0
    if evenness(source_shares(k, "geometric", decay=lo)) > target:
        raise ValueError(
            f"target evenness {target} is below what geometric shares can reach for K={k}"
        )
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        e = evenness(source_shares(k, "geometric", decay=mid))
        if abs(e - target) < tol:
            break
        if e < target:
            lo = mid
        else:
            hi = mid
    return source_shares(k, "geometric", decay=0.5 * (lo + hi))


# ---------------------------------------------------------------------------
# Cultural profiles of the incoming populations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceSet:
    """The generated incoming populations, with realised (not target) geometry."""

    labels: tuple[str, ...]
    shares: np.ndarray  # (K,) sums to 1
    profiles: np.ndarray  # (K, F) trait indices
    target_distances: np.ndarray  # (K,) requested distance from resident
    realised_distance_to_resident: np.ndarray  # (K,) measured
    realised_pairwise: np.ndarray  # (K, K) measured, symmetric, zero diagonal
    arrangement: str

    @property
    def k(self) -> int:
        return len(self.labels)

    @property
    def evenness(self) -> float:
        return evenness(self.shares)

    @property
    def mean_inter_source_distance(self) -> float:
        if self.k < 2:
            return float("nan")
        iu = np.triu_indices(self.k, k=1)
        return float(self.realised_pairwise[iu].mean())

    def to_dict(self) -> dict:
        return {
            "labels": list(self.labels),
            "shares": [float(x) for x in self.shares],
            "profiles": self.profiles.astype(int).tolist(),
            "target_distances": [float(x) for x in self.target_distances],
            "realised_distance_to_resident": [
                float(x) for x in self.realised_distance_to_resident
            ],
            "realised_pairwise": self.realised_pairwise.astype(float).tolist(),
            "arrangement": self.arrangement,
            "evenness": self.evenness,
            "mean_inter_source_distance": self.mean_inter_source_distance,
        }


def _differing_feature_sets(
    k: int, n_diff: np.ndarray, n_features: int, arrangement: str, rng: np.random.Generator
) -> list[np.ndarray]:
    """Choose, per source, which features differ from the resident profile."""
    if arrangement == "independent":
        return [rng.choice(n_features, size=int(n_diff[i]), replace=False) for i in range(k)]
    if arrangement == "nested":
        # All sources differ on the same leading features: minimises the chance
        # that two sources differ on disjoint parts of culture space.
        order = rng.permutation(n_features)
        return [order[: int(n_diff[i])] for i in range(k)]
    if arrangement == "disjoint":
        # Allocate consecutive, non-overlapping blocks where the feature budget
        # allows; wrap around once exhausted and report the overlap honestly via
        # the realised pairwise matrix.
        order = rng.permutation(n_features)
        out, cursor = [], 0
        for i in range(k):
            take = int(n_diff[i])
            idx = np.array([order[(cursor + j) % n_features] for j in range(take)], dtype=np.int64)
            cursor += take
            out.append(idx)
        return out
    raise ValueError(f"unknown arrangement {arrangement!r}; known: {ARRANGEMENTS}")


def generate_source_set(
    schema: CultureSchema,
    resident_profile: np.ndarray,
    shares: np.ndarray,
    distances: np.ndarray,
    rng: np.random.Generator,
    *,
    arrangement: str = "independent",
    metric: str = "hamming",
    labels: tuple[str, ...] | None = None,
) -> SourceSet:
    """Generate K source cultures at approximately the requested distances.

    Achievable distances are multiples of 1/F, so the requested distance is
    rounded to the nearest achievable value and the realised distance is measured
    and stored. With F = 20 the rounding error never exceeds 0.025; with F = 5 it
    can reach 0.1, which is why configurations are warned about small F.
    """
    k = len(shares)
    if len(distances) != k:
        raise ValueError("one target distance is required per source")
    if arrangement not in ARRANGEMENTS:
        raise ValueError(f"unknown arrangement {arrangement!r}; known: {ARRANGEMENTS}")
    f = schema.n_features
    resident = np.asarray(resident_profile, dtype=TRAIT_DTYPE).reshape(-1)
    limits = schema.n_traits

    n_diff = np.clip(np.round(np.asarray(distances, dtype=np.float64) * f), 0, f).astype(int)
    feature_sets = _differing_feature_sets(k, n_diff, f, arrangement, rng)

    profiles = np.repeat(resident.reshape(1, -1), k, axis=0)
    for i, idx in enumerate(feature_sets):
        if idx.size == 0:
            continue
        # Offset in [1, n_traits-1] guarantees a trait different from the resident's.
        offs = np.array([rng.integers(1, limits[j]) for j in idx], dtype=np.int64)
        profiles[i, idx] = (
            (resident[idx].astype(np.int64) + offs) % limits[idx]
        ).astype(TRAIT_DTYPE)

    dist = get_distance(metric)
    res_block = np.repeat(resident.reshape(1, -1), k, axis=0)
    to_resident = dist(profiles, res_block, schema)
    pairwise = np.zeros((k, k), dtype=np.float64)
    for i in range(k):
        row = dist(profiles, np.repeat(profiles[i : i + 1], k, axis=0), schema)
        pairwise[i, :] = row

    if labels is None:
        labels = tuple(_source_label(i) for i in range(k))
    return SourceSet(
        labels=labels,
        shares=np.asarray(shares, dtype=np.float64),
        profiles=profiles,
        target_distances=np.asarray(distances, dtype=np.float64),
        realised_distance_to_resident=to_resident,
        realised_pairwise=pairwise,
        arrangement=arrangement,
    )


def _source_label(i: int) -> str:
    """Culture B, C, D, ... -- synthetic labels only. A is reserved for residents."""
    letters = "BCDEFGHIJKLMNOPQRSTUVWXYZ"
    if i < len(letters):
        return f"Culture {letters[i]}"
    return f"Culture S{i:03d}"
