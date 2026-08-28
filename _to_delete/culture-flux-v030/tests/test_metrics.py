"""Metric behaviour on populations with known composition."""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.agents.population import initialise_resident_population
from culture_flux.culture.features import CultureSchema
from culture_flux.influence.base import UniformInfluence, get_influence_model
from culture_flux.metrics.base import (
    MetricContext,
    available_metrics,
    compute_metrics,
    get_metric,
    metric_table,
)
from culture_flux.rng import RunRNG

SCHEMA = CultureSchema.uniform(10, 5)


def _ctx(pop, seed=0, founders="auto"):
    if founders == "auto":
        founders = np.unique(pop.culture, axis=0)
    return MetricContext(
        population=pop,
        schema=SCHEMA,
        step=0,
        year=0.0,
        generation=0.0,
        initial_resident_profile=np.zeros(SCHEMA.n_features, dtype=np.int16),
        initial_culture=pop.culture.copy(),
        influence=UniformInfluence(),
        rng=np.random.default_rng(seed),
        founding_profiles=founders,
    )


def _city(n_resident=800, n_migrant=200, migrant_distance_features=5):
    pop = initialise_resident_population(n_resident, SCHEMA, RunRNG(1), within_noise=0.0)
    culture = np.zeros((n_migrant, SCHEMA.n_features), dtype=np.int16)
    culture[:, :migrant_distance_features] = 1
    pop.add_agents(culture, source_id=1, arrival_step=1)
    return pop


# -- known closed forms ----------------------------------------------------

def test_a_homogeneous_city_has_zero_cultural_diversity():
    pop = initialise_resident_population(500, SCHEMA, RunRNG(1))
    m = compute_metrics(_ctx(pop))
    assert m["cultural_fractionalization"] == 0.0
    assert m["cultural_entropy"] == 0.0
    assert m["cultural_richness"] == 1.0
    assert approx(m["dominant_profile_share"], 1.0)
    assert approx(m["resident_trait_retention"], 1.0)
    assert approx(m["source_fractionalization"], 0.0)


def test_retention_equals_one_minus_migrant_share_times_cultural_distance():
    """The compositional arithmetic, checked exactly. Under the null rule this
    is ALL that retention can do -- which is the point of measuring it here."""
    pop = _city(n_resident=800, n_migrant=200, migrant_distance_features=5)
    m = compute_metrics(_ctx(pop))
    expected = 1.0 - 0.2 * 0.5
    assert approx(m["resident_trait_retention"], expected, tol=1e-12)
    assert approx(m["mean_distance_from_founding_culture"], 1.0 - expected, tol=1e-12)


def test_founder_retention_is_exactly_one_when_no_transmission_has_occurred():
    """A sensitive detector: any mechanism that silently changes resident
    culture drops this below 1.0."""
    m = compute_metrics(_ctx(_city()))
    assert m["founder_subpopulation_retention"] == 1.0


def test_min_trait_persistence_catches_a_feature_being_hollowed_out():
    pop = _city(n_resident=500, n_migrant=500, migrant_distance_features=2)
    m = compute_metrics(_ctx(pop))
    assert approx(m["resident_trait_retention"], 0.9, tol=1e-12)
    assert approx(m["min_trait_persistence"], 0.5, tol=1e-12)  # the two shared features


def test_two_equal_groups_give_the_expected_fractionalization():
    pop = _city(n_resident=500, n_migrant=500)
    m = compute_metrics(_ctx(pop))
    assert approx(m["source_fractionalization"], 0.5, tol=1e-12)
    assert approx(m["cultural_fractionalization"], 0.5, tol=1e-12)
    assert approx(m["cultural_effective_number"], 2.0, tol=1e-12)


def test_source_and_cultural_diversity_are_different_measurements():
    """Same origins, identical cultures: origin diversity is high, cultural
    diversity is zero. Conflating the two would make this impossible to see."""
    pop = initialise_resident_population(500, SCHEMA, RunRNG(1))
    pop.add_agents(np.zeros((500, SCHEMA.n_features), dtype=np.int16), source_id=1, arrival_step=1)
    m = compute_metrics(_ctx(pop))
    assert approx(m["source_fractionalization"], 0.5, tol=1e-12)
    assert m["cultural_fractionalization"] == 0.0


