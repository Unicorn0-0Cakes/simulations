"""The conformist rule: frequency dependence, its regimes, and its invariants.

The parameterisation is the point. ``conformity`` spans anti-conformity (< 1),
neutral unbiased transmission (= 1) and conformity (> 1) continuously, so the
neutral case is a value rather than a separate rule. These tests pin each regime
to a behaviour that distinguishes it from the others.
"""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.agents.population import Population, initialise_resident_population
from culture_flux.culture.features import CultureSchema, FeatureSpec
from culture_flux.dynamics.base import get_transmission_rule
from culture_flux.dynamics.conformist import ConformistTransmission
from culture_flux.experiment.config import ConfigError, ExperimentConfig
from culture_flux.experiment.run import ExperimentRun
from culture_flux.influence.base import UniformInfluence
from culture_flux.networks import MultiplexNetwork, WellMixedLayer
from culture_flux.rng import RunRNG


def _pop_from(culture: np.ndarray, schema: CultureSchema) -> Population:
    n = culture.shape[0]
    return Population(
        schema=schema,
        agent_id=np.arange(n, dtype=np.int64),
        source_id=np.zeros(n, dtype=np.int16),
        arrival_step=np.full(n, -1, dtype=np.int32),
        migration_generation=np.zeros(n, dtype=np.int8),
        culture=culture.astype(np.int16),
    )


def _drive(pop, rule, events=100, seed=0, influence=None):
    net = MultiplexNetwork()
    net.add_layer(WellMixedLayer(pop.size))
    rng = np.random.default_rng(seed)
    infl = influence or UniformInfluence()
    return sum(rule.step(pop, net, infl, s, rng) for s in range(events))


def cfg(**overrides) -> ExperimentConfig:
    base = {
        "name": "c",
        "seed": 1,
        "schema_version": 3,
        "population": {"initial_size": 300},
        "culture": {"features": 8, "traits_per_feature": 4},
        "migration": {
            "total_share": 0.3,
            "source_count": 2,
            "source_distribution": "even",
            "cultural_distance": 0.5,
            "duration_years": 5.0,
        },
        "dynamics": {"transmission_rule": "conformist", "rule_params": {}},
        "runtime": {"total_years": 20.0, "steps_per_year": 12},
        "output": {"write_final_population": False},
    }
    for key, value in overrides.items():
        if "." in key:
            section, field = key.split(".", 1)
            base.setdefault(section, {})[field] = value
        else:
            base[key] = value
    return ExperimentConfig.from_dict(base)


def _majority_share(seed_frac: float, conformity: float, *, n=2000, steps=40, seed=0) -> float:
    """Start a population with a given majority on one binary feature and report
    the majority share after some steps."""
    schema = CultureSchema.uniform(1, 2)
    rng = np.random.default_rng(seed)
    culture = (rng.random((n, 1)) < seed_frac).astype(np.int16)
    pop = _pop_from(culture, schema)
    rule = ConformistTransmission(conformity=conformity, n_models=9)
    _drive(pop, rule, events=steps, seed=seed + 1)
    return float((pop.culture[:, 0] == 1).mean())


# -- the regimes -----------------------------------------------------------

def test_conformity_above_one_amplifies_an_existing_majority():
    """The defining behaviour: the majority grows beyond its own frequency."""
    start = 0.65
    end = _majority_share(start, conformity=5.0)
    assert end > start + 0.1, end


def test_anti_conformity_below_one_erodes_a_majority():
    start = 0.80
    end = _majority_share(start, conformity=0.2)
    assert end < start - 0.05, end


def test_neutral_transmission_leaves_the_expected_frequency_unchanged():
    """conformity = 1 is unbiased transmission -- copy in proportion to
    frequency. It drifts stochastically but has no systematic direction, so it
    must not show the strong pull of the conformist case."""
    start = 0.65
    ends = [_majority_share(start, conformity=1.0, seed=s) for s in range(6)]
    mean = float(np.mean(ends))
    assert abs(mean - start) < 0.06, ends
    conformist = float(np.mean([_majority_share(start, conformity=5.0, seed=s) for s in range(6)]))
    assert conformist > mean + 0.08


