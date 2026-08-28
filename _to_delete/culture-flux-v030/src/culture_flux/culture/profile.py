"""Cultural profiles.

A profile is a length-F integer vector of trait indices. A *population's*
culture is an (N, F) integer array -- struct-of-arrays, not one object per
agent, because sweeps of 10^5 runs cannot afford per-agent Python objects.

``CulturalProfile`` exists for the small number of places where a single named
profile is the natural unit (a source population's modal culture, the resident
founding culture) and converts freely to and from rows of the array.

Nothing here assumes that a profile is tied to an agent's origin. An agent
carries both ``source_id`` (immutable provenance, a bookkeeping label) and a
cultural profile (mutable). Keeping them in separate arrays is what makes the
statement "culture is not ancestry" enforceable rather than aspirational.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .features import CultureSchema

#: dtype used for trait indices throughout. int16 admits 32767 traits per
#: feature, far beyond any plausible use, and halves memory versus int32.
TRAIT_DTYPE = np.int16


@dataclass(frozen=True)
class CulturalProfile:
    """One named cultural profile (a point in culture space)."""

    label: str
    traits: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.traits) < 1:
            raise ValueError("a cultural profile needs at least one feature")

    @classmethod
    def from_array(cls, label: str, arr: np.ndarray) -> "CulturalProfile":
        return cls(label=label, traits=tuple(int(x) for x in np.asarray(arr).ravel()))

    def to_array(self) -> np.ndarray:
        return np.asarray(self.traits, dtype=TRAIT_DTYPE)

    def validate_against(self, schema: CultureSchema) -> None:
        if len(self.traits) != schema.n_features:
            raise ValueError(
                f"profile {self.label!r} has {len(self.traits)} features, "
                f"schema declares {schema.n_features}"
            )
        limits = schema.n_traits
        for i, (t, lim) in enumerate(zip(self.traits, limits)):
            if not 0 <= t < lim:
                raise ValueError(
                    f"profile {self.label!r} feature {schema.names[i]!r}: trait {t} "
                    f"outside admissible range [0, {lim})"
                )

    def __len__(self) -> int:
        return len(self.traits)


def empty_culture_matrix(n_agents: int, schema: CultureSchema) -> np.ndarray:
    """Allocate an (N, F) trait matrix filled with -1 (explicitly unset)."""
    if n_agents < 0:
        raise ValueError("n_agents must be non-negative")
    return np.full((n_agents, schema.n_features), -1, dtype=TRAIT_DTYPE)


def validate_culture_matrix(matrix: np.ndarray, schema: CultureSchema) -> None:
    """Raise unless every entry is a legal trait index for its feature."""
    if matrix.ndim != 2:
        raise ValueError(f"culture matrix must be 2-D, got shape {matrix.shape}")
    if matrix.shape[1] != schema.n_features:
        raise ValueError(
            f"culture matrix has {matrix.shape[1]} features, "
            f"schema declares {schema.n_features}"
        )
    if matrix.size == 0:
        return
    if matrix.min() < 0:
        raise ValueError("culture matrix contains unset (-1) or negative traits")
    over = matrix >= schema.n_traits[None, :]
    if bool(over.any()):
        bad_feature = int(np.argmax(over.any(axis=0)))
        raise ValueError(
            f"culture matrix: feature {schema.names[bad_feature]!r} contains a trait "
            f"index >= its declared n_traits ({schema.n_traits[bad_feature]})"
        )


def profile_keys(matrix: np.ndarray, schema: CultureSchema | None = None) -> np.ndarray:
    """Map each row to an integer identifying its distinct cultural profile.

    Returns an (N,) array of group indices. Used by every metric that needs the
    distribution over *whole* cultural configurations (fractionalisation,
    entropy, dominance) rather than over individual traits.

    Two paths. When a schema is supplied and the cultural state space fits in an
    int64, each profile is encoded as a single mixed-radix integer and grouped in
    one dimension -- an order of magnitude faster than lexsorting an (N, F)
    array, which dominated profiling at N = 10^4. Otherwise the general
    row-wise path is used. Both return identical groupings; the equivalence is
    tested.
    """
    if matrix.size == 0:
        return np.zeros(0, dtype=np.int64)
    codes = encode_profiles(matrix, schema)
    if codes is not None:
        _, inverse = np.unique(codes, return_inverse=True)
        return np.asarray(inverse, dtype=np.int64).ravel()
    _, inverse = np.unique(matrix, axis=0, return_inverse=True)
    return np.asarray(inverse, dtype=np.int64).ravel()


#: Safety margin below 2**63 for the mixed-radix encoding.
_MAX_STATE_SPACE = 2**62


def encode_profiles(matrix: np.ndarray, schema: CultureSchema | None) -> np.ndarray | None:
    """One int64 per profile via mixed-radix encoding, or None if it will not fit.

    Returning None rather than raising lets callers fall back silently to the
    general path; returning a wrong answer on overflow would be far worse than
    being slow, so the bound is checked before any arithmetic.
    """
    if schema is None:
        return None
    limits = schema.n_traits
    total = 1
    for lim in limits:
        total *= int(lim)
        if total > _MAX_STATE_SPACE:
            return None
    codes = np.zeros(matrix.shape[0], dtype=np.int64)
    for j in range(matrix.shape[1]):
        codes = codes * int(limits[j]) + matrix[:, j].astype(np.int64)
    return codes
