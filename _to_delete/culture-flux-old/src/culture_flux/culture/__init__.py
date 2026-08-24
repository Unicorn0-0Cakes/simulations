"""Culture representation: feature schema, profiles, distance."""

from __future__ import annotations

from .distance import (
    available_distances,
    distance_to_profile,
    get_distance,
    mean_pairwise_distance,
    register_distance,
)
from .features import CultureSchema, FeatureSpec
from .profile import (
    TRAIT_DTYPE,
    CulturalProfile,
    empty_culture_matrix,
    encode_profiles,
    profile_keys,
    validate_culture_matrix,
)

__all__ = [
    "CultureSchema",
    "FeatureSpec",
    "CulturalProfile",
    "TRAIT_DTYPE",
    "empty_culture_matrix",
    "validate_culture_matrix",
    "profile_keys",
    "encode_profiles",
    "get_distance",
    "register_distance",
    "available_distances",
    "distance_to_profile",
    "mean_pairwise_distance",
]
