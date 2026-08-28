"""Declarative experiment configuration.

A configuration is data, never code. It is loadable from JSON (always) or YAML
(when PyYAML is installed), is validated on construction, and hashes to a stable
digest computed over canonical JSON -- so a YAML file and its JSON equivalent
produce the same ``config_hash`` and the same results.

Three keys are derived from every configuration:

``config_hash``
    Digest of the whole scientific configuration. Identifies a condition.

``baseline_key``
    Digest of the parts that define the pre-migration city. Two configurations
    sharing a seed and a baseline key start from a byte-identical resident
    population, which is what makes "same M, different K" a controlled contrast.

``condition_key``
    Digest of everything else. Streams that depend on it are free to diverge.

Names, descriptions and output paths are excluded from all three: relabelling an
experiment must not change its results.

Validation is strict about the difference between *wrong* and *questionable*.
Wrong raises. Questionable appends to ``warnings``, which is carried into the run
manifest -- so that, for example, a schema too coarse to represent the requested
cultural distance is recorded against every run that used it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..culture.distance import available_distances
from ..dynamics.base import DECLARED_RULES, IMPLEMENTED_RULES
from ..influence.base import available_influence_models
from ..metrics.base import available_metrics
from ..migration.schedule import DECLARED_ARRIVAL_PROFILES, MIGRATION_MODES
from ..migration.sources import ARRANGEMENTS, DISTANCE_PRESETS, SHARE_DISTRIBUTIONS
from ..networks.base import DECLARED_LAYERS
from ..version import CONFIG_SCHEMA_VERSION


class ConfigError(ValueError):
    """Raised when a configuration cannot describe a runnable experiment."""


@dataclass
class PopulationConfig:
    initial_size: int = 2000
    #: Per-feature probability that an agent's trait departs from its group's
    #: modal profile at initialisation. 0 = perfectly homogeneous groups.
    within_source_noise: float = 0.0


@dataclass
class CultureConfig:
    features: int = 10
    traits_per_feature: int = 5
    distance_metric: str = "hamming"


@dataclass
class MigrationConfig:
    mode: str = "addition"
    #: M -- migrant share of the FINAL population.
    total_share: float = 0.30
    #: K -- number of distinct incoming populations.
    source_count: int = 1
    source_distribution: str = "even"
    #: Shape parameters, used according to source_distribution.
    decay: float = 0.5
    concentration: float = 1.0
    explicit_shares: list[float] | None = None
    #: H -- if set, overrides source_distribution with geometric shares whose
    #: Pielou evenness equals this value.
    target_evenness: float | None = None
    #: D -- a float in [0, 1], a preset name, or one value per source.
    cultural_distance: Any = "medium"
    arrangement: str = "independent"
    #: V -- the same total arrivals spread over this many years.
    start_year: float = 0.0
    duration_years: float = 10.0
    arrival_profile: str = "uniform"


@dataclass
class NetworkConfig:
    layers: list[str] = field(default_factory=lambda: ["citywide"])


@dataclass
class DynamicsConfig:
    transmission_rule: str = "null"
    #: Keyed BY RULE NAME: {"axelrod_homophily": {...}, "conformist": {...}}.
    #: Keying rather than flattening is what lets one configuration carry the
    #: settings for several rules, so a sweep can vary `transmission_rule` --
    #: which is how the null control arm and an active arm are run from a single
    #: base config. Parameters for rules not currently selected are kept and
    #: still validated, so a typo in an unused block is not stored up for later.
    rule_params: dict = field(default_factory=dict)
    influence_model: str = "uniform"


@dataclass
class RuntimeConfig:
    total_years: float = 50.0
    steps_per_year: int = 12
    years_per_generation: float = 25.0
    measure_every_steps: int = 12


@dataclass
class MetricsConfig:
    #: None means "every implemented metric".
    include: list[str] | None = None
    include_placeholders: bool = True


@dataclass
class OutputConfig:
    directory: str = "results"
    write_final_population: bool = True
    write_timeseries: bool = True
    #: "auto" uses parquet when pyarrow is importable, else CSV.
    format: str = "auto"


@dataclass
class ExperimentConfig:
    name: str = "unnamed"
    description: str = ""
    seed: int = 1
    schema_version: int = CONFIG_SCHEMA_VERSION
    population: PopulationConfig = field(default_factory=PopulationConfig)
    culture: CultureConfig = field(default_factory=CultureConfig)
    migration: MigrationConfig = field(default_factory=MigrationConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    dynamics: DynamicsConfig = field(default_factory=DynamicsConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.warnings = []
        self.validate()

    # -- validation --------------------------------------------------------
    def validate(self) -> None:
        w = self.warnings
        if self.schema_version != CONFIG_SCHEMA_VERSION:
            raise ConfigError(
                f"config schema version {self.schema_version} != "
                f"current {CONFIG_SCHEMA_VERSION}; migrate the file explicitly"
            )
        if int(self.seed) < 0:
            raise ConfigError("seed must be a non-negative integer")

        p = self.population
        if p.initial_size < 1:
            raise ConfigError("population.initial_size must be >= 1")
        if not 0.0 <= p.within_source_noise <= 1.0:
            raise ConfigError("population.within_source_noise must lie in [0, 1]")

        c = self.culture
        if c.features < 1:
            raise ConfigError("culture.features must be >= 1")
        if c.traits_per_feature < 2:
            raise ConfigError(
                "culture.traits_per_feature must be >= 2; a feature with one trait "
                "cannot vary"
            )
        if c.distance_metric not in available_distances():
            raise ConfigError(
                f"culture.distance_metric {c.distance_metric!r} is not registered; "
                f"available: {sorted(available_distances())}"
            )

        m = self.migration
        if m.mode not in MIGRATION_MODES:
            raise ConfigError(f"migration.mode must be one of {MIGRATION_MODES}")
        if not 0.0 <= m.total_share < 1.0:
            raise ConfigError(
                "migration.total_share must lie in [0, 1); a share of exactly 1 "
                "leaves no residents and makes retention undefined"
            )
        if m.source_count < 1:
            raise ConfigError("migration.source_count must be >= 1")
        if m.source_distribution not in SHARE_DISTRIBUTIONS:
            raise ConfigError(
                f"migration.source_distribution must be one of {SHARE_DISTRIBUTIONS}"
            )
        if m.source_distribution == "single" and m.source_count != 1:
            raise ConfigError("migration.source_distribution 'single' requires source_count == 1")
        if m.source_distribution == "explicit":
            if m.explicit_shares is None or len(m.explicit_shares) != m.source_count:
                raise ConfigError(
                    "migration.explicit_shares must list exactly source_count weights"
                )
        if m.target_evenness is not None and not 0.0 < m.target_evenness <= 1.0:
            raise ConfigError("migration.target_evenness must lie in (0, 1]")
        if m.arrangement not in ARRANGEMENTS:
            raise ConfigError(f"migration.arrangement must be one of {ARRANGEMENTS}")
        if m.arrival_profile not in DECLARED_ARRIVAL_PROFILES:
            raise ConfigError(
                f"migration.arrival_profile must be one of {DECLARED_ARRIVAL_PROFILES}"
            )
        if m.duration_years <= 0:
            raise ConfigError("migration.duration_years must be > 0")
        if m.start_year < 0:
            raise ConfigError("migration.start_year must be >= 0")
        self._validate_distance(m.cultural_distance, m.source_count)

        for layer in self.network.layers:
            if layer not in DECLARED_LAYERS:
                raise ConfigError(
                    f"network layer {layer!r} is not declared; declared: {DECLARED_LAYERS}"
                )
        if not self.network.layers:
            raise ConfigError("network.layers must name at least one layer")

        d = self.dynamics
        if d.transmission_rule not in DECLARED_RULES:
            raise ConfigError(
                f"dynamics.transmission_rule {d.transmission_rule!r} is not declared; "
                f"declared: {DECLARED_RULES}"
            )
        if not isinstance(d.rule_params, dict):
            raise ConfigError(
                "dynamics.rule_params must be a mapping keyed by rule name, e.g. "
                '{"axelrod_homophily": {"events_per_agent_per_step": 1.0}}'
            )
        from ..dynamics.base import get_transmission_rule

        for rule_name, params in d.rule_params.items():
            if rule_name not in DECLARED_RULES:
                raise ConfigError(
                    f"dynamics.rule_params names an undeclared rule {rule_name!r}; "
                    f"declared: {DECLARED_RULES}"
                )
            if not isinstance(params, dict):
                raise ConfigError(
                    f"dynamics.rule_params[{rule_name!r}] must be a mapping"
                )
            if rule_name not in IMPLEMENTED_RULES:
                continue
            # Construct now so bad parameters are rejected by `validate` rather
            # than three minutes into a sweep.
            try:
                get_transmission_rule(rule_name, params)
            except (ValueError, TypeError) as exc:
                raise ConfigError(
                    f"dynamics.rule_params[{rule_name!r}] invalid: {exc}"
                ) from exc
        if d.influence_model not in available_influence_models():
            raise ConfigError(
                f"dynamics.influence_model {d.influence_model!r} is not registered; "
                f"available: {available_influence_models()}"
            )

        r = self.runtime
        if r.total_years <= 0:
            raise ConfigError("runtime.total_years must be > 0")
        if r.steps_per_year < 1:
            raise ConfigError("runtime.steps_per_year must be >= 1")
        if r.years_per_generation <= 0:
            raise ConfigError("runtime.years_per_generation must be > 0")
        if r.measure_every_steps < 1:
            raise ConfigError("runtime.measure_every_steps must be >= 1")

        if self.metrics.include is not None:
            known = available_metrics()
            unknown = [n for n in self.metrics.include if n not in known]
            if unknown:
                raise ConfigError(f"metrics.include names unregistered metrics: {unknown}")

        if self.output.format not in ("auto", "parquet", "csv"):
            raise ConfigError("output.format must be 'auto', 'parquet' or 'csv'")

        # -- questionable but runnable -------------------------------------
        if m.start_year + m.duration_years > r.total_years:
            w.append(
                f"migration window ends at year {m.start_year + m.duration_years:g} but the "
                f"run ends at year {r.total_years:g}; the configured total share will "
                "not be reached"
            )
        if c.features < 10:
            w.append(
                f"culture.features = {c.features}: achievable cultural distances are "
                f"multiples of {1 / c.features:.3g}, so the realised distance may differ "
                "noticeably from the target"
            )
        if r.steps_per_year == 1:
            w.append(
                "runtime.steps_per_year = 1 makes a step indistinguishable from a year; "
                "a step/year confusion would be undetectable in this configuration"
            )
        if d.transmission_rule not in IMPLEMENTED_RULES:
            w.append(
                f"transmission rule {d.transmission_rule!r} is declared but not implemented; "
                "the run will fail at construction"
            )
        if d.transmission_rule == "null":
            w.append(
                "transmission_rule = 'null': no agent will change culture. Metric "
                "movement is compositional only."
            )
        if d.transmission_rule == "axelrod_homophily":
            w.append(
                "transmission_rule = 'axelrod_homophily' is an Axelrod-FAMILY rule "
                "specified in dynamics/homophily.py, not a verified reproduction of "
                "Axelrod (1997), which has not been read (L-Q3). See A-016."
            )
            if (
                d.rule_params.get("axelrod_homophily", {}).get("update_scheme", "batched")
                == "batched"
            ):
                w.append(
                    "update_scheme = 'batched' is an approximation to asynchronous "
                    "updating, not an optimisation of it (A-017)."
                )
        n_mig_approx = int(round(m.total_share * p.initial_size / max(1e-12, 1 - m.total_share)))
        if m.source_count > 1 and n_mig_approx < 10 * m.source_count:
            w.append(
                f"about {n_mig_approx} migrants across {m.source_count} sources: integer "
                "rounding will distort the requested share distribution"
            )

    @staticmethod
    def _validate_distance(value: Any, k: int) -> None:
        def check_one(v: Any) -> None:
            if isinstance(v, str):
                if v not in DISTANCE_PRESETS:
                    raise ConfigError(
                        f"migration.cultural_distance preset {v!r} unknown; "
                        f"known: {sorted(DISTANCE_PRESETS)}"
                    )
            else:
                fv = float(v)
                if not 0.0 <= fv <= 1.0:
                    raise ConfigError("migration.cultural_distance must lie in [0, 1]")

        if isinstance(value, (list, tuple)):
            if len(value) != k:
                raise ConfigError(
                    "migration.cultural_distance, when a list, needs one value per source"
                )
            for v in value:
                check_one(v)
        else:
            check_one(value)

    # -- serialisation -----------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("warnings", None)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ExperimentConfig":
        data = dict(data)
        data.pop("warnings", None)
        unknown = set(data) - {f for f in cls.__dataclass_fields__}
        if unknown:
            raise ConfigError(
                f"unknown top-level configuration keys: {sorted(unknown)}. "
                "Silently ignoring them would let a typo change nothing and be "
                "mistaken for a null result."
            )
        sections = {
            "population": PopulationConfig,
            "culture": CultureConfig,
            "migration": MigrationConfig,
            "network": NetworkConfig,
            "dynamics": DynamicsConfig,
            "runtime": RuntimeConfig,
            "metrics": MetricsConfig,
            "output": OutputConfig,
        }
        kwargs: dict[str, Any] = {}
        for key, klass in sections.items():
            payload = data.pop(key, None)
            if payload is None:
                kwargs[key] = klass()
                continue
            if not isinstance(payload, dict):
                raise ConfigError(f"configuration section {key!r} must be a mapping")
            unknown_keys = set(payload) - {f for f in klass.__dataclass_fields__}
            if unknown_keys:
                raise ConfigError(
                    f"unknown keys in section {key!r}: {sorted(unknown_keys)}"
                )
            kwargs[key] = klass(**payload)
        kwargs.update(data)
        return cls(**kwargs)

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentConfig":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise ConfigError(
                    f"{p.name} is YAML but PyYAML is not installed. Install it, or "
                    "use the equivalent .json file -- both hash identically."
                ) from exc
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
        if not isinstance(data, dict):
            raise ConfigError(f"{p.name} does not contain a configuration mapping")
        return cls.from_dict(data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(canonical_json(self.to_dict()) + "\n", encoding="utf-8")

    # -- derived keys ------------------------------------------------------
    def _scientific_dict(self) -> dict:
        d = self.to_dict()
        for k in ("name", "description", "output"):
            d.pop(k, None)
        return d

    @property
    def config_hash(self) -> str:
        return _digest(self._scientific_dict())

    @property
    def baseline_key(self) -> str:
        """Identifies the pre-migration city: population size, noise, schema."""
        return _digest(
            {
                "population": asdict(self.population),
                "culture": asdict(self.culture),
                "schema_version": self.schema_version,
            }
        )

    @property
    def condition_key(self) -> str:
        """Identifies everything that may differ between conditions."""
        d = self._scientific_dict()
        d.pop("population", None)
        d.pop("culture", None)
        d.pop("seed", None)
        return _digest(d)


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no incidental whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_default)


def _default(o: Any) -> Any:
    if isinstance(o, Path):
        return str(o)
    if hasattr(o, "tolist"):
        return o.tolist()
    raise TypeError(f"cannot serialise {type(o).__name__} into a configuration")


def _digest(obj: Any) -> str:
    return hashlib.blake2b(canonical_json(obj).encode("utf-8"), digest_size=16).hexdigest()
