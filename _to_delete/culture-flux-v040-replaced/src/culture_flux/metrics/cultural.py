"""Outcome metrics over a population's culture.

Naming discipline: every metric here describes a *measurable quantity*, never an
outcome *category*. There is no ``assimilation_index`` and no ``is_transformed``
flag, because "assimilation", "integration", "fragmentation" and the rest are
regions of a measured space whose boundaries are an empirical question (RQ7).
Classifying runs into those regions is the job of the analysis layer, working
from these numbers, and it will be done by fitting -- not by a threshold written
into the engine.

Placeholders return NaN and say what they are waiting for. A metric that cannot
yet be computed must be visibly absent, because a plausible-looking zero is worse
than a NaN.
"""

from __future__ import annotations

import numpy as np

from ..agents.population import RESIDENT_SOURCE_ID
from ..culture.distance import distance_to_profile, mean_pairwise_distance
from ..culture.profile import profile_keys
from . import diversity as div
from .base import MetricContext, register_metric


# ---------------------------------------------------------------------------
# Derived quantities shared by several metrics, computed once per measurement
# ---------------------------------------------------------------------------

def _profile_shares(ctx: MetricContext) -> np.ndarray:
    """Population shares of each distinct whole cultural profile."""
    return ctx.cached(
        "profile_shares",
        lambda: div.shares_from_labels(profile_keys(ctx.population.culture, ctx.schema)),
    )


def _founding_distance(ctx: MetricContext) -> np.ndarray:
    """Per-agent cultural distance from the founding resident profile."""
    return ctx.cached(
        "founding_distance",
        lambda: distance_to_profile(
            ctx.population.culture,
            ctx.initial_resident_profile,
            ctx.schema,
            ctx.distance_metric,
        ),
    )

# ---------------------------------------------------------------------------
# Composition -- who is here (population share, never influence)
# ---------------------------------------------------------------------------

@register_metric(
    "population_size",
    description="Number of agents currently in the city.",
    category="composition",
)
def population_size(ctx: MetricContext) -> float:
    return float(ctx.population.size)


@register_metric(
    "resident_population_share",
    description="Fraction of agents whose source is the resident founding population. "
    "A count, carrying no implication about influence.",
    category="composition",
)
def resident_population_share(ctx: MetricContext) -> float:
    n = ctx.population.size
    return float(ctx.population.resident_mask.sum() / n) if n else float("nan")


@register_metric(
    "source_fractionalization",
    description="1 - sum(p^2) over source-population labels, residents included. "
    "Measures diversity of ORIGIN, not of culture.",
    category="composition",
)
def source_fractionalization(ctx: MetricContext) -> float:
    n = ctx.population.size
    if n == 0:
        return float("nan")
    return ctx.cached(
        "source_fractionalization",
        lambda: div.fractionalization(div.shares_from_labels(ctx.population.source_id)),
    )


@register_metric(
    "incoming_source_evenness",
    description="Pielou evenness of the incoming populations' relative sizes, "
    "residents excluded. The realised value of H.",
    category="composition",
)
def incoming_source_evenness(ctx: MetricContext) -> float:
    mig = ctx.population.source_id[ctx.population.migrant_mask]
    if mig.size == 0:
        return float("nan")
    return div.pielou_evenness(div.shares_from_labels(mig))


@register_metric(
    "incoming_source_count",
    description="Number of distinct incoming populations actually present. "
    "The realised value of K, which can fall below the configured K under "
    "integer rounding at small migrant totals.",
    category="composition",
)
def incoming_source_count(ctx: MetricContext) -> float:
    mig = ctx.population.source_id[ctx.population.migrant_mask]
    return float(np.unique(mig).size) if mig.size else 0.0


# ---------------------------------------------------------------------------
# Cultural diversity -- what is believed, independent of who believes it
# ---------------------------------------------------------------------------

