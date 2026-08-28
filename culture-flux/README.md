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

## Status: v0.5.0-two-rules — the mechanism matters more than the migration

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

The model now has two transmission rules from different families, and they
**disagree about the direction of the migration effect**.

Same city, same arrivals, same seeds, M = 0.30, compositional baseline 0.850:

| mechanism | resident-culture retention |
|---|---|
| null (composition only) | 0.850 |
| homophilous copying | 0.73 — residents pulled towards the migrants |
| conformist transmission | 0.9999 — migrants almost entirely assimilated |

A single-rule study here would have been confidently wrong in whichever direction
its author happened to pick. Assumption **A-016** required two rules before any
result; this is what that requirement was for.

**And the project's central question returned a null.** Holding total migration
constant and splitting the incoming population into ten cultures instead of one
made no detectable difference to retention under *either* rule: +0.011 ± 0.032
(z = 0.35) and +0.0000 (z = 0.88), across 240 runs at 20 seeds per cell. That is
H0-1, and it contradicts H1, H2 and H3 alike. Still one point in a
six-dimensional parameter space — but it is a designed comparison, not a pilot.

**The mechanism moved the outcome far more than the source diversity did.** If
that survives a proper design, the research questions are aimed at the wrong
variable.

Two hazards found along the way, both of which retracted earlier headlines of
this project:

* **A plateau can look exactly like an equilibrium** (A-028). Two runs held ~30
  cultures for 1,600 years, richness drifting slightly *upward*, then collapsed.
  That retracted v0.3's "sharp threshold", which turned out to be the boundary at
  which collapse fell inside the observation window.
* **Above a drift rate of ~10⁻³ the homophily rule is indistinguishable from
  drift alone** (P-8). A first attempt at the comparison above ran there and was
  measuring the noise floor. Every result must state its regime.

Details in [docs/research/pilot_notes.md](docs/research/pilot_notes.md) (P-1 to
P-9). **L-Q13 is answered:** the network results are established territory — Klemm
et al. (2003), Flache & Macy (2011), Battiston et al. (2017) — so those pilots are
replications registered as validation target V-6. **S5 is the priority read:** its
title points the opposite way from what pilot P-7 observed about drift.

| | Declared | Implemented |
|---|---|---|
| Agent attributes | 19 | 5 |
| Transmission rules | 7 | 3 (null, homophily, conformist) |
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

## The instrument page

`culture-flux.html` is a self-contained results explorer — real output from the
stored runs, embedded at build time, with no second implementation of the model
and no network access. Open it in any browser. Regenerate it from stored output
with:

```bash
python3 -m culture_flux.cli sweep configs/sweeps/rq2_three_arm.json \
        --out results/rq2 --workers 0
python3 analysis/export_web_data.py --batch results/rq2
```

See `USER_MANUAL.md` for how to read it, and `methods.html` for the full
specification, parameters and validation status.

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

# the invariant suite (297 tests)
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

`configs/sweeps/rq2_three_arm.json` is the research question as a design: total
incoming share fixed at 0.30, source count varying over {1, 2, 4, 10}, run under
all three mechanisms on matched seeds.

For that contrast to be valid, three things must be held identical, and RNG
streams are seeded in three nested tiers to guarantee each:

| tier | held constant across | guarantees |
|---|---|---|
| **baseline key** | any change to migration, network or dynamics | a byte-identical pre-migration city |
| **scenario key** | any change to network or dynamics | byte-identical arrivals: same source cultures, sizes, schedule |
| **condition key** | — | free to diverge |

So "same M, different K" compares cultural environments rather than two different
cities, and "same migration, different rule" compares mechanisms rather than two
different migrations. Both are tested directly, not assumed.

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
  dynamics/      transmission rules (null, homophilous copying, conformist) + drift
  metrics/       diversity indices, outcome metrics, registry
  experiment/    configuration, run, sweep
  io/            manifests, writers, run directories
  cli.py
configs/         smoke (json + yaml), four reference baselines, five sweeps
tests/           297 invariant tests + a dependency-free runner
results/         run output (gitignored)
notebooks/       analysis (empty — nothing worth analysing yet)
```

---

## Where the assumptions are

Thirty-one registered in
[docs/research/assumption_registry.md](docs/research/assumption_registry.md),
each with justification, implementation location, expected effect, uncertainty
and whether a sensitivity analysis is required before publication. The ones most
likely to change conclusions:

- **A-016** the transmission rule was specified without the literature — and
  pilot P-9 shows the rule choice dominates every migration variable
- **A-028** a finite horizon may report a plateau as an equilibrium — the hazard
  that retracted this project's own previous headline
- **A-018** no innovation, now parameterised: the drift rate decides whether
  monoculture is inevitable, and above ~10⁻³ it decides everything
- **A-019** how encounters divide across social settings — the weak-tie weight
  governs how long diversity lasts, and the default sits in the fast-collapse
  regime
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
