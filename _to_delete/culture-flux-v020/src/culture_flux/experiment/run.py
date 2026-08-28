"""The experiment run: initialise, migrate, (not yet) transmit, measure.

What a v0.1 run actually does
-----------------------------
1. Builds the culture schema from the configuration.
2. Initialises the resident city from the ``resident_init`` stream, which depends
   on (seed, baseline_key) only.
3. Generates K source cultures at the requested distances and sizes, and MEASURES
   the geometry it actually produced.
4. Resolves M, H and V into an exact integer arrival schedule.
5. Steps the clock. At each step, scheduled arrivals enter (and, in replacement
   mode, an equal number of residents leave). The transmission rule is applied --
   in v0.1 it is the null and applies nothing.
6. Measures on the configured cadence.

Because the only transmission rule is the null, every trajectory a v0.1 run
produces is compositional. The engine says so, in the manifest, in the metric
table, and in ``RunResult.is_null_dynamics``. Nothing about that is a defect: it
is the baseline every future mechanism has to be measured against.

Reproducibility contract
------------------------
``run_hash`` digests the scientific content of a result -- the final culture
matrix, the final provenance labels, and the full metric time series -- and
excludes anything wall-clock or path-dependent. Two runs with the same model
version, configuration and seed must produce the same ``run_hash`` on any
machine. ``verify`` checks exactly that.
"""

from __future__ import annotations

import hashlib
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from ..agents.population import RESIDENT_SOURCE_ID, Population, draw_profiles, initialise_resident_population
from ..culture.features import CultureSchema
from ..culture.profile import TRAIT_DTYPE
from ..dynamics.base import get_transmission_rule
from ..influence.base import get_influence_model
from ..metrics.base import MetricContext, available_metrics, compute_metrics, default_metric_names
from ..migration.schedule import MigrationPlan, build_plan
from ..migration.sources import (
    SourceSet,
    generate_source_set,
    resolve_distance,
    shares_for_target_evenness,
    source_shares,
)
from ..networks.base import build_network
from ..rng import RunRNG
from ..time import SimulationClock, TimeSpec
from ..version import MODEL_VERSION, OUTPUT_SCHEMA_VERSION, RNG_LAYOUT_VERSION
from .config import ExperimentConfig, canonical_json


@dataclass
class RunResult:
    """Everything one run produced, in memory."""

    config: ExperimentConfig
    manifest: dict[str, Any]
    timeseries: list[dict[str, float]]
    final_metrics: dict[str, float]
    population: Population
    source_set: SourceSet
    plan: MigrationPlan
    run_hash: str
    warnings: list[str] = field(default_factory=list)

    @property
    def is_null_dynamics(self) -> bool:
        return not bool(self.manifest["dynamics"]["changes_culture"])

    def metric_names(self) -> tuple[str, ...]:
        return tuple(self.final_metrics)


def resolve_source_shares(cfg: ExperimentConfig, rng: RunRNG) -> np.ndarray:
    m = cfg.migration
    if m.target_evenness is not None:
        return shares_for_target_evenness(m.source_count, m.target_evenness)
    return source_shares(
        m.source_count,
        m.source_distribution,
        rng("source_shares"),
        decay=m.decay,
        concentration=m.concentration,
        explicit=m.explicit_shares,
    )


def resolve_distances(cfg: ExperimentConfig) -> np.ndarray:
    value = cfg.migration.cultural_distance
    k = cfg.migration.source_count
    if isinstance(value, (list, tuple)):
        return np.array([resolve_distance(v) for v in value], dtype=np.float64)
    return np.full(k, resolve_distance(value), dtype=np.float64)


