"""Migration accounting: conservation, allocation, and the M/K/H/D separation."""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.culture.features import CultureSchema
from culture_flux.migration.schedule import (
    build_plan,
    largest_remainder,
    total_migrants,
)
from culture_flux.migration.sources import (
    evenness,
    generate_source_set,
    resolve_distance,
    shares_for_target_evenness,
    source_shares,
)

SCHEMA = CultureSchema.uniform(20, 5)
RESIDENT = np.zeros(SCHEMA.n_features, dtype=np.int16)


# -- integer allocation ----------------------------------------------------

def test_largest_remainder_conserves_the_total_exactly():
    for total in (0, 1, 7, 100, 9999):
        for shares in ([1.0], [0.5, 0.5], [0.7, 0.2, 0.1], [1 / 3] * 3, [0.1] * 10):
            counts = largest_remainder(np.array(shares), total)
            assert int(counts.sum()) == total, (shares, total)


def test_largest_remainder_never_returns_a_negative_count():
    counts = largest_remainder(np.array([0.999, 0.001]), 3)
    assert int(counts.min()) >= 0


def test_largest_remainder_error_is_bounded_by_one_agent_per_group():
    shares = np.array([1 / 3, 1 / 3, 1 / 3])
    counts = largest_remainder(shares, 100)
    assert bool((np.abs(counts - shares * 100) < 1.0).all())


def test_largest_remainder_is_deterministic():
    a = largest_remainder(np.array([1 / 3] * 3), 100)
    b = largest_remainder(np.array([1 / 3] * 3), 100)
    assert np.array_equal(a, b)


def test_allocating_a_positive_total_across_zero_groups_is_rejected():
    with raises(ValueError, "zero groups"):
        largest_remainder(np.zeros(0), 5)


# -- how many arrive -------------------------------------------------------

def test_addition_mode_reaches_the_requested_FINAL_migrant_share():
    for m in (0.05, 0.1, 0.3, 0.5, 0.6):
        n0 = 100000
        k = total_migrants("addition", m, n0)
        assert approx(k / (n0 + k), m, tol=1e-4), m


def test_replacement_mode_reaches_the_same_share_at_constant_population():
    for m in (0.05, 0.3, 0.6):
        n0 = 100000
        k = total_migrants("replacement", m, n0)
        assert approx(k / n0, m, tol=1e-4), m


def test_zero_migration_produces_no_migrants():
    assert total_migrants("addition", 0.0, 1000) == 0


def test_a_migrant_share_of_one_is_rejected():
    """It would leave no residents, making retention undefined rather than zero."""
    with raises(ValueError, "0, 1"):
        total_migrants("addition", 1.0, 1000)


# -- the schedule ----------------------------------------------------------

def _plan(**kw):
    args = dict(
        mode="addition",
        total_share=0.3,
        n_initial=10000,
        shares=np.array([0.5, 0.5]),
        steps_per_year=12,
        start_year=0.0,
        duration_years=10.0,
    )
    args.update(kw)
    return build_plan(**args)


def test_scheduled_arrivals_conserve_the_migrant_total():
    p = _plan()
    assert int(p.arrivals.sum()) == p.n_migrants_total
    assert np.array_equal(p.arrivals.sum(axis=0), p.counts_by_source)


def test_velocity_changes_timing_but_not_cumulative_migration():
    """RQ5 depends on this exactly: same total, different speed."""
    slow, fast = _plan(duration_years=50.0), _plan(duration_years=2.0)
    assert slow.n_migrants_total == fast.n_migrants_total
    assert slow.arrivals.shape[0] > fast.arrivals.shape[0]


def test_source_count_changes_composition_but_not_the_migrant_total():
    """The central contrast: same M, different K."""
    one = _plan(shares=np.array([1.0]))
    ten = _plan(shares=np.full(10, 0.1))
    assert one.n_migrants_total == ten.n_migrants_total
    assert one.counts_by_source.size == 1 and ten.counts_by_source.size == 10


def test_unimplemented_arrival_profiles_raise_rather_than_approximate():
    with raises(NotImplementedError, "not implemented"):
        _plan(profile="front_loaded")


def test_unknown_arrival_profile_raises():
    with raises(ValueError, "unknown arrival profile"):
        _plan(profile="sinusoidal")


