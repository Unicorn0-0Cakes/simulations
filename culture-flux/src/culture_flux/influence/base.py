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


class NetworkDegreeInfluence(InfluenceModel):
    """Influence proportional to how many people attend to you.

    The cheapest non-uniform model, and the first thing that breaks the
    share-equals-influence identity (A-009). In-degree in the attention layer is
    "how many people are exposed to my culture" -- a structural position, not a
    property of the person and not a property of their origin.

    ``exponent`` tunes how sharply influence scales with position: 0 reproduces
    the uniform null exactly, 1 is linear in in-degree. Anything above 1 is
    available and unjustified. The ``floor`` keeps an agent nobody attends to
    from having exactly zero influence, which would make them unlearnable-from
    rather than merely obscure (A-026).

    Requires an attention layer. Without one it raises rather than silently
    falling back to uniform, because a run that quietly reverted to the null
    influence model would be indistinguishable in its output from one that
    used this one.
    """

    name = "network_degree"

    def __init__(self, exponent: float = 1.0, floor: float = 0.1) -> None:
        if exponent < 0:
            raise ValueError("influence exponent must be >= 0")
        if not 0.0 < floor <= 1.0:
            raise ValueError("influence floor must lie in (0, 1]")
        self.exponent = float(exponent)
        self.floor = float(floor)
        self.network = None

    def bind(self, network) -> None:
        """Attach the network this model reads. Called once per run."""
        self.network = network

    def weights(self, population: Population, step: int) -> np.ndarray:
        if self.network is None:
            raise RuntimeError(
                "network_degree influence was not bound to a network. It cannot "
                "fall back to uniform, because the output would be "
                "indistinguishable from a run that meant to be uniform."
            )
        layer = self.network.layers.get("friendship")
        if layer is None or not hasattr(layer, "ties"):
            raise RuntimeError(
                "network_degree influence requires a 'friendship' attention layer; "
                "the configured network has none"
            )
        n = population.size
        in_degree = np.bincount(layer.ties.ravel(), minlength=n)[:n].astype(np.float64)
        scaled = np.power(in_degree, self.exponent) if self.exponent != 0 else np.ones(n)
        top = scaled.max()
        if top <= 0:
            return np.ones(n, dtype=np.float64)
        return self.floor + (1.0 - self.floor) * (scaled / top)

    def describe(self) -> dict:
        d = super().describe()
        d.update({"exponent": self.exponent, "floor": self.floor, "reads": "friendship in-degree"})
        return d


_REGISTRY: dict[str, type[InfluenceModel]] = {
    "uniform": UniformInfluence,
    "network_degree": NetworkDegreeInfluence,
}


def get_influence_model(name: str, params: dict | None = None) -> InfluenceModel:
    if name not in _REGISTRY:
        raise KeyError(f"unknown influence model {name!r}; registered: {sorted(_REGISTRY)}")
    try:
        return _REGISTRY[name](**(params or {}))
    except TypeError as exc:
        raise ValueError(
            f"influence model {name!r} rejected its parameters {params!r}: {exc}"
        ) from exc


def register_influence_model(name: str, cls: type[InfluenceModel]) -> None:
    if name in _REGISTRY:
        raise ValueError(f"influence model {name!r} already registered")
    _REGISTRY[name] = cls


def available_influence_models() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))
