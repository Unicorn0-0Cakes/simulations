"""Cultural transmission rules.

**No transmission rule is implemented in v0.1.** This is the deliberate centre of
the release: the instrument can initialise, migrate, and measure, but nobody
changes their culture. Every metric trajectory a v0.1 run produces is therefore
*compositional* -- it moves only because the mix of people changed, never
because anyone was influenced.

That is worth having on its own. It is the null model. A future transmission rule
that cannot beat it is not detecting cultural dynamics; it is re-describing
arithmetic. ``NullTransmission`` stays in the codebase permanently as the
baseline arm of every experiment, not as a placeholder to be deleted.

The rules the corpus points towards -- Axelrod-style homophilous trait copying,
conformist/frequency-dependent bias, prestige bias, payoff bias, vertical
transmission, and the acculturation-orientation schemes -- will each implement
``TransmissionRule`` and be selected by name. Choosing among them is a literature
question, not an engineering one: see docs/literature/literature_matrix.md and
open question L-Q3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..agents.population import Population
from ..influence.base import InfluenceModel
from ..networks.base import MultiplexNetwork


class TransmissionRule(ABC):
    """Applies one step of cultural change to a population."""

    name: str = "abstract"
    #: False until a rule actually changes anyone's culture. Recorded in the
    #: manifest so that no analysis can mistake a null run for a dynamic one.
    changes_culture: bool = True

    @abstractmethod
    def step(
        self,
        population: Population,
        network: MultiplexNetwork,
        influence: InfluenceModel,
        step: int,
        rng: np.random.Generator,
    ) -> int:
        """Advance one step. Returns the number of trait changes applied."""

    def describe(self) -> dict:
        return {
            "name": self.name,
            "class": type(self).__name__,
            "changes_culture": self.changes_culture,
        }


class NullTransmission(TransmissionRule):
    """Nobody influences anybody. The compositional baseline (assumption A-011)."""

    name = "null"
    changes_culture = False

    def step(
        self,
        population: Population,
        network: MultiplexNetwork,
        influence: InfluenceModel,
        step: int,
        rng: np.random.Generator,
    ) -> int:
        return 0


#: Rules the corpus indicates we will need. Named here so the configuration can
#: reject them with a useful message instead of a KeyError, and so the gap
#: between planned and implemented is machine-readable.
DECLARED_RULES = (
    "null",
    "axelrod_homophily",
    "conformist",
    "prestige_biased",
    "payoff_biased",
    "vertical",
    "acculturation_orientation",
)
IMPLEMENTED_RULES = ("null", "axelrod_homophily", "conformist")

_REGISTRY: dict[str, type[TransmissionRule]] = {"null": NullTransmission}


def get_transmission_rule(name: str, params: dict | None = None) -> TransmissionRule:
    """Construct a rule by name.

    ``params`` is passed to the rule's constructor. Rules validate their own
    parameters and reject unknown ones, so a misspelled parameter fails at
    configuration time rather than being silently ignored -- the same discipline
    the configuration layer applies to its own keys.
    """
    if name in _REGISTRY:
        try:
            return _REGISTRY[name](**(params or {}))
        except TypeError as exc:
            raise ValueError(
                f"transmission rule {name!r} rejected its parameters {params!r}: {exc}"
            ) from exc
    if name in DECLARED_RULES:
        raise NotImplementedError(
            f"transmission rule {name!r} is declared but not implemented in v0.1 "
            f"(implemented: {IMPLEMENTED_RULES}). See docs/model/ROADMAP.md."
        )
    raise KeyError(f"unknown transmission rule {name!r}; declared: {DECLARED_RULES}")


def register_transmission_rule(name: str, cls: type[TransmissionRule]) -> None:
    if name in _REGISTRY:
        raise ValueError(f"transmission rule {name!r} already registered")
    _REGISTRY[name] = cls


def available_transmission_rules() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def _register_builtin_rules() -> None:
    """Deferred import: homophily imports from this module, so registering it at
    module scope would be circular."""
    from .conformist import ConformistTransmission
    from .homophily import HomophilousTraitCopying

    if "axelrod_homophily" not in _REGISTRY:
        _REGISTRY["axelrod_homophily"] = HomophilousTraitCopying
    if "conformist" not in _REGISTRY:
        _REGISTRY["conformist"] = ConformistTransmission


_register_builtin_rules()