def test_the_regime_label_matches_the_parameter():
    assert "conformist" == ConformistTransmission(conformity=3.0).describe()["regime"]
    assert "anti-conformist" == ConformistTransmission(conformity=0.4).describe()["regime"]
    assert "neutral" in ConformistTransmission(conformity=1.0).describe()["regime"]


# -- invariants ------------------------------------------------------------

def test_an_agent_can_never_adopt_a_trait_nobody_it_observed_was_carrying():
    """`0 ** 0` is 1 in NumPy, which at conformity = 0 would otherwise let an
    agent adopt an unobserved trait out of nowhere."""
    schema = CultureSchema.uniform(4, 6)
    culture = np.zeros((500, 4), dtype=np.int16)
    culture[:, 0] = 3  # only trait 3 is present on feature 0
    pop = _pop_from(culture, schema)
    _drive(pop, ConformistTransmission(conformity=0.0, n_models=5), events=60)
    assert set(np.unique(pop.culture[:, 0]).tolist()) == {3}


def test_copying_without_drift_never_introduces_a_new_trait():
    schema = CultureSchema.uniform(5, 5)
    pop = initialise_resident_population(400, schema, RunRNG(1), within_noise=0.5)
    before = [set(np.unique(pop.culture[:, j]).tolist()) for j in range(5)]
    _drive(pop, ConformistTransmission(conformity=2.0), events=200)
    after = [set(np.unique(pop.culture[:, j]).tolist()) for j in range(5)]
    for b, a in zip(before, after):
        assert a <= b


def test_a_homogeneous_population_is_an_absorbing_state():
    schema = CultureSchema.uniform(5, 4)
    pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.0)
    assert _drive(pop, ConformistTransmission(conformity=3.0)) == 0


def test_there_is_no_similarity_gate_unlike_the_homophily_rule():
    """The substantive difference between the two families: agents with nothing
    in common still influence each other, so cultural distance is not
    self-reinforcing and the frozen-apart states do not arise the same way."""
    schema = CultureSchema.uniform(4, 4)
    culture = np.vstack([np.zeros((100, 4)), np.ones((100, 4))]).astype(np.int16)
    pop = _pop_from(culture, schema)
    assert _drive(pop, ConformistTransmission(conformity=2.0), events=60) > 0


def test_population_size_and_trait_admissibility_are_preserved():
    schema = CultureSchema.uniform(6, 5)
    pop = initialise_resident_population(300, schema, RunRNG(1), within_noise=0.5)
    _drive(pop, ConformistTransmission(conformity=2.0), events=100)
    assert pop.size == 300
    pop.validate()


def test_a_fully_resistant_feature_never_changes():
    schema = CultureSchema(
        (
            FeatureSpec("sacred", n_traits=4, resistance=1.0),
            FeatureSpec("open", n_traits=4),
            FeatureSpec("open2", n_traits=4),
        )
    )
    pop = initialise_resident_population(300, schema, RunRNG(1), within_noise=0.5)
    before = pop.culture[:, 0].copy()
    assert _drive(pop, ConformistTransmission(conformity=2.0), events=200) > 0
    assert np.array_equal(pop.culture[:, 0], before)


def test_a_feature_with_zero_transmission_rate_never_changes():
    schema = CultureSchema(
        (
            FeatureSpec("locked", n_traits=4, transmission_rate=0.0),
            FeatureSpec("open", n_traits=4),
        )
    )
    pop = initialise_resident_population(300, schema, RunRNG(1), within_noise=0.5)
    before = pop.culture[:, 0].copy()
    _drive(pop, ConformistTransmission(conformity=2.0), events=200)
    assert np.array_equal(pop.culture[:, 0], before)


