"""Diversity indices over a categorical distribution.

Pure functions on a share vector or a label array. No knowledge of culture,
agents or migration -- so the same code measures source-population diversity,
cultural-profile diversity, and anything else categorical, and a test of the
index is a test of every use of it.

Several indices are provided deliberately. Fractionalisation (1 - sum p^2) is the
conventional choice in the migration literature, but it is only one member of the
Hill family and it weights common categories heavily. Reporting the family means
a result that holds only under one weighting is visible as such.

Hill numbers unify them:

    q = 0  richness (count of categories, ignores abundance)
    q = 1  exp(Shannon) (weights categories by frequency)
    q = 2  1 / sum p^2  = inverse Simpson (weights common categories)

and each is an "effective number of categories", so they are directly comparable
to one another in a way that raw index values are not.
"""

from __future__ import annotations

import numpy as np


def shares_from_labels(labels: np.ndarray) -> np.ndarray:
    """Proportions of each distinct label. Empty input gives an empty vector."""
    arr = np.asarray(labels).ravel()
    if arr.size == 0:
        return np.zeros(0, dtype=np.float64)
    _, counts = np.unique(arr, return_counts=True)
    return counts.astype(np.float64) / float(arr.size)


def _clean(p: np.ndarray) -> np.ndarray:
    arr = np.asarray(p, dtype=np.float64).ravel()
    if arr.size == 0:
        return arr
    if (arr < -1e-12).any():
        raise ValueError("shares must be non-negative")
    arr = np.clip(arr, 0.0, None)
    total = arr.sum()
    if total <= 0:
        raise ValueError("shares must not sum to zero")
    return arr / total


def richness(p: np.ndarray) -> float:
    """Number of categories present. Hill number at q = 0."""
    arr = _clean(p) if np.asarray(p).size else np.zeros(0)
    return float((arr > 0).sum())


def fractionalization(p: np.ndarray) -> float:
    """F = 1 - sum(p_i^2). Probability two randomly drawn members differ.

    Bounded in [0, 1). Equals 0 for a single category and 1 - 1/k for k even
    categories, so it is bounded above by the number of categories -- which is
    exactly why it should not be read as "amount of diversity" without K in view.
    """
    arr = _clean(p)
    return float(1.0 - np.square(arr).sum())


def simpson(p: np.ndarray) -> float:
    """Simpson concentration, sum(p_i^2). The complement of fractionalisation."""
    arr = _clean(p)
    return float(np.square(arr).sum())


def hhi(p: np.ndarray) -> float:
    """Herfindahl-Hirschman concentration index. Identical to Simpson on shares."""
    return simpson(p)


def shannon_entropy(p: np.ndarray, base: float = np.e) -> float:
    """Shannon entropy. Zero for one category; log(k) for k even categories."""
    arr = _clean(p)
    nz = arr[arr > 0]
    h = float(-(nz * np.log(nz)).sum())
    return h if base == np.e else h / float(np.log(base))


def normalised_entropy(p: np.ndarray) -> float:
    """Shannon entropy divided by log(k). Identical to Pielou evenness."""
    arr = _clean(p)
    k = int((arr > 0).sum())
    if k <= 1:
        return 1.0 if k == 1 else float("nan")
    return shannon_entropy(arr) / float(np.log(k))


def pielou_evenness(p: np.ndarray) -> float:
    """Evenness of the distribution, independent of how many categories exist."""
    return normalised_entropy(p)


def hill_number(p: np.ndarray, q: float = 1.0) -> float:
    """Effective number of categories of order q."""
    arr = _clean(p)
    nz = arr[arr > 0]
    if nz.size == 0:
        return float("nan")
    if abs(q - 1.0) < 1e-12:
        return float(np.exp(shannon_entropy(nz)))
    return float(np.power(np.power(nz, q).sum(), 1.0 / (1.0 - q)))


def effective_number(p: np.ndarray) -> float:
    """Inverse Simpson, 1 / sum(p^2). Hill number at q = 2."""
    return hill_number(p, q=2.0)


def max_share(p: np.ndarray) -> float:
    """Share of the largest category. A dominance measure, not a diversity one."""
    arr = _clean(p)
    return float(arr.max())
