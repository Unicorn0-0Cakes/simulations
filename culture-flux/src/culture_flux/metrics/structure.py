"""Metrics over social and spatial structure.

These three were registered as placeholders in v0.1 and are implemented here.
Each replaces its placeholder registration, so the metric name is stable across
versions and a stored v0.1 run with a NaN in that column is still readable.

Segregation
-----------
Multi-group segregation is measured by **Theil's information index H**:

    H = (E - sum_u (n_u / N) E_u) / E

where E is the entropy of the citywide distribution over categories and E_u the
entropy within unit u. It is 0 when every unit mirrors the city and 1 when every
unit is internally uniform. Theil's H rather than the more familiar index of
dissimilarity because dissimilarity is defined for two groups and cultural
profiles are many -- collapsing them to two would require choosing which
division matters, which is exactly the kind of decision this project refuses to
make inside the instrument.

Modularity
----------
Newman's Q over the attention layer, symmetrised for measurement, with
communities given by whole cultural profile. Q > 0 means agents are tied to
culturally similar agents more than chance; Q near 0 means ties ignore culture.

An important caveat, recorded as A-025: with homophilous rewiring switched on,
positive modularity is partly a *direct consequence* of the rewiring rule rather
than an emergent property. Modularity is informative about enclave formation
only when compared against a matched run with rewiring disabled.
"""

from __future__ import annotations

import numpy as np

from ..culture.profile import profile_keys
from .base import MetricContext, register_metric


def _theil_h(categories: np.ndarray, units: np.ndarray) -> float:
    """Multi-group Theil information index of segregation, in [0, 1]."""
    n = categories.shape[0]
    if n == 0 or units.shape[0] != n:
        return float("nan")
    cat_codes, cat_idx = np.unique(categories, return_inverse=True)
    unit_codes, unit_idx = np.unique(units, return_inverse=True)
    n_cat, n_unit = cat_codes.size, unit_codes.size
    if n_cat < 2 or n_unit < 2:
        # One category means nothing to segregate; one unit means nowhere to
        # segregate into. Both are 0 segregation, not undefined.
        return 0.0
    table = np.zeros((n_unit, n_cat), dtype=np.float64)
    np.add.at(table, (unit_idx, cat_idx), 1.0)
    unit_totals = table.sum(axis=1)
    overall = table.sum(axis=0) / n

    def entropy(p: np.ndarray) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            terms = np.where(p > 0, -p * np.log(p), 0.0)
        return terms.sum(axis=-1)

    e_total = float(entropy(overall))
    if e_total <= 0:
        return 0.0
    shares = np.divide(
        table, unit_totals[:, None], out=np.zeros_like(table), where=unit_totals[:, None] > 0
    )
    e_units = entropy(shares)
    weighted = float((unit_totals / n * e_units).sum())
    return float(max(0.0, min(1.0, (e_total - weighted) / e_total)))


def _residential_units(ctx: MetricContext) -> np.ndarray | None:
    net = ctx.extras.get("network")
    if net is None:
        return None
    for name in ("neighbourhood", "household", "workplace"):
        membership = net.group_membership(name)
        if membership is not None and membership.shape[0] == ctx.population.size:
            return membership
    return None


@register_metric(
    "spatial_segregation",
    description="Theil's multi-group information index over cultural profiles "
    "across residential units. 0 = every neighbourhood mirrors the city; "
    "1 = every neighbourhood is internally uniform. NaN when the network has no "
    "spatial layer, because there is then nowhere to segregate into.",
    category="structure",
)
def spatial_segregation(ctx: MetricContext) -> float:
    units = _residential_units(ctx)
    if units is None or ctx.population.size == 0:
        return float("nan")
    return _theil_h(profile_keys(ctx.population.culture, ctx.schema), units)


@register_metric(
    "origin_spatial_segregation",
    description="The same index computed over SOURCE POPULATION rather than "
    "culture. Reported separately because people can be residentially sorted by "
    "origin while culturally mixed, or the reverse, and collapsing the two would "
    "hide exactly that distinction.",
    category="structure",
)
def origin_spatial_segregation(ctx: MetricContext) -> float:
    units = _residential_units(ctx)
    if units is None or ctx.population.size == 0:
        return float("nan")
    return _theil_h(ctx.population.source_id, units)


@register_metric(
    "network_modularity",
    description="Newman modularity of the attention layer, symmetrised, with "
    "communities given by whole cultural profile. Positive means ties run "
    "between culturally similar agents more than chance. Interpretable as "
    "enclave formation only against a matched run with rewiring off (A-025).",
    category="structure",
)
def network_modularity(ctx: MetricContext) -> float:
    net = ctx.extras.get("network")
    if net is None or ctx.population.size == 0:
        return float("nan")
    layer = net.layers.get("friendship")
    if layer is None or not hasattr(layer, "symmetric_edges"):
        return float("nan")
    src, dst = layer.symmetric_edges()
    m = src.shape[0]
    if m == 0:
        return float("nan")
    comm = profile_keys(ctx.population.culture, ctx.schema)
    n_comm = int(comm.max()) + 1
    internal = np.bincount(comm[src][comm[src] == comm[dst]], minlength=n_comm).astype(np.float64)
    degree = np.bincount(comm[src], minlength=n_comm).astype(np.float64) + np.bincount(
        comm[dst], minlength=n_comm
    ).astype(np.float64)
    q = (internal / m - np.square(degree / (2.0 * m))).sum()
    return float(q)


@register_metric(
    "cross_cultural_interaction_rate",
    description="Share of encounters in the most recent step that paired agents "
    "with different cultural profiles. Counts encounters, not successful copies: "
    "the question is who meets whom, which a success-weighted measure would "
    "confound with how readily they influence one another.",
    category="interaction",
)
def cross_cultural_interaction_rate(ctx: MetricContext) -> float:
    encounters = int(ctx.extras.get("encounters", 0))
    if encounters <= 0:
        return float("nan")
    return float(int(ctx.extras.get("cross_cultural_encounters", 0)) / encounters)


@register_metric(
    "mean_group_cultural_homogeneity",
    description="Mean over residential units of the share of the unit holding "
    "its own most common cultural profile. A local-convergence measure: high "
    "values with low citywide dominance is the signature of locally uniform, "
    "globally varied culture.",
    category="structure",
)
def mean_group_cultural_homogeneity(ctx: MetricContext) -> float:
    units = _residential_units(ctx)
    if units is None or ctx.population.size == 0:
        return float("nan")
    keys = profile_keys(ctx.population.culture, ctx.schema)
    unit_codes, unit_idx = np.unique(units, return_inverse=True)
    cat_codes, cat_idx = np.unique(keys, return_inverse=True)
    table = np.zeros((unit_codes.size, cat_codes.size), dtype=np.float64)
    np.add.at(table, (unit_idx, cat_idx), 1.0)
    totals = table.sum(axis=1)
    present = totals > 0
    if not bool(present.any()):
        return float("nan")
    return float((table[present].max(axis=1) / totals[present]).mean())
