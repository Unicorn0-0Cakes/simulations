"""Population initialisation and mutation invariants."""

from __future__ import annotations

import numpy as np
from _harness import raises

from culture_flux.agents.attributes import ATTRIBUTES, implemented_attributes, unimplemented_attributes
from culture_flux.agents.population import (
    RESIDENT_SOURCE_ID,
    draw_profiles,
    initialise_resident_population,
)
from culture_flux.culture.features import CultureSchema
from culture_flux.rng import RunRNG

SCHEMA = CultureSchema.uniform(10, 5)


def _pop(n=500, noise=0.0, seed=1, baseline="b", condition="c"):
    return initialise_resident_population(
        n, SCHEMA, RunRNG(seed, baseline, condition), within_noise=noise
    )


def test_identical_seed_and_baseline_give_identical_initial_populations():
    a, b = _pop(seed=4), _pop(seed=4)
    assert np.array_equal(a.culture, b.culture)
    assert np.array_equal(a.source_id, b.source_id)


def test_initial_population_ignores_the_condition_key():
    """Same city, different experiment: the controlled contrast requires it."""
    a = _pop(noise=0.3, seed=4, condition="M=0.3,K=1")
    b = _pop(noise=0.3, seed=4, condition="M=0.3,K=10")
    assert np.array_equal(a.culture, b.culture)


def test_different_seeds_give_different_populations_when_there_is_variation():
    a, b = _pop(noise=0.3, seed=4), _pop(noise=0.3, seed=5)
    assert not np.array_equal(a.culture, b.culture)


def test_zero_noise_gives_a_perfectly_homogeneous_city():
    p = _pop(noise=0.0)
    assert len(np.unique(p.culture, axis=0)) == 1


def test_noise_introduces_variation_at_roughly_the_requested_rate():
    p = _pop(n=20000, noise=0.2)
    departure_rate = float((p.culture != 0).mean())
    assert 0.18 < departure_rate < 0.22


def test_draw_profiles_never_produces_an_illegal_trait():
    g = np.random.default_rng(0)
    modal = np.zeros(SCHEMA.n_features, dtype=np.int16)
    out = draw_profiles(modal, 5000, SCHEMA, 0.5, g)
    assert int(out.min()) >= 0
    assert bool((out < SCHEMA.n_traits[None, :]).all())


def test_noise_always_changes_the_trait_when_it_fires():
    """A 'redraw' that can return the original trait would silently halve the
    effective noise rate."""
    g = np.random.default_rng(0)
    modal = np.zeros(SCHEMA.n_features, dtype=np.int16)
    out = draw_profiles(modal, 50000, SCHEMA, 1.0, g)
    assert int((out == 0).sum()) == 0


def test_population_size_cannot_be_zero_or_negative():
    with raises(ValueError, "at least one agent"):
        initialise_resident_population(0, SCHEMA, RunRNG(1))


def test_adding_agents_grows_the_population_and_keeps_ids_unique():
    p = _pop(100)
    before = p.size
    culture = np.zeros((25, SCHEMA.n_features), dtype=np.int16)
    ids = p.add_agents(culture, source_id=1, arrival_step=3)
    assert p.size == before + 25
    assert len(np.unique(p.agent_id)) == p.size
    assert not set(ids.tolist()) & set(range(before))


def test_adding_agents_with_the_wrong_width_is_rejected():
    p = _pop(10)
    with raises(ValueError, "shape"):
        p.add_agents(np.zeros((5, 3), dtype=np.int16), source_id=1, arrival_step=0)


def test_removing_agents_shrinks_every_array_together():
    p = _pop(100)
    removed = p.remove_agents(np.arange(10))
    assert removed == 10 and p.size == 90
    assert p.culture.shape[0] == 90 == p.source_id.shape[0] == p.arrival_step.shape[0]


def test_removal_out_of_range_is_rejected():
    p = _pop(10)
    with raises(IndexError, "out of range"):
        p.remove_agents(np.array([99]))


def test_provenance_and_culture_are_separate_arrays():
    """Culture must be able to change without provenance changing, and vice
    versa. If they were the same object, 'culture is not ancestry' would be a
    comment rather than a property of the code."""
    p = _pop(50)
    p.culture[0, 0] = 3
    assert p.source_id[0] == RESIDENT_SOURCE_ID
    assert p.culture is not p.source_id


def test_founders_are_marked_as_generation_zero_with_no_arrival_step():
    p = _pop(20)
    assert bool((p.migration_generation == 0).all())
    assert bool((p.arrival_step == -1).all())


def test_source_shares_sum_to_one():
    p = _pop(100)
    p.add_agents(np.zeros((50, SCHEMA.n_features), dtype=np.int16), 1, 0)
    assert abs(sum(p.source_shares().values()) - 1.0) < 1e-12


def test_the_implemented_agent_is_smaller_than_the_declared_agent():
    """A guard against the gap between the agent the paper describes and the
    agent the code allocates closing -- or widening -- unnoticed."""
    assert len(implemented_attributes()) == 5
    assert len(unimplemented_attributes()) == 14
    assert len(ATTRIBUTES) == 19
