# Architecture

## Layer separation

The brief (section 15) requires model, experiment, metrics, visualisation, UI and
data export to stay separate. Here that separation is enforced by import
direction: **a layer may import from layers below it, never above.**

```
                 cli.py                    (thin: argument parsing, printing)
                    |
       experiment/  |  io/                 (config, run, sweep | manifests, writers)
                    |
                 metrics/                  (measurement -- reads state, never writes)
                    |
    dynamics/  influence/  networks/       (mechanism -- currently null/uniform/well-mixed)
                    |
              agents/  migration/          (population state, arrival accounting)
                    |
                  culture/                 (features, profiles, distance)
                    |
              rng.py    time.py            (determinism, timescales)
```

Consequences worth stating:

- **The engine has no GUI dependency and no plotting import.** A future UI reads
  stored run output; it cannot be inserted into the loop, because nothing in the
  loop knows it exists.
- **Metrics cannot mutate state.** They receive a `MetricContext` and return
  floats. A metric that needed to change the population would be a mechanism
  wearing a measurement's name.
- **`culture/` knows nothing about migration, agents or time.** So the distance
  and diversity code can be tested — and reused — without constructing a run.

## Struct-of-arrays

A `Population` is a set of parallel NumPy arrays plus an (N, F) culture matrix.
Agents are rows, not objects. See [STACK_DECISION.md](STACK_DECISION.md) for why.

The practical rule this imposes: any new agent attribute is a new array of length
N, and every mutation that changes N must change all of them together.
`Population.validate()` enforces that and runs after every mutation.

## Three separations the science depends on

These are load-bearing, not stylistic.

### 1. Provenance is not culture

`source_id` (immutable, bookkeeping) and the culture matrix (mutable) are
different arrays. No mechanism may branch on `source_id` except measurement.
Registered as A-002; tested.

The model therefore *cannot* express "people from group X behave differently
because they are from group X". If externally-imposed categorical treatment is
ever needed — discrimination, legal status — it must be added as an explicit
treatment layer that says so, not by letting origin leak into behaviour.

### 2. Population share is not cultural influence

`PopulationShare` is computed from counts by the metrics layer. `CulturalInfluence`
is produced by an `InfluenceModel`. v0.1 ships `UniformInfluence`, under which
they coincide — but as the output of a named, replaceable null model that appears
in the manifest, and with the gap between them measured every run
(`influence_share_divergence`). Registered as A-009.

### 3. Step is not year is not generation

`SimulationClock` exposes each conversion explicitly. Nothing in the codebase can
treat them as interchangeable, and a configuration where one step equals one year
emits a warning that is carried into every run manifest, because that is the
configuration in which a confusion would be undetectable.

## Determinism

Named RNG streams, seeded from `(seed, baseline_key, condition_key, stream_index,
layout_version)`. Two classes:

- **Baseline streams** (`culture_schema`, `resident_init`) ignore the condition
  key. Runs sharing a seed and a baseline key have byte-identical resident
  populations regardless of their migration settings.
- **Condition streams** may diverge.

This is what makes the project's central comparison valid. "30% arriving as one
culture" and "30% arriving as ten" must differ only in the incoming cultural
environment — not in the city they arrive into. Tested directly.

Streams for mechanisms that do not exist yet (`network_init`, `network_rewire`,
`vital_events`) are **already declared**. Adding those mechanisms later will
therefore not shift the draws consumed by any existing one, so v0.1 runs remain
reproducible under later versions of the code — provided `MODEL_VERSION` changes
only when behaviour does.

Undeclared stream names raise rather than silently creating a fresh unrecorded
stream.

## Declared versus implemented

The brief asks for a great deal that must not be built yet. Rather than omit it,
the codebase declares it, in machine-readable form, with an `implemented` flag:

| What | Where | Declared | Implemented |
|---|---|---|---|
| Agent attributes | `agents/attributes.py` | 19 | 5 |
| Transmission rules | `dynamics/base.py` | 7 | 1 (the null) |
| Network layers | `networks/base.py` | 5 | 1 (well-mixed) |
| Feature kinds | `culture/features.py` | 3 | 1 (categorical) |
| Arrival profiles | `migration/schedule.py` | 4 | 1 (uniform) |
| Metrics | `metrics/` | 21 | 16 |

Three properties follow, and each is deliberate:

1. **Requesting something unimplemented raises `NotImplementedError` with a
   pointer**, never a silent approximation. Asking for ordinal features gets an
   error, not categorical features pretending.
2. **`culture-flux status` prints both columns**, so the gap between the model
   the brief describes and the model the code runs is one command away.
3. **The counts are pinned in the test suite**, so the gap cannot drift unnoticed
   in either direction.

## The null as a permanent fixture

`NullTransmission` is not a placeholder awaiting deletion. It is the control arm.

Under it, every metric trajectory is *compositional* — it moves only because the
mix of people changed. That baseline is quantitatively exact and worth having:
retention under the null is `1 − M·D̄`, and the response surface over (M, D) is a
plane. A future transmission rule that produces a plane is reproducing arithmetic,
not modelling culture. This gives the project a sharp, falsifiable check that most
simulation work lacks.

## What a run produces

One directory per run:

```
<experiment>__<config_hash8>__seed<NNNN>/
    manifest.json           provenance, full config, realised geometry, accounting
    config.resolved.json    the configuration as run, canonically ordered
    timeseries.parquet      one row per measurement (not per step, never per agent)
    culture_distribution.*  one row per distinct cultural profile
    final_population.*      one row per agent (optional; the only output scaling with N)
    metrics_final.json      the last measurement
    run_hash.txt            the reproducibility digest
```

`run_hash` digests the final culture matrix, the provenance arrays and the full
metric series, and excludes timestamps, paths and machine names. `culture-flux
verify <dir>` re-runs from the stored manifest and compares.

## Extension points

| To add | Implement | Register | Then |
|---|---|---|---|
| A transmission rule | `TransmissionRule` | `register_transmission_rule` | add to `DECLARED_RULES` if absent |
| An influence model | `InfluenceModel` | `register_influence_model` | — |
| A distance metric | a function | `@register_distance` | state whether it is a true metric |
| A metric | a function of `MetricContext` | `@register_metric` | `status="placeholder"` until computable |
| A network layer | `NetworkLayer` | add to `IMPLEMENTED_LAYERS` | — |

Every one of these requires an assumption-registry entry if it embodies a choice
the literature has not settled — which, at this stage, all of them do.
