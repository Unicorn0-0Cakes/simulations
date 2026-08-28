"""Version and provenance constants.

MODEL_VERSION identifies the *scientific* model, not the package release.
Bump it whenever a change could alter the trajectory of a run for a given
(seed, configuration). Runs record it; ``verify`` refuses to compare across
model versions.
"""

from __future__ import annotations

MODEL_VERSION = "0.4.0-metastability"

# Bump when the RNG stream layout changes in a way that breaks replay.
RNG_LAYOUT_VERSION = 1

# Bump when the on-disk output schema changes.
OUTPUT_SCHEMA_VERSION = 1

# Bump when the configuration schema changes in a non-backward-compatible way.
CONFIG_SCHEMA_VERSION = 3
