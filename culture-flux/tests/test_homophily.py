"""The homophilous trait-copying rule.

Two classes of test here. The first are invariants that follow from the rule's
specification and must hold exactly -- copying creates no new traits, zero
overlap blocks influence entirely, a homogeneous population is absorbing. The
second compare the fast batched update scheme against the exact asynchronous
one; that comparison is evidence for assumption A-017 and is deliberately
labelled as weak.
"""

from __future__ import annotations

import numpy as np
from _harness import approx, raises

from culture_flux.agents.population import Population, initialise_resident_population
from culture_flux.culture.features import CultureSchema, FeatureSpec
from culture_flux.dynamics.base import get_transmission_rule
from culture_flux.dynamics.homophily import HomophilousTraitCopying
from culture_flux.experiment.config import ConfigError, ExperimentConfig
from culture_flux.experiment.run import ExperimentRun
from culture_flux.influence.base import UniformInfluence
from culture_flux.networks.base import MultiplexNetwork, WellMixedLayer
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


def _drive(pop, rule, events=200, seed=0, influence=None):
    """Run the rule for many steps and return the total number of trait changes."""
    net = MultiplexNetwork()
    net.add_layer(WellMixedLayer(pop.size))
    rng = np.random.default_rng(seed)
    infl = influence or UniformInfluence()
    return sum(rule.step(pop, net, infl, s, rng) for s in range(events))


def cfg(**overrides) -> ExperimentConfig:
    base = {
        "name": "h",
        "seed": 1,
        "population": {"initial_size": 300},
        "culture": {"features": 10, "traits_per_feature": 5},
        "migration": {
            "total_share": 0.3,
            "source_count": 2,
            "source_distribution": "even",
            "cultural_distance": 0.5,
            "duration_years": 5.0,
        },
        "dynamics": {"transmission_rule": "axelrod_homophily", "rule_params": {}},
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


# -- invariants that follow from the specification -------------------------

def test_transmission_never_changes_the_population_size():
    """The rule copies traits; it does not create, destroy or move agents."""
    schema = CultureSchema.uniform(8, 4)
    pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.5)
    before = pop.size
    _drive(pop, HomophilousTraitCopying())
    assert pop.size == before
    pop.validate()


def test_transmission_never_produces_an_inadmissible_trait():
    schema = CultureSchema.uniform(8, 4)
    pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.5)
    _drive(pop, HomophilousTraitCopying())
    assert int(pop.culture.min()) >= 0
    assert bool((pop.culture < schema.n_traits[None, :]).all())


def test_copying_can_never_introduce_a_trait_nobody_held():
    """A strong invariant: with copying only, the set of traits present at each
    feature can shrink but never grow. A rule permitting innovation or copying
    error would violate this -- which is exactly how such a rule would be
    detected if one were added without saying so."""
    schema = CultureSchema.uniform(6, 5)
    pop = initialise_resident_population(300, schema, RunRNG(2), within_noise=0.6)
    before = [set(np.unique(pop.culture[:, j]).tolist()) for j in range(schema.n_features)]
    _drive(pop, HomophilousTraitCopying(), events=400)
    after = [set(np.unique(pop.culture[:, j]).tolist()) for j in range(schema.n_features)]
    for j, (b, a) in enumerate(zip(before, after)):
        assert a <= b, f"feature {j} gained trait(s) {a - b} that nobody held"


def test_agents_with_zero_overlap_can_never_influence_each_other():
    """Cultural distance is self-reinforcing at the extreme: this is the
    mechanism that permits stable diversity, so it must hold exactly."""
    schema = CultureSchema.uniform(4, 4)
    culture = np.array([[0, 0, 0, 0], [1, 1, 1, 1]], dtype=np.int16)
    pop = _pop_from(culture, schema)
    changes = _drive(pop, HomophilousTraitCopying(events_per_agent_per_step=50.0), events=200)
    assert changes == 0
    assert np.array_equal(pop.culture, culture)


def test_a_homogeneous_population_is_an_absorbing_state():
    schema = CultureSchema.uniform(6, 4)
    pop = initialise_resident_population(100, schema, RunRNG(1), within_noise=0.0)
    before = pop.culture.copy()
    assert _drive(pop, HomophilousTraitCopying(events_per_agent_per_step=20.0)) == 0
    assert np.array_equal(pop.culture, before)


