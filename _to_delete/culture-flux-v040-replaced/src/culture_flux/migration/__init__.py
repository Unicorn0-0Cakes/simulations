"""Migration: source composition, cultural geometry, and arrival accounting."""

from __future__ import annotations

from .schedule import (
    ARRIVAL_PROFILES,
    DECLARED_ARRIVAL_PROFILES,
    MIGRATION_MODES,
    MigrationPlan,
    build_plan,
    largest_remainder,
    total_migrants,
)
from .sources import (
    ARRANGEMENTS,
    DISTANCE_PRESETS,
    SHARE_DISTRIBUTIONS,
    SourceSet,
    evenness,
    generate_source_set,
    resolve_distance,
    shares_for_target_evenness,
    source_shares,
)

__all__ = [
    "SourceSet",
    "generate_source_set",
    "source_shares",
    "shares_for_target_evenness",
    "evenness",
    "resolve_distance",
    "SHARE_DISTRIBUTIONS",
    "ARRANGEMENTS",
    "DISTANCE_PRESETS",
    "MigrationPlan",
    "build_plan",
    "total_migrants",
    "largest_remainder",
    "MIGRATION_MODES",
    "ARRIVAL_PROFILES",
    "DECLARED_ARRIVAL_PROFILES",
]
