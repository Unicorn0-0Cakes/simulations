# Validation Strategy

Three kinds of validation, kept separate because they answer different questions
and because conflating them is the standard way simulation work overclaims.

| Kind | Question | Status |
|---|---|---|
| Verification | Does the software do what the specification says? | **partially complete** |
| Internal validation | Does the model reproduce known qualitative behaviour of its predecessors when configured like them? | **blocked — see below** |
| Empirical validation | Do outputs correspond to real-world observations? | **not started, and not close** |

**The model has not been empirically validated. Nothing in this repository has
been compared against data from any real population.** No claim of empirical
validity may be made until the conditions in section 3 are met, and stating this
plainly in any output is a requirement, not a courtesy.

---

## 1. Verification — does the code implement the rules?

The only one of the three currently in progress.

### What is verified

244 invariant tests, all passing, run under warnings-as-errors. They test
scientifically meaningful properties, not that functions return without raising:

**Determinism and provenance**
- Identical (seed, configuration) produce identical draws in every named stream.
- Baseline streams are unaffected by the condition key — the property that makes
  "same M, different K" a controlled contrast.
- Condition streams do diverge across conditions.
- Consuming one stream does not shift another (so adding a mechanism later
  cannot silently change an existing one's draws).
- The string-to-seed mapping is pinned to a literal value, because Python's
  built-in `hash` is process-salted and would break replay.
- The run hash excludes wall-clock time, output paths and experiment names, and
  a run replayed from its own manifest reproduces its hash.

**Cultural distance — metric axioms**
- Identity: d(x, x) = 0 for every registered metric.
- Symmetry, boundedness in [0, 1], triangle inequality on random triples.
- Maximal difference gives exactly 1.
- Categorical traits are unordered: trait 0-vs-1 and 0-vs-4 are equidistant.
- Salience weighting reduces to unweighted Hamming at equal salience, and
  demonstrably changes the answer when saliences differ.

**Diversity indices — closed forms and invariances**
- Fractionalisation is 0 for one category and exactly 1 − 1/k for k even ones.
- Fractionalisation and Simpson concentration sum to 1.
- Entropy is 0 for one category, log k for k even, and maximised by evenness.
- Hill numbers recover richness (q=0), exp-Shannon (q=1) and inverse Simpson
  (q=2), equal k for k even categories at every order, and are non-increasing in q.
- Indices are invariant to category relabelling and reordering.
- Evenness separates H from K in both directions.

**Migration accounting — conservation**
- Largest-remainder allocation conserves the total exactly at every tested size,
  never returns a negative count, and errs by less than one agent per group.
- Both migration modes reach the requested *final* migrant share.
- Population is conserved: `n_final = n_initial + arrivals − displaced`.
- Replacement mode holds population exactly constant.
- Population never goes negative, including at 95% replacement.
- Velocity changes timing but not the arrival total.
- Source count changes composition but not the arrival total.

**Population initialisation**
- Same seed and baseline give byte-identical populations; different seeds do not.
- Zero noise gives a perfectly homogeneous city.
- Noise produces variation at the requested rate (±0.02 at N = 20,000) and always
  changes the trait when it fires — a redraw that could return the original
  would silently halve the effective rate.
- No trait index outside the schema is ever produced.
- Provenance and culture are separate arrays.

**Configuration**
- Every impossible configuration is rejected with a specific message: negative
  seed, empty population, M outside [0, 1), single-trait features, zero sources,
  unknown metric / rule / layer / distance name, mismatched share lists.
- Unknown keys are rejected rather than ignored — a silently-dropped typo looks
  exactly like a null result.
- Renaming an experiment or changing its output directory does not change its
  hash; changing any scientific parameter does.
- Migration settings do not change the baseline key; population settings do.
- The shipped JSON and YAML configurations hash identically.

**The null contract**
- No agent changes culture: trait-change count is 0, founder retention is exactly
  1.0, resident cultures remain a single distinct profile, and migrant cultures
  remain exactly their source profiles.
- Retention equals `1 − migrant_share · distance` to machine precision — the
  compositional arithmetic, verified.
- Velocity has exactly no effect on the endpoint under the null.
- Unimplemented transmission rules, network layers, feature kinds and arrival
  profiles raise `NotImplementedError` rather than silently approximating.

**The transmission rule (v0.2)**
- Copying never introduces a trait nobody held — the set of traits present at
  each feature can shrink but never grow. A rule with innovation or copying error
  would violate this, so an undeclared one could not be added silently.
- Agents with zero cultural overlap never influence each other, exactly.
- A homogeneous population is an absorbing state; a zero interaction rate changes
  nothing; a feature with zero transmission rate or full resistance never changes.
- Population size and trait admissibility are preserved under transmission.
- Influence weighting demonstrably biases whose culture spreads, so the influence
  layer is operative rather than decorative.
- The rule departs measurably from the compositional baseline, and changes
  founder culture, which the null never does.
- Batched and asynchronous update schemes agree within noise (weak evidence —
  see A-017) and obey the same invariants.
- The hybridisation placeholder still returns NaN even though novel profiles now
  exist and it would return a plausible number.

**Network structure (v0.3)**
- Group layers keep interaction local: sampled partners always share the focal
  agent's group, and an agent alone in a group returns itself rather than a
  stranger, so a rule cannot cross a boundary the network says is closed.
- Layer weights are honoured in proportion and normalised, so only ratios matter;
  a zero-weight layer is built and measurable but never sampled.
- A single-layer multiplex reproduces that layer's sampling exactly, draw for
  draw — so the citywide-only configuration is bit-identical to the pre-multiplex
  engine and every earlier result still stands.
- Rewiring preserves out-degree exactly, never creates a self-tie, and
  demonstrably raises cultural similarity across ties. With one candidate
  (no homophily) it demonstrably does not — the control condition is pinned.
- Theil's H is 0 when every unit mirrors the city, exactly 1 under complete
  separation, between the two under partial sorting, 0 rather than NaN with one
  category or one unit, and invariant to relabelling.
- Structure metrics return NaN, never 0, when the context has no network: "no
  spatial layer exists" and "there is no segregation" must not share a value.
- `network_degree` influence refuses to fall back to uniform when unbound or
  when no attention layer exists, because a silent fallback would be
  indistinguishable in the output from a run that meant to be uniform. At
  exponent 0 it reproduces the uniform null exactly.
- Configurations that name a structure-reading influence model without a
  friendship layer are rejected at validation.

**Guards against the model prejudging its own question**
- Every placeholder metric returns NaN, never a plausible zero, and every one
  states what it is blocked on.
- No metric name contains an outcome category or threshold word.
- The count of implemented versus declared agent attributes is pinned, so the gap
  between the agent the paper describes and the agent the code allocates cannot
  drift unnoticed.

### What is NOT verified

- **The parquet writer.** pyarrow is not installed in the environment where the
  suite was run, so only the CSV fallback path has been exercised. `write_table`'s
  parquet branch is untested.
- **Numerical behaviour at large N.** Everything is tested at N ≤ 20,000.
- **Sampled pairwise distance at scale.** The estimator is checked for accuracy at
  N = 400 against the exact value; its behaviour at N = 10⁶ is not.
- **Any transmission rule**, because none exists.
- **Cross-platform stability beyond the two environments tested.** The shipped
  smoke run produces an identical `run_hash` on Python 3.11 / NumPy 2.4.4 and on
  Python 3.10 / NumPy 2.2.6, and that value is pinned in the test suite
  (`test_the_shipped_smoke_run_matches_its_pinned_hash`). This is a *tripwire*,
  not a guarantee: NumPy's NEP 19 explicitly does **not** promise `Generator`
  stream stability across major versions, so a future NumPy could silently break
  replay of stored runs. The pin will catch it. Other architectures (ARM vs x86)
  have not been tested.

### Verification tasks outstanding

1. Install pyarrow and re-run; add a round-trip test (write parquet, read back,
   compare to the in-memory table).
2. Extend the cross-environment check to a second CPU architecture and to more
   than one configuration and seed.
3. Property-based testing (Hypothesis) for the allocation and distance functions,
   which are the two places where hand-chosen cases are most likely to miss an edge.
4. A performance benchmark, so that later optimisation can be shown not to have
   changed results — same seed, same hash, less time.

---

## 2. Internal validation — does it behave like its predecessors?

**Blocked, and blocked for a reason that a transmission rule did not unblock.**

v0.2 implements an Axelrod-*family* rule (A-016), so target V-1 is now
*runnable*. It is not *closeable*: closing it means comparing this model's
behaviour against what Axelrod (1997) reports, and the paper has not been read.
Comparing against a remembered summary would be worse than not comparing at all,
because it would produce a validation claim with nothing behind it.

**What has been measured instead** is this model's own behaviour, which is a
legitimate thing to know and is not validation. See
[pilot_notes.md](pilot_notes.md):

- Dependence on traits-per-feature: at Q = 2 the population freezes into
  monoculture within 200 simulated years; higher Q takes longer but reaches the
  same state by 2,000 years. Time to convergence rises with Q; the endpoint does
  not change.
- In a well-mixed population, every configuration tested converged to a single
  culture. Sustained diversity was never a long-run outcome.

Whether either matches what the source paper reports is unknown. **V-1 remains
open.** Its status must not be changed to "reproduced" or "failed" on the basis
of anything except the paper.

### Planned procedure

For each predecessor model, configure this instrument as closely as its
specification allows, and check whether the *qualitative* behaviour it reports is
reproduced. Qualitative, not quantitative: the aim is to detect a model that
cannot do what its ancestors do, not to match their numbers.

Candidate targets, each conditional on extraction confirming the paper actually
reports it:

| Target | Source | Behaviour to reproduce | Extraction dependency |
|---|---|---|---|
| V-1 | P3 Axelrod 1997 | Local convergence with global polarisation: stable multi-culture end states under local interaction, and dependence of the outcome on traits-per-feature. **Runnable in v0.2; not closeable without the paper.** Note that this model is well-mixed (A-010), so the *local* interaction the target concerns is not yet available — V-1 may need Phase 3 regardless of the reading. | L-Q2, L-Q3, L-Q10 |
| V-2 | P1 Mesoudi 2018 | Whatever relationship between migration rate and between-group variation the paper reports | L-Q5, L-Q10 |
| V-3 | P4 Erten et al. 2018 | Dependence of multicultural outcomes on acculturation orientations | L-Q9 |
| V-4 | P5 Chuang et al. 2019 | Enclave formation versus integration as a function of network structure | L-Q8 |
| V-5 | P2 Paolillo & Jager 2020 | Interaction between network formation and acculturation | L-Q8 |

V-1 is the priority: Axelrod's model is the direct ancestor of the current
representation, it is fully specified in its paper, and reproducing it would
verify the culture and distance layers against something external.

### Rules

- A target is written down **before** the attempt, with what counts as reproduced
  and what counts as failed.
- A failure to reproduce is recorded here, not quietly re-parameterised away.
- Configuring this model to match a predecessor may be impossible where
  representations differ. "Cannot be configured to match" is a legitimate and
  informative outcome; record why.

---

## 3. Empirical validation — does it correspond to reality?

**Not started, and not appropriate to start yet.**

### Preconditions

Before any comparison to real data:

1. A transmission mechanism exists and has passed internal validation.
2. All `required` sensitivity analyses in the assumption registry have been run,
   and the outcomes are shown not to be artefacts of A-001, A-003, A-006 or A-013.
3. A target observable is specified in advance — a measured quantity in real
   populations that this model produces an analogue of, named before any data is
   examined.
4. It is established what the model would have to produce to be **wrong**.

### The fitting prohibition

The model must not be tuned until its output resembles a real case. A model with
enough free parameters will fit anything, and a fitted model of this kind
predicts nothing — it has been made to agree, which is not evidence.

If parameters are ever estimated from data, that is a separate exercise with a
separate name (calibration), reported separately, with out-of-sample evaluation,
and never described as validation.

### The comparison problem

The deeper obstacle is measurement, not compute. This model's dependent variables
are cultural-profile distributions over synthetic features. No real dataset
measures that. Any empirical comparison requires either:

- an aggregate observable that both the model and the data can produce (e.g. a
  diversity index computed over survey-measured attitudes, with all the
  attendant questions about whether survey items correspond to model features), or
- a deliberate downward step to a coarser, more robust comparison — for example,
  whether an observed trajectory is monotone or non-monotone, which is a much
  weaker claim and correspondingly harder to explain away.

The second is more honest and should be attempted first. Deciding between them is
itself a research task and is not yet scheduled.

### What may be said in the meantime

Permitted: "conditional on the assumptions registered in
`assumption_registry.md`, the model produces X."

Not permitted: any statement about real cities, real migration, or real cultural
change; any statement implying the parameters correspond to measured quantities;
any use of the word "predicts" about the world rather than about the model.

---

## 4. Ongoing discipline

- Every substantive result is accompanied by the assumption IDs it depends on.
- Every published figure traces to a run directory and a run hash.
- The test suite runs before every result-generating sweep, and its pass count is
  recorded in the sweep manifest.
- A failed verification test blocks result generation. It is not triaged as a
  known issue.
