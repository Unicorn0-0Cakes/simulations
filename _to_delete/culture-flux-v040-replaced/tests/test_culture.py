"""Culture representation and the distance metric's mathematical properties."""

from __future__ import annotations

import numpy as np
from _harness import raises

from culture_flux.culture.distance import (
    available_distances,
    distance_to_profile,
    get_distance,
    hamming,
    mean_pairwise_distance,
    weighted_hamming,
)
from culture_flux.culture.features import CultureSchema, FeatureSpec
from culture_flux.culture.profile import (
    CulturalProfile,
    profile_keys,
    validate_culture_matrix,
)

SCHEMA = CultureSchema.uniform(10, 5)


def _rand(n, schema, seed=0):
    g = np.random.default_rng(seed)
    return np.stack(
        [g.integers(0, schema.n_traits[j], size=n) for j in range(schema.n_features)], axis=1
    ).astype(np.int16)


# -- schema ---------------------------------------------------------------

def test_single_trait_feature_rejected():
    """A feature with one trait cannot vary, so it cannot carry culture."""
    with raises(ValueError, "n_traits"):
        FeatureSpec("f", n_traits=1)


def test_unimplemented_feature_kinds_raise_rather_than_being_coerced():
    for kind in ("continuous", "ordinal"):
        with raises(NotImplementedError, "not implemented"):
            FeatureSpec("f", kind=kind)


def test_duplicate_feature_names_rejected():
    with raises(ValueError, "duplicate"):
        CultureSchema((FeatureSpec("a"), FeatureSpec("a")))


def test_state_space_size_is_traits_to_the_power_of_features():
    assert CultureSchema.uniform(4, 3).max_distinct_profiles() == 81


def test_uniform_schema_reports_itself_uniform():
    assert SCHEMA.is_uniform
    mixed = CultureSchema((FeatureSpec("a", salience=1.0), FeatureSpec("b", salience=2.0)))
    assert not mixed.is_uniform


# -- distance axioms ------------------------------------------------------

def test_identical_profiles_have_distance_zero():
    x = _rand(200, SCHEMA)
    assert float(hamming(x, x, SCHEMA).max()) == 0.0
    assert float(weighted_hamming(x, x, SCHEMA).max()) == 0.0


def test_distance_is_symmetric():
    a, b = _rand(200, SCHEMA, 1), _rand(200, SCHEMA, 2)
    assert np.allclose(hamming(a, b, SCHEMA), hamming(b, a, SCHEMA))


def test_distance_is_bounded_in_unit_interval():
    a, b = _rand(500, SCHEMA, 3), _rand(500, SCHEMA, 4)
    d = hamming(a, b, SCHEMA)
    assert float(d.min()) >= 0.0 and float(d.max()) <= 1.0


def test_maximally_different_profiles_have_distance_one():
    a = np.zeros((1, SCHEMA.n_features), dtype=np.int16)
    b = np.ones((1, SCHEMA.n_features), dtype=np.int16)
    assert float(hamming(a, b, SCHEMA)[0]) == 1.0


def test_triangle_inequality_holds():
    a, b, c = _rand(400, SCHEMA, 5), _rand(400, SCHEMA, 6), _rand(400, SCHEMA, 7)
    ab = hamming(a, b, SCHEMA)
    bc = hamming(b, c, SCHEMA)
    ac = hamming(a, c, SCHEMA)
    assert bool((ac <= ab + bc + 1e-12).all())


def test_distance_counts_features_not_trait_magnitudes():
    """Categorical traits are unordered: 0-vs-1 and 0-vs-4 differ equally."""
    base = np.zeros((1, SCHEMA.n_features), dtype=np.int16)
    near = base.copy(); near[0, 0] = 1
    far = base.copy(); far[0, 0] = 4
    assert float(hamming(base, near, SCHEMA)[0]) == float(hamming(base, far, SCHEMA)[0])


def test_weighted_hamming_reduces_to_hamming_under_equal_salience():
    a, b = _rand(100, SCHEMA, 8), _rand(100, SCHEMA, 9)
    assert np.allclose(hamming(a, b, SCHEMA), weighted_hamming(a, b, SCHEMA))


