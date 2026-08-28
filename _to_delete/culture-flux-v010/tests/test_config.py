"""Configuration validation, hashing, and the derived experiment keys."""

from __future__ import annotations

import json
from pathlib import Path

from _harness import raises

from culture_flux.experiment.config import ConfigError, ExperimentConfig, canonical_json
from culture_flux.experiment.sweep import SweepSpec

ROOT = Path(__file__).resolve().parent.parent


def cfg(**overrides) -> ExperimentConfig:
    base = {
        "name": "t",
        "seed": 1,
        "population": {"initial_size": 500},
        "culture": {"features": 10, "traits_per_feature": 5},
        "migration": {"total_share": 0.3, "source_count": 2, "source_distribution": "even"},
        "runtime": {"total_years": 10.0},
    }
    for key, value in overrides.items():
        if "." in key:
            section, field = key.split(".", 1)
            base.setdefault(section, {})[field] = value
        else:
            base[key] = value
    return ExperimentConfig.from_dict(base)


# -- rejection of impossible configurations --------------------------------

def test_negative_seed_rejected():
    with raises(ConfigError, "seed"):
        cfg(seed=-1)


def test_empty_population_rejected():
    with raises(ConfigError, "initial_size"):
        cfg(**{"population.initial_size": 0})


def test_migrant_share_outside_the_unit_interval_rejected():
    for bad in (-0.1, 1.0, 1.5):
        with raises(ConfigError, "total_share"):
            cfg(**{"migration.total_share": bad})


def test_single_trait_features_rejected():
    with raises(ConfigError, "traits_per_feature"):
        cfg(**{"culture.traits_per_feature": 1})


def test_zero_sources_rejected():
    with raises(ConfigError, "source_count"):
        cfg(**{"migration.source_count": 0})


def test_unknown_distance_metric_rejected():
    with raises(ConfigError, "distance_metric"):
        cfg(**{"culture.distance_metric": "cosine"})


def test_unknown_transmission_rule_rejected():
    with raises(ConfigError, "transmission_rule"):
        cfg(**{"dynamics.transmission_rule": "telepathy"})


def test_unknown_network_layer_rejected():
    with raises(ConfigError, "network layer"):
        cfg(**{"network.layers": ["subway"]})


def test_unknown_metric_name_rejected():
    with raises(ConfigError, "unregistered"):
        cfg(**{"metrics.include": ["not_a_metric"]})


def test_mismatched_explicit_shares_rejected():
    with raises(ConfigError, "explicit_shares"):
        cfg(**{"migration.source_distribution": "explicit", "migration.source_count": 3})


def test_per_source_distance_list_must_match_the_source_count():
    with raises(ConfigError, "one value per source"):
        cfg(**{"migration.cultural_distance": [0.2, 0.4, 0.6]})  # source_count is 2


def test_unknown_keys_are_rejected_rather_than_ignored():
    """A silently ignored typo would look exactly like a null result."""
    with raises(ConfigError, "unknown"):
        ExperimentConfig.from_dict({"populaton": {"initial_size": 10}})
    with raises(ConfigError, "unknown keys in section"):
        ExperimentConfig.from_dict({"population": {"initial_sizes": 10}})


def test_degenerate_time_configurations_rejected():
    with raises(ConfigError, "total_years"):
        cfg(**{"runtime.total_years": 0.0})
    with raises(ConfigError, "steps_per_year"):
        cfg(**{"runtime.steps_per_year": 0})


# -- warnings, not errors --------------------------------------------------

def test_a_migration_window_past_the_end_of_the_run_warns():
    c = cfg(**{"migration.duration_years": 100.0, "runtime.total_years": 10.0})
    assert any("migration window" in w for w in c.warnings)


def test_a_coarse_culture_schema_warns_about_distance_resolution():
    c = cfg(**{"culture.features": 4})
    assert any("achievable cultural distances" in w for w in c.warnings)


def test_the_null_transmission_rule_always_warns():
    assert any("compositional only" in w for w in cfg().warnings)


def test_too_few_migrants_per_source_warns_about_rounding():
    c = cfg(**{"population.initial_size": 20, "migration.source_count": 8})
    assert any("integer rounding" in w for w in c.warnings)


# -- hashing and keys ------------------------------------------------------

def test_the_same_configuration_hashes_identically():
    assert cfg().config_hash == cfg().config_hash


