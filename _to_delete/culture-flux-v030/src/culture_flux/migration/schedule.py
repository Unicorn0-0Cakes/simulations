"""Migration accounting and arrival timing.

What M means
------------
``total_share`` (M) is the migrant share of the **final** population. Defining it
on the final population, rather than as a multiple of the initial one, is what
makes the addition and replacement modes comparable: both end at migrant share
M, so a contrast between them isolates *whether residents left*, not how big the
city got. See assumption A-008.

``addition``     residents stay; the city grows.
                 n_migrants = round(M * N0 / (1 - M)); final N = N0 + n_migrants.
``replacement``  each arrival displaces one resident; final N = N0.
                 n_migrants = round(M * N0).

Integer allocation
------------------
Shares are real; agents are not. Every split from shares to counts uses the
largest-remainder (Hamilton) method, which is deterministic and conserves the
total exactly. No stochastic rounding: it would put a random component into the
composition of the population, which is precisely the thing the experiment holds
constant across conditions. The residual rounding error is bounded by one agent
per source and is recorded in the manifest.

Velocity
--------
``duration_years`` spreads the same total arrivals over a different length of
time. Cumulative migration is therefore held exactly constant while V varies,
which is what RQ5 requires. In v0.1 the within-window profile is uniform; other
profiles are declared and rejected rather than approximated.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIGRATION_MODES = ("addition", "replacement")
ARRIVAL_PROFILES = ("uniform",)
DECLARED_ARRIVAL_PROFILES = ("uniform", "front_loaded", "back_loaded", "pulse")


def largest_remainder(shares: np.ndarray, total: int) -> np.ndarray:
    """Split ``total`` integer units across ``shares``, conserving the total exactly.

    Deterministic. Ties in the remainder are broken by index order, so the result
    depends only on the inputs -- never on hash ordering or platform.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    p = np.asarray(shares, dtype=np.float64)
    if p.size == 0:
        if total != 0:
            raise ValueError("cannot allocate a positive total across zero groups")
        return np.zeros(0, dtype=np.int64)
    if (p < 0).any():
        raise ValueError("shares must be non-negative")
    s = p.sum()
    if s <= 0:
        raise ValueError("shares must not sum to zero")
    p = p / s
    exact = p * total
    base = np.floor(exact).astype(np.int64)
    remainder = int(total - base.sum())
    if remainder > 0:
        order = np.argsort(-(exact - base), kind="stable")
        base[order[:remainder]] += 1
    assert int(base.sum()) == total
    return base


@dataclass(frozen=True)
class MigrationPlan:
    """A fully resolved migration schedule. Nothing here is stochastic."""

    mode: str
    total_share: float
    n_initial: int
    n_migrants_total: int
    n_final_expected: int
    counts_by_source: np.ndarray  # (K,) sums to n_migrants_total
    arrivals: np.ndarray  # (n_windows, K) sums to counts_by_source
    arrival_steps: np.ndarray  # (n_windows,) step index of each arrival window
    start_year: float
    duration_years: float
    profile: str
    realised_final_share: float

    def validate(self) -> None:
        if int(self.counts_by_source.sum()) != self.n_migrants_total:
            raise AssertionError("source counts do not sum to the migrant total")
        if int(self.arrivals.sum()) != self.n_migrants_total:
            raise AssertionError("scheduled arrivals do not sum to the migrant total")
        if (self.arrivals < 0).any():
            raise AssertionError("negative arrivals scheduled")
        if not np.array_equal(self.arrivals.sum(axis=0), self.counts_by_source):
            raise AssertionError("per-source arrival totals do not match source counts")

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "total_share_requested": self.total_share,
            "realised_final_migrant_share": self.realised_final_share,
            "n_initial": self.n_initial,
            "n_migrants_total": self.n_migrants_total,
            "n_final_expected": self.n_final_expected,
            "counts_by_source": self.counts_by_source.astype(int).tolist(),
            "arrival_steps": self.arrival_steps.astype(int).tolist(),
            "start_year": self.start_year,
            "duration_years": self.duration_years,
            "profile": self.profile,
        }


def total_migrants(mode: str, total_share: float, n_initial: int) -> int:
    """Number of arrivals needed to reach final migrant share ``total_share``."""
    if mode not in MIGRATION_MODES:
        raise ValueError(f"unknown migration mode {mode!r}; known: {MIGRATION_MODES}")
    if not 0.0 <= total_share < 1.0:
        raise ValueError("total_share must lie in [0, 1); a share of 1 leaves no residents")
    if n_initial < 1:
        raise ValueError("n_initial must be >= 1")
    if total_share == 0.0:
        return 0
    if mode == "addition":
        return int(round(total_share * n_initial / (1.0 - total_share)))
    return int(round(total_share * n_initial))


def build_plan(
    *,
    mode: str,
    total_share: float,
    n_initial: int,
    shares: np.ndarray,
    steps_per_year: int,
    start_year: float,
    duration_years: float,
    profile: str = "uniform",
) -> MigrationPlan:
    """Resolve M, K, H and V into an exact integer arrival schedule."""
    if profile not in ARRIVAL_PROFILES:
        if profile in DECLARED_ARRIVAL_PROFILES:
            raise NotImplementedError(
                f"arrival profile {profile!r} is declared but not implemented in v0.1 "
                f"(implemented: {ARRIVAL_PROFILES}). See docs/model/ROADMAP.md."
            )
        raise ValueError(
            f"unknown arrival profile {profile!r}; declared: {DECLARED_ARRIVAL_PROFILES}"
        )
    if duration_years <= 0:
        raise ValueError("migration duration must be > 0 years")
    if start_year < 0:
        raise ValueError("migration start_year must be >= 0")

    n_mig = total_migrants(mode, total_share, n_initial)
    counts = largest_remainder(shares, n_mig)

    n_windows = max(1, int(round(duration_years * steps_per_year)))
    first_step = int(round(start_year * steps_per_year))
    # Arrivals land at the END of each window, so an agent arriving in step s is
    # present for measurement at step s but not before.
    arrival_steps = first_step + 1 + np.arange(n_windows, dtype=np.int64)

    arrivals = np.zeros((n_windows, len(counts)), dtype=np.int64)
    for j, c in enumerate(counts):
        arrivals[:, j] = largest_remainder(np.full(n_windows, 1.0), int(c))

    n_final = n_initial + n_mig if mode == "addition" else n_initial
    realised = (n_mig / n_final) if n_final else 0.0

    plan = MigrationPlan(
        mode=mode,
        total_share=float(total_share),
        n_initial=int(n_initial),
        n_migrants_total=int(n_mig),
        n_final_expected=int(n_final),
        counts_by_source=counts,
        arrivals=arrivals,
        arrival_steps=arrival_steps,
        start_year=float(start_year),
        duration_years=float(duration_years),
        profile=profile,
        realised_final_share=float(realised),
    )
    plan.validate()
    return plan
