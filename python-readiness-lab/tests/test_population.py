import pytest

from readiness_lab.population import MAX_POPULATION, admit_births


def test_admits_every_birth_when_capacity_is_available() -> None:
    assert admit_births(90_000, 5_000) == 5_000


def test_admits_only_remaining_capacity() -> None:
    assert admit_births(99_998, 10) == 2


def test_admits_no_births_at_population_cap() -> None:
    assert admit_births(MAX_POPULATION, 25) == 0


def test_zero_requested_births_returns_zero() -> None:
    assert admit_births(10_000, 0) == 0


@pytest.mark.parametrize("current_population", [-1, MAX_POPULATION + 1])
def test_rejects_invalid_current_population(current_population: int) -> None:
    with pytest.raises(ValueError):
        admit_births(current_population, 1)


def test_rejects_negative_requested_births() -> None:
    with pytest.raises(ValueError):
        admit_births(10_000, -1)