@register_metric(
    "cultural_fractionalization",
    description="1 - sum(p^2) over distinct whole cultural profiles.",
    category="cultural_diversity",
)
def cultural_fractionalization(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return div.fractionalization(_profile_shares(ctx))


@register_metric(
    "cultural_entropy",
    description="Shannon entropy (nats) over distinct whole cultural profiles.",
    category="cultural_diversity",
)
def cultural_entropy(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return div.shannon_entropy(_profile_shares(ctx))


@register_metric(
    "cultural_effective_number",
    description="Inverse Simpson over cultural profiles: the effective number of "
    "cultures present, comparable across runs with different profile counts.",
    category="cultural_diversity",
)
def cultural_effective_number(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return div.effective_number(_profile_shares(ctx))


@register_metric(
    "cultural_richness",
    description="Count of distinct whole cultural profiles present.",
    category="cultural_diversity",
)
def cultural_richness(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return div.richness(_profile_shares(ctx))


@register_metric(
    "dominant_profile_share",
    description="Population share of the single most common cultural profile. "
    "A dominance measure; says nothing about WHICH profile dominates.",
    category="cultural_diversity",
)
def dominant_profile_share(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return div.max_share(_profile_shares(ctx))


# ---------------------------------------------------------------------------
# Persistence and change relative to the initial state
# ---------------------------------------------------------------------------

@register_metric(
    "resident_trait_retention",
    description="Mean fraction of features on which a randomly chosen CURRENT "
    "resident of the city still carries the founding resident trait. Averaged "
    "over the whole population, migrants included, because the question is what "
    "the city believes -- not what the founders' descendants believe.",
    category="persistence",
)
def resident_trait_retention(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return float(1.0 - _founding_distance(ctx).mean())


@register_metric(
    "founder_subpopulation_retention",
    description="The same quantity computed only over agents of resident origin. "
    "Under a null transmission rule this is exactly 1.0; any departure from 1.0 "
    "is evidence that a transmission mechanism is active.",
    category="persistence",
)
def founder_subpopulation_retention(ctx: MetricContext) -> float:
    mask = ctx.population.source_id == RESIDENT_SOURCE_ID
    if not bool(mask.any()):
        return float("nan")
    d = distance_to_profile(
        ctx.population.culture[mask],
        ctx.initial_resident_profile,
        ctx.schema,
        ctx.distance_metric,
    )
    return float(1.0 - d.mean())


@register_metric(
    "mean_distance_from_founding_culture",
    description="Mean cultural distance of the current population from the "
    "founding resident profile. The complement of resident_trait_retention.",
    category="persistence",
)
def mean_distance_from_founding_culture(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    return float(_founding_distance(ctx).mean())


@register_metric(
    "min_trait_persistence",
    description="Over features, the LOWEST frequency of the founding resident "
    "trait. Detects a culture being hollowed out feature by feature while its "
    "mean retention still looks healthy.",
    category="persistence",
)
def min_trait_persistence(ctx: MetricContext) -> float:
    if ctx.population.size == 0:
        return float("nan")
    match = ctx.population.culture == np.asarray(ctx.initial_resident_profile).reshape(1, -1)
    return float(match.mean(axis=0).min())


@register_metric(
    "mean_pairwise_cultural_distance",
    description="Mean cultural distance between two randomly drawn agents. "
    "Sampled above 200k pairs, from the run's own metric stream.",
    category="cultural_diversity",
)
def mean_pairwise_cultural_distance(ctx: MetricContext) -> float:
    return float(
        mean_pairwise_distance(
            ctx.population.culture, ctx.schema, ctx.distance_metric, rng=ctx.rng
        )
    )


# ---------------------------------------------------------------------------
# Population share versus cultural influence
# ---------------------------------------------------------------------------

@register_metric(
    "influence_share_divergence",
    description="Largest absolute gap between a group's share of cultural "
    "influence and its share of the population. Exactly 0 under the uniform "
    "influence null; non-zero is the signature of a non-uniform influence model.",
    category="influence",
)
def influence_share_divergence(ctx: MetricContext) -> float:
    pop = ctx.population
    if pop.size == 0:
        return float("nan")
    infl = ctx.influence.group_influence(pop, ctx.step)
    shares = pop.source_shares()
    return float(max(abs(infl.get(k, 0.0) - v) for k, v in shares.items()))


# ---------------------------------------------------------------------------
# Declared but not yet computable
# ---------------------------------------------------------------------------

@register_metric(
    "hybridization_index",
    description="Share of agents whose cultural profile matches no founding "
    "profile -- resident or incoming. Requires a transmission rule: without one, "
    "novel profiles cannot arise and the metric is trivially 0, which would be "
    "mistaken for a finding.",
    category="hybridisation",
    status="placeholder",
    blocked_on="a transmission rule (dynamics.IMPLEMENTED_RULES) and a decision on "
    "whether 'novel' means 'exactly no founding profile' or 'beyond distance d from "
    "every founding profile' -- see assumption A-012",
)
def hybridization_index(ctx: MetricContext) -> float:
    return float("nan")


@register_metric(
    "dominant_cultural_lineage",
    description="Which founding culture the currently dominant profile descends "
    "from, as a share of the population.",
    category="persistence",
    status="placeholder",
    blocked_on="lineage tracking through transmission events -- profiles alone do "
    "not carry ancestry once traits can be copied",
)
def dominant_cultural_lineage(ctx: MetricContext) -> float:
    return float("nan")


# ---------------------------------------------------------------------------
# Novelty relative to the founding cultures
#
# These do NOT define "hybrid" -- that is A-012, still open. They report the
# distance-to-nearest-founder distribution, which is the raw material any
# eventual definition would be built from, and which is informative on its own.
# ---------------------------------------------------------------------------

def _nearest_founder_distance(ctx: MetricContext) -> np.ndarray | None:
    """Per-agent distance to the closest founding profile, or None.

    None -- rather than an array of NaN -- when the founding set was not
    supplied, so that each metric returns NaN explicitly instead of averaging
    NaNs and emitting a warning, or worse, comparing NaN to zero and getting a
    confident False.
    """

    def compute() -> np.ndarray | None:
        founders = ctx.founding_profiles
        if founders is None or len(founders) == 0:
            return None
        dists = np.stack(
            [
                distance_to_profile(ctx.population.culture, f, ctx.schema, ctx.distance_metric)
                for f in founders
            ],
            axis=0,
        )
        return dists.min(axis=0)

    return ctx.cached("nearest_founder_distance", compute)


@register_metric(
    "mean_distance_to_nearest_founding_culture",
    description="Mean over agents of the distance to the closest founding profile "
    "(resident or incoming). Exactly 0 while no trait has moved. Rises as "
    "recombination carries agents away from every founding culture.",
    category="hybridisation",
)
def mean_distance_to_nearest_founding_culture(ctx: MetricContext) -> float:
    d = _nearest_founder_distance(ctx)
    if d is None or ctx.population.size == 0:
        return float("nan")
    return float(d.mean())


@register_metric(
    "max_distance_to_nearest_founding_culture",
    description="The furthest any single agent has moved from every founding "
    "profile. The leading edge of novelty, which a mean hides.",
    category="hybridisation",
)
def max_distance_to_nearest_founding_culture(ctx: MetricContext) -> float:
    d = _nearest_founder_distance(ctx)
    if d is None or ctx.population.size == 0:
        return float("nan")
    return float(d.max())


@register_metric(
    "share_off_founding_profiles",
    description="Share of agents whose profile is not exactly equal to any "
    "founding profile. Reported WITHOUT being called hybridisation: a single "
    "copied trait satisfies it, which is precisely why it cannot serve as a "
    "hybridisation index on its own (A-012).",
    category="hybridisation",
)
def share_off_founding_profiles(ctx: MetricContext) -> float:
    d = _nearest_founder_distance(ctx)
    if d is None or ctx.population.size == 0:
        return float("nan")
    return float((d > 0).mean())


# ---------------------------------------------------------------------------
# Convergence diagnostics
# ---------------------------------------------------------------------------

@register_metric(
    "interactable_pair_fraction",
    description="Estimated fraction of agent pairs that could still influence "
    "each other -- overlap strictly between 0 and 1. Reaching 0 means the "
    "population is in an absorbing state and further simulation cannot change "
    "it, which distinguishes a genuine equilibrium from a run that was too short.",
    category="convergence",
)
def interactable_pair_fraction(ctx: MetricContext) -> float:
    pop = ctx.population
    n = pop.size
    if n < 2:
        return float("nan")
    rng = ctx.rng
    sample = 20_000
    i = rng.integers(0, n, size=sample)
    j = rng.integers(0, n - 1, size=sample)
    j = j + (j >= i)
    from ..culture.distance import get_distance

    d = get_distance(ctx.distance_metric)(pop.culture[i], pop.culture[j], ctx.schema)
    return float(((d > 0.0) & (d < 1.0)).mean())
