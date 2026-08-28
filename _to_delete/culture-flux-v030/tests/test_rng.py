"""Seeded randomness: the foundation every reproducibility claim rests on."""

from __future__ import annotations

import numpy as np
from _harness import raises

from culture_flux.rng import BASELINE_STREAMS, CONDITION_STREAMS, RunRNG, key_to_int


def test_same_seed_and_keys_give_identical_draws():
    a = RunRNG(7, "base", "cond")
    b = RunRNG(7, "base", "cond")
    for name in BASELINE_STREAMS + CONDITION_STREAMS:
        assert np.array_equal(a(name).random(50), b(name).random(50)), name


def test_baseline_streams_ignore_the_condition_key():
    """The controlled contrast depends on this: same seed, different migration
    settings, byte-identical resident population."""
    a = RunRNG(7, "base", "condition-one")
    b = RunRNG(7, "base", "condition-two")
    for name in BASELINE_STREAMS:
        assert np.array_equal(a(name).random(50), b(name).random(50)), name


def test_condition_streams_diverge_across_conditions():
    a = RunRNG(7, "base", "condition-one")
    b = RunRNG(7, "base", "condition-two")
    for name in CONDITION_STREAMS:
        assert not np.array_equal(a(name).random(50), b(name).random(50)), name


def test_different_seeds_diverge_everywhere():
    a, b = RunRNG(1, "base", "cond"), RunRNG(2, "base", "cond")
    for name in BASELINE_STREAMS + CONDITION_STREAMS:
        assert not np.array_equal(a(name).random(50), b(name).random(50)), name


def test_streams_are_independent_of_one_another():
    """Consuming one stream must not shift another: adding a mechanism later
    must not change the draws an existing mechanism sees."""
    a = RunRNG(3, "base", "cond")
    a("misc").random(1000)
    first = a("resident_init").random(20)
    b = RunRNG(3, "base", "cond")
    second = b("resident_init").random(20)
    assert np.array_equal(first, second)


def test_undeclared_stream_raises():
    r = RunRNG(1)
    with raises(KeyError, "undeclared"):
        r("not_a_stream")


def test_negative_seed_rejected():
    with raises(ValueError, "non-negative"):
        RunRNG(-1)


def test_key_hashing_is_stable_across_processes():
    """`hash()` is salted per process; a stored run must replay in a new one."""
    assert key_to_int("abc") == key_to_int("abc")
    assert key_to_int("abc") != key_to_int("abd")
    assert key_to_int("") == 16476032584258269876  # pinned: changing it breaks replay


def test_state_roundtrip_restores_the_stream_position():
    r = RunRNG(11, "b", "c")
    r("misc").random(10)
    state = r.get_state()
    expected = r("misc").random(5)
    restored = RunRNG(11, "b", "c")
    restored.set_state(state)
    assert np.array_equal(restored("misc").random(5), expected)


def test_state_with_wrong_layout_version_refuses_to_load():
    r = RunRNG(1)
    state = r.get_state()
    state["layout_version"] = 999
    with raises(ValueError, "layout version"):
        r.set_state(state)