def test_drift_composes_with_the_conformist_rule_too():
    schema = CultureSchema.uniform(5, 4)
    pop = initialise_resident_population(300, schema, RunRNG(1), within_noise=0.0)
    rule = ConformistTransmission(conformity=2.0, drift_rate=0.05)
    assert _drive(pop, rule, events=40) > 0
    assert int(np.unique(pop.culture).size) > 1


def test_influence_weighting_biases_which_traits_are_counted():
    class Skewed(UniformInfluence):
        name = "skewed-test-only"

        def weights(self, population, step):
            w = np.ones(population.size)
            w[population.culture[:, 0] == 1] = 50.0
            return w

    schema = CultureSchema.uniform(1, 2)
    rng = np.random.default_rng(0)
    culture = (rng.random((1500, 1)) < 0.35).astype(np.int16)
    results = {}
    for label, infl in (("uniform", UniformInfluence()), ("skewed", Skewed())):
        pop = _pop_from(culture.copy(), schema)
        _drive(pop, ConformistTransmission(conformity=1.0, n_models=9), events=30, influence=infl)
        results[label] = float((pop.culture[:, 0] == 1).mean())
    assert results["skewed"] > results["uniform"] + 0.1


def test_the_rule_is_deterministic_under_a_fixed_generator():
    schema = CultureSchema.uniform(6, 4)
    outs = []
    for _ in range(2):
        pop = initialise_resident_population(300, schema, RunRNG(1), within_noise=0.5)
        _drive(pop, ConformistTransmission(conformity=2.0), seed=7)
        outs.append(pop.culture.copy())
    assert np.array_equal(outs[0], outs[1])


# -- parameter validation --------------------------------------------------

def test_impossible_parameters_are_rejected():
    with raises(ValueError, "conformity"):
        ConformistTransmission(conformity=-1.0)
    with raises(ValueError, "n_models"):
        ConformistTransmission(n_models=0)
    with raises(ValueError, "drift_rate"):
        ConformistTransmission(drift_rate=2.0)


def test_unknown_parameters_are_rejected_not_ignored():
    with raises(ValueError, "rejected its parameters"):
        get_transmission_rule("conformist", {"conformty": 2.0})


def test_bad_parameters_fail_at_configuration_time():
    with raises(ConfigError, "invalid"):
        cfg(**{"dynamics.rule_params": {"conformist": {"conformity": -3}}})


# -- end to end ------------------------------------------------------------

def test_the_conformist_rule_runs_and_departs_from_the_null():
    active = ExperimentRun(cfg(), seed=1).execute()
    null = ExperimentRun(
        cfg(**{"dynamics.transmission_rule": "null", "dynamics.rule_params": {}}), seed=1
    ).execute()
    assert active.manifest["dynamics"]["trait_changes_total"] > 0
    assert active.final_metrics["founder_subpopulation_retention"] < 1.0
    assert null.final_metrics["founder_subpopulation_retention"] == 1.0


def test_both_rules_share_the_same_resident_baseline_at_a_given_seed():
    """The controlled contrast must survive a change of transmission rule: the
    two arms have to start from the same city."""
    a = ExperimentRun(cfg(), seed=1).execute()
    b = ExperimentRun(
        cfg(**{"dynamics.transmission_rule": "axelrod_homophily", "dynamics.rule_params": {}}),
        seed=1,
    ).execute()
    assert a.config.baseline_key == b.config.baseline_key
    assert np.array_equal(a.source_set.profiles, b.source_set.profiles)
    assert a.plan.n_migrants_total == b.plan.n_migrants_total


def test_the_two_rules_produce_different_outcomes():
    """If they agreed exactly, one of them would not be a second family."""
    a = ExperimentRun(cfg(), seed=1).execute()
    b = ExperimentRun(
        cfg(**{"dynamics.transmission_rule": "axelrod_homophily", "dynamics.rule_params": {}}),
        seed=1,
    ).execute()
    assert a.run_hash != b.run_hash
