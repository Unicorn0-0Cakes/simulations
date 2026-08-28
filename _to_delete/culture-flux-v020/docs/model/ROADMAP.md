# Roadmap

Phases, not dates. Each phase has an entry condition, because building the next
thing before its prerequisite exists is how a model acquires mechanisms nobody
can justify.

**The rule between phases: stop and review.** No phase begins automatically.

---

## Phase 0 — Scientific skeleton *(complete)*

Repository, registries, configuration architecture, determinism, culture
representation, distance and diversity metrics, population initialisation,
migration accounting, experiment and sweep abstractions, metrics registry, 180
invariant tests, CLI, README.

Deliberately absent: any cultural transmission.

---

## Phase 1 — Literature extraction *(SKIPPED — outstanding)*

> **This phase was skipped at the user's direction and Phase 2 was begun without
> it.** Everything below remains outstanding, and assumption A-016 records the
> cost: the model's transmission rule was chosen without the corpus behind it.
> Nothing derived from that rule can be defended until this is done.

**Entry condition:** the six core papers are accessible.

Fill the literature matrix from full texts, following
[../literature/extraction_protocol.md](../literature/extraction_protocol.md).
Answer L-Q1 to L-Q12. Update every assumption's `Evidence` and `Status`.

**Why this is next and not the transmission rule.** The transmission rule is the
single most consequential choice in the model and there are at least four
plausible candidates in the corpus. Choosing one before reading would mean either
picking arbitrarily or picking from memory — and a mechanism chosen from memory
is exactly the kind of thing that cannot be defended in review.

**Exit condition:** L-Q3 (which transmission rule, and why) has an answer with a
page reference, and L-Q6 (does any predecessor vary source count at fixed total
migration) has an answer, since it determines whether the project's central claim
is novel.

---

## Phase 2 — The first transmission rule *(largely complete; entry condition unmet)*

Done:
- `axelrod_homophily` implemented against `TransmissionRule`, registered as
  A-016 — **not** justified by an extracted source, which was the entry
  condition.
- Interaction on the well-mixed layer, with partner choice routed through the
  influence model so that layer is operative rather than decorative.
- 25 verification tests: conservation, absorbing-state properties, degenerate
  parameters, the no-innovation invariant, and fast-vs-exact update agreement.
- Comparison against the null on matched seeds, and a sweep configuration
  (`configs/sweeps/null_vs_homophily.json`) that runs both arms by construction.
- Pilot characterisation recorded in `docs/research/pilot_notes.md`.

Outstanding:
- **V-1 cannot be closed without Axelrod (1997).** See the validation strategy.
- ODD protocol document.
- A second transmission rule from a different family, without which no
  substantive result can be reported (A-016 sensitivity requirement).

**Exit condition, revised:** the model produces cultural change that is
demonstrably not compositional — **met** — *and* V-1 has a written outcome —
**not met, and blocked on Phase 1.**

---

## Phase 3 — Structure and influence

**Entry condition:** Phase 2 exited.

- Structured network layers: household, neighbourhood, workplace, friendship.
  Construction via NetworkX, simulation over NumPy adjacency.
- The first non-uniform influence model — network degree is the cheapest and
  breaks the share-equals-influence identity (A-009) at minimal cost.
- Spatial segregation, network modularity and cross-cultural interaction metrics
  become computable; three placeholders retire.
- Homophilous rewiring, and with it the possibility of enclave formation.

**Note:** three of the outcomes in the brief — enclaves, spatial segregation,
network modularity — are *impossible* before this phase. A null result on any of
them in Phase 2 is an artefact of A-010, not a finding, and must be reported as
such.

---

## Phase 4 — Demography

**Entry condition:** Phase 3 exited, and a reason to need generational turnover.

Births, deaths, ageing, vertical transmission, second-generation agents. The
`vital_events` RNG stream is already reserved. This is where "migration
generation" stops taking only the values 0 and 1, and where acculturation can be
observed on the timescale at which it is usually studied.

---

## Phase 5 — The experimental programme

**Entry condition:** all `required` sensitivity analyses from the assumption
registry have been run and the results are robust to A-001, A-003, A-006, A-013.

The full M × K × D × H × V design with adequate replication. Threshold-surface
detection per RQ7. Pre-registered analysis plan, frozen hypothesis registry
commit hash.

---

## Phase 6 — Presentation

**Entry condition:** results worth presenting.

A results explorer reading stored output, in the style of `cce.html` elsewhere in
this repository: real numbers from completed runs, embedded at build time, with
no second implementation of the model. The GUI never becomes the engine.

---

## Explicitly out of scope

Real ethnic, racial, religious or national populations; calibration against real
cities; policy claims; economics; politics; institutions; media systems; machine
learning. Several of these may become appropriate eventually. None is appropriate
before Phase 5, and some never are.
