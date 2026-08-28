"""The three timescales must stay distinguishable."""

from __future__ import annotations

from _harness import approx, raises

from culture_flux.time import SimulationClock, TimeSpec


def test_steps_years_and_generations_are_not_interchangeable():
    clock = SimulationClock(TimeSpec(steps_per_year=12, years_per_generation=25.0), 50.0)
    assert clock.total_steps == 600
    assert approx(clock.year_of_step(600), 50.0)
    assert approx(clock.generation_of_step(600), 2.0)
    assert clock.year_of_step(600) != clock.generation_of_step(600)
    assert clock.total_steps != clock.total_years


def test_conversions_are_consistent_with_one_another():
    spec = TimeSpec(steps_per_year=4, years_per_generation=20.0)
    clock = SimulationClock(spec, 100.0)
    for step in (0, 7, 123, 400):
        assert approx(clock.generation_of_step(step), clock.year_of_step(step) / 20.0)
    assert clock.steps_in_years(10.0) == 40


def test_advancing_moves_all_three_clocks_together():
    clock = SimulationClock(TimeSpec(steps_per_year=12), 1.0)
    y0, g0 = clock.year, clock.generation
    clock.advance()
    assert clock.year > y0 and clock.generation > g0


def test_the_clock_refuses_to_run_past_the_end():
    clock = SimulationClock(TimeSpec(steps_per_year=1), 2.0)
    clock.advance(); clock.advance()
    assert clock.finished
    with raises(RuntimeError, "past the end"):
        clock.advance()


def test_the_final_step_is_always_a_measurement_step():
    clock = SimulationClock(TimeSpec(steps_per_year=12, measure_every_steps=7), 1.0)
    assert clock.is_measurement_step(clock.total_steps)


def test_the_step_equals_year_configuration_is_flagged():
    assert TimeSpec(steps_per_year=1).degenerate_step_year
    assert not TimeSpec(steps_per_year=12).degenerate_step_year


def test_degenerate_time_specifications_are_rejected():
    for kw in ({"steps_per_year": 0}, {"years_per_generation": 0.0}, {"measure_every_steps": 0}):
        with raises(ValueError):
            TimeSpec(**kw)
    with raises(ValueError, "total_years"):
        SimulationClock(TimeSpec(), 0.0)