def test_salience_weighting_actually_changes_the_answer():
    schema = CultureSchema((FeatureSpec("a", salience=9.0), FeatureSpec("b", salience=1.0)))
    a = np.array([[0, 0]], dtype=np.int16)
    b = np.array([[1, 0]], dtype=np.int16)  # differs on the heavy feature only
    assert abs(float(weighted_hamming(a, b, schema)[0]) - 0.9) < 1e-12
    assert abs(float(hamming(a, b, schema)[0]) - 0.5) < 1e-12


def test_unknown_metric_name_raises_with_the_registry_listed():
    with raises(KeyError, "unknown cultural distance metric"):
        get_distance("euclidean-ish")


def test_every_registered_metric_returns_zero_on_identity():
    x = _rand(50, SCHEMA, 10)
    for name in available_distances():
        assert float(get_distance(name)(x, x, SCHEMA).max()) == 0.0, name


def test_mean_pairwise_distance_refuses_to_sample_without_a_generator():
    big = _rand(1200, SCHEMA, 11)  # 719,400 pairs > the 200k exact limit
    with raises(ValueError, "explicit rng"):
        mean_pairwise_distance(big, SCHEMA)


def test_mean_pairwise_sampling_approximates_the_exact_value():
    x = _rand(400, SCHEMA, 12)
    exact = mean_pairwise_distance(x, SCHEMA)
    sampled = mean_pairwise_distance(
        x, SCHEMA, max_pairs=100, sample_pairs=5000, rng=np.random.default_rng(0)
    )
    assert abs(exact - sampled) < 0.02


# -- profiles and matrices -------------------------------------------------

def test_profile_rejects_traits_outside_the_schema():
    p = CulturalProfile("bad", tuple([9] * SCHEMA.n_features))
    with raises(ValueError, "outside admissible range"):
        p.validate_against(SCHEMA)


def test_profile_rejects_wrong_width():
    with raises(ValueError, "features"):
        CulturalProfile("short", (0, 1)).validate_against(SCHEMA)


def test_culture_matrix_validation_catches_unset_and_overflow():
    m = np.full((3, SCHEMA.n_features), -1, dtype=np.int16)
    with raises(ValueError, "unset"):
        validate_culture_matrix(m, SCHEMA)
    m2 = np.zeros((3, SCHEMA.n_features), dtype=np.int16)
    m2[0, 0] = 99
    with raises(ValueError, "n_traits"):
        validate_culture_matrix(m2, SCHEMA)


def test_profile_keys_group_identical_rows_and_separate_different_ones():
    m = np.array([[0, 0], [0, 0], [0, 1]], dtype=np.int16)
    keys = profile_keys(m)
    assert keys[0] == keys[1] and keys[0] != keys[2]
    assert len(np.unique(keys)) == 2


def test_distance_to_profile_matches_row_by_row_computation():
    m = _rand(100, SCHEMA, 13)
    target = m[0]
    d = distance_to_profile(m, target, SCHEMA)
    assert float(d[0]) == 0.0
    manual = (m != target[None, :]).sum(axis=1) / SCHEMA.n_features
    assert np.allclose(d, manual)


def test_fast_and_general_profile_grouping_agree():
    """The mixed-radix encoding is an optimisation, not a different definition."""
    from culture_flux.culture.profile import encode_profiles

    m = _rand(2000, SCHEMA, 21)
    fast = profile_keys(m, SCHEMA)
    general = profile_keys(m)
    # Group indices may be numbered differently; the PARTITION must be identical.
    assert len(np.unique(fast)) == len(np.unique(general))
    for k in np.unique(fast):
        rows = np.flatnonzero(fast == k)
        assert len(np.unique(general[rows])) == 1
    assert encode_profiles(m, SCHEMA) is not None


def test_encoding_declines_rather_than_overflowing_on_a_huge_state_space():
    """A wrong answer on overflow would be far worse than being slow."""
    from culture_flux.culture.profile import encode_profiles

    huge = CultureSchema.uniform(200, 10)  # 10**200 profiles
    m = np.zeros((3, 200), dtype=np.int16)
    assert encode_profiles(m, huge) is None
    assert profile_keys(m, huge).tolist() == [0, 0, 0]