def test_renaming_an_experiment_does_not_change_its_hash():
    """Labels must never change results."""
    a, b = cfg(name="alpha"), cfg(name="beta", description="different words")
    assert a.config_hash == b.config_hash


def test_changing_the_output_directory_does_not_change_the_hash():
    assert cfg().config_hash == cfg(**{"output.directory": "/tmp/elsewhere"}).config_hash


def test_changing_a_scientific_parameter_changes_the_hash():
    assert cfg().config_hash != cfg(**{"migration.total_share": 0.31}).config_hash


def test_migration_settings_do_not_change_the_baseline_key():
    """This is what guarantees 'same M, different K' compares like with like."""
    a = cfg(**{"migration.source_count": 1, "migration.source_distribution": "single"})
    b = cfg(**{"migration.source_count": 10})
    assert a.baseline_key == b.baseline_key
    assert a.condition_key != b.condition_key


def test_population_settings_do_change_the_baseline_key():
    assert cfg().baseline_key != cfg(**{"population.initial_size": 501}).baseline_key


def test_canonical_json_is_order_independent():
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_a_roundtrip_through_dict_preserves_the_hash():
    c = cfg()
    assert ExperimentConfig.from_dict(c.to_dict()).config_hash == c.config_hash


def test_json_and_yaml_shipped_configs_are_identical_in_content():
    try:
        import yaml  # noqa: F401
    except ImportError:
        return
    a = ExperimentConfig.load(ROOT / "configs" / "smoke.json")
    b = ExperimentConfig.load(ROOT / "configs" / "smoke.yaml")
    assert a.config_hash == b.config_hash


def test_every_shipped_configuration_validates():
    for path in sorted((ROOT / "configs").glob("*.json")):
        ExperimentConfig.load(path)


# -- sweeps ----------------------------------------------------------------

def test_sweep_expansion_produces_the_advertised_number_of_runs():
    spec = SweepSpec(
        name="s",
        base=cfg(),
        axes={"migration.total_share": [0.1, 0.2, 0.3], "migration.source_count": [1, 4]},
        replicates=5,
    )
    assert spec.n_conditions == 6
    assert spec.n_runs == 30
    assert len(spec.expand()) == 30


def test_every_swept_condition_is_a_distinct_scientific_configuration():
    spec = SweepSpec(name="s", base=cfg(), axes={"migration.total_share": [0.1, 0.2, 0.3]})
    assert len({c.config_hash for c, _ in spec.expand()}) == 3


def test_replicates_differ_only_in_seed():
    spec = SweepSpec(name="s", base=cfg(), axes={"migration.total_share": [0.2]}, replicates=4)
    pairs = spec.expand()
    assert len({c.config_hash for c, _ in pairs}) == 1
    assert sorted(s for _, s in pairs) == [1, 2, 3, 4]


def test_a_sweep_axis_naming_a_nonexistent_field_is_rejected():
    with raises(ConfigError, "no field"):
        SweepSpec(name="s", base=cfg(), axes={"migration.total_shares": [0.1]})


def test_an_empty_sweep_axis_is_rejected():
    with raises(ConfigError, "non-empty"):
        SweepSpec(name="s", base=cfg(), axes={"migration.total_share": []})


def test_the_shipped_sweeps_load_and_expand():
    for path in sorted((ROOT / "configs" / "sweeps").glob("*.json")):
        spec = SweepSpec.load(path)
        assert spec.n_runs > 0
        assert json.loads(spec.manifest())["n_runs"] == spec.n_runs


def test_an_invalid_swept_combination_names_the_combination():
    """Large designs make an unlabelled validation failure expensive to
    diagnose, so expansion reports which condition was invalid."""
    base = ExperimentConfig.load(ROOT / "configs" / "baseline_v0.json")
    spec = SweepSpec(name="bad", base=base, axes={"migration.source_count": [1, 4]})
    with raises(ConfigError, "source_count=4"):
        spec.expand()


def test_a_zero_migration_condition_expands_and_is_valid():
    """M = 0 is the control condition of the whole design; it must survive
    expansion alongside multi-source axes."""
    spec = SweepSpec(
        name="z",
        base=cfg(),
        axes={"migration.total_share": [0.0, 0.3], "migration.source_count": [1, 16]},
    )
    assert len(spec.expand()) == 4
