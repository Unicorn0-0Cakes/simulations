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

| Term | Provisional signature | Measurable now? |
|---|---|---|
| Resident persistence | High `resident_trait_retention`; `dominant_profile_share` high and located at the founding profile | Partly — the location of the dominant profile is not yet reported |
| Assimilation | Incoming agents' cultures converge on the founding profile; low `cultural_fractionalization`; high retention | No — requires transmission |
| Integration | Sustained moderate `cultural_fractionalization`; retention neither near 1 nor near 0; no single dominant profile | No |
| Incoming dominance | `dominant_profile_share` high at a non-founding profile; low retention | No |
| Hybridisation | Mass at profiles far from *every* founding profile | No — and undefined (A-012) |
| Multicultural equilibrium | Several profiles at stable non-trivial shares, persisting over time | No — "stable" requires dynamics to stabilise |
| Fragmentation | High `cultural_richness`, low `dominant_profile_share`, high effective number | No |
| Enclave | Cultural clustering *within network or spatial structure* rather than in the population as a whole | No — requires structured network layers |
| Phase transition | Discontinuity in an outcome under a smooth parameter change, with between-replicate variance peaking at the same location | No — requires dynamics and large replicate counts |

Every "No" is a statement about v0.1, not a permanent limitation.

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
