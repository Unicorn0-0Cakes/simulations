"""Cultural feature schema.

A culture is a vector over F *features*; each feature carries a *trait*. The
schema declares, per feature, everything the model may later need in order to
treat features differently from one another:

``kind``
    ``categorical`` (unordered), ``ordinal`` (ordered levels), or ``continuous``.
    v0.1 implements categorical only; the other kinds are declarable and are
    rejected at construction with a clear message rather than silently coerced.

``n_traits``
    Number of admissible trait values for categorical/ordinal features.

``salience``
    Weight of the feature in distance and (later) in influence. Default 1.0.

``transmission_rate``
    Per-feature multiplier on adoption probability. Declared, unused in v0.1.

``resistance``
    Per-feature multiplier on resistance to change. Declared, unused in v0.1.

Declaring these now, and carrying them through distance computation, means the
step from "all features alike" to "features differ" is a parameter change rather
than a rewrite. Every field except ``kind`` and ``n_traits`` currently defaults
to the value that makes features interchangeable, which is assumption A-001.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

FEATURE_KINDS = ("categorical", "ordinal", "continuous")
IMPLEMENTED_KINDS = ("categorical",)


@dataclass(frozen=True)
class FeatureSpec:
    """Declaration of one cultural feature."""

    name: str
    kind: str = "categorical"
    n_traits: int = 5
    salience: float = 1.0
    transmission_rate: float = 1.0
    resistance: float = 0.0

    def __post_init__(self) -> None:
        if self.kind not in FEATURE_KINDS:
            raise ValueError(
                f"feature {self.name!r}: unknown kind {self.kind!r}; "
                f"expected one of {FEATURE_KINDS}"
            )
        if self.kind not in IMPLEMENTED_KINDS:
            raise NotImplementedError(
                f"feature {self.name!r}: kind {self.kind!r} is declarable but not "
                f"implemented in v0.1 (implemented: {IMPLEMENTED_KINDS}). "
                "See docs/model/ROADMAP.md."
            )
        if self.n_traits < 2:
            raise ValueError(
                f"feature {self.name!r}: n_traits must be >= 2 "
                "(a feature with one trait cannot vary and cannot be transmitted)"
            )
        if self.salience < 0:
            raise ValueError(f"feature {self.name!r}: salience must be >= 0")
        if not 0.0 <= self.resistance <= 1.0:
            raise ValueError(f"feature {self.name!r}: resistance must lie in [0, 1]")
        if self.transmission_rate < 0:
            raise ValueError(f"feature {self.name!r}: transmission_rate must be >= 0")


@dataclass(frozen=True)
class CultureSchema:
    """The set of features shared by every agent in a run."""

    features: tuple[FeatureSpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if len(self.features) < 1:
            raise ValueError("a culture schema needs at least one feature")
        names = [f.name for f in self.features]
        if len(set(names)) != len(names):
            dupes = sorted({n for n in names if names.count(n) > 1})
            raise ValueError(f"duplicate feature names: {dupes}")
        if all(f.salience == 0 for f in self.features):
            raise ValueError("at least one feature must have non-zero salience")

    # -- convenience -------------------------------------------------------
    @classmethod
    def uniform(cls, n_features: int, traits_per_feature: int) -> "CultureSchema":
        """Homogeneous schema: F interchangeable categorical features.

        This is the Axelrod-style baseline and the v0.1 default. Feature
        interchangeability is assumption A-001 and is expected to be relaxed.
        """
        if n_features < 1:
            raise ValueError("n_features must be >= 1")
        return cls(
            tuple(
                FeatureSpec(name=f"f{i:02d}", kind="categorical", n_traits=traits_per_feature)
                for i in range(n_features)
            )
        )

    @property
    def n_features(self) -> int:
        return len(self.features)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.features)

    @property
    def n_traits(self) -> np.ndarray:
        return np.array([f.n_traits for f in self.features], dtype=np.int64)

    @property
    def salience(self) -> np.ndarray:
        return np.array([f.salience for f in self.features], dtype=np.float64)

    @property
    def transmission_rate(self) -> np.ndarray:
        return np.array([f.transmission_rate for f in self.features], dtype=np.float64)

    @property
    def resistance(self) -> np.ndarray:
        return np.array([f.resistance for f in self.features], dtype=np.float64)

    @property
    def is_uniform(self) -> bool:
        """True when every feature is interchangeable with every other."""
        first = self.features[0]
        return all(
            f.kind == first.kind
            and f.n_traits == first.n_traits
            and f.salience == first.salience
            and f.transmission_rate == first.transmission_rate
            and f.resistance == first.resistance
            for f in self.features
        )

    def max_distinct_profiles(self) -> int:
        """Size of the cultural state space."""
        total = 1
        for f in self.features:
            total *= f.n_traits
        return total

    def to_dict(self) -> dict:
        return {
            "features": [
                {
                    "name": f.name,
                    "kind": f.kind,
                    "n_traits": f.n_traits,
                    "salience": f.salience,
                    "transmission_rate": f.transmission_rate,
                    "resistance": f.resistance,
                }
                for f in self.features
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CultureSchema":
        return cls(tuple(FeatureSpec(**f) for f in data["features"]))