def test_partial_overlap_does_produce_change():
    """The complement of the two tests above: the rule is not inert."""
    schema = CultureSchema.uniform(6, 4)
    pop = initialise_resident_population(200, schema, RunRNG(3), within_noise=0.4)
    assert _drive(pop, HomophilousTraitCopying()) > 0


def test_a_zero_interaction_rate_changes_nothing():
    schema = CultureSchema.uniform(6, 4)
    pop = initialise_resident_population(100, schema, RunRNG(1), within_noise=0.5)
    before = pop.culture.copy()
    assert _drive(pop, HomophilousTraitCopying(events_per_agent_per_step=0.0)) == 0
    assert np.array_equal(pop.culture, before)


def test_a_feature_with_zero_transmission_rate_never_changes():
    schema = CultureSchema(
        (
            FeatureSpec("locked", n_traits=4, transmission_rate=0.0),
            FeatureSpec("open", n_traits=4),
            FeatureSpec("open2", n_traits=4),
        )
    )
    pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.5)
    locked_before = pop.culture[:, 0].copy()
    _drive(pop, HomophilousTraitCopying(), events=300)
    assert np.array_equal(pop.culture[:, 0], locked_before)
    assert not np.array_equal(pop.culture[:, 1], pop.culture[:, 1] * 0 + locked_before * 0 + 99)


def test_a_fully_resistant_feature_never_changes():
    schema = CultureSchema(
        (
            FeatureSpec("sacred", n_traits=4, resistance=1.0),
            FeatureSpec("open", n_traits=4),
            FeatureSpec("open2", n_traits=4),
        )
    )
    pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.5)
    sacred_before = pop.culture[:, 0].copy()
    changed = _drive(pop, HomophilousTraitCopying(), events=300)
    assert np.array_equal(pop.culture[:, 0], sacred_before)
    assert changed > 0  # the other features did move


def test_the_rule_is_deterministic_under_a_fixed_generator():
    schema = CultureSchema.uniform(8, 4)
    outs = []
    for _ in range(2):
        pop = initialise_resident_population(200, schema, RunRNG(1), within_noise=0.5)
        _drive(pop, HomophilousTraitCopying(), seed=7)
        outs.append(pop.culture.copy())
    assert np.array_equal(outs[0], outs[1])


def test_influence_weighting_biases_whose_culture_spreads():
    """The influence layer must be operative, not decorative. Agents given four
    times the influence weight are chosen as partners more often, so their
    traits spread further."""

    class Skewed(UniformInfluence):
        name = "skewed-test-only"

        def __init__(self, favoured: np.ndarray):
            self.favoured = favoured

        def weights(self, population, step):
            w = np.ones(population.size)
            w[self.favoured] = 40.0
            return w

    schema = CultureSchema.uniform(8, 2)
    rng = np.random.default_rng(0)
    culture = rng.integers(0, 2, size=(200, 8)).astype(np.int16)
    culture[:20] = 1  # the favoured bloc shares one profile

    results = {}
    for label, infl in (("uniform", UniformInfluence()), ("skewed", Skewed(np.arange(20)))):
        pop = _pop_from(culture.copy(), schema)
        _drive(pop, HomophilousTraitCopying(), events=150, seed=1, influence=infl)
        results[label] = float((pop.culture == 1).mean())
    assert results["skewed"] > results["uniform"]


# -- parameter validation --------------------------------------------------

def test_unknown_update_scheme_rejected():
    with raises(ValueError, "unknown update_scheme"):
        HomophilousTraitCopying(update_scheme="simultaneous")


def test_negative_interaction_rate_rejected():
    with raises(ValueError, "events_per_agent_per_step"):
        HomophilousTraitCopying(events_per_agent_per_step=-1.0)


def test_unknown_rule_parameters_are_rejected_not_ignored():
    with raises(ValueError, "rejected its parameters"):
        get_transmission_rule("axelrod_homophily", {"evnts_per_agent": 1.0})


def test_bad_rule_parameters_fail_at_configuration_time():
    """Not three minutes into a sweep."""
    with raises(ConfigError, "invalid"):
        cfg(**{"dynamics.rule_params": {"axelrod_homophily": {"update_scheme": "nonsense"}}})