class ExperimentRun:
    """One (configuration, seed) execution."""

    def __init__(self, config: ExperimentConfig, seed: int | None = None) -> None:
        self.config = config
        self.seed = int(config.seed if seed is None else seed)
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        self.rng = RunRNG(
            seed=self.seed,
            baseline_key=config.baseline_key,
            condition_key=config.condition_key,
        )
        self.schema = CultureSchema.uniform(config.culture.features, config.culture.traits_per_feature)
        self.clock = SimulationClock(
            TimeSpec(
                steps_per_year=config.runtime.steps_per_year,
                years_per_generation=config.runtime.years_per_generation,
                measure_every_steps=config.runtime.measure_every_steps,
            ),
            total_years=config.runtime.total_years,
        )
        self.influence = get_influence_model(config.dynamics.influence_model)
        self.rule = get_transmission_rule(
            config.dynamics.transmission_rule,
            config.dynamics.rule_params.get(config.dynamics.transmission_rule, {}),
        )
        self.metric_names = self._resolve_metric_names()

    def _resolve_metric_names(self) -> tuple[str, ...]:
        cfg = self.config.metrics
        if cfg.include is not None:
            return tuple(cfg.include)
        names = list(default_metric_names())
        if cfg.include_placeholders:
            names += [n for n, s in available_metrics().items() if s.status == "placeholder"]
        return tuple(names)

    # -- execution ---------------------------------------------------------
    def execute(self) -> RunResult:
        cfg = self.config
        started_wall = time.time()
        started_iso = datetime.now(timezone.utc).isoformat()

        population = initialise_resident_population(
            cfg.population.initial_size,
            self.schema,
            self.rng,
            within_noise=cfg.population.within_source_noise,
        )
        initial_resident_profile = population.culture[0].copy() if not cfg.population.within_source_noise else np.zeros(
            self.schema.n_features, dtype=TRAIT_DTYPE
        )
        initial_culture = population.culture.copy()

        shares = resolve_source_shares(cfg, self.rng)
        distances = resolve_distances(cfg)
        source_set = generate_source_set(
            self.schema,
            initial_resident_profile,
            shares,
            distances,
            self.rng("source_culture_gen"),
            arrangement=cfg.migration.arrangement,
            metric=cfg.culture.distance_metric,
        )
        for i, label in enumerate(source_set.labels):
            population.source_labels[i + 1] = label

        plan = build_plan(
            mode=cfg.migration.mode,
            total_share=cfg.migration.total_share,
            n_initial=cfg.population.initial_size,
            shares=source_set.shares,
            steps_per_year=cfg.runtime.steps_per_year,
            start_year=cfg.migration.start_year,
            duration_years=cfg.migration.duration_years,
            profile=cfg.migration.arrival_profile,
        )
        network = build_network({"layers": cfg.network.layers}, population.size)

        founding_profiles = np.vstack(
            [initial_resident_profile.reshape(1, -1), source_set.profiles]
        )

        arrivals_by_step: dict[int, np.ndarray] = {
            int(s): plan.arrivals[i] for i, s in enumerate(plan.arrival_steps)
        }
        migrant_gen = self.rng("migrant_init")
        sched_gen = self.rng("migration_schedule")
        interaction_gen = self.rng("interaction")
        metric_gen = self.rng("misc")

        timeseries: list[dict[str, float]] = []
        arrived_total = 0
        displaced_total = 0
        trait_changes_total = 0

        def measure() -> dict[str, float]:
            ctx = MetricContext(
                population=population,
                schema=self.schema,
                step=self.clock.step,
                year=self.clock.year,
                generation=self.clock.generation,
                initial_resident_profile=initial_resident_profile,
                initial_culture=initial_culture,
                founding_profiles=founding_profiles,
                influence=self.influence,
                rng=metric_gen,
                distance_metric=cfg.culture.distance_metric,
                source_labels=population.source_labels,
            )
            row: dict[str, float] = {
                "step": float(self.clock.step),
                "year": float(self.clock.year),
                "generation": float(self.clock.generation),
                "arrivals_cumulative": float(arrived_total),
                "displaced_cumulative": float(displaced_total),
                "trait_changes_cumulative": float(trait_changes_total),
            }
            row.update(compute_metrics(ctx, self.metric_names))
            return row

        timeseries.append(measure())

        while not self.clock.finished:
            step = self.clock.advance()
            counts = arrivals_by_step.get(step)
            if counts is not None:
                for j, n in enumerate(counts):
                    n = int(n)
                    if n <= 0:
                        continue
                    culture = draw_profiles(
                        source_set.profiles[j],
                        n,
                        self.schema,
                        cfg.population.within_source_noise,
                        migrant_gen,
                    )
                    population.add_agents(
                        culture, source_id=j + 1, arrival_step=step, migration_generation=1
                    )
                    arrived_total += n
                if cfg.migration.mode == "replacement":
                    displaced_total += self._displace(population, int(counts.sum()), sched_gen)
            trait_changes_total += int(
                self.rule.step(population, network, self.influence, step, interaction_gen)
            )
            if self.clock.is_measurement_step():
                timeseries.append(measure())

        if timeseries[-1]["step"] != float(self.clock.step):
            timeseries.append(measure())

        finished_wall = time.time()
        final_metrics = dict(timeseries[-1])
        run_hash = _hash_result(population, timeseries)

        manifest = self._build_manifest(
            population=population,
            source_set=source_set,
            plan=plan,
            network=network,
            timeseries=timeseries,
            started_iso=started_iso,
            duration_s=finished_wall - started_wall,
            arrived_total=arrived_total,
            displaced_total=displaced_total,
            trait_changes_total=trait_changes_total,
            run_hash=run_hash,
        )
        return RunResult(
            config=cfg,
            manifest=manifest,
            timeseries=timeseries,
            final_metrics=final_metrics,
            population=population,
            source_set=source_set,
            plan=plan,
            run_hash=run_hash,
            warnings=list(cfg.warnings),
        )

    @staticmethod
    def _displace(population: Population, n: int, rng: np.random.Generator) -> int:
        """Remove ``n`` residents chosen uniformly at random (assumption A-008b).

        Uniform choice is the neutral placeholder. Real out-migration is
        selective on age, tenure and culture, and any of those would push the
        result in a direction the model has no warrant for yet.
        """
        if n <= 0:
            return 0
        idx = np.flatnonzero(population.source_id == RESIDENT_SOURCE_ID)
        if idx.size == 0:
            return 0
        take = min(n, idx.size)
        chosen = rng.choice(idx, size=take, replace=False)
        return population.remove_agents(chosen)

    def _build_manifest(self, **kw: Any) -> dict[str, Any]:
        cfg = self.config
        population: Population = kw["population"]
        source_set: SourceSet = kw["source_set"]
        plan: MigrationPlan = kw["plan"]
        return {
            "model_version": MODEL_VERSION,
            "rng_layout_version": RNG_LAYOUT_VERSION,
            "output_schema_version": OUTPUT_SCHEMA_VERSION,
            "config_schema_version": cfg.schema_version,
            "run_hash": kw["run_hash"],
            "config_hash": cfg.config_hash,
            "baseline_key": cfg.baseline_key,
            "condition_key": cfg.condition_key,
            "seed": self.seed,
            "experiment_name": cfg.name,
            "description": cfg.description,
            "config": cfg.to_dict(),
            "config_warnings": list(cfg.warnings),
            "culture_schema": self.schema.to_dict(),
            "culture_state_space": self.schema.max_distinct_profiles(),
            "source_set": source_set.to_dict(),
            "migration_plan": plan.to_dict(),
            "network": kw["network"].describe(),
            "dynamics": {
                "transmission_rule": self.rule.describe(),
                "influence_model": self.influence.describe(),
                "changes_culture": self.rule.changes_culture,
                "trait_changes_total": kw["trait_changes_total"],
            },
            "accounting": {
                "n_initial": cfg.population.initial_size,
                "n_final": population.size,
                "arrivals_total": kw["arrived_total"],
                "arrivals_planned": plan.n_migrants_total,
                "displaced_total": kw["displaced_total"],
                "final_migrant_share": float(population.migrant_mask.mean())
                if population.size
                else float("nan"),
                "requested_migrant_share": cfg.migration.total_share,
                "source_counts": {str(k): v for k, v in population.source_counts().items()},
                "source_labels": {str(k): v for k, v in population.source_labels.items()},
            },
            "timing": {
                "started_utc": kw["started_iso"],
                "wall_seconds": round(float(kw["duration_s"]), 6),
                "total_steps": self.clock.total_steps,
                "total_years": cfg.runtime.total_years,
                "steps_per_year": cfg.runtime.steps_per_year,
                "years_per_generation": cfg.runtime.years_per_generation,
                "generations_elapsed": self.clock.generation,
                "measurements": len(kw["timeseries"]),
            },
            "metrics": {
                "names": list(self.metric_names),
                "placeholders": [
                    n
                    for n in self.metric_names
                    if available_metrics()[n].status == "placeholder"
                ],
            },
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "platform": platform.platform(),
            },
        }


def _hash_result(population: Population, timeseries: list[dict[str, float]]) -> str:
    """Digest of scientific content only. Excludes timing, paths and hostnames."""
    h = hashlib.blake2b(digest_size=16)
    h.update(np.ascontiguousarray(population.culture).tobytes())
    h.update(np.ascontiguousarray(population.source_id).tobytes())
    h.update(np.ascontiguousarray(population.arrival_step).tobytes())
    rounded = [
        {k: (None if v != v else round(float(v), 10)) for k, v in row.items()}
        for row in timeseries
    ]
    h.update(canonical_json(rounded).encode("utf-8"))
    return h.hexdigest()
