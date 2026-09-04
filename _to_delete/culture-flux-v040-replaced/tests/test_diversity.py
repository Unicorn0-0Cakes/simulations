"""Diversity indices: known closed forms, bounds, and invariances."""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.metrics import diversity as div


def test_fractionalization_of_a_single_category_is_zero():
    assert div.fractionalization(np.array([1.0])) == 0.0


def test_fractionalization_of_k_even_categories_is_one_minus_one_over_k():
    for k in (2, 3, 5, 10, 100):
        assert approx(div.fractionalization(np.full(k, 1.0 / k)), 1.0 - 1.0 / k)


def test_fractionalization_is_bounded_below_one():
    """The index cannot reach 1: it is capped by the number of categories, which
    is why it must never be read as 'amount of diversity' on its own."""
    for k in (2, 10, 1000):
        assert div.fractionalization(np.full(k, 1.0 / k)) < 1.0


def test_fractionalization_is_invariant_to_relabelling_and_ordering():
    p = np.array([0.5, 0.3, 0.2])
    assert approx(div.fractionalization(p), div.fractionalization(p[::-1]))


def test_fractionalization_and_simpson_are_complements():
    p = np.array([0.4, 0.35, 0.25])
    assert approx(div.fractionalization(p) + div.simpson(p), 1.0)
    assert approx(div.hhi(p), div.simpson(p))


def test_entropy_is_zero_for_one_category_and_log_k_for_k_even():
    assert div.shannon_entropy(np.array([1.0])) == 0.0
    for k in (2, 7, 50):
        assert approx(div.shannon_entropy(np.full(k, 1.0 / k)), float(np.log(k)))


def test_entropy_is_maximised_by_the_even_distribution():
    even = div.shannon_entropy(np.array([0.25, 0.25, 0.25, 0.25]))
    skewed = div.shannon_entropy(np.array([0.7, 0.1, 0.1, 0.1]))
    assert even > skewed


def test_pielou_evenness_is_one_for_even_shares_regardless_of_k():
    for k in (2, 4, 16):
        assert approx(div.pielou_evenness(np.full(k, 1.0 / k)), 1.0)


def test_evenness_separates_H_from_K():
    """The point of reporting both: two distributions with the same K can differ
    in evenness, and two with the same evenness can differ in K."""
    a = div.pielou_evenness(np.array([0.25, 0.25, 0.25, 0.25]))
    b = div.pielou_evenness(np.array([0.9, 0.05, 0.03, 0.02]))
    assert a > b
    assert approx(div.pielou_evenness(np.full(4, 0.25)), div.pielou_evenness(np.full(9, 1 / 9)))


def test_hill_numbers_recover_the_familiar_indices():
    p = np.array([0.5, 0.3, 0.2])
    assert approx(div.hill_number(p, 0.0), div.richness(p))
    assert approx(div.hill_number(p, 1.0), float(np.exp(div.shannon_entropy(p))))
    assert approx(div.hill_number(p, 2.0), 1.0 / div.simpson(p))
    assert approx(div.effective_number(p), div.hill_number(p, 2.0))


def test_hill_numbers_of_k_even_categories_equal_k_at_every_order():
    for k in (2, 5, 20):
        p = np.full(k, 1.0 / k)
        for q in (0.0, 0.5, 1.0, 2.0, 3.0):
            assert approx(div.hill_number(p, q), float(k), tol=1e-8)


def test_hill_numbers_are_non_increasing_in_q():
    p = np.array([0.6, 0.2, 0.15, 0.05])
    values = [div.hill_number(p, q) for q in (0.0, 0.5, 1.0, 2.0, 4.0)]
    assert all(a >= b - 1e-9 for a, b in zip(values, values[1:]))


def test_unnormalised_input_is_normalised_not_rejected():
    assert approx(div.fractionalization(np.array([2.0, 2.0])), 0.5)


def test_negative_and_empty_shares_are_rejected():
    with raises(ValueError, "non-negative"):
        div.fractionalization(np.array([0.5, -0.5, 1.0]))
    with raises(ValueError, "sum to zero"):
        div.fractionalization(np.array([0.0, 0.0]))


def test_shares_from_labels_counts_categories_correctly():
    labels = np.array([0, 0, 0, 1, 2, 2])
    p = div.shares_from_labels(labels)
    assert approx(float(p.sum()), 1.0)
    assert approx(div.max_share(p), 0.5)
    assert div.richness(p) == 3.0


def test_max_share_is_dominance_not_diversity():
    """A high-diversity index and a high dominance share can coexist; both are
    reported so that neither stands in for the other."""
    p = np.array([0.5] + [0.5 / 20] * 20)
    assert div.max_share(p) == 0.5
    assert div.fractionalization(p) > 0.7