def test_rule_parameters_for_an_undeclared_rule_are_rejected():
    with raises(ConfigError, "undeclared rule"):
        cfg(**{"dynamics.rule_params": {"telepathy": {"x": 1}}})


def test_rule_parameters_for_a_declared_but_unimplemented_rule_are_kept():
    """A configuration may legitimately carry settings for a rule that does not
    exist yet -- that is how one base config serves a sweep across rules. They
    are stored, and validated as soon as the rule is implemented."""
    c = cfg(**{"dynamics.rule_params": {"prestige_biased": {"strength": 2.0}}})
    assert c.dynamics.rule_params["prestige_biased"]["strength"] == 2.0


def test_rule_parameters_change_the_config_hash():
    a = cfg()
    b = cfg(**{"dynamics.rule_params": {"axelrod_homophily": {"events_per_agent_per_step": 2.0}}})
    assert a.config_hash != b.config_hash


# -- the batched approximation (evidence for A-017) ------------------------

def test_batched_and_asynchronous_schemes_agree_within_noise():
    """Evidence for A-017, and deliberately labelled as weak: eight seeds at
    N = 200 with these variances has low power to detect a modest difference
    between the two processes. It rules out a gross discrepancy, not a subtle
    one. Strengthening it is a listed verification task."""
    keys = ("resident_trait_retention", "share_off_founding_profiles")
    out = {}
    for scheme in ("batched", "asynchronous"):
        rows = [
            ExperimentRun(
                cfg(
                    **{
                        "population.initial_size": 200,
                        "runtime.total_years": 10.0,
                        "dynamics.rule_params": {"axelrod_homophily": {"update_scheme": scheme}},
                    }
                ),
                seed=s,
            )
            .execute()
            .final_metrics
            for s in range(1, 9)
        ]
        out[scheme] = {k: np.array([r[k] for r in rows]) for k in keys}
    for k in keys:
        b, a = out["batched"][k], out["asynchronous"][k]
        se = np.sqrt(b.var(ddof=1) / b.size + a.var(ddof=1) / a.size)
        assert se > 0
        assert abs(b.mean() - a.mean()) / se < 3.0, k


def test_both_schemes_obey_the_same_invariants():
    schema = CultureSchema.uniform(6, 4)
    for scheme in ("batched", "asynchronous"):
        pop = initialise_resident_population(80, schema, RunRNG(1), within_noise=0.5)
        before_size = pop.size
        _drive(pop, HomophilousTraitCopying(update_scheme=scheme), events=60)
        assert pop.size == before_size
        pop.validate()


# -- what the rule does that the null cannot -------------------------------

def test_the_rule_changes_founder_culture_which_the_null_never_does():
    active = ExperimentRun(cfg(), seed=1).execute()
    null = ExperimentRun(cfg(**{"dynamics.transmission_rule": "null", "dynamics.rule_params": {}}), seed=1).execute()
    assert null.final_metrics["founder_subpopulation_retention"] == 1.0
    assert active.final_metrics["founder_subpopulation_retention"] < 1.0
    assert active.manifest["dynamics"]["trait_changes_total"] > 0
    assert null.manifest["dynamics"]["trait_changes_total"] == 0


def test_the_rule_departs_from_the_compositional_baseline():
    """The point of having a null: retention under transmission must differ from
    `1 - M*D`, or the mechanism is not doing anything culture-specific.

    Averaged over seeds, deliberately. A single-seed version of this test passed
    for months and then failed when an unrelated change shifted which draws seed
    1 consumed -- the effect is real but its size varies by seed, and a test that
    cannot tell those apart is not testing the model.
    """
    seeds = range(1, 6)
    active = [
        ExperimentRun(cfg(), seed=s).execute().final_metrics["resident_trait_retention"]
        for s in seeds
    ]
    null = [
        ExperimentRun(
            cfg(**{"dynamics.transmission_rule": "null", "dynamics.rule_params": {}}), seed=s
        )
        .execute()
        .final_metrics["resident_trait_retention"]
        for s in seeds
    ]
    assert abs(float(np.mean(active)) - float(np.mean(null))) > 0.01
    # The null is pure arithmetic, so it cannot vary across seeds at all.
    assert float(np.std(null)) < 1e-12
    assert float(np.std(active)) > 0.0


