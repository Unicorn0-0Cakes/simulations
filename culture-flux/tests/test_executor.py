"""Sweep execution: resume correctness, parallel determinism, and honest reporting."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from _harness import raises

from culture_flux.experiment.config import ExperimentConfig
from culture_flux.experiment.executor import _execute_one, execute_sweep, is_complete
from culture_flux.experiment.sweep import SweepSpec

ROOT = Path(__file__).resolve().parent.parent


def _base() -> ExperimentConfig:
    return ExperimentConfig.from_dict(
        {
            "name": "x",
            "seed": 1,
            "schema_version": 3,
            "population": {"initial_size": 120},
            "culture": {"features": 6, "traits_per_feature": 4},
            "migration": {
                "total_share": 0.2,
                "source_count": 2,
                "source_distribution": "even",
                "cultural_distance": 0.5,
                "duration_years": 2.0,
            },
            "runtime": {"total_years": 4.0, "steps_per_year": 12},
            "output": {"write_final_population": False},
        }
    )


def _spec(replicates=2) -> SweepSpec:
    return SweepSpec(
        name="t",
        base=_base(),
        axes={"migration.total_share": [0.1, 0.2]},
        replicates=replicates,
    )


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="cf-exec-"))


def _hashes(root: Path) -> dict:
    import csv

    with (root / "run_summary.csv").open(encoding="utf-8") as fh:
        return {(r["name"], r["seed"]): r["run_hash"] for r in csv.DictReader(fh)}


# -- resume ----------------------------------------------------------------

def test_a_completed_sweep_is_entirely_skipped_on_a_second_run():
    root = _tmp()
    try:
        first = execute_sweep(_spec(), root, workers=1)
        assert first["counts"] == {"completed": 4}
        second = execute_sweep(_spec(), root, workers=1)
        assert second["counts"] == {"skipped": 4}
        assert second["wall_seconds_total"] == 0.0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_resume_off_re_runs_everything():
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        again = execute_sweep(_spec(), root, workers=1, resume=False)
        assert again["counts"] == {"completed": 4}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_half_written_run_directory_is_re_run_not_trusted():
    """A directory left by a killed process must not be mistaken for a result."""
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        victim = sorted(p for p in root.iterdir() if p.is_dir())[0]
        (victim / "run_hash.txt").unlink()
        assert not is_complete(victim)
        again = execute_sweep(_spec(), root, workers=1)
        assert again["counts"] == {"completed": 1, "skipped": 3}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_run_from_another_model_version_is_re_run():
    """Results are not comparable across model versions, so a stored run from an
    older one is not a result for this sweep."""
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        victim = sorted(p for p in root.iterdir() if p.is_dir())[0]
        manifest = json.loads((victim / "manifest.json").read_text())
        manifest["model_version"] = "0.0.0-ancient"
        (victim / "manifest.json").write_text(json.dumps(manifest))
        assert not is_complete(victim)
        again = execute_sweep(_spec(), root, workers=1)
        assert again["counts"]["completed"] == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_corrupt_manifest_is_re_run_rather_than_raising():
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        victim = sorted(p for p in root.iterdir() if p.is_dir())[0]
        (victim / "manifest.json").write_text("{not json")
        assert not is_complete(victim)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_extending_a_sweep_runs_only_the_new_conditions():
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        wider = SweepSpec(
            name="t", base=_base(), axes={"migration.total_share": [0.1, 0.2, 0.3]}, replicates=2
        )
        out = execute_sweep(wider, root, workers=1)
        assert out["counts"] == {"completed": 2, "skipped": 4}
    finally:
        shutil.rmtree(root, ignore_errors=True)


# -- parallelism does not change results -----------------------------------

def test_serial_and_parallel_execution_produce_identical_run_hashes():
    """Determinism must come from (seed, config) alone -- never from execution
    order, worker identity, or how many workers there are."""
    a, b = _tmp(), _tmp()
    try:
        execute_sweep(_spec(replicates=3), a, workers=1)
        execute_sweep(_spec(replicates=3), b, workers=2)
        assert _hashes(a) == _hashes(b)
        assert len(_hashes(a)) == 6
    finally:
        shutil.rmtree(a, ignore_errors=True)
        shutil.rmtree(b, ignore_errors=True)


# -- the summary table -----------------------------------------------------

def test_the_summary_has_one_row_per_run_with_axes_and_metrics():
    root = _tmp()
    try:
        execute_sweep(_spec(), root, workers=1)
        import csv

        with (root / "run_summary.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 4
        assert "migration.total_share" in rows[0]
        assert "resident_trait_retention" in rows[0]
        assert "run_hash" in rows[0] and "seed" in rows[0]
        assert {r["migration.total_share"] for r in rows} == {"0.1", "0.2"}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dict_valued_axes_are_flattened_to_a_stable_string():
    """Network specifications are whole mappings; the summary must stay a
    rectangular, diffable table."""
    root = _tmp()
    try:
        spec = SweepSpec(
            name="n",
            base=_base(),
            axes={
                "network.layers": [
                    {"citywide": {"weight": 1.0}},
                    {"neighbourhood": {"weight": 1.0, "target_size": 30}},
                ]
            },
            replicates=1,
        )
        execute_sweep(spec, root, workers=1)
        import csv

        with (root / "run_summary.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2
        assert all(r["network.layers"].startswith("{") for r in rows)
    finally:
        shutil.rmtree(root, ignore_errors=True)


# -- failures are reported, never swallowed --------------------------------

def test_a_failing_run_is_recorded_with_its_error():
    task = {
        "config": {"population": {"initial_size": -5}},
        "seed": 1,
        "directory": "/tmp/never-created",
        "name": "bad",
        "config_hash": "x",
        "axis_values": {},
    }
    out = _execute_one(task)
    assert out["status"] == "failed"
    assert "initial_size" in out["error"]
    assert out["traceback"]


def test_the_batch_manifest_lists_failures_rather_than_only_counting_them():
    """A batch that quietly dropped 3% of its runs would still look complete in
    an aggregate table."""
    root = _tmp()
    try:
        manifest = execute_sweep(_spec(), root, workers=1)
        assert manifest["failures"] == []
        assert "counts" in manifest and manifest["total_runs"] == 4
        assert manifest["model_version"]
        assert manifest["sweep"]["n_runs"] == 4
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_the_batch_manifest_records_what_it_would_take_to_reproduce_it():
    root = _tmp()
    try:
        m = execute_sweep(_spec(), root, workers=1)
        for key in ("model_version", "sweep", "started_utc", "finished_utc", "workers", "resume"):
            assert key in m, key
        assert m["sweep"]["base_config_hash"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_the_shipped_sweeps_all_expand_under_the_executor_s_path():
    for path in sorted((ROOT / "configs" / "sweeps").glob("*.json")):
        spec = SweepSpec.load(path)
        pairs = spec.expand()
        assert len(pairs) == spec.n_runs
