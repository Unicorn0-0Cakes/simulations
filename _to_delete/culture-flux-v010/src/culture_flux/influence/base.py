"""Cultural influence -- kept structurally separate from population share.

The single most consequential claim the project must NOT smuggle in is that
being 30% of the population means holding 30% of the cultural influence. So the
two are different objects in the code, not the same number used twice.

``PopulationShare``  a fact about counts. Computed by ``metrics.diversity``.
``CulturalInfluence`` a modelled quantity. Produced by an ``InfluenceModel``.

An ``InfluenceModel`` returns a per-agent non-negative weight. Downstream
mechanisms (interaction partner choice, transmission bias) will consume weights;
none exist yet.

v0.1 ships exactly one model, ``UniformInfluence``, in which every agent carries
weight 1. Under it, group influence *does* equal group share -- but as the
explicit output of a named, replaceable null model that appears in the manifest,
not as an unexamined identity. Registering it as A-009 is the point of the file.

Models that later derive influence from network position, prestige, institutional
presence, economic payoff, visibility or media exposure implement the same
interface and are selected by name in the configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..agents.population import Population


class InfluenceModel(ABC):
    """Maps a population to per-agent cultural influence weights."""

    name: str = "abstract"

    @abstractmethod
    def weights(self, population: Population, step: int) -> np.ndarray:
        """Return non-negative weights, shape (N,). Need not be normalised."""

    def group_influence(self, population: Population, step: int) -> dict[int, float]:
        """Share of total influence held by each source group.

        Provided so that ``CulturalInfluence_i`` can be reported alongside
        ``PopulationShare_i`` in every run, making any divergence between them
        visible in the output rather than buried in a mechanism.
        """
        w = self.weights(population, step)
        if w.shape[0] != population.size:
            raise ValueError("influence weights must have one entry per agent")
        if (w < 0).any():
            raise ValueError("influence weights must be non-negative")
        total = float(w.sum())
        if total <= 0:
            raise ValueError("total influence must be positive")
        out: dict[int, float] = {}
        for sid in np.unique(population.source_id):
            out[int(sid)] = float(w[population.source_id == sid].sum() / total)
        return out

    def describe(self) -> dict:
        return {"name": self.name, "class": type(self).__name__}


class UniformInfluence(InfluenceModel):
    """Every agent carries equal influence. The explicit null (assumption A-009).

    Under this model group influence equals group population share by
    construction. That is a *modelling choice being tested*, not a background
    truth: results obtained under it are conditional on it, and any claim about
    influence must eventually be re-derived under a non-uniform model.
    """

    name = "uniform"

    def weights(self, population: Population, step: int) -> np.ndarray:
        return np.ones(population.size, dtype=np.float64)


_REGISTRY: dict[str, type[InfluenceModel]] = {"uniform": UniformInfluence}


def get_influence_model(name: str) -> InfluenceModel:
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise KeyError(
            f"unknown influence model {name!r}; registered: {sorted(_REGISTRY)}"
        ) from None


def register_influence_model(name: str, cls: type[InfluenceModel]) -> None:
    if name in _REGISTRY:
        raise ValueError(f"influence model {name!r} already registered")
    _REGISTRY[name] = cls


def available_influence_models() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))
