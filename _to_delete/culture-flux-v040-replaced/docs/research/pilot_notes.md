# Pilot Notes — first runs under an active transmission rule

**These are not results.** They are exploratory runs at a single parameter point
with one rule, one arrangement, one network assumption and small samples, made to
find out whether the instrument behaves sensibly and where its limits are. They
were run before any pre-registered analysis plan exists, so nothing here may be
reported as a finding, and every number below should be expected to move.

Model versions 0.2.0-homophily (P-1 to P-3), 0.3.0-structure (P-4, P-5) and
0.4.0-metastability (P-6). Rule: `axelrod_homophily` as specified in
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

## P-5 — A sharp transition, in a structural parameter — **PARTIALLY RETRACTED**

> **Retraction notice (P-6).** The "transition" reported below is not a
> transition. Extending the runs shows it is a difference in *time to collapse*:
> at N = 1000 the same weak-tie weight that produced monoculture at N = 500
> sustains ~30 cultures for 1,800 years and then collapses anyway. What P-5
> located was the boundary at which the collapse happens to fall inside a
> 2,000-year observation window at N = 500 — a property of the horizon, not of
> the model. Read P-5 for the data and P-6 for what it means. The variance peak
> is real and is now better explained as variance in collapse *timing*.

### The original entry, kept as recorded

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

### What survives the retraction

1. **The weak-tie weight must still be a swept variable, not a fixed default.**
   It strongly affects how long diversity lasts, even if it does not set a true
   threshold. It joins M, K, D, H and V as an experimental variable.
2. **The default of 0.05 still sits in the fast-collapse regime.**
3. The variance peak is real; P-6 reinterprets it as variance in *when* the
   collapse happens rather than *whether* it happens.

### What this is not

**It is not novel, and this has now been checked.** L-Q13 is answered: an
established literature exists on exactly this. Klemm, Eguíluz, Toral & San Miguel
(*Phys. Rev. E* 67, 026120, 2003) and Flache & Macy (*J. Math. Sociology* 35,
146–176, 2011, "Small Worlds and Cultural Polarization") are directly on the
point, and Battiston, Nicosia, Latora & San Miguel (*Sci. Rep.* 7, 1809, 2017,
"Layered social influence promotes multiculturality in the Axelrod model")
indicates the multiplex work of v0.3 is also traversing known ground. Citations
verified; contents not extracted.

**So P-5 is a replication.** Its value changes accordingly, and improves in one
respect: an instrument that independently reproduces a known transition is an
instrument with some claim to working. It is registered as internal-validation
target **V-6** — *not* as reproduced, because the papers have not been read and
neither the published direction nor the published threshold has been compared.

It is also not established. One value of N, one neighbourhood size, one Q, one F,
one rule, five seeds. The threshold's *location* is a percolation-like quantity
that should be expected to move with N and with the number of neighbourhoods, and
that scaling has not been tested at all.

---

## P-6 — The transition was an observation horizon, and the plateau is metastable

**Setup.** Scaling test. Neighbourhoods of 50 throughout; population varied so
the *number* of neighbourhoods varies. The prediction under test was that the
threshold should scale as 1/N, i.e. that `w x N` — long-range links per
neighbourhood — should be the invariant.

**It is not.** At `w x N = 1`, N = 250 gave 80% monoculture and N = 500 gave none.
At `w x N = 5`, N = 500 gave monoculture in every run while N = 1000 gave 30.7
distinct cultures and **not one run had frozen**.

That last clause is the whole finding. Every N = 1000 run was still changing when
it ended. So the comparison was never between "sustains diversity" and "does
not" — it was between runs that had finished and runs that had not.

**Extending them settles it.** N = 1000, w = 0.005 (the weight that produced
monoculture at N = 500), run to 6,000 years, two seeds:

```
year:  0   200  400  600  800  1000 1200 1400 1600 1800 2000 2200 2400 2600 2800 3000
seed1: 999  30   28   29   30   36   35   34   35   39   23   13    4    2    1    1
seed2: 1000 28   27   30   28   34   35   38   35   38   26   13    4    4    2    1
```

Both seeds hold ~30 cultures for **1,600 years**, with richness drifting gently
*upward* — and then collapse to a single culture within about 800 years. Both end
frozen, `interactable_pair_fraction` = 0.

### What this means

**There is no threshold in the weak-tie weight.** There is a plateau whose
*duration* depends on it, and on N. Every configuration tested that leaves the
city connected ends in monoculture; the parameters govern how long that takes.
P-1, P-4 and P-6 now agree, and P-5's apparent threshold was the boundary at
which collapse fell inside the observation window.

**The plateau is metastable, and it is extremely convincing while it lasts.**
1,600 years of stable — even slightly rising — cultural richness is exactly what
a multicultural equilibrium would look like. It is not one. Anyone reporting the
year-1000 state of these runs would report a robust multicultural equilibrium and
be wrong.

**"The metrics stopped moving" is not evidence of equilibrium.** Richness was
flat while traits changed underneath it continuously. This is why the absorption
report added in v0.4 tracks *trait changes*, not metric stability, and why it
never reports `confidence: certain` for an active rule.

**The only structurally guaranteed persistent diversity is exact disconnection.**
At w = 0 the neighbourhoods cannot interact at all, so per-neighbourhood
convergence is a true absorbing state — by construction rather than by
observation. Everything else is a plateau of some length.

### Consequences for the research programme

This generalises well beyond the weak-tie parameter, and it is the most
important caution the project has produced:

1. **Any "cultural equilibrium" this model reports at a finite horizon may be a
   plateau.** That includes every outcome state in the brief: multicultural
   equilibrium, fragmentation, integration. A migration threshold could be a
   horizon artefact in exactly the same way.
2. **Runs must be reported with their absorption status.** The manifest now
   carries `absorption.absorbed`, `quiescent_years` and a confidence that is
   never "certain" under an active rule.
3. **Time-to-collapse is a dependent variable in its own right**, and possibly a
   more honest one than any end-state classification. "How long does diversity
   last under condition X" is answerable; "does diversity persist" may not be.
4. **Convergence time grows steeply with N.** A design must either run every cell
   to absorption — expensive and superlinear — or report a horizon and treat
   every result as conditional on it. There is no cheap third option.

### Caveats

Two seeds at the extended horizon. One neighbourhood size, one Q, one F, one
rule, no migration. The *shape* of the result — long plateau, then collapse — is
consistent across every seed examined, but its timing is not characterised.

---

## What these notes are for

They set the agenda for the next design rather than answering anything:

1. **Report absorption status with every result.** `absorption.absorbed`,
   `quiescent_years`, and the fact that confidence is never certain under an
   active rule. An unabsorbed run is a transient whatever its metrics say.
2. **Treat time-to-collapse as a dependent variable**, not just end state. It may
   be the only thing about equilibrium this model can honestly report.
3. **The weak-tie weight is an experimental variable, not a setting** — it
   governs plateau duration even though it sets no threshold.
4. **Budget for superlinear convergence time in N.** Either run every cell to
   absorption or state the horizon and treat every result as conditional on it.
5. H3 needs a replicate count sized to estimate a probability — hundreds per
   condition, not tens.
6. `arrangement` must be crossed with K, or the K effect is unattributable.
7. **L-Q13 is answered: P-5/P-6 are replications.** Read S1–S3 before designing
   further network work; S3's title indicates the multiplex ground is also taken.
