"""Metrics: an extensible registry over diversity, persistence and structure."""

from __future__ import annotations

from . import cultural as _cultural  # noqa: F401  (registers the metrics)
from . import diversity
from .base import (
    METRIC_STATUSES,
    MetricContext,
    MetricSpec,
    available_metrics,
    compute_metrics,
    default_metric_names,
    get_metric,
    metric_table,
    register_metric,
)

__all__ = [
    "MetricContext",
    "MetricSpec",
    "register_metric",
    "get_metric",
    "available_metrics",
    "default_metric_names",
    "compute_metrics",
    "metric_table",
    "METRIC_STATUSES",
    "diversity",
]
