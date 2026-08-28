# Outcome Typology — a vocabulary, not a classifier

The project brief names outcomes the instrument should be able to investigate:
resident-culture persistence, assimilation, integration, incoming-culture
dominance, hybridisation, multicultural equilibrium, fragmentation, enclaves,
and phase transitions between them.

**None of these is implemented, and none should be.** This file exists to keep
them out of the code while keeping them available for thinking.

## Why they are not in the engine

A name like "assimilation" bundles a measurement with a threshold and a
direction. Encode it and the model stops being able to discover where the
boundary is, because the boundary was supplied. RQ7 asks whether these regions
exist and where their edges lie; an instrument that sorts runs into them cannot
answer that question, only restate its own definitions.

So the engine measures continuous quantities with descriptive names, and the
`test_no_metric_encodes_an_outcome_CATEGORY_or_a_threshold` test enforces it.

## The vocabulary, and its measurable signature

Each row says what the state would look like *in metric space* — a hypothesis
about a region, to be checked, not a rule to be applied. The signatures are
provisional and several are not yet measurable.

**Updated for v0.2.** With an active rule the "measurable now?" column changed
less than expected, because pilot P-1 found that the well-mixed assumption drives
every configuration to monoculture. Several outcomes are now measurable in
principle and unreachable in practice, which is a different and more useful kind
of "no".

| Term | Provisional signature | Measurable now? |
|---|---|---|
| Resident persistence | High `resident_trait_retention`; `dominant_profile_share` high and located at the founding profile | Partly — the location of the dominant profile is not yet reported |
| Assimilation | Incoming agents' cultures converge on the founding profile; low `cultural_fractionalization`; high retention | **Yes** — and observed: pilot P-2 ended on the resident profile in 17–50% of runs |
| Integration | Sustained moderate `cultural_fractionalization`; retention neither near 1 nor near 0; no single dominant profile | Measurable, **unreachable** under A-010 — appears only as a transient |
| Incoming dominance | `dominant_profile_share` high at an incoming founding profile; low retention | **Yes**, and did not occur in any of 30 pilot runs at M = 0.30 |
| Hybridisation | Mass at profiles far from *every* founding profile | Distribution now reported; the **index** stays NaN, undefined (A-012). Pilot P-2: 50–80% of converged runs ended on a recombinant, which is why the naive index is useless |
| Multicultural equilibrium | Several profiles at stable non-trivial shares, persisting over time | Measurable, **unreachable** under A-010 |
| Fragmentation | High `cultural_richness`, low `dominant_profile_share`, high effective number | Measurable, **unreachable** under A-010 |
| Enclave | Cultural clustering *within network or spatial structure* rather than in the population as a whole | No — requires structured network layers |
| Phase transition | Discontinuity in an outcome under a smooth parameter change, with between-replicate variance peaking at the same location | Not yet — needs replicate counts sized to estimate rates, and persistent states to transition between |

Every "No" and every "unreachable" is a statement about the current assumptions — chiefly A-010 — not a permanent limitation. `interactable_pair_fraction` is the metric that distinguishes "this outcome persisted" from "this outcome was passed through on the way to monoculture", and must be reported alongside any of these.

## How classification should eventually work

When there is something to classify:

1. Run the design. Each run is a point in metric space.
2. Look for structure in that space *without* imposing labels — clustering,
   mixture models, or simply plotting.
3. Only then ask whether the clusters correspond to the vocabulary above, and say
   plainly where they do not.
4. Report boundaries with uncertainty, as fitted quantities.

If the metric space turns out to be unimodal and smooth, the honest conclusion is
that these categories are ways of talking rather than distinct states of the
system — which would itself be a substantive finding about a widely used
vocabulary, and one worth publishing.
