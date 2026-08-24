"""Structured network layers, and the metrics defined over them."""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.agents.population import Population, initialise_resident_population
from culture_flux.culture.features import CultureSchema
from culture_flux.influence.base import NetworkDegreeInfluence, UniformInfluence
from culture_flux.metrics.base import MetricContext, compute_metrics
from culture_flux.metrics.structure import _theil_h
from culture_flux.networks import (
    AttentionTieLayer,
    GroupLayer,
    MultiplexNetwork,
    WellMixedLayer,
    build_network,
)
from culture_flux.rng import RunRNG

SCHEMA = CultureSchema.uniform(8, 4)


def _net(spec, n=600, seed=0):
    return build_network({"layers": spec}, n, np.random.default_rng(seed))


def _pop(n=600, noise=0.5, seed=1):
    return initialise_resident_population(n, SCHEMA, RunRNG(seed), within_noise=noise)


# -- group layers ----------------------------------------------------------

def test_every_agent_belongs_to_exactly_one_group():
    layer = GroupLayer("household", 500, 4.0, np.random.default_rng(0))
    assert layer.membership.shape[0] == 500
    assert layer.membership.ndim == 1


def test_group_count_follows_the_target_size():
    layer = GroupLayer("household", 1000, 4.0, np.random.default_rng(0))
    assert layer.n_groups == 250


def test_sampled_partners_always_share_the_focal_agent_s_group():
    """The whole point of a group layer: interaction is local."""
    rng = np.random.default_rng(0)
    layer = GroupLayer("neighbourhood", 800, 20.0, rng)
    focal = rng.integers(0, 800, size=2000)
    partner = layer.sample_partners(focal, rng)
    assert np.array_equal(layer.membership[focal], layer.membership[partner])


def test_a_lone_agent_returns_itself_rather_than_a_stranger():
    """Silently reassigning would let a rule interact across a boundary the
    network says is closed."""
    rng = np.random.default_rng(0)
    layer = GroupLayer("household", 4, 1.0, rng)
    layer.membership = np.array([0, 1, 1, 2], dtype=np.int32)
    layer._index_dirty = True
    focal = np.array([0, 3])
    assert np.array_equal(layer.sample_partners(focal, rng), focal)


def test_adding_agents_extends_membership_without_disturbing_existing_agents():
    rng = np.random.default_rng(0)
    layer = GroupLayer("workplace", 100, 10.0, rng)
    before = layer.membership.copy()
    layer.add_agents(50, rng)
    assert layer.size() == 150
    assert np.array_equal(layer.membership[:100], before)


def test_clustered_assignment_concentrates_arrivals_more_than_random():
    """The residential sorting mechanism. Off by default (A-022) precisely
    because leaving it on would build enclaves into the initialisation."""
    rng = np.random.default_rng(1)
    spread = []
    for clustering in (0.0, 0.95):
        layer = GroupLayer(
            "neighbourhood", 1000, 25.0, np.random.default_rng(1),
            assignment="clustered", clustering=clustering,
        )
        layer.note_source_placement(1, np.arange(3, dtype=np.int32))
        layer.add_agents(300, rng, source_id=1)
        arrivals = layer.membership[1000:]
        spread.append(np.unique(arrivals).size)
    assert spread[1] < spread[0]


def test_group_layer_rejects_impossible_parameters():
    rng = np.random.default_rng(0)
    with raises(ValueError, "target_size"):
        GroupLayer("household", 100, 0.0, rng)
    with raises(ValueError, "clustering"):
        GroupLayer("household", 100, 4.0, rng, clustering=1.5)
    with raises(ValueError, "unknown assignment"):
        GroupLayer("household", 100, 4.0, rng, assignment="by-income")


# -- attention ties --------------------------------------------------------

def test_every_agent_holds_exactly_the_configured_out_degree():
    layer = AttentionTieLayer("friendship", 300, 6, np.random.default_rng(0))
    assert layer.ties.shape == (300, 6)


