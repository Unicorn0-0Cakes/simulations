"""A two-function stand-in for the parts of pytest these tests use.

The suite is written as plain functions so it runs under pytest when pytest is
installed and under ``python tests/run_tests.py`` when it is not. Nothing in the
tests imports pytest, so there is exactly one version of each test rather than
two that can drift apart.
"""

from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def raises(exc_type, match: str | None = None):
    try:
        yield
    except exc_type as exc:
        if match is not None and match.lower() not in str(exc).lower():
            raise AssertionError(
                f"expected {exc_type.__name__} matching {match!r}, got: {exc}"
            ) from None
        return
    raise AssertionError(f"expected {exc_type.__name__}, nothing was raised")


def approx(value: float, expected: float, tol: float = 1e-9) -> bool:
    return abs(float(value) - float(expected)) <= tol
