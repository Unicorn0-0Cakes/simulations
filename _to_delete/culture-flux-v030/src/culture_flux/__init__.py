"""culture-flux: an experimental instrument for cultural dynamics under migration.

This package is a *scientific skeleton*, not a finished model. It provides
reproducible initialisation, culture representation, distance and diversity
measurement, migration composition, and a run/sweep abstraction. It does not
yet implement cultural transmission: the only dynamics rule available in
v0.1 is the explicit null (``dynamics.NullTransmission``), under which no
agent ever changes culture. Metric movement under the null is therefore
*compositional only* — it is the baseline against which any future
transmission rule must be compared.

See docs/model/ARCHITECTURE.md and README.md for current status.
"""

from __future__ import annotations

from .version import (
    CONFIG_SCHEMA_VERSION,
    MODEL_VERSION,
    OUTPUT_SCHEMA_VERSION,
    RNG_LAYOUT_VERSION,
)

__all__ = [
    "MODEL_VERSION",
    "RNG_LAYOUT_VERSION",
    "OUTPUT_SCHEMA_VERSION",
    "CONFIG_SCHEMA_VERSION",
]
