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
    "spatial_segregation",
    description="Dissimilarity or isolation index over neighbourhood units.",
    category="structure",
    status="placeholder",
    blocked_on="an implemented neighbourhood network layer",
)
def spatial_segregation(ctx: MetricContext) -> float:
    return float("nan")


@register_metric(
    "network_modularity",
    description="Newman modularity of the friendship layer under a cultural partition.",
    category="structure",
    status="placeholder",
    blocked_on="an implemented friendship layer and a choice of partition definition",
)
def network_modularity(ctx: MetricContext) -> float:
    return float("nan")


@register_metric(
    "cross_cultural_interaction_rate",
    description="Fraction of realised interactions occurring between agents of "
    "different cultural profiles.",
    category="interaction",
    status="placeholder",
    blocked_on="an interaction mechanism -- no interactions occur in v0.1",
)
def cross_cultural_interaction_rate(ctx: MetricContext) -> float:
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