def test_ties_never_point_at_the_agent_itself():
    layer = AttentionTieLayer("friendship", 300, 6, np.random.default_rng(0))
    assert not bool((layer.ties == np.arange(300)[:, None]).any())


def test_sampled_partners_are_always_tied_neighbours():
    rng = np.random.default_rng(0)
    layer = AttentionTieLayer("friendship", 200, 5, rng)
    focal = rng.integers(0, 200, size=1000)
    partner = layer.sample_partners(focal, rng)
    assert bool((layer.ties[focal] == partner[:, None]).any(axis=1).all())


def test_rewiring_preserves_out_degree_exactly():
    rng = np.random.default_rng(0)
    layer = AttentionTieLayer("friendship", 300, 6, rng, rewire_rate=0.5)
    pop = _pop(300)
    before = layer.ties.shape
    layer.rewire(pop, rng)
    assert layer.ties.shape == before
    assert not bool((layer.ties == np.arange(300)[:, None]).any())


def test_rewiring_increases_cultural_similarity_across_ties():
    """The enclave mechanism: structure follows culture."""
    rng = np.random.default_rng(0)
    pop = _pop(400, noise=1.0, seed=3)
    layer = AttentionTieLayer("friendship", 400, 6, rng, rewire_rate=1.0, rewire_candidates=8)

    def mean_similarity() -> float:
        src = np.repeat(np.arange(400), 6)
        dst = layer.ties.ravel()
        return float((pop.culture[src] == pop.culture[dst]).mean())

    before = mean_similarity()
    for _ in range(5):
        layer.rewire(pop, rng)
    assert mean_similarity() > before


def test_a_zero_rewire_rate_changes_nothing():
    rng = np.random.default_rng(0)
    layer = AttentionTieLayer("friendship", 200, 4, rng, rewire_rate=0.0)
    before = layer.ties.copy()
    assert layer.rewire(_pop(200), rng) == 0
    assert np.array_equal(layer.ties, before)


def test_one_rewire_candidate_is_no_homophily_at_all():
    """k = 1 makes 'best of k' a uniform draw. Worth pinning, because it is the
    control condition for any claim about homophilous rewiring."""
    rng = np.random.default_rng(0)
    pop = _pop(300, noise=1.0)
    layer = AttentionTieLayer("friendship", 300, 6, rng, rewire_rate=1.0, rewire_candidates=1)

    def mean_similarity() -> float:
        src = np.repeat(np.arange(300), 6)
        return float((pop.culture[src] == pop.culture[layer.ties.ravel()]).mean())

    before = mean_similarity()
    for _ in range(5):
        layer.rewire(pop, rng)
    assert abs(mean_similarity() - before) < 0.05


# -- the multiplex ---------------------------------------------------------

def test_a_single_layer_multiplex_reduces_to_that_layer():
    """The v0.2 engine is the citywide-only special case; it must stay exact."""
    net = MultiplexNetwork()
    net.add_layer(WellMixedLayer(500), 1.0)
    a = net.sample_partners(np.arange(50), np.random.default_rng(4))
    b = WellMixedLayer(500).sample_partners(np.arange(50), np.random.default_rng(4))
    assert np.array_equal(a, b)


def test_layer_weights_are_honoured_in_proportion():
    rng = np.random.default_rng(0)
    net = _net({"household": {"weight": 0.9, "target_size": 2}, "citywide": {"weight": 0.1}}, n=2000)
    household = net.layers["household"]
    focal = rng.integers(0, 2000, size=20000)
    partner = net.sample_partners(focal, rng)
    same_group = float((household.membership[focal] == household.membership[partner]).mean())
    # 0.9 of draws are within-household; the citywide 0.1 lands in the same
    # 2-person household only by chance, so the share should sit just above 0.9.
    assert 0.88 < same_group < 0.94


def test_weights_are_normalised_so_only_ratios_matter():
    a = _net({"household": {"weight": 3.0}, "citywide": {"weight": 1.0}})
    b = _net({"household": {"weight": 30.0}, "citywide": {"weight": 10.0}})
    assert a.normalised_weights == b.normalised_weights


