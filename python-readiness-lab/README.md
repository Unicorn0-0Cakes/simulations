# Anthropic Python Readiness Lab

A simulation-driven training environment for building independent Python fluency under assessment conditions.

## Core rule

The repository may provide specifications, tests, review, and progressively smaller hints. The learner writes the implementation.

## Training modes

1. **Guided** — concepts, questions, and hints are allowed.
2. **Independent** — solve from the specification and tests without implementation help.
3. **Timed** — solve a variation in a fresh branch under assessment-like constraints.

## First milestone: Population Cap

Implement a population-control function that admits births without ever allowing the simulated population to exceed 100,000.

Start here:

```bash
cd python-readiness-lab
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
```

The initial test suite should fail because `admit_births` is intentionally unfinished. Read the specification in `src/readiness_lab/population.py`, implement it yourself, and make the tests pass.

## Assessment workflow

For each exercise:

1. Read the specification and restate the invariants.
2. Predict edge cases before coding.
3. Implement the smallest correct solution.
4. Run tests and diagnose failures.
5. Refactor only after correctness.
6. Record what you learned in `learning_log.md`.

## Mastery standard

A skill is considered mastered only when it can be reconstructed, explained, tested, and modified without AI-generated implementation code.