def test_incoming_evenness_ignores_residents():
    pop = initialise_resident_population(9000, SCHEMA, RunRNG(1))
    for sid in (1, 2):
        c = np.zeros((500, SCHEMA.n_features), dtype=np.int16)
        c[:, 0] = sid
        pop.add_agents(c, source_id=sid, arrival_step=1)
    m = compute_metrics(_ctx(pop))
    assert approx(m["incoming_source_evenness"], 1.0, tol=1e-12)
    assert m["incoming_source_count"] == 2.0


def test_population_share_and_influence_agree_only_because_the_null_says_so():
    """Under UniformInfluence the divergence is exactly 0 -- as an output of a
    named model, not as an unexamined identity."""
    m = compute_metrics(_ctx(_city()))
    assert m["influence_share_divergence"] == 0.0


def test_a_non_uniform_influence_model_would_show_up_immediately():
    class Skewed(UniformInfluence):
        name = "skewed-test-only"

        def weights(self, population, step):
            w = np.ones(population.size)
            w[population.migrant_mask] = 4.0
            return w

    pop = _city(n_resident=500, n_migrant=500)
    ctx = _ctx(pop)
    ctx.influence = Skewed()
    m = compute_metrics(ctx, ("influence_share_divergence",))
    assert approx(m["influence_share_divergence"], 0.3, tol=1e-12)


# -- the registry ----------------------------------------------------------

def test_every_placeholder_metric_returns_nan_rather_than_a_plausible_zero():
    placeholders = [n for n, s in available_metrics().items() if s.status == "placeholder"]
    assert placeholders
    values = compute_metrics(_ctx(_city()), tuple(placeholders))
    for name, value in values.items():
        assert value != value, f"{name} returned {value}, not NaN"


def test_every_placeholder_says_what_it_is_blocked_on():
    for name, spec in available_metrics("placeholder").items():
        assert spec.blocked_on.strip(), name


def test_founder_relative_metrics_degrade_to_nan_without_a_founding_set():
    """Not to zero. `(nan > 0).mean()` would return a confident 0.0, which reads
    as 'nothing novel has appeared' rather than 'not measured'."""
    values = compute_metrics(
        _ctx(_city(), founders=None),
        (
            "mean_distance_to_nearest_founding_culture",
            "max_distance_to_nearest_founding_culture",
            "share_off_founding_profiles",
        ),
    )
    for name, v in values.items():
        assert v != v, f"{name} returned {v}, not NaN"


#: Metrics that are undefined without a network in the context. They return NaN
#: rather than 0, because "no spatial layer exists" and "there is no segregation"
#: are different statements and must not share a value.
NEEDS_NETWORK = (
    "spatial_segregation",
    "origin_spatial_segregation",
    "network_modularity",
    "cross_cultural_interaction_rate",
    "mean_group_cultural_homogeneity",
)


def test_every_implemented_metric_returns_a_finite_number():
    values = compute_metrics(_ctx(_city()))
    for name, value in values.items():
        if name in NEEDS_NETWORK:
            continue
        assert np.isfinite(value), f"{name} returned {value}"


def test_structure_metrics_are_nan_without_a_network_not_zero():
    values = compute_metrics(_ctx(_city()), NEEDS_NETWORK)
    for name, value in values.items():
        assert value != value, f"{name} returned {value}, not NaN"


def test_metric_names_are_unique_and_described():
    rows = metric_table()
    assert len({r["name"] for r in rows}) == len(rows)
    for r in rows:
        assert r["description"].strip() and r["category"].strip()


def test_no_metric_encodes_an_outcome_CATEGORY_or_a_threshold():
    """Transformation thresholds must be found in the data, never asserted in
    the instrument. A metric named for an outcome state would be a threshold in
    disguise."""
    banned = ("assimilat", "integrat", "fragment", "dominan_state", "threshold", "tipping", "transformed")
    for r in metric_table():
        low = r["name"].lower()
        for word in banned:
            assert word not in low, f"metric {r['name']} names an outcome category"


def test_an_unknown_metric_name_raises_with_the_registry_listed():
    with raises(KeyError, "unknown metric"):
        get_metric("vibes")


def test_influence_model_registry_rejects_unknown_names():
    with raises(KeyError, "unknown influence model"):
        get_influence_model("charisma")
