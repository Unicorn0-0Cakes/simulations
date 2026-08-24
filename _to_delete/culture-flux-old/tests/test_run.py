"""End-to-end run behaviour: reproducibility, accounting, and the null contract."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from _harness import approx, raises

from culture_flux.dynamics.base import get_transmission_rule
from culture_flux.experiment.config import ExperimentConfig
from culture_flux.experiment.run import ExperimentRun
from culture_flux.io.manifest import check_replayable
from culture_flux.version import MODEL_VERSION

ROOT = Path(__file__).resolve().parent.parent


def cfg(**overrides) -> ExperimentConfig:
    base = {
        "name": "t",
        "seed": 1,
        "population": {"initial_size": 400},
        "culture": {"features": 10, "traits_per_feature": 5},
        "migration": {
            "total_share": 0.3,
            "source_count": 2,
            "source_distribution": "even",
            "cultural_distance": 0.5,
            "duration_years": 5.0,
        },
        "runtime": {"total_years": 10.0, "steps_per_year": 12},
        "output": {"write_final_population": False},
    }
    for key, value in overrides.items():
        if "." in key:
            section, field = key.split(".", 1)
            base.setdefault(section, {})[field] = value
        else:
            base[key] = value
    return ExperimentConfig.from_dict(base)


def run(**overrides):
    c = cfg(**overrides)
    return ExperimentRun(c, seed=overrides.get("seed", c.seed)).execute()


# -- reproducibility -------------------------------------------------------

def test_the_same_seed_and_configuration_reproduce_the_same_run_hash():
    assert run().run_hash == run().run_hash


def test_a_different_seed_gives_a_different_run():
    a = ExperimentRun(cfg(), seed=1).execute()
    b = ExperimentRun(cfg(), seed=2).execute()
    assert a.run_hash != b.run_hash


def test_the_run_hash_excludes_wall_clock_and_paths():
    a, b = run(), run(**{"output.directory": "/tmp/other", "name": "renamed"})
    assert a.run_hash == b.run_hash
    assert a.manifest["timing"]["started_utc"] != "" and b.manifest["timing"]["started_utc"] != ""


def test_the_manifest_records_everything_needed_to_replay():
    m = run().manifest
    for key in ("model_version", "rng_layout_version", "seed", "config", "config_hash", "run_hash"):
        assert key in m, key
    assert m["model_version"] == MODEL_VERSION
    assert check_replayable(m) == []
    replayed = ExperimentRun(ExperimentConfig.from_dict(m["config"]), seed=m["seed"]).execute()
    assert replayed.run_hash == m["run_hash"]


def test_a_manifest_from_another_model_version_refuses_replay():
    m = dict(run().manifest)
    m["model_version"] = "0.0.0-ancient"
    assert check_replayable(m)


def test_the_manifest_is_json_serialisable():
    json.dumps(run().manifest, default=str)


# -- the null contract -----------------------------------------------------

def test_no_agent_changes_culture_under_the_null_rule():
    """The defining property of v0.1. If this ever fails, some mechanism has
    started acting without being declared."""
    r = run()
    assert r.is_null_dynamics
    assert r.manifest["dynamics"]["trait_changes_total"] == 0
    assert r.final_metrics["founder_subpopulation_retention"] == 1.0
    resident = r.population.culture[r.population.resident_mask]
    assert int(np.unique(resident, axis=0).shape[0]) == 1


def test_migrant_cultures_are_exactly_their_source_profiles_under_the_null():
    r = run()
    for j, _ in enumerate(r.source_set.labels):
        rows = r.population.culture[r.population.source_id == j + 1]
        assert np.array_equal(np.unique(rows, axis=0), r.source_set.profiles[j : j + 1])


def test_unimplemented_transmission_rules_raise_at_construction():
    with raises(NotImplementedError, "not implemented"):
        get_transmission_rule("conformist")


# -- migration accounting --------------------------------------------------

def test_population_is_conserved_up_to_declared_arrivals():
    r = run()
    a = r.manifest["accounting"]
    assert a["n_final"] == a["n_initial"] + a["arrivals_total"] - a["displaced_total"]
    assert a["arrivals_total"] == a["arrivals_planned"]


def test_replacement_mode_holds_the_population_constant():
    r = run(**{"migration.mode": "replacement"})
    a = r.manifest["accounting"]
    assert a["n_final"] == a["n_initial"]
    assert a["displaced_total"] == a["arrivals_total"]


def test_both_modes_reach_the_requested_final_migrant_share():
    for mode in ("addition", "replacement"):
        a = run(**{"migration.mode": mode}).manifest["accounting"]
        assert approx(a["final_migrant_share"], 0.3, tol=0.005), mode


def test_zero_migration_leaves_the_city_untouched():
    r = run(**{"migration.total_share": 0.0})
    a = r.manifest["accounting"]
    assert a["arrivals_total"] == 0 and a["n_final"] == a["n_initial"]
    assert r.final_metrics["resident_trait_retention"] == 1.0
    assert r.final_metrics["cultural_fractionalization"] == 0.0


def test_population_never_goes_negative_even_at_extreme_replacement():
    r = run(**{"migration.mode": "replacement", "migration.total_share": 0.95})
    assert r.population.size == r.manifest["accounting"]["n_initial"]
    assert r.population.size > 0


# -- the central experimental contrast -------------------------------------

def test_same_M_different_K_holds_the_city_and_the_migrant_total_constant():
    """Scenarios 1-4 of the research brief. Everything about the arrival volume
    and the pre-migration city must match; only the cultural environment differs."""
    one = run(**{"migration.source_count": 1, "migration.source_distribution": "single"})
    ten = run(**{"migration.source_count": 10})
    assert one.plan.n_migrants_total == ten.plan.n_migrants_total
    assert one.population.size == ten.population.size
    assert one.config.baseline_key == ten.config.baseline_key
    assert approx(
        one.final_metrics["resident_population_share"],
        ten.final_metrics["resident_population_share"],
        tol=1e-12,
    )
    assert one.final_metrics["incoming_source_count"] == 1.0
    assert ten.final_metrics["incoming_source_count"] == 10.0
    assert ten.final_metrics["source_fractionalization"] > one.final_metrics["source_fractionalization"]


def test_the_resident_population_is_byte_identical_across_migration_conditions():
    one = run(**{"migration.source_count": 1, "migration.source_distribution": "single"})
    ten = run(**{"migration.source_count": 10})
    a = one.population.culture[one.population.resident_mask]
    b = ten.population.culture[ten.population.resident_mask]
    assert np.array_equal(a, b)


def test_velocity_changes_the_path_but_not_the_endpoint_under_the_null():
    """Under a null rule, path dependence is impossible by construction. Any
    future rule that produces the same result is not modelling history."""
    slow = run(**{"migration.duration_years": 9.0})
    fast = run(**{"migration.duration_years": 1.0})
    assert slow.plan.n_migrants_total == fast.plan.n_migrants_total
    assert approx(
        slow.final_metrics["resident_trait_retention"],
        fast.final_metrics["resident_trait_retention"],
        tol=1e-12,
    )
    mid = len(slow.timeseries) // 3
    assert slow.timeseries[mid]["arrivals_cumulative"] < fast.timeseries[mid]["arrivals_cumulative"]


def test_greater_cultural_distance_lowers_retention_at_fixed_M():
    near = run(**{"migration.cultural_distance": 0.2})
    far = run(**{"migration.cultural_distance": 0.8})
    assert far.final_metrics["resident_trait_retention"] < near.final_metrics["resident_trait_retention"]


# -- time series -----------------------------------------------------------

def test_the_time_series_starts_before_migration_and_ends_at_the_final_step():
    r = run()
    assert r.timeseries[0]["step"] == 0.0
    assert r.timeseries[0]["arrivals_cumulative"] == 0.0
    assert r.timeseries[-1]["step"] == float(r.manifest["timing"]["total_steps"])


def test_every_time_series_row_has_the_same_columns():
    rows = run().timeseries
    first = list(rows[0])
    assert all(list(r) == first for r in rows)


def test_cumulative_arrivals_never_decrease():
    values = [r["arrivals_cumulative"] for r in run().timeseries]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_years_and_generations_advance_at_different_rates():
    r = run()
    last = r.timeseries[-1]
    assert last["year"] != last["generation"]
    assert approx(last["generation"], last["year"] / 25.0)


# -- shipped configurations ------------------------------------------------

def test_the_shipped_smoke_configuration_runs():
    r = ExperimentRun(ExperimentConfig.load(ROOT / "configs" / "smoke.json")).execute()
    assert r.population.size > 0
    assert r.is_null_dynamics


def test_seeds_change_the_source_cultures_even_though_the_null_metrics_do_not():
    """Zero between-replicate variance under the null must be a property of the
    null, not of a dead RNG. The source cultures DO differ across seeds; the
    metrics simply are not sensitive to WHICH features differ when the realised
    distance is held fixed."""
    a = ExperimentRun(cfg(**{"migration.source_count": 3}), seed=1).execute()
    b = ExperimentRun(cfg(**{"migration.source_count": 3}), seed=2).execute()
    assert not np.array_equal(a.source_set.profiles, b.source_set.profiles)
    assert approx(
        a.final_metrics["resident_trait_retention"],
        b.final_metrics["resident_trait_retention"],
        tol=1e-12,
    )
    assert a.run_hash != b.run_hash


def test_source_count_does_not_move_retention_under_the_null():
    """The compositional baseline for RQ2, stated as an invariant. Any K effect
    a future transmission rule shows is attributable to the mechanism, because
    there is exactly none here."""
    values = [
        ExperimentRun(
            cfg(
                **{
                    "migration.source_count": k,
                    "migration.source_distribution": "single" if k == 1 else "even",
                }
            ),
            seed=1,
        )
        .execute()
        .final_metrics["resident_trait_retention"]
        for k in (1, 2, 5, 10)
    ]
    assert max(values) - min(values) < 1e-12


def test_source_count_does_move_composition_diversity_under_the_null():
    """...but composition is not flat, so the manipulation demonstrably works."""
    one = ExperimentRun(
        cfg(**{"migration.source_count": 1, "migration.source_distribution": "single"}), seed=1
    ).execute()
    ten = ExperimentRun(cfg(**{"migration.source_count": 10}), seed=1).execute()
    assert ten.final_metrics["source_fractionalization"] > one.final_metrics["source_fractionalization"]
    assert ten.final_metrics["cultural_effective_number"] > one.final_metrics["cultural_effective_number"]
