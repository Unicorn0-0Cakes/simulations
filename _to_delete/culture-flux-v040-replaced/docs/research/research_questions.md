# Research Question Registry

Provisional. Expect these to change as the literature matrix fills — in
particular, RQ2 and RQ3 are the project's claim to novelty and rest on open
question L-Q6 (whether any predecessor varies source count at fixed total
migration). If a predecessor does, the questions need reframing.

Each question records what would have to be measured to answer it and what would
make it unanswerable with the current instrument.

---

## RQ1 — Magnitude

**How does total incoming population share affect retention of an initially
dominant cultural configuration?**

- **Manipulated:** M ∈ [0, 0.6].
- **Measured:** `resident_trait_retention`, `min_trait_persistence`,
  `dominant_profile_share`, and their trajectories.
- **Answerable now?** Only compositionally. Under the null rule retention is
  exactly `1 − M·D̄`, which is arithmetic, not a finding. This is the baseline
  RQ1 must be reported against.
- **Blocked on:** a transmission rule.

---

## RQ2 — Source count

**Holding incoming population share constant, how does the number of source
cultures affect cultural transformation?**

- **Manipulated:** K ∈ {1, 2, 4, 8, 16} at fixed M. The four scenarios in the
  brief (30% as one culture, two, three, or ten) are the smallest version.
- **Measured:** retention, `cultural_fractionalization`,
  `cultural_effective_number`, `dominant_profile_share`.
- **Design requirement:** the resident population must be byte-identical across
  K conditions at a given seed. Guaranteed by the baseline-key mechanism and
  tested (`test_run.py::test_the_resident_population_is_byte_identical_across_migration_conditions`).
- **Confound to control:** K cannot be varied without also changing
  distance-between-sources unless `arrangement` is held fixed and reported —
  see A-006.
- **Blocked on:** a transmission rule. Under the null, K affects composition
  metrics only, in a way that is exactly predictable.

---

## RQ3 — Evenness

**How does source-population evenness interact with source count?**

- **Manipulated:** H (Pielou evenness) at fixed K and M, via
  `shares_for_target_evenness`. K = 4 at H ∈ {0.5, 0.75, 1.0} is the minimal grid.
- **Measured:** the same outcomes as RQ2, plus `incoming_source_evenness` as the
  realised manipulation check.
- **Note:** K and H are not independent at the extremes — as H → 0 at fixed K,
  the configuration approaches K = 1. The realised effective number of sources
  (`cultural_effective_number` over source labels) is the quantity to analyse
  against, not nominal K.
- **Blocked on:** a transmission rule.

---

## RQ4 — Distance

**How does cultural distance interact with migration magnitude?**

- **Manipulated:** D × M, fully crossed.
- **Measured:** retention surface over (M, D); curvature and interaction terms.
- **Answerable now?** Compositionally, the surface is the plane `1 − M·D`. A
  transmission rule that produces a plane is producing composition, not culture.
  This is a sharp, falsifiable check on any future mechanism.
- **Blocked on:** a transmission rule.

---

## RQ5 — Velocity

**Does migration velocity alter long-run outcomes when cumulative migration is
held constant?**

- **Manipulated:** V as `duration_years` at fixed total arrivals. Conservation is
  exact and tested.
- **Measured:** final-state metrics, and whether trajectories converge to the
  same endpoint.
- **Answerable now?** The null answer is proven: velocity has *no* effect on the
  endpoint, exactly (tested). Any velocity effect a future model shows is
  therefore attributable to the mechanism, not to accounting.
- **Blocked on:** a transmission rule and a decision on A-014 (arrival profiles).

---

## RQ6 — Hybridisation

**Under what parameter combinations do hybrid cultural configurations emerge?**

- **Blocked on:** two things, not one. A transmission rule (novel profiles cannot
  arise without one), *and* a defensible definition of "hybrid" — see A-012. The
  metric is registered and returns NaN until both are settled.
- **Likely form of the answer:** the distribution of distance-to-nearest-founding-
  culture, reported in full rather than reduced to an index.

---

## RQ7 — Transition regions

**Can statistically identifiable transition regions be detected between
resident-dominant, hybrid, multicultural, fragmented and incoming-dominant
states?**

This is the question the instrument exists for, and the one most easily answered
badly.

- **The trap:** naming five states and then classifying runs into them imposes
  the answer. Nothing in the engine names an outcome state; the metric suite is
  checked for this (`test_metrics.py::test_no_metric_encodes_an_outcome_CATEGORY_or_a_threshold`).
- **The intended approach:** treat each run as a point in metric space; look for
  multimodality, discontinuity in the response surface, and divergence between
  replicates near candidate boundaries. Regimes, if they exist, should be
  recoverable from the data. If they are not recoverable, that is the finding.
- **What would count as evidence of a transition:** a discontinuity or sharp
  gradient in an outcome as a parameter varies smoothly, with between-replicate
  variance peaking at the same location — the standard signature of a critical
  region. Hysteresis would require running the parameter up and down, which
  requires path-dependent dynamics, which requires transmission.
- **Blocked on:** a transmission rule, plus an analysis plan that does not yet
  exist.

---

## Null questions

Worth stating, because a negative answer to any of these is publishable and
several are currently the *most likely* outcomes:

- **RQ2-null.** Source count has no detectable effect on any outcome once M is
  held constant. (H3 in the hypothesis registry predicts an effect in the
  opposite direction to the intuitive one; the null is that neither happens.)
- **RQ7-null.** Outcomes vary smoothly with parameters and no transition regions
  exist. A smooth response surface is a real finding about cultural dynamics and
  should be reported as one, not treated as a failed search.
- **RQ-instrument-null.** Any apparent effect is an artefact of the culture
  representation (A-001, A-003, A-013) rather than of the dynamics. Guarding
  against this is what the `required` sensitivity tests are for.
