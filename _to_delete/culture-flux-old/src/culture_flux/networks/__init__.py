"""Multiplex network layers (abstractions; one degenerate layer implemented)."""

from __future__ import annotations

from .base import (
    DECLARED_LAYERS,
    IMPLEMENTED_LAYERS,
    MultiplexNetwork,
    NetworkLayer,
    WellMixedLayer,
    build_network,
)

__all__ = [
    "NetworkLayer",
    "WellMixedLayer",
    "MultiplexNetwork",
    "build_network",
    "DECLARED_LAYERS",
    "IMPLEMENTED_LAYERS",
]
