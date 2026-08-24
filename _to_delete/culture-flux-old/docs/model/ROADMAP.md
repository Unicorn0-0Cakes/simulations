# Roadmap

Phases, not dates. Each phase has an entry condition, because building the next
thing before its prerequisite exists is how a model acquires mechanisms nobody
can justify.

**The rule between phases: stop and review.** No phase begins automatically.

---

## Phase 0 — Scientific skeleton *(complete)*

Repository, registries, configuration architecture, determinism, culture
representation, distance and diversity metrics, population initialisation,
migration accounting, experiment and sweep abstractions, metrics registry, 172
invariant tests, CLI, README.

Deliberately absent: any cultural transmission.

---

## Phase 1 — Literature extraction *(next; no code)*

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

## Phase 2 — The first transmission rule

**Entry condition:** Phase 1 complete for at least P1 and P3.

- One rule, implemented against `TransmissionRule`, justified by an extracted
  source, registered as an assumption.
- Interaction on the well-mixed layer.
- Verification tests for the rule: conservation properties, behaviour at
  degenerate parameters, and a case with a known analytic answer if one exists.
- Internal validation target V-1 (Axelrod local convergence / global
  polarisation) attempted, and the result recorded whether or not it succeeds.
- Comparison against the null on the same seeds: the compositional baseline
  subtracted from every result.
- ODD protocol document, for framework-independent reporting.

**Exit condition:** the model produces cultural change that is demonstrably not
compositional, and V-1 either reproduces or has a written explanation of why not.

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
