"""Time model.

Three timescales are kept distinct and are NOT interchangeable:

``step``
    The unit of simulation advance. Everything the engine does happens on a step
    boundary. Its duration in simulated time is a modelling choice.

``year``
    Simulated calendar time. Derived from steps via ``steps_per_year``.
    Migration magnitude and velocity are expressed in years, because that is how
    migration data is reported.

``generation``
    Demographic turnover time. Derived from years via ``years_per_generation``.
    Vertical cultural transmission and "migration generation" (1st, 1.5, 2nd)
    are generational, not annual, phenomena.

Different processes may legitimately run on different clocks -- interaction
every step, migration every year, reproduction every generation, measurement on
its own cadence. ``SimulationClock`` exposes each conversion explicitly so that
no part of the codebase can quietly assume 1 step == 1 year == 1 generation.

A deliberate guard: ``steps_per_year == 1`` is permitted but recorded, because
it is the configuration in which a step/year confusion would be undetectable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSpec:
    """Declarative description of the three timescales."""

    steps_per_year: int = 12
    years_per_generation: float = 25.0
    measure_every_steps: int = 12

    def __post_init__(self) -> None:
        if self.steps_per_year < 1:
            raise ValueError("steps_per_year must be >= 1")
        if self.years_per_generation <= 0:
            raise ValueError("years_per_generation must be > 0")
        if self.measure_every_steps < 1:
            raise ValueError("measure_every_steps must be >= 1")

    @property
    def degenerate_step_year(self) -> bool:
        """True when one step equals one year (a confusion-prone configuration)."""
        return self.steps_per_year == 1


class SimulationClock:
    """Advances steps and converts between the three timescales."""

    def __init__(self, spec: TimeSpec, total_years: float) -> None:
        if total_years <= 0:
            raise ValueError("total_years must be > 0")
        self.spec = spec
        self.total_years = float(total_years)
        self.total_steps = int(round(total_years * spec.steps_per_year))
        if self.total_steps < 1:
            raise ValueError("configuration yields fewer than one simulation step")
        self.step = 0

    # -- conversions -------------------------------------------------------
    def year_of_step(self, step: int) -> float:
        return step / self.spec.steps_per_year

    def generation_of_step(self, step: int) -> float:
        return self.year_of_step(step) / self.spec.years_per_generation

    def steps_in_years(self, years: float) -> int:
        return int(round(years * self.spec.steps_per_year))

    # -- current position --------------------------------------------------
    @property
    def year(self) -> float:
        return self.year_of_step(self.step)

    @property
    def generation(self) -> float:
        return self.generation_of_step(self.step)

    @property
    def finished(self) -> bool:
        return self.step >= self.total_steps

    def advance(self) -> int:
        if self.finished:
            raise RuntimeError("clock advanced past the end of the run")
        self.step += 1
        return self.step

    def is_measurement_step(self, step: int | None = None) -> bool:
        s = self.step if step is None else step
        return s % self.spec.measure_every_steps == 0 or s == self.total_steps

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SimulationClock(step={self.step}/{self.total_steps}, "
            f"year={self.year:.3f}, generation={self.generation:.4f})"
        )