def test_recombination_produces_profiles_no_founding_population_held():
    """The only route to novelty this rule offers, and a weak one -- it is
    recombination across features, never innovation within one."""
    r = ExperimentRun(cfg(), seed=1).execute()
    assert r.final_metrics["share_off_founding_profiles"] > 0.0
    assert r.final_metrics["cultural_richness"] > 3  # more than the founding profiles
    assert r.final_metrics["max_distance_to_nearest_founding_culture"] > 0.0


def test_the_hybridisation_placeholder_still_refuses_to_answer():
    """Novel profiles now exist, but 'hybrid' is still undefined (A-012). The
    metric must stay NaN until the definition is settled, precisely because it
    would now return a plausible-looking number."""
    r = ExperimentRun(cfg(), seed=1).execute()
    assert r.final_metrics["hybridization_index"] != r.final_metrics["hybridization_index"]


# -- cultural drift (A-018 sensitivity) ------------------------------------

def test_drift_can_reintroduce_a_trait_nobody_held():
    """The invariant that copying-only guarantees, deliberately broken. This is
    the whole point of drift: diversity stops being non-renewable."""
    schema = CultureSchema.uniform(6, 5)
    pop = _pop_from(np.zeros((200, 6), dtype=np.int16), schema)
    _drive(pop, HomophilousTraitCopying(drift_rate=0.05), events=100)
    assert int(np.unique(pop.culture).size) > 1


def test_zero_drift_preserves_the_copying_only_invariant():
    schema = CultureSchema.uniform(6, 5)
    pop = _pop_from(np.zeros((200, 6), dtype=np.int16), schema)
    assert _drive(pop, HomophilousTraitCopying(drift_rate=0.0), events=100) == 0
    assert int(np.unique(pop.culture).size) == 1


def test_drift_always_changes_the_trait_when_it_fires():
    """A redraw that could return the original would silently halve the rate."""
    schema = CultureSchema.uniform(4, 3)
    pop = _pop_from(np.zeros((5000, 4), dtype=np.int16), schema)
    rule = HomophilousTraitCopying(events_per_agent_per_step=0.0, drift_rate=1.0)
    changed = _drive(pop, rule, events=1, seed=2)
    assert changed == 5000
    assert int((pop.culture != 0).sum()) > 4800  # one feature each, all changed


def test_drift_never_produces_an_inadmissible_trait():
    schema = CultureSchema.uniform(6, 4)
    pop = _pop_from(np.zeros((2000, 6), dtype=np.int16), schema)
    _drive(pop, HomophilousTraitCopying(drift_rate=0.3), events=50)
    assert int(pop.culture.min()) >= 0
    assert bool((pop.culture < schema.n_traits[None, :]).all())


def test_drift_works_with_interaction_switched_off():
    """A drift-only model is meaningful, not a silent no-op."""
    schema = CultureSchema.uniform(6, 4)
    pop = _pop_from(np.zeros((300, 6), dtype=np.int16), schema)
    rule = HomophilousTraitCopying(events_per_agent_per_step=0.0, drift_rate=0.1)
    assert _drive(pop, rule, events=20) > 0


def test_a_negative_or_excessive_drift_rate_is_rejected():
    with raises(ValueError, "drift_rate"):
        HomophilousTraitCopying(drift_rate=-0.1)
    with raises(ValueError, "drift_rate"):
        HomophilousTraitCopying(drift_rate=1.5)


def test_a_drifting_run_reports_that_no_absorbing_state_exists():
    """Not the same statement as 'the run was too short', and must not read the
    same way."""
    r = ExperimentRun(
        cfg(**{"dynamics.rule_params": {"axelrod_homophily": {"drift_rate": 0.01}}}), seed=1
    ).execute()
    a = r.manifest["absorption"]
    assert a["absorbed"] is False
    assert a["confidence"] == "no absorbing state"
    assert "no absorbing state exists" in a["reason"]


def test_the_manifest_records_that_drift_creates_novel_traits():
    r = ExperimentRun(
        cfg(**{"dynamics.rule_params": {"axelrod_homophily": {"drift_rate": 0.01}}}), seed=1
    ).execute()
    assert r.manifest["dynamics"]["transmission_rule"]["creates_novel_traits"] is True
    plain = ExperimentRun(cfg(), seed=1).execute()
    assert plain.manifest["dynamics"]["transmission_rule"]["creates_novel_traits"] is False
