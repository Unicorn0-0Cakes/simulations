"""Multiplex network abstractions.

The city is not one well-mixed pool. It is several overlapping structures with
different sizes and different interaction intensities -- household,
neighbourhood, work/school, an attention network, and a weak citywide layer --
and who an agent actually encounters is a draw across all of them.

``MultiplexNetwork`` holds named layers with relative weights and answers the
one question the transmission rule asks: *given these focal agents, who does
each of them meet this time?* Each event picks a layer in proportion to its
weight and then a neighbour within that layer. Nothing materialises an adjacency
matrix.

The weights ARE the model of social life. Setting household to 0.30 and citywide
to 0.05 says most encounters happen among a handful of people and hardly any are
with strangers. That is assumption A-019 -- the one the project brief itself
offered as its example -- and it is the parameter most likely to change results
without anyone noticing it was set.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from ..agents.population import Population

#: Layer names the research programme expects to need.
DECLARED_LAYERS = (
    "household",
    "neighbourhood",
    "workplace",
    "friendship",
    "citywide",
)
IMPLEMENTED_LAYERS = DECLARED_LAYERS

#: Provisional defaults (A-019). Every value is a placeholder: no source has been
#: extracted for how encounters divide across settings. Weights are normalised,
#: so only their ratios matter.
DEFAULT_LAYER_SPECS: dict[str, dict] = {
    "household": {"weight": 0.30, "target_size": 3.0},
    "neighbourhood": {"weight": 0.20, "target_size": 150.0},
    "workplace": {"weight": 0.30, "target_size": 25.0},
    "friendship": {"weight": 0.15, "degree": 8, "rewire_rate": 0.0, "rewire_candidates": 4},
    "citywide": {"weight": 0.05},
}


class NetworkLayer(ABC):
    """One relational layer of the city."""

    name: str = "abstract"

    @abstractmethod
    def size(self) -> int:
        """Number of agents the layer currently covers."""

    @abstractmethod
    def neighbours(self, agent_index: int) -> np.ndarray:
        """Indices adjacent to ``agent_index`` in this layer."""

    @abstractmethod
    def sample_partners(self, focal: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """One neighbour per focal agent. May return the focal index itself when
        the agent has no neighbour in this layer; callers drop self-pairs."""

    def add_agents(self, n: int, rng: np.random.Generator, source_id: int = 0) -> None:
        raise NotImplementedError(f"layer {self.name!r} does not support growth")

    def rewire(self, population: Population, rng: np.random.Generator) -> int:
        """Update ties. Returns the number changed. No-op by default."""
        return 0

    def describe(self) -> dict:
        return {"name": self.name, "class": type(self).__name__, "size": self.size()}


class WellMixedLayer(NetworkLayer):
    """Complete graph: every agent adjacent to every other.

    The absence of structure, stated explicitly (A-010). Kept as the ``citywide``
    layer -- where it belongs, as the weak tail of encounters with strangers --
    and usable alone, which is what v0.1 and v0.2 did and what every result
    produced before v0.3 assumed.
    """

    name = "citywide"

    def __init__(self, n: int) -> None:
        if n < 0:
            raise ValueError("layer size cannot be negative")
        self._n = int(n)

    def size(self) -> int:
        return self._n

    def neighbours(self, agent_index: int) -> np.ndarray:
        if not 0 <= agent_index < self._n:
            raise IndexError("agent index out of range for this layer")
        idx = np.arange(self._n, dtype=np.int64)
        return idx[idx != agent_index]

    def sample_partners(self, focal: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        return rng.integers(0, self._n, size=focal.shape[0])

    def add_agents(self, n: int, rng: np.random.Generator, source_id: int = 0) -> None:
        if n < 0:
            raise ValueError("cannot add a negative number of agents")
        self._n += int(n)


@dataclass
class MultiplexNetwork:
    """Named layers with relative interaction weights."""

    layers: dict[str, NetworkLayer] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    _names: tuple[str, ...] = ()
    _cdf: np.ndarray | None = None

    def add_layer(self, layer: NetworkLayer, weight: float = 1.0) -> None:
        if layer.name in self.layers:
            raise ValueError(f"layer {layer.name!r} already present")
        if weight < 0:
            raise ValueError(f"layer {layer.name!r}: weight must be >= 0")
        self.layers[layer.name] = layer
        self.weights[layer.name] = float(weight)
        self._rebuild_cdf()

    def _rebuild_cdf(self) -> None:
        """Recompute the layer-choice distribution.

        Tolerates a zero total while the network is still being assembled -- the
        first layer added may legitimately carry weight 0 -- and defers the
        complaint to ``sample_partners``, which is where a weightless network
        actually becomes a problem.
        """
        self._names = tuple(self.layers)
        w = np.array([self.weights[n] for n in self._names], dtype=np.float64)
        total = w.sum()
        self._cdf = np.cumsum(w / total) if total > 0 else None

    @property
    def normalised_weights(self) -> dict[str, float]:
        total = sum(self.weights.values())
        return {n: w / total for n, w in self.weights.items()}

    @property
    def is_well_mixed_only(self) -> bool:
        """True when the only weighted layer is the citywide complete graph."""
        active = [n for n, w in self.weights.items() if w > 0]
        return active == ["citywide"]

    # -- what the transmission rule consumes -------------------------------
    def sample_partners(self, focal: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """One partner per focal agent, drawing the layer by weight each event.

        With a single layer this reduces exactly to that layer's own sampling and
        consumes the same draws, so a citywide-only configuration behaves
        identically to the pre-multiplex engine.
        """
        if not self.layers:
            raise RuntimeError("cannot sample partners from a network with no layers")
        if self._cdf is None:
            raise RuntimeError("at least one network layer must carry a positive weight")
        active = [n for n in self._names if self.weights[n] > 0]
        if len(active) == 1:
            return self.layers[active[0]].sample_partners(focal, rng)
        choice = np.searchsorted(self._cdf, rng.random(focal.shape[0]), side="right")
        choice = np.clip(choice, 0, len(self._names) - 1)
        out = np.empty(focal.shape[0], dtype=np.int64)
        for k, name in enumerate(self._names):
            mask = choice == k
            if bool(mask.any()):
                out[mask] = self.layers[name].sample_partners(focal[mask], rng)
        return out

    # -- lifecycle ---------------------------------------------------------
    def add_agents(self, n: int, rng: np.random.Generator, source_id: int = 0) -> None:
        for layer in self.layers.values():
            layer.add_agents(n, rng, source_id)

    def rewire(self, population: Population, rng: np.random.Generator) -> int:
        return sum(layer.rewire(population, rng) for layer in self.layers.values())

    def group_membership(self, name: str) -> np.ndarray | None:
        """Membership array of a group layer, for segregation metrics."""
        layer = self.layers.get(name)
        return getattr(layer, "membership", None)

    def describe(self) -> dict:
        return {
            "layers": [layer.describe() for layer in self.layers.values()],
            "weights": self.normalised_weights,
            "declared_layers": list(DECLARED_LAYERS),
            "implemented_layers": list(IMPLEMENTED_LAYERS),
            "well_mixed_only": self.is_well_mixed_only,
        }


def build_network(spec: dict, n_agents: int, rng: np.random.Generator) -> MultiplexNetwork:
    """Build the multiplex network described by a configuration fragment.

    ``spec["layers"]`` maps layer name -> parameters. A layer present with weight
    0 is built but never sampled, which is useful for measuring structure that
    does not drive interaction.
    """
    layers = spec.get("layers") or {}
    if not isinstance(layers, dict):
        raise TypeError(
            "network.layers must be a mapping of layer name to parameters, e.g. "
            '{"household": {"weight": 0.3, "target_size": 3}}'
        )
    if not layers:
        raise ValueError("network.layers must name at least one layer")

    net = MultiplexNetwork()
    for name, params in layers.items():
        if name not in DECLARED_LAYERS:
            raise ValueError(f"unknown network layer {name!r}; declared: {DECLARED_LAYERS}")
        params = dict(params or {})
        weight = float(params.pop("weight", DEFAULT_LAYER_SPECS[name].get("weight", 1.0)))
        net.add_layer(_build_layer(name, params, n_agents, rng), weight)
    return net


def _build_layer(
    name: str, params: dict, n_agents: int, rng: np.random.Generator
) -> NetworkLayer:
    from .layers import AttentionTieLayer, GroupLayer

    defaults = {k: v for k, v in DEFAULT_LAYER_SPECS[name].items() if k != "weight"}
    merged = {**defaults, **params}
    if name == "citywide":
        if merged:
            raise ValueError(f"layer 'citywide' takes no parameters, got {sorted(merged)}")
        return WellMixedLayer(n_agents)
    if name == "friendship":
        unknown = set(merged) - {"degree", "rewire_rate", "rewire_candidates"}
        if unknown:
            raise ValueError(f"layer 'friendship': unknown parameters {sorted(unknown)}")
        return AttentionTieLayer(name, n_agents, rng=rng, **merged)
    unknown = set(merged) - {"target_size", "assignment", "clustering"}
    if unknown:
        raise ValueError(f"layer {name!r}: unknown parameters {sorted(unknown)}")
    return GroupLayer(name, n_agents, rng=rng, **merged)
