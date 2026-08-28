# Pilot Notes — first runs under an active transmission rule

**These are not results.** They are exploratory runs at a single parameter point
with one rule, one arrangement, one network assumption and small samples, made to
find out whether the instrument behaves sensibly and where its limits are. They
were run before any pre-registered analysis plan exists, so nothing here may be
reported as a finding, and every number below should be expected to move.

Model version 0.2.0-homophily. Rule: `axelrod_homophily` as specified in
`dynamics/homophily.py` (assumption A-016), batched update scheme (A-017),
uniform influence (A-009), well-mixed network (A-010).

---

## P-1 — The well-mixed assumption determines the long-run outcome

**Setup.** N = 500, F = 10, no migration, random initial population, run to
2,000 simulated years (12M interaction events). Q ∈ {2, 3, 5, 10}.

**Observation.** *Every* configuration converged to a single culture and froze
(`cultural_richness` = 1, `interactable_pair_fraction` = 0, zero further trait
changes). Only the time to convergence differed: Q = 2 froze within 200 years,
Q ≥ 3 took longer but still converged by 2,000.

At the 200-year horizon the picture looks entirely different — Q = 5 showed 379
distinct profiles and `interactable_pair_fraction` = 0.998, which reads like
sustained diversity but is a transient on its way to monoculture.

**Why this matters more than anything else here.** Under A-010, "multicultural
equilibrium" and "cultural fragmentation" are not merely hard to observe — they
appear not to be available at all as long-run outcomes. The only long-run state
is monoculture, and the only open question is *which* culture wins.

This escalates A-010 from "consequential" to **outcome-determining**, and it has
three immediate consequences:

1. **Any finite-horizon result must report `interactable_pair_fraction`.** A run
   that has not frozen is describing a transient, and a transient can be made to
   look like any outcome by choosing the horizon.
2. **RQ6 (hybridisation) and the multicultural/fragmentation regions of RQ7 are
   not answerable in Phase 2.** They need structured networks.
3. **H2 and H4 are largely untestable now.** H3 — which concerns the
   *probability* that an alternative culture becomes dominant — is the one
   hypothesis this configuration can speak to.

Structured local interaction is the standard route by which Axelrod-family models
sustain diversity. Whether that holds here is a Phase 3 question, and P-1 is the
reason Phase 3 is not optional.

---

## P-2 — Which culture wins

**Setup.** M = 0.30 held constant, N = 500, F = 10, Q = 5, D = 0.50, sources
`independent`, run to convergence (1,200–1,500 years). K ∈ {1, 3, 10}, 10 seeds
per condition. All 30 runs converged to a single culture.

Reported quantity: `mean_distance_from_founding_culture` at convergence. Because
the population is a monoculture, this is the distance of the *winning* profile
from the resident founding profile. 0.00 means the resident culture won; 0.50
means an incoming culture won outright; anything between means a recombinant
profile won.

| K | mean distance | sd | P(resident wins) | P(incoming wins) | P(recombinant wins) |
|---|---|---|---|---|---|
| 1 | 0.120 | 0.092 | 0.30 | 0.00 | 0.70 |
| 3 | 0.160 | 0.097 | 0.20 | 0.00 | 0.80 |
| 10 | 0.070 | 0.082 | 0.50 | 0.00 | 0.50 |

Compositional (null) baseline for every K: M·D = 0.150.

A separate 30-seed run of the K = 1 condition gave 0.1467 ± 0.0202 (se) —
statistically indistinguishable from the compositional baseline.

**Observations, all provisional.**

- **No incoming culture ever won outright, in any of the 30 runs.** The winner
  was always either the resident founding profile or a recombinant of it. At
  M = 0.30 with this rule, "incoming-culture dominance" did not occur.
- **The winner is usually a recombinant.** 50–80% of runs ended on a profile no
  founding population held. This is recombination across features, not
  innovation within one — the rule creates no new traits (tested), so novelty is
  bounded by what the founding profiles jointly contain.
- **The K trend is non-monotone and underpowered.** K = 10 shows the resident
  culture surviving most often (0.50) and the smallest mean distance. That is
  the direction **H3 (Fragmentation)** predicts and the opposite of **H2
  (Diversity)**. With 10 seeds and sd ≈ 0.09, the standard error on each mean is
  ≈ 0.03, so the K = 3 vs K = 10 gap is roughly 2 se. **This is a signal worth
  designing an experiment around, and nothing more.**

**Confounds not controlled in this pilot.** `arrangement` was fixed at
`independent`, so K also varied the realised distance *between* sources (A-006).
Sample sizes are far below what estimating a *probability* requires — H3 is about
a rate, and 10 runs cannot estimate one usefully. Only one value of M, D, F, Q,
N and interaction rate was examined.

---

## P-3 — The rule departs from the compositional baseline

At the 50-year horizon (N = 1000, F = 10, Q = 5, M = 0.30, K = 2, D = 0.50):
retention 0.78 under the rule versus exactly 0.85 under the null on the same
seed. Founder-subpopulation retention fell from exactly 1.000 to 0.780, and 144
distinct profiles existed where 3 founding profiles started.

This is the check the null exists for: the mechanism is doing something that
composition alone does not do. It says nothing yet about whether it is doing
something *right*.

---

## What these notes are for

They set the agenda for the next design rather than answering anything:

1. Phase 3 (structured networks) is now a prerequisite for most of the research
   questions, not an enhancement.
2. Any Phase 2 design must run to convergence and report freezing, or state
   plainly that it concerns transients.
3. H3 needs a replicate count sized to estimate a probability — hundreds per
   condition, not tens.
4. `arrangement` must be crossed with K, or the K effect is unattributable.
