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

## Status: v0.4.0-metastability — the equilibria are plateaus

**Read this before using any result.** The model now has an active transmission
rule, `axelrod_homophily`. It is a rule *in the family* Axelrod (1997)
introduced; it is **not** a verified reproduction of that model, because the
paper has not been read. Every detail is specified in `dynamics/homophily.py` and
nowhere else. This is registered as **assumption A-016**, the least-supported
choice in the codebase, and the configuration layer warns on every run that uses
it.

The null rule remains and remains mandatory: retention under it is exactly
`1 − M·D̄`, so subtracting the null arm removes the compositional component from
any result. A rule that reproduces the plane is reproducing arithmetic.
`configs/sweeps/null_vs_homophily.json` runs both arms by construction.

**The most important thing found so far is a hazard, not a result.**

Two cultural configurations held ~30 distinct cultures for **1,600 simulated
years** — stable, with richness even drifting slightly upward — and then
collapsed to a single culture. Both seeds. Anyone reporting the year-1,000 state
of those runs would have reported a robust multicultural equilibrium and been
wrong.

That retracted this project's own previous headline. v0.3 reported a sharp
threshold in how much long-range interaction a city can sustain; extending the
runs showed it was the boundary at which collapse happened to fall inside the
observation window. There is no threshold — there is a plateau whose *duration*
depends on the parameters. Every connected configuration tested ends in
monoculture. Only exact disconnection sustains diversity, and that is true by
construction rather than by observation.

**"The metrics stopped moving" is not evidence of equilibrium.** Cultural
richness was flat while traits changed underneath it continuously. So absorption
is now tracked by trait changes, written into every manifest, and never reported
as certain under an active rule.

This generalises past the parameter that produced it: every outcome state in the
research brief — multicultural equilibrium, integration, fragmentation — and any
migration threshold could be a horizon artefact in exactly the same way.

Details in [docs/research/pilot_notes.md](docs/research/pilot_notes.md)
(P-4 to P-6). **L-Q13 is answered:** this is established territory — Klemm et al.
(2003), Flache & Macy (2011), Battiston et al. (2017) — so the network pilots are
replications, and are registered as validation target V-6 rather than as findings.

| | Declared | Implemented |
|---|---|---|
| Agent attributes | 19 | 5 |
| Transmission rules | 7 | 2 (null, homophily) |
| Sweep execution | — | parallel, resumable |
| Network layers | 5 | **5** |
| Influence models | — | 2 (uniform, network degree) |
| Cultural feature kinds | 3 | 1 (categorical) |
| Metrics | 27 | 25 |

Requesting anything unimplemented raises `NotImplementedError` with a pointer to
the roadmap — never a silent approximation. `culture-flux status` prints both
columns, and the counts are pinned in the test suite so the gap cannot drift.

**Nothing here has been empirically validated, and internal validation is
blocked.** No output has been compared to data from any real population, no
parameter is calibrated, and validation target V-1 cannot be closed without the
Axelrod paper. See
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

# run one, in parallel, resuming anything already complete
python3 -m culture_flux.cli sweep configs/sweeps/null_vs_homophily.json \
        --out results/batch-1 --workers 0

# the invariant suite (263 tests)
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
  networks/      household, neighbourhood, workplace, attention ties, citywide
  dynamics/      transmission rules (null + homophilous trait copying)
  metrics/       diversity indices, outcome metrics, registry
  experiment/    configuration, run, sweep
  io/            manifests, writers, run directories
  cli.py
configs/         smoke (json + yaml), three reference baselines, four sweeps
tests/           263 invariant tests + a dependency-free runner
results/         run output (gitignored)
notebooks/       analysis (empty — nothing worth analysing yet)
```

---

## Where the assumptions are

Thirty registered in
[docs/research/assumption_registry.md](docs/research/assumption_registry.md),
each with justification, implementation location, expected effect, uncertainty
and whether a sensitivity analysis is required before publication. The ones most
likely to change conclusions:

- **A-028** a finite horizon may report a plateau as an equilibrium — the hazard
  that retracted this project's own previous headline
- **A-019** how encounters divide across social settings — the weak-tie weight
  governs how long diversity lasts, and the default sits in the fast-collapse
  regime
- **A-016** the transmission rule was specified here, not extracted from any paper
- **A-027** connectivity, not locality, is what determines whether diversity
  persists — recorded as a finding that constrains interpretation
- **A-018** no innovation, error or drift: traits are only ever copied, so
  novelty is bounded by what the founding cultures jointly contain
- **A-001** all cultural features are interchangeable
- **A-006** how multiple source cultures are arranged in culture space
- **A-009** cultural influence is uniform across agents
- **A-013** F = 20 features of 5 traits, chosen for convenience

All nine outcomes named in the research brief are now *measurable* — spatial
segregation, network modularity and cross-cultural interaction rate are
implemented, and only the hybridisation index remains deliberately undefined
(A-012). But measurable is not reachable: under the default weak-tie weight,
multicultural equilibrium, fragmentation and enclaves do not occur, because the
city homogenises. Check `interactable_pair_fraction` and the weak-tie weight
before reading any null result as a finding.

---

## What comes next

**Phase 1 — literature extraction — was skipped and is still outstanding.** The
transmission rule was chosen without it, which is what A-016 records. Two things
are blocked on it: internal validation target V-1, and any defence of the rule.

Phase 3 is done and Phase 5's design has changed because of it:

- **Absorption status must be reported with every result**, and time-to-collapse
  is probably a more honest dependent variable than any end-state label.
- **The weak-tie weight belongs on the experimental axes** — it governs plateau
  duration. `configs/sweeps/weak_tie_threshold.json` is that design.
- **Convergence time grows steeply with population size.** A design must either
  run every cell to absorption or state its horizon and treat every result as
  conditional on it.
- **Read the secondary corpus (S1–S3) before further network work.** S3's title
  indicates the multiplex ground is already taken.

See [docs/model/ROADMAP.md](docs/model/ROADMAP.md).

---

## Citing the state of this work

Any output derived from this version must state: the model version; the seed and
configuration hash of every run behind it; which transmission rule was active and
that it is unvalidated against the literature (A-016); the network configuration
and in particular the weak-tie weight (A-019); whether the runs reached an
absorbing state or describe transients, with the `absorption` block from the
manifest; and that no empirical validation has been
performed. The rule must not be described as "Axelrod's model".

Reproducibility is a property of `(model_version, config_hash, seed)`. Runs
across different model versions are not comparable and `verify` refuses to
compare them.
