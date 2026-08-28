"""Agent attribute registry.

The full agent specification the research programme eventually needs (age,
household, workplace, conformity, prestige sensitivity, migration generation,
parent links...) is declared here, in one place, with an ``implemented`` flag.
Nothing is allocated until it is implemented.

The point of declaring unimplemented attributes rather than omitting them is
traceability: the gap between "the agent the paper describes" and "the agent the
code allocates" is visible in a machine-readable table, and
``unimplemented_attributes()`` is printed by ``culture-flux status`` and asserted
in the test suite, so the gap cannot quietly close or quietly widen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttributeSpec:
    name: str
    dtype: str
    description: str
    implemented: bool
    group: str


ATTRIBUTES: tuple[AttributeSpec, ...] = (
    # -- identity and provenance (implemented) -----------------------------
    AttributeSpec("agent_id", "int64", "Unique, stable within a run.", True, "identity"),
    AttributeSpec(
        "source_id",
        "int16",
        "Index of the population the agent entered from; 0 = resident founding "
        "population. Immutable bookkeeping provenance, NOT culture.",
        True,
        "identity",
    ),
    AttributeSpec(
        "arrival_step",
        "int32",
        "Simulation step at which the agent entered the city; -1 for founders.",
        True,
        "identity",
    ),
    AttributeSpec(
        "migration_generation",
        "int8",
        "0 = resident founder, 1 = arrived by migration. Later: 2+ for descendants "
        "of migrants, which requires reproduction.",
        True,
        "identity",
    ),
    AttributeSpec("culture", "int16[F]", "Trait index per cultural feature. Mutable.", True, "culture"),
    # -- demography (declared, not implemented) ----------------------------
    AttributeSpec("age", "float32", "Age in simulated years.", False, "demography"),
    AttributeSpec("birth_step", "int32", "Step of birth.", False, "demography"),
    AttributeSpec("parent_a", "int64", "Index of first parent; -1 if founder.", False, "demography"),
    AttributeSpec("parent_b", "int64", "Index of second parent; -1 if founder.", False, "demography"),
    # -- structural position (declared, not implemented) -------------------
    AttributeSpec("household_id", "int64", "Household network membership.", False, "structure"),
    AttributeSpec("neighbourhood_id", "int32", "Residential location.", False, "structure"),
    AttributeSpec("workplace_id", "int64", "Work or school membership.", False, "structure"),
    # -- behavioural dispositions (declared, not implemented) --------------
    AttributeSpec("conservatism", "float32", "Resistance to changing own culture.", False, "behaviour"),
    AttributeSpec("conformity", "float32", "Strength of frequency-dependent bias.", False, "behaviour"),
    AttributeSpec("anticonformity", "float32", "Strength of negative frequency dependence.", False, "behaviour"),
    AttributeSpec("interaction_rate", "float32", "Relative interaction frequency.", False, "behaviour"),
    AttributeSpec("prestige_sensitivity", "float32", "Weight on model prestige.", False, "behaviour"),
    AttributeSpec("payoff_sensitivity", "float32", "Weight on trait payoff.", False, "behaviour"),
    AttributeSpec("openness", "float32", "Willingness to adopt out-group traits.", False, "behaviour"),
)

_BY_NAME = {a.name: a for a in ATTRIBUTES}


def get_attribute(name: str) -> AttributeSpec:
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"unknown agent attribute {name!r}") from None


def implemented_attributes() -> tuple[AttributeSpec, ...]:
    return tuple(a for a in ATTRIBUTES if a.implemented)


def unimplemented_attributes() -> tuple[AttributeSpec, ...]:
    return tuple(a for a in ATTRIBUTES if not a.implemented)