def test_a_zero_weight_layer_is_built_but_never_sampled():
    """Useful for measuring structure that does not drive interaction."""
    rng = np.random.default_rng(0)
    net = _net({"household": {"weight": 0.0, "target_size": 2}, "citywide": {"weight": 1.0}}, n=1000)
    assert "household" in net.layers
    focal = rng.integers(0, 1000, size=5000)
    partner = net.sample_partners(focal, rng)
    hh = net.layers["household"]
    same = float((hh.membership[focal] == hh.membership[partner]).mean())
    assert same < 0.05


def test_the_citywide_only_network_reports_itself_as_unstructured():
    assert _net({"citywide": {}}).is_well_mixed_only
    assert not _net({"household": {}, "citywide": {}}).is_well_mixed_only


def test_adding_agents_grows_every_layer_together():
    rng = np.random.default_rng(0)
    net = _net({"household": {}, "friendship": {}, "citywide": {}}, n=200)
    net.add_agents(50, rng)
    assert {layer.size() for layer in net.layers.values()} == {250}


def test_unknown_layers_and_parameters_are_rejected():
    with raises(ValueError, "unknown network layer"):
        _net({"subway": {}})
    with raises(ValueError, "unknown parameters"):
        _net({"friendship": {"degre": 4}})
    with raises(ValueError, "takes no parameters"):
        _net({"citywide": {"target_size": 4}})


# -- segregation index -----------------------------------------------------

def test_theil_h_is_zero_when_every_unit_mirrors_the_city():
    cats = np.array([0, 1] * 50)
    units = np.tile(np.arange(25), 4)
    assert approx(_theil_h(cats, units), 0.0, tol=1e-9)


def test_theil_h_is_one_under_complete_separation():
    cats = np.array([0] * 50 + [1] * 50)
    units = np.array([0] * 50 + [1] * 50)
    assert approx(_theil_h(cats, units), 1.0, tol=1e-9)


def test_theil_h_lies_between_the_extremes_for_partial_sorting():
    cats = np.array([0] * 50 + [1] * 50)
    units = np.concatenate([np.zeros(40), np.ones(10), np.zeros(10), np.ones(40)]).astype(int)
    h = _theil_h(cats, units)
    assert 0.0 < h < 1.0


def test_theil_h_is_zero_with_only_one_category_or_one_unit():
    """Nothing to segregate, or nowhere to segregate into -- both are 0, not NaN."""
    assert _theil_h(np.zeros(50, dtype=int), np.tile(np.arange(5), 10)) == 0.0
    assert _theil_h(np.array([0, 1] * 25), np.zeros(50, dtype=int)) == 0.0


def test_theil_h_is_invariant_to_relabelling():
    cats = np.array([0] * 30 + [1] * 40 + [2] * 30)
    units = np.tile(np.arange(10), 10)
    relabelled = np.where(cats == 0, 7, np.where(cats == 1, 3, 9))
    assert approx(_theil_h(cats, units), _theil_h(relabelled, units))


# -- structure metrics end to end -----------------------------------------

def _ctx_with_network(pop, net, seed=0, **extras):
    base = {"network": net}
    base.update(extras)
    return MetricContext(
        population=pop,
        schema=pop.schema,
        step=1,
        year=1.0,
        generation=0.04,
        initial_resident_profile=np.zeros(pop.n_features, dtype=np.int16),
        initial_culture=pop.culture.copy(),
        influence=UniformInfluence(),
        rng=np.random.default_rng(seed),
        founding_profiles=np.unique(pop.culture, axis=0),
        extras=base,
    )


