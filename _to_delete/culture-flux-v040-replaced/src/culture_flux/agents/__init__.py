"""Agent state, attribute registry and population initialisation."""

from __future__ import annotations

from .attributes import (
    ATTRIBUTES,
    AttributeSpec,
    get_attribute,
    implemented_attributes,
    unimplemented_attributes,
)
from .population import (
    RESIDENT_SOURCE_ID,
    Population,
    draw_profiles,
    initialise_resident_population,
)

__all__ = [
    "Population",
    "initialise_resident_population",
    "draw_profiles",
    "RESIDENT_SOURCE_ID",
    "ATTRIBUTES",
    "AttributeSpec",
    "get_attribute",
    "implemented_attributes",
    "unimplemented_attributes",
]
