# Pilot Notes — first runs under an active transmission rule

**These are not results.** They are exploratory runs at a single parameter point
with one rule, one arrangement, one network assumption and small samples, made to
find out whether the instrument behaves sensibly and where its limits are. They
were run before any pre-registered analysis plan exists, so nothing here may be
reported as a finding, and every number below should be expected to move.

Model versions 0.2.0-homophily (P-1 to P-3) and 0.3.0-structure (P-4, P-5). Rule: `axelrod_homophily` as specified in
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

## P-4 — Structure alone does not sustain diversity; *disconnection* does

**Setup.** N = 500, F = 10, Q = 5, no migration, 2,000 simulated years, homophily
rule. Five network configurations, all with local interaction.

| Configuration | Distinct cultures at 2,000y | Segregation | Frozen |
|---|---|---|---|
| neighbourhood only — 10 islands of 50 | **10** | 1.00 | yes |
| islands + 0.1% citywide encounters | 11 | 0.99 | not yet |
| islands + 1% citywide encounters | **1** | 0.00 | yes |
| islands + 5% citywide encounters | **1** | 0.00 | yes |
| household + neighbourhood + workplace, no citywide layer at all | **1** | 0.00 | yes |

Two things here, and the second is the important one.

**The machinery can produce local convergence with global variation.** Ten
disconnected neighbourhoods froze into exactly ten cultures, one per
neighbourhood, at maximal segregation. So the earlier monoculture result was not
a defect in the rule.

**But locality is not what does it — disconnection is.** The last row is the
finding. Households, neighbourhoods and workplaces are all local, all small, and
contain no citywide layer whatsoever; every encounter is with someone who shares
a container. It still collapsed to a single culture, because randomly assigned
overlapping memberships stitch the city into one connected component. A person
links their household to their workplace, which links to someone else's
household, and so on. Locality without disconnection is not locality at all, for
these purposes.

This is a caution against reading "we added realistic social structure" as "we
enabled cultural diversity". A structurally rich city can be, and here is,
topologically indistinguishable from a well-mixed one.

---

## P-5 — A sharp transition, in a structural parameter

**Setup.** As P-4, islands of 50 with a varying share of encounters drawn from the
weak citywide layer. Five seeds per point, 2,000 years.

| Citywide encounter share | Mean distinct cultures | sd | P(monoculture) | Segregation |
|---|---|---|---|---|
| 0.0000 | 10.0 | 0.00 | 0.00 | 1.00 |
| 0.0005 | 10.0 | 0.00 | 0.00 | 1.00 |
| 0.0010 | 11.2 | 1.10 | 0.00 | 0.98 |
| 0.0020 | 10.6 | 2.61 | 0.00 | 0.96 |
| **0.0030** | **4.2** | **3.96** | **0.20** | **0.70** |
| 0.0050 | 1.2 | 0.45 | 0.80 | 0.19 |
| 0.0075 | 1.0 | 0.00 | 1.00 | 0.00 |
| 0.0100 | 1.0 | 0.00 | 1.00 | 0.00 |

**The transition is sharp**, between roughly 0.2% and 0.75% of encounters, and
**between-replicate variance peaks inside it** (sd 3.96 at w = 0.003, against 0
at both extremes). Rising variance at the boundary is the signature RQ7 names as
evidence of a critical region, and here it appears without anyone looking for it.

**Fewer than one encounter in a hundred being with a stranger is enough to
homogenise the entire city.** Below that, ten cultures persist indefinitely.

### Why this is the most consequential thing found so far

The project exists to ask whether a *migration* threshold exists. What the
instrument has produced instead is a sharp threshold in a **structural**
parameter that nobody proposed studying, set by default at 0.05 — an order of
magnitude above the transition, deep in the homogenising regime.

Three consequences:

1. **Any migration threshold this model reports is conditional on where the
   weak-tie weight was set**, and that parameter is a placeholder with no
   evidence behind it (A-019). A threshold surface in M could move, vanish or
   appear entirely as a function of a number chosen for convenience.
2. **The weak-tie weight must be a swept variable, not a fixed default**, in any
   design that claims to locate a threshold. It joins M, K, D, H and V as an
   experimental variable.
3. **The default configuration sits in the regime where diversity cannot
   survive**, which is exactly the regime least able to distinguish the outcomes
   the project cares about.

### What this is not

It is not novel. A small number of long-range links collapsing local structure is
the small-world effect, and Axelrod-family models are the classic setting for it;
this is very likely a known result being rediscovered. That is recorded as open
question **L-Q13** and must be checked against the corpus before any of it is
written up as a contribution.

It is also not established. One value of N, one neighbourhood size, one Q, one F,
one rule, five seeds. The threshold's *location* is a percolation-like quantity
that should be expected to move with N and with the number of neighbourhoods, and
that scaling has not been tested at all.

---

## What these notes are for

They set the agenda for the next design rather than answering anything:

1. **The weak-tie weight is an experimental variable, not a setting.** It has a
   sharp transition in it and the default sits on the wrong side. Sweep it
   alongside M, K, D, H and V, or every result is conditional on an unexamined
   number.
2. **Test how the transition scales with N and neighbourhood count** before
   trusting any threshold location.
3. Any design must run to convergence and report `interactable_pair_fraction`,
   or state plainly that it concerns transients.
4. H3 needs a replicate count sized to estimate a probability — hundreds per
   condition, not tens.
5. `arrangement` must be crossed with K, or the K effect is unattributable.
6. Answer L-Q13 before presenting P-5 as anything but a replication.