def test_a_perfectly_sorted_city_reports_maximal_segregation():
    schema = CultureSchema.uniform(4, 2)
    culture = np.vstack([np.zeros((100, 4)), np.ones((100, 4))]).astype(np.int16)
    pop = Population(
        schema=schema,
        agent_id=np.arange(200, dtype=np.int64),
        source_id=np.array([0] * 100 + [1] * 100, dtype=np.int16),
        arrival_step=np.full(200, -1, dtype=np.int32),
        migration_generation=np.zeros(200, dtype=np.int8),
        culture=culture,
    )
    net = _net({"neighbourhood": {"target_size": 100}}, n=200)
    net.layers["neighbourhood"].membership = np.array([0] * 100 + [1] * 100, dtype=np.int32)
    net.layers["neighbourhood"]._index_dirty = True
    m = compute_metrics(_ctx_with_network(pop, net), ("spatial_segregation", "origin_spatial_segregation"))
    assert approx(m["spatial_segregation"], 1.0, tol=1e-9)
    assert approx(m["origin_spatial_segregation"], 1.0, tol=1e-9)


def test_a_randomly_mixed_city_reports_low_segregation():
    pop = _pop(1000, noise=1.0)
    net = _net({"neighbourhood": {"target_size": 50}}, n=1000)
    m = compute_metrics(_ctx_with_network(pop, net), ("origin_spatial_segregation",))
    assert m["origin_spatial_segregation"] < 0.05


def test_modularity_is_near_zero_for_ties_that_ignore_culture():
    pop = _pop(500, noise=1.0, seed=9)
    net = _net({"friendship": {"degree": 6}}, n=500)
    m = compute_metrics(_ctx_with_network(pop, net), ("network_modularity",))
    assert abs(m["network_modularity"]) < 0.15


def test_cross_cultural_interaction_rate_reads_the_rule_s_counters():
    pop = _pop(100)
    net = _net({"citywide": {}}, n=100)
    ctx = _ctx_with_network(pop, net, encounters=1000, cross_cultural_encounters=250)
    assert approx(
        compute_metrics(ctx, ("cross_cultural_interaction_rate",))["cross_cultural_interaction_rate"],
        0.25,
    )
    ctx0 = _ctx_with_network(pop, net, encounters=0, cross_cultural_encounters=0)
    v = compute_metrics(ctx0, ("cross_cultural_interaction_rate",))["cross_cultural_interaction_rate"]
    assert v != v  # no encounters is unmeasured, not zero


# -- degree-based influence ------------------------------------------------

def test_degree_influence_refuses_to_fall_back_to_uniform():
    """A silent fallback would produce output indistinguishable from a run that
    meant to be uniform."""
    model = NetworkDegreeInfluence()
    with raises(RuntimeError, "not bound"):
        model.weights(_pop(50), 0)
    model.bind(_net({"citywide": {}}, n=50))
    with raises(RuntimeError, "friendship"):
        model.weights(_pop(50), 0)


def test_degree_influence_is_higher_for_more_attended_agents():
    pop = _pop(300)
    net = _net({"friendship": {"degree": 4}}, n=300)
    model = NetworkDegreeInfluence()
    model.bind(net)
    w = model.weights(pop, 0)
    in_degree = np.bincount(net.layers["friendship"].ties.ravel(), minlength=300)[:300]
    assert np.corrcoef(w, in_degree)[0, 1] > 0.9
    assert float(w.min()) >= model.floor


def test_a_zero_exponent_reproduces_the_uniform_null():
    pop = _pop(200)
    net = _net({"friendship": {}}, n=200)
    model = NetworkDegreeInfluence(exponent=0.0)
    model.bind(net)
    w = model.weights(pop, 0)
    assert float(w.max() - w.min()) == 0.0


def test_degree_influence_makes_share_and_influence_diverge():
    """The point of A-009: under a non-uniform model the two must come apart."""
    pop = _pop(400)
    pop.add_agents(np.zeros((100, pop.n_features), dtype=np.int16), source_id=1, arrival_step=1)
    net = _net({"friendship": {}}, n=500)
    model = NetworkDegreeInfluence()
    model.bind(net)
    infl = model.group_influence(pop, 0)
    shares = pop.source_shares()
    assert max(abs(infl[k] - v) for k, v in shares.items()) > 0.0
