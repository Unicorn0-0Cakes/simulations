"""Population state and initialisation.

Struct-of-arrays. One ``Population`` holds parallel arrays of length N plus an
(N, F) culture matrix. Agents are rows, never objects: a sweep of 10^5 runs at
N = 10^4 cannot afford Python per agent.

Two invariants are enforced on every mutation and asserted in the test suite:

* ``len()`` of every array agrees, and N is never negative.
* Every trait index is admissible under the schema.

Provenance versus culture
-------------------------
``source_id`` records where an agent entered from. It never changes and it never
determines behaviour. The culture matrix is a separate, mutable array. Nothing in
the engine may branch on ``source_id`` except bookkeeping and measurement -- if a
future mechanism needs "people like me", it must read culture or network
position, not origin. This is assumption A-002 and the test suite checks that
resident and migrant cultures are drawn through the same code path.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..culture.features import CultureSchema
from ..culture.profile import TRAIT_DTYPE, validate_culture_matrix
from ..rng import RunRNG

RESIDENT_SOURCE_ID = 0


@dataclass
class Population:
    """Mutable population state."""

    schema: CultureSchema
    agent_id: np.ndarray
    source_id: np.ndarray
    arrival_step: np.ndarray
    migration_generation: np.ndarray
    culture: np.ndarray
    source_labels: dict[int, str] = field(default_factory=dict)
    _next_agent_id: int = 0

    def __post_init__(self) -> None:
        self.validate()
        if self._next_agent_id == 0 and self.size:
            self._next_agent_id = int(self.agent_id.max()) + 1

    # -- invariants --------------------------------------------------------
    def validate(self) -> None:
        n = self.agent_id.shape[0]
        if n < 0:
            raise ValueError("population size cannot be negative")
        for name in ("source_id", "arrival_step", "migration_generation"):
            arr = getattr(self, name)
            if arr.shape[0] != n:
                raise ValueError(
                    f"population array {name!r} has length {arr.shape[0]}, expected {n}"
                )
        if self.culture.shape[0] != n:
            raise ValueError(
                f"culture matrix has {self.culture.shape[0]} rows, expected {n}"
            )
        validate_culture_matrix(self.culture, self.schema)
        if n and len(np.unique(self.agent_id)) != n:
            raise ValueError("agent_id values are not unique")
        if n and int(self.source_id.min()) < 0:
            raise ValueError("source_id must be non-negative")

    # -- views -------------------------------------------------------------
    @property
    def size(self) -> int:
        return int(self.agent_id.shape[0])

    @property
    def n_features(self) -> int:
        return self.schema.n_features

    def mask_source(self, source_id: int) -> np.ndarray:
        return self.source_id == source_id

    @property
    def resident_mask(self) -> np.ndarray:
        return self.source_id == RESIDENT_SOURCE_ID

    @property
    def migrant_mask(self) -> np.ndarray:
        return self.source_id != RESIDENT_SOURCE_ID

    def source_counts(self) -> dict[int, int]:
        if self.size == 0:
            return {}
        ids, counts = np.unique(self.source_id, return_counts=True)
        return {int(i): int(c) for i, c in zip(ids, counts)}

    def source_shares(self) -> dict[int, float]:
        n = self.size
        return {k: v / n for k, v in self.source_counts().items()} if n else {}

    # -- mutation ----------------------------------------------------------
    def add_agents(
        self,
        culture: np.ndarray,
        source_id: int,
        arrival_step: int,
        migration_generation: int = 1,
    ) -> np.ndarray:
        """Append agents and return their new agent_ids."""
        culture = np.asarray(culture, dtype=TRAIT_DTYPE)
        if culture.ndim != 2 or culture.shape[1] != self.n_features:
            raise ValueError(
                f"incoming culture must have shape (n, {self.n_features}), got {culture.shape}"
            )
        k = culture.shape[0]
        if k == 0:
            return np.zeros(0, dtype=np.int64)
        new_ids = np.arange(self._next_agent_id, self._next_agent_id + k, dtype=np.int64)
        self._next_agent_id += k
        self.agent_id = np.concatenate([self.agent_id, new_ids])
        self.source_id = np.concatenate(
            [self.source_id, np.full(k, source_id, dtype=np.int16)]
        )
        self.arrival_step = np.concatenate(
            [self.arrival_step, np.full(k, arrival_step, dtype=np.int32)]
        )
        self.migration_generation = np.concatenate(
            [self.migration_generation, np.full(k, migration_generation, dtype=np.int8)]
        )
        self.culture = np.vstack([self.culture, culture])
        self.validate()
        return new_ids

    def remove_agents(self, index: np.ndarray) -> int:
        """Remove agents by positional index. Returns the number removed."""
        index = np.asarray(index, dtype=np.int64)
        if index.size == 0:
            return 0
        if index.min() < 0 or index.max() >= self.size:
            raise IndexError("removal index out of range")
        keep = np.ones(self.size, dtype=bool)
        keep[index] = False
        removed = int((~keep).sum())
        self.agent_id = self.agent_id[keep]
        self.source_id = self.source_id[keep]
        self.arrival_step = self.arrival_step[keep]
        self.migration_generation = self.migration_generation[keep]
        self.culture = self.culture[keep]
        self.validate()
        return removed

    def copy(self) -> "Population":
        return Population(
            schema=self.schema,
            agent_id=self.agent_id.copy(),
            source_id=self.source_id.copy(),
            arrival_step=self.arrival_step.copy(),
            migration_generation=self.migration_generation.copy(),
            culture=self.culture.copy(),
            source_labels=dict(self.source_labels),
            _next_agent_id=self._next_agent_id,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Population(N={self.size}, F={self.n_features}, sources={self.source_counts()})"


def draw_profiles(
    modal: np.ndarray,
    n: int,
    schema: CultureSchema,
    within_noise: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw ``n`` cultural profiles around a modal profile.

    With probability ``within_noise`` per feature, an agent's trait is redrawn
    uniformly from the *other* traits of that feature; otherwise it copies the
    modal profile. ``within_noise = 0`` yields a perfectly homogeneous group.

    This is the single code path by which *all* groups are initialised --
    residents and every incoming source alike (assumption A-002). Within-group
    heterogeneity is a provisional placeholder: real populations are not
    uniform-random perturbations of a modal type (assumption A-004).
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if not 0.0 <= within_noise <= 1.0:
        raise ValueError("within_noise must lie in [0, 1]")
    modal = np.asarray(modal, dtype=TRAIT_DTYPE).reshape(1, -1)
    if modal.shape[1] != schema.n_features:
        raise ValueError("modal profile width does not match the schema")
    out = np.repeat(modal, n, axis=0)
    if n == 0 or within_noise == 0.0:
        return out
    limits = schema.n_traits
    flip = rng.random((n, schema.n_features)) < within_noise
    # Draw an offset in [1, n_traits-1] so the redrawn trait always differs.
    offsets = np.empty((n, schema.n_features), dtype=np.int64)
    for j in range(schema.n_features):
        offsets[:, j] = rng.integers(1, limits[j], size=n)
    alt = (out.astype(np.int64) + offsets) % limits[None, :]
    out = np.where(flip, alt.astype(TRAIT_DTYPE), out)
    return out.astype(TRAIT_DTYPE)


def initialise_resident_population(
    n_agents: int,
    schema: CultureSchema,
    rng: RunRNG,
    *,
    within_noise: float = 0.0,
    resident_profile: np.ndarray | None = None,
) -> Population:
    """Create the pre-migration city.

    The founding resident profile defaults to the all-zero profile. That choice
    is arbitrary but harmless: trait *labels* carry no meaning, so any fixed
    profile is equivalent to any other up to relabelling, and fixing it makes
    resident-retention metrics comparable across runs without extra bookkeeping
    (assumption A-005).

    ``within_noise = 0`` gives the "initially culturally homogeneous urban
    population" the research question specifies. It is a limiting case, not a
    claim about real cities.
    """
    if n_agents < 1:
        raise ValueError("initial population must contain at least one agent")
    gen = rng("resident_init")
    if resident_profile is None:
        profile = np.zeros(schema.n_features, dtype=TRAIT_DTYPE)
    else:
        profile = np.asarray(resident_profile, dtype=TRAIT_DTYPE)
    culture = draw_profiles(profile, n_agents, schema, within_noise, gen)
    return Population(
        schema=schema,
        agent_id=np.arange(n_agents, dtype=np.int64),
        source_id=np.full(n_agents, RESIDENT_SOURCE_ID, dtype=np.int16),
        arrival_step=np.full(n_agents, -1, dtype=np.int32),
        migration_generation=np.zeros(n_agents, dtype=np.int8),
        culture=culture,
        source_labels={RESIDENT_SOURCE_ID: "Resident"},
        _next_agent_id=n_agents,
    )
