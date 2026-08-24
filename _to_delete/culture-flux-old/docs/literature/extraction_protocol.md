# Literature Extraction Protocol

The matrix is only worth having if its cells mean the same thing in every row.
This is the procedure that makes that true.

## Rules

1. **One paper, one pass, full text.** Extract from the published version. If
   only a preprint is accessible, mark the row `(preprint)` and re-extract when
   the published version is available.
2. **Quote or cite, never paraphrase a number.** Any parameter value entered in
   the matrix carries a page or section reference. A number without a locator is
   not extracted; it is remembered, which is not the same thing.
3. **Absence is a finding.** If a paper does not report replicate counts, the
   cell reads `NOT REPORTED`, not `NYE` and not a guess. The two are different
   states and the difference matters for the validation strategy.
4. **Never fill a cell from another paper's description of this one.** Reviews
   compress, and the compression is exactly where the detail we need is lost.
5. **Record the disagreements.** Where two papers make incompatible modelling
   choices, that goes in "Differences from our proposed model" for both, and
   becomes a candidate sensitivity analysis rather than a decision to make by
   preference.

## Order

Read for structure before reading for numbers:

1. **P3 (Axelrod 1997)** first. It is the ancestor of the trait-vector
   representation this codebase provisionally uses, and its assumptions are the
   ones most likely to have been inherited without examination.
2. **P1 (Mesoudi 2018)** — closest to our dependent variable (maintenance of
   between-group variation under migration).
3. **P4 (Erten et al. 2018)** and **P6 (Kunst & Mesoudi 2025)** — the
   acculturation-orientation strand; P6 is the framing review, so it also serves
   as a map of the secondary corpus.
4. **P2 (Paolillo & Jager 2020)** and **P5 (Chuang et al. 2019)** — the network
   strand, which the model does not need until Phase 3 but whose representational
   choices constrain the agent design now.

## After each paper

- Fill its column in the matrix.
- Update any open question in the matrix's question table that it answers, and
  add any it raises.
- For every assumption in
  [../research/assumption_registry.md](../research/assumption_registry.md) that
  the paper bears on: update the `Evidence` field, and change `Status` from
  `provisional` to `supported` or `contradicted`. A paper that bears on an
  assumption without settling it updates `Evidence` and leaves `Status` alone.
- If a paper's mechanism is worth reusing, record it in the matrix — do not
  implement it in the same sitting. Reading and building in one pass is how a
  model acquires a mechanism no one can later justify.
