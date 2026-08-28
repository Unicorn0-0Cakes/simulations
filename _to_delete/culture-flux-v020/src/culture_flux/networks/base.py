"""Multiplex network abstractions.

The eventual city is not one well-mixed pool. It is several overlapping
structures with different sizes, densities and rewiring rates -- household,
neighbourhood, work/school, friendship, and a weak citywide layer -- and the
interaction rate between two agents is a function of *all* of them.

v0.1 defines the abstractions and ships one concrete layer, ``WellMixedLayer``,
in which every agent is adjacent to every other. That layer is not a model of a
city; it is the degenerate case against which structured layers must later be
compared, and it is named so that no run can use structure without saying so.

Design notes for the layers that follow:

* A layer owns *membership* (which group an agent belongs to) or *ties* (an edge
  list), never both, so that group-based and tie-based layers stay distinguishable.
* Layers expose ``interaction_weights`` rather than a raw adjacency matrix, so a
  10^5-agent citywide layer never has to be materialised as N^2 floats.
* Rewiring is a method on the layer, so homophily and segregation dynamics live
  next to the structure they modify rather than in the engine loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from ..agents.population import Population

#: Layer names the research programme expects to need. Implemented layers are a
#: subset; ``MultiplexNetwork`` refuses to build an unimplemented one.
DECLARED_LAYERS = (
    "household",
    "neighbourhood",
    "workplace",
    "friendship",
    "citywide",
)
IMPLEMENTED_LAYERS = ("citywide",)


class NetworkLayer(ABC):
    """One relational layer of the city."""

    name: str = "abstract"

    @abstractmethod
    def size(self) -> int:
        """Number of agents the layer currently covers."""

    @abstractmethod
    def neighbours(self, agent_index: int) -> np.ndarray:
        """Indices of agents adjacent to ``agent_index`` in this layer."""

    def add_agents(self, n: int, rng: np.random.Generator) -> None:
        """Extend the layer to cover ``n`` newly arrived agents."""
        raise NotImplementedError(f"layer {self.name!r} does not support growth yet")

    def rewire(self, population: Population, rng: np.random.Generator) -> int:
        """Update ties. Returns the number of ties changed. No-op by default."""
        return 0

    def describe(self) -> dict:
        return {"name": self.name, "class": type(self).__name__, "size": self.size()}


class WellMixedLayer(NetworkLayer):
    """Complete graph: every agent adjacent to every other.

    The absence of structure, stated explicitly (assumption A-010). Every result
    obtained under it is a result about a city with no households, no
    neighbourhoods and no workplaces.
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

    def add_agents(self, n: int, rng: np.random.Generator) -> None:
        if n < 0:
            raise ValueError("cannot add a negative number of agents")
        self._n += int(n)


@dataclass
class MultiplexNetwork:
    """A named stack of layers, all covering the same agent index space."""

    layers: dict[str, NetworkLayer] = field(default_factory=dict)

    def add_layer(self, layer: NetworkLayer) -> None:
        if layer.name in self.layers:
            raise ValueError(f"layer {layer.name!r} already present")
        self.layers[layer.name] = layer

    def add_agents(self, n: int, rng: np.random.Generator) -> None:
        for layer in self.layers.values():
            layer.add_agents(n, rng)

    def describe(self) -> dict:
        return {
            "layers": [layer.describe() for layer in self.layers.values()],
            "declared_layers": list(DECLARED_LAYERS),
            "implemented_layers": list(IMPLEMENTED_LAYERS),
        }


def build_network(spec: dict, n_agents: int) -> MultiplexNetwork:
    """Build the multiplex network described by a configuration fragment."""
    net = MultiplexNetwork()
    requested = spec.get("layers", ["citywide"])
    for name in requested:
        if name not in DECLARED_LAYERS:
            raise ValueError(f"unknown network layer {name!r}; declared: {DECLARED_LAYERS}")
        if name not in IMPLEMENTED_LAYERS:
            raise NotImplementedError(
                f"network layer {name!r} is declared but not implemented in v0.1 "
                f"(implemented: {IMPLEMENTED_LAYERS}). See docs/model/ROADMAP.md."
            )
        net.add_layer(WellMixedLayer(n_agents))
    return net
