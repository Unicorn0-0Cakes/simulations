"""Deterministic named random-number streams.

Design rules (see docs/model/ARCHITECTURE.md and docs/research/validation_strategy.md):

1. Every stochastic process draws from a *named* stream. Streams are never shared
   between processes, so adding a new stochastic mechanism cannot shift the draws
   consumed by an existing one.

2. Streams are seeded in three tiers, so that each experimental contrast holds
   constant exactly what it should:

   ``BASELINE_STREAMS`` -- seed + baseline key (population size, culture schema).
       Two runs sharing these start from a byte-identical resident population,
       whatever else differs. This is what makes "30% arriving as one culture"
       and "30% arriving as ten" a comparison of cultural environments rather
       than of two different cities.

   ``SCENARIO_STREAMS`` -- the above plus the scenario key (the migration
       configuration). Two runs sharing these face the *same arrivals*: the same
       source cultures, the same relative sizes, the same arrival schedule.
       This is what makes "same migration, different transmission rule" a
       controlled contrast -- which assumption A-016 requires, since no result
       may rest on a single rule.

   ``CONDITION_STREAMS`` -- the above plus the condition key (network, dynamics).
       Free to diverge.

   The tiers are nested: changing the network cannot perturb who arrived, and
   changing migration cannot perturb the city they arrived into.

3. Adding a stream name at the END of a tuple is safe -- existing stream indices
   are unchanged, so old runs still replay. Inserting in the middle is not, and
   requires bumping ``RNG_LAYOUT_VERSION``.

4. The mapping from (seed, keys, stream name) to a Generator is pure and
   version-stamped (``RNG_LAYOUT_VERSION``), so a run can be replayed from its
   manifest alone.

Undeclared stream names raise. This is deliberate: a typo must not silently
create a fresh, unrecorded stream.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .version import RNG_LAYOUT_VERSION

#: Streams seeded from the run seed + baseline key only. Identical across
#: conditions that share those, by contract.
BASELINE_STREAMS = (
    "culture_schema",  # which features exist, how many traits each carries
    "resident_init",  # the initial resident population
)

#: Streams fixed by the migration scenario. Identical across runs that differ
#: only in network or dynamics.
SCENARIO_STREAMS = (
    "source_culture_gen",  # cultural profiles assigned to incoming source populations
    "source_shares",  # relative sizes of incoming source populations
    "migrant_init",  # individual migrant agents
    "migration_schedule",  # arrival timing / stochastic rounding / displacement
)

#: Streams that may legitimately differ between experimental conditions.
CONDITION_STREAMS = (
    "network_init",
    "network_rewire",
    "interaction",
    "vital_events",  # reserved for births/deaths/emigration
    "misc",
)

ALL_STREAMS = BASELINE_STREAMS + SCENARIO_STREAMS + CONDITION_STREAMS


def _stream_index(name: str) -> int:
    try:
        return ALL_STREAMS.index(name)
    except ValueError:  # pragma: no cover - defensive
        raise KeyError(f"undeclared RNG stream {name!r}") from None


def key_to_int(key: str) -> int:
    """Stable 64-bit integer from a string key.

    ``hash()`` is salted per interpreter process and must never be used for
    anything that has to reproduce across sessions.
    """
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


class RunRNG:
    """Container of named ``numpy.random.Generator`` objects for one run.

    Parameters
    ----------
    seed:
        The run seed. Non-negative integer.
    baseline_key:
        Stable string describing the pre-migration city. Runs sharing
        (seed, baseline_key) share an identical resident population.
    scenario_key:
        Stable string describing the migration scenario. Runs sharing it face
        identical arrivals.
    condition_key:
        Stable string describing network and dynamics settings.
    """

    def __init__(
        self,
        seed: int,
        baseline_key: str = "",
        scenario_key: str = "",
        condition_key: str = "",
    ) -> None:
        seed = int(seed)
        if seed < 0:
            raise ValueError(f"seed must be non-negative, got {seed}")
        self.seed = seed
        self.baseline_key = baseline_key
        self.scenario_key = scenario_key
        self.condition_key = condition_key
        self._baseline_int = key_to_int(baseline_key)
        self._scenario_int = key_to_int(scenario_key)
        self._condition_int = key_to_int(condition_key)
        self._gens: dict[str, np.random.Generator] = {}

    def _make(self, name: str) -> np.random.Generator:
        idx = _stream_index(name)
        if name in BASELINE_STREAMS:
            entropy = (self.seed, self._baseline_int, 0, 0, idx, RNG_LAYOUT_VERSION)
        elif name in SCENARIO_STREAMS:
            entropy = (
                self.seed,
                self._baseline_int,
                self._scenario_int,
                0,
                idx,
                RNG_LAYOUT_VERSION,
            )
        else:
            entropy = (
                self.seed,
                self._baseline_int,
                self._scenario_int,
                self._condition_int,
                idx,
                RNG_LAYOUT_VERSION,
            )
        return np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy)))

    def __call__(self, name: str) -> np.random.Generator:
        gen = self._gens.get(name)
        if gen is None:
            gen = self._make(name)
            self._gens[name] = gen
        return gen

    def stream(self, name: str) -> np.random.Generator:
        """Alias of ``__call__`` for call sites where it reads better."""
        return self(name)

    def get_state(self) -> dict:
        """Capture enough to resume every stream that has been touched."""
        return {
            "seed": self.seed,
            "baseline_key": self.baseline_key,
            "scenario_key": self.scenario_key,
            "condition_key": self.condition_key,
            "layout_version": RNG_LAYOUT_VERSION,
            "streams": {k: g.bit_generator.state for k, g in self._gens.items()},
        }

    def set_state(self, state: dict) -> None:
        if state["layout_version"] != RNG_LAYOUT_VERSION:
            raise ValueError(
                "RNG layout version mismatch: checkpoint "
                f"{state['layout_version']} vs current {RNG_LAYOUT_VERSION}"
            )
        self.seed = int(state["seed"])
        self.baseline_key = state["baseline_key"]
        self.scenario_key = state.get("scenario_key", "")
        self.condition_key = state["condition_key"]
        self._baseline_int = key_to_int(self.baseline_key)
        self._scenario_int = key_to_int(self.scenario_key)
        self._condition_int = key_to_int(self.condition_key)
        self._gens = {}
        for name, bg_state in state["streams"].items():
            gen = self._make(name)
            gen.bit_generator.state = bg_state
            self._gens[name] = gen

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"RunRNG(seed={self.seed}, baseline_key={self.baseline_key!r}, "
            f"scenario_key={self.scenario_key!r}, condition_key={self.condition_key!r}, "
            f"touched={sorted(self._gens)})"
        )
