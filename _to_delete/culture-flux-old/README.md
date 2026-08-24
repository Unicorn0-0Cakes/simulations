# culture-flux

An experimental instrument for studying cultural dynamics under migration.

> **How does source-population diversity alter cultural transformation
> thresholds under migration in an initially culturally homogeneous urban
> population?**

The specific question: holding total migration constant, does changing the
*number*, *relative size*, *cultural distance* and *distribution* of incoming
populations produce systematically different long-run outcomes? Thirty per cent
arriving as one culture and thirty per cent arriving as ten are the same
migration magnitude and a different cultural information environment. Whether
that difference matters is what this instrument exists to find out.

---

## Status: v0.1.0-skeleton — scientific skeleton, no cultural dynamics

**There is no cultural transmission mechanism in this version.** Nobody changes
their culture. Every metric trajectory a v0.1 run produces is *compositional* —
it moves only because the mix of people changed.

That is the intended state, and the null model is worth having on its own:
retention under it is exactly `1 − M·D̄`, and the response surface over
(magnitude, distance) is a plane. A future transmission rule that reproduces a
plane is reproducing arithmetic, not modelling culture. `NullTransmission` stays
permanently as the control arm of every experiment.

| | Declared | Implemented |
|---|---|---|
| Agent attributes | 19 | 5 |
| Transmission rules | 7 | 1 (the null) |
| Network layers | 5 | 1 (well-mixed) |
| Cultural feature kinds | 3 | 1 (categorical) |
| Metrics | 21 | 16 |

Requesting anything unimplemented raises `NotImplementedError` with a pointer to
the roadmap — never a silent approximation. `culture-flux status` prints both
columns, and the counts are pinned in the test suite so the gap cannot drift.

**Nothing here has been empirically validated.** No output has been compared to
data from any real population, and no parameter is calibrated to anything. See
[docs/research/validation_strategy.md](docs/research/validation_strategy.md).

---

## What it will not assume

The instrument is built so that it *cannot* quietly encode the conclusions people
usually bring to this topic:

- **Population share is not cultural influence.** They are separate objects in
  the code. v0.1 ships `UniformInfluence`, under which they coincide — as the
  explicit output of a named, replaceable null model, with the gap between them
  measured every run.
- **Origin is not culture.** `source_id` is immutable bookkeeping; the culture
  matrix is separate and mutable. No mechanism may branch on origin except
  measurement. Residents and migrants are initialised through the same code path.
- **No outcome is preferred, and no threshold is asserted.** No metric is named
  for an outcome category — there is no `assimilation_index` — and a test
  enforces it. Transformation thresholds, if they exist, are to be detected from
  simulation behaviour, not written into the instrument.
- **Cultures are synthetic.** Culture A (resident) and Cultures B, C, D…
  (incoming). No real ethnic, racial, religious or national population is
  modelled.

---

## Quick start

```bash
cd culture-flux

# what exists and what does not
python3 -m culture_flux.cli status                    # from ./src, or install first

# the registered metrics, with placeholders marked
python3 -m culture_flux.cli metrics

# validate a configuration without running it
python3 -m culture_flux.cli validate configs/smoke.json

# a smoke run
python3 -m culture_flux.cli run configs/smoke.json --seed 1

# re-run a stored run and compare its hash
python3 -m culture_flux.cli verify results/smoke__<hash>__seed0001

# expand a sweep without spending compute on it
python3 -m culture_flux.cli sweep configs/sweeps/source_count_at_fixed_M.json --dry-run

# the invariant suite (172 tests)
python3 tests/run_tests.py        # no dependencies
pytest                            # if pytest is installed
```

Install (optional — everything above runs from `src/` without it):

```bash
pip install -e ".[storage,yaml,dev]"
culture-flux status
```

Requires Python 3.10+ and NumPy. Everything else is optional; the engine falls
back to CSV when pyarrow is absent and says so in the manifest.

---

## The central contrast

`configs/sweeps/source_count_at_fixed_M.json` is the research question in its
smallest form: total incoming share fixed at 0.30, source count varying over
{1, 2, 3, 10}. Identical migration magnitude, different cultural environment.

For that contrast to be valid, the cities being compared must be identical. They
are, by construction: RNG streams for the pre-migration population are seeded
from the run seed and a *baseline key* that excludes all migration settings, so
two runs sharing a seed have byte-identical resident populations whatever their
migration configuration. This is tested directly, not assumed.

---

## Repository

```
docs/
  literature/    literature matrix (bibliographic details verified, content NOT YET EXTRACTED)
                 extraction protocol
  research/      assumption registry (15 entries), research questions (7),
                 hypotheses (4 + 7 nulls), validation strategy, outcome typology
  model/         architecture, stack decision, config schema, data outputs, roadmap
src/culture_flux/
  rng.py         named deterministic streams
  time.py        step / year / generation, kept distinct
  culture/       feature schema, profiles, distance registry
  agents/        struct-of-arrays population, attribute registry
  migration/     source composition and geometry, arrival accounting
  influence/     cultural influence, separate from population share
  networks/      multiplex layer abstractions
  dynamics/      transmission rules (the null only)
  metrics/       diversity indices, outcome metrics, registry
  experiment/    configuration, run, sweep
  io/            manifests, writers, run directories
  cli.py
configs/         smoke (json + yaml), reference baseline, two sweeps
tests/           172 invariant tests + a dependency-free runner
results/         run output (gitignored)
notebooks/       analysis (empty — nothing worth analysing yet)
```

---

## Where the assumptions are

Fifteen registered in
[docs/research/assumption_registry.md](docs/research/assumption_registry.md),
each with justification, implementation location, expected effect, uncertainty
and whether a sensitivity analysis is required before publication. The ones most
likely to change conclusions:

- **A-001** all cultural features are interchangeable
- **A-006** how multiple source cultures are arranged in culture space
- **A-009** cultural influence is uniform across agents
- **A-010** the city is a single well-mixed pool
- **A-013** F = 20 features of 5 traits, chosen for convenience

Three of the outcomes named in the research brief — enclaves, spatial
segregation, network modularity — are *impossible* under A-010. A null result on
any of them before structured networks exist is an artefact, not a finding.

---

## What comes next

Phase 1 is literature extraction, and it involves no code. The transmission rule
is the single most consequential choice in the model, there are at least four
plausible candidates in the core corpus, and choosing one before reading would
mean choosing it arbitrarily. See [docs/model/ROADMAP.md](docs/model/ROADMAP.md).

---

## Citing the state of this work

Any output derived from this version must state: the model version, the seed and
configuration hash of every run behind it, that no transmission mechanism was
active, and that no empirical validation has been performed.

Reproducibility is a property of `(model_version, config_hash, seed)`. Runs
across different model versions are not comparable and `verify` refuses to
compare them.