def test_zero_duration_is_rejected():
    with raises(ValueError, "duration"):
        _plan(duration_years=0.0)


# -- source composition ----------------------------------------------------

def test_source_shares_always_sum_to_one():
    g = np.random.default_rng(0)
    for k in (1, 2, 5, 16):
        for dist, kw in (
            ("even", {}),
            ("geometric", {"decay": 0.6}),
            ("dirichlet", {"concentration": 2.0}),
        ):
            p = source_shares(k, dist, g, **kw)
            assert approx(float(p.sum()), 1.0, tol=1e-12), (k, dist)
            assert p.size == k


def test_even_shares_are_maximally_even():
    assert approx(evenness(source_shares(5, "even")), 1.0)


def test_geometric_shares_are_less_even_as_decay_falls():
    a = evenness(source_shares(5, "geometric", decay=0.9))
    b = evenness(source_shares(5, "geometric", decay=0.3))
    assert a > b


def test_evenness_can_be_targeted_exactly_at_fixed_K():
    """RQ3 requires H to be an independent variable, not a by-product of K."""
    for k in (3, 5, 10):
        for target in (0.5, 0.7, 0.95):
            shares = shares_for_target_evenness(k, target)
            assert approx(evenness(shares), target, tol=1e-6), (k, target)
            assert approx(float(shares.sum()), 1.0, tol=1e-12)


def test_single_source_is_even_by_convention():
    assert evenness(np.array([1.0])) == 1.0


def test_dirichlet_shares_require_an_explicit_generator():
    with raises(ValueError, "explicit rng"):
        source_shares(3, "dirichlet")


def test_explicit_shares_must_match_the_source_count():
    with raises(ValueError, "exactly K"):
        source_shares(3, "explicit", explicit=[0.5, 0.5])


# -- source cultures -------------------------------------------------------

def _sources(k=4, d=0.5, arrangement="independent", seed=0):
    return generate_source_set(
        SCHEMA,
        RESIDENT,
        np.full(k, 1.0 / k),
        np.full(k, d),
        np.random.default_rng(seed),
        arrangement=arrangement,
    )


def test_realised_distance_matches_the_target_within_schema_resolution():
    """Only multiples of 1/F are achievable; the realised value is measured, not
    assumed."""
    s = _sources(k=4, d=0.5)
    assert bool((np.abs(s.realised_distance_to_resident - 0.5) <= 1 / SCHEMA.n_features).all())


def test_zero_distance_reproduces_the_resident_culture_exactly():
    s = _sources(k=2, d=0.0)
    assert float(s.realised_distance_to_resident.max()) == 0.0


def test_maximal_distance_differs_on_every_feature():
    s = _sources(k=2, d=1.0)
    assert float(s.realised_distance_to_resident.min()) == 1.0


def test_the_pairwise_matrix_is_symmetric_with_a_zero_diagonal():
    s = _sources(k=5)
    assert np.allclose(s.realised_pairwise, s.realised_pairwise.T)
    assert float(np.abs(np.diag(s.realised_pairwise)).max()) == 0.0


def test_arrangement_controls_distance_BETWEEN_sources_at_fixed_distance_from_residents():
    """Hypotheses H2-H4 turn on this: two source cultures equally far from the
    resident culture can be near-identical to each other or maximally far."""
    nested = _sources(k=3, d=0.3, arrangement="nested")
    disjoint = _sources(k=3, d=0.3, arrangement="disjoint")
    assert disjoint.mean_inter_source_distance > nested.mean_inter_source_distance
    for s in (nested, disjoint):
        assert bool(
            (np.abs(s.realised_distance_to_resident - 0.3) <= 1 / SCHEMA.n_features).all()
        )


def test_source_labels_never_reuse_the_resident_letter():
    s = _sources(k=3)
    assert s.labels[0] == "Culture B"
    assert "Culture A" not in s.labels


def test_distance_presets_resolve_and_unknown_ones_raise():
    assert resolve_distance("near") == 0.25
    assert resolve_distance(0.42) == 0.42
    with raises(KeyError, "unknown cultural-distance preset"):
        resolve_distance("quite far")
    with raises(ValueError, "0, 1"):
        resolve_distance(1.5)
