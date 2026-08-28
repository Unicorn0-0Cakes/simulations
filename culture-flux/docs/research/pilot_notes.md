# Pilot Notes — first runs under an active transmission rule

**These are not results.** They are exploratory runs at a single parameter point
with one rule, one arrangement, one network assumption and small samples, made to
find out whether the instrument behaves sensibly and where its limits are. They
were run before any pre-registered analysis plan exists, so nothing here may be
reported as a finding, and every number below should be expected to move.

Model versions 0.2.0-homophily (P-1 to P-3), 0.3.0-structure (P-4, P-5) 0.4.0-metastability (P-6)
0.5.0-two-rules (P-7 to P-10). Rule: `axelrod_homophily` as specified in
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

## P-7 — Monoculture was an artefact of an unexamined default

**Setup.** N = 500, ten neighbourhoods of 50, weak-tie weight 0.05 — the
*fast-collapse* regime in which P-1, P-4, P-5 and P-6 all produced monoculture.
3,000 years. The only thing varied is `drift_rate`: the per-agent-per-step
probability of one feature changing to a random different trait. Two seeds each.

Cultural richness by year:

| drift | 0 | 250 | 500 | 750 | 1000 | 1250 | 1500 | 1750 | 2000 | 2250 | 2500 | 2750 | 3000 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 500 | 16 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10⁻⁵ | 500 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |
| 10⁻⁴ | 500 | 22 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |
| **10⁻³** | 500 | 52 | 24 | **109** | 14 | 12 | 9 | 16 | 12 | 20 | 19 | 22 | **66** |
| 10⁻² | 500 | 321 | 329 | 400 | 385 | 365 | 381 | 372 | 330 | 356 | 433 | 402 | 370 |

Final state, averaged over seeds:

| drift | richness | segregation | dominant share |
|---|---|---|---|
| 0 | 1.0 | 0.00 | 1.000 |
| 10⁻⁵ | 1.0 | 0.00 | 1.000 |
| 10⁻⁴ | 1.5 | 0.14 | 0.998 |
| 10⁻³ | 48.5 | 0.36 | 0.186 |
| 10⁻² | 401.5 | 0.40 | 0.041 |

### What this does to the previous pilots

**"Every connected configuration ends in monoculture" was conditional on
`drift_rate = 0`, and nobody had examined that default.** It was inherited from
the rule family (A-018) rather than chosen. Somewhere between 10⁻⁴ and 10⁻³ the
system stops collapsing at all and settles into a sustained, fluctuating state
with real spatial segregation.

P-1, P-4, P-5 and P-6 are not wrong — they are results about a copying-only
world. But the headline they supported ("monoculture is the only long-run
outcome") is now known to be a statement about one corner of the parameter space,
and a corner chosen by default.

**P-6's hazard survives intact and gets sharper.** At drift ≥ 10⁻³ there is no
absorbing state at all, so "has it converged?" is not even the right question:
the right question is whether the *distribution* is stationary. And the
trajectory at 10⁻³ swings hard — 24, then 109, then 14, then 66 — so a single
snapshot of a single run is close to meaningless there. Time-averaging over a
stationary window is required, and no analysis code does that yet.

### What it does not establish

Where the transition sits. Two seeds, one N, one neighbourhood size, one
weak-tie weight, one rule. The interaction between drift and the weak-tie weight
is unexamined and is likely to matter: both govern the same balance between
mixing and regeneration.

### And it is prior art again — with a direction that may contradict this

**Klemm, Eguíluz, Toral & San Miguel (2003), "Global culture: A noise-induced
transition in finite systems", *Phys. Rev. E* 67, 045101(R)** — a companion to
S1, same group, same year. Citation verified; contents not extracted.

The title is worth reading twice. It says noise *induces global culture* — that
is, drives the system towards monoculture. What P-7 observes is drift
*sustaining* diversity, which is the opposite direction. Three possibilities, and
no way to choose between them without reading the paper:

1. The title compresses a non-monotone result (plausible: a small amount of noise
   can behave very differently from a lot).
2. Their noise enters differently from this drift.
3. This implementation is wrong.

**That is exactly why the paper must be read rather than cited from its title**,
and it is the sharpest illustration so far of why Phase 1 was not optional.
Registered as validation target **V-7**, explicitly unresolved.

---

## P-8 — There is a drift rate above which transmission stops mattering

**Why this exists.** A first attempt at the three-arm comparison (P-9) was run at
`drift_rate = 10⁻³`, the rate P-7 identified as sustaining diversity. It produced
a striking result: retention 0.278 under the homophily rule, far below the
compositional baseline of 0.850. Before writing that up, one control:

**Setup.** N = 500, M = 0.30, D = 0.50, 1,500 years, tail-averaged over years
1,000–1,500. Three seeds. Random-culture expectation at Q = 5 is retention 0.200;
the compositional baseline is 0.850.

| condition | retention | richness |
|---|---|---|
| drift only, no interaction at all | 0.304 | 714.0 |
| homophily + drift 10⁻³ | **0.278** | 36.8 |
| homophily + drift 10⁻⁴ | 0.765 | 2.0 |
| homophily, no drift | 0.900 | 1.0 |

**The homophily arm at 10⁻³ is indistinguishable from drift alone** — in fact
marginally below it. That arm was measuring noise, not cultural transmission, and
the parameter choice for the comparison was wrong. The first attempt at P-9 is
therefore discarded rather than reported.

### What this does to P-7

P-7 said drift above ~10⁻³ "sustains diversity". True, and now qualified:
transmission is still doing something at that rate — richness 36.8 against 714
without it, so it suppresses drift-generated variety twentyfold — but the
*founding cultures* are not retained above chance. The diversity at 10⁻³ is
churn, not cultural persistence.

So there are two regimes, and the boundary between them is somewhere between
10⁻⁴ and 10⁻³ at these settings:

* **transmission-dominated** (drift ≤ 10⁻⁴): the founding cultures still organise
  the population, and questions about their fate are answerable.
* **drift-dominated** (drift ≥ 10⁻³): culture is noise, and any measured "effect"
  of migration, source count or network structure is measuring the noise floor.

**Any result must state which regime it is in**, and any parameter sweep that
crosses the boundary is reporting two different models. This is the second time a
default has silently decided an outcome (A-018 was the first) and it is the
strongest argument yet that the registry should be consulted before the
experiment, not after.

---

## P-9 — The first answer to RQ2, and it is a null

**Setup.** The three-arm design A-016 requires: null, homophilous copying, and
conformist transmission (conformity = 3, 5 models), on matched seeds, in the
transmission-dominated regime (drift = 10⁻⁴). M = 0.30 held constant,
D = 0.50, N = 500 in ten neighbourhoods, weak-tie weight 0.05, K ∈ {1, 4, 10},
four seeds each, 1,500 years, tail-averaged over years 1,000–1,500.

All three arms share a seed, a baseline key and a **scenario key**, so they face
a byte-identical city and byte-identical arrivals. Only the mechanism differs.

| rule | K | retention | sd | richness | dominant share | segregation |
|---|---|---|---|---|---|---|
| null | 1 | 0.8501 | 0.0000 | 2.0 | 0.700 | 0.008 |
| null | 4 | 0.8501 | 0.0000 | 5.0 | 0.700 | 0.030 |
| null | 10 | 0.8501 | 0.0000 | 11.0 | 0.700 | 0.057 |
| homophily | 1 | 0.7299 | 0.1135 | 2.0 | 0.919 | 0.168 |
| homophily | 4 | 0.6748 | 0.2211 | 1.6 | 0.947 | 0.130 |
| homophily | 10 | 0.7648 | 0.0435 | 1.8 | 0.933 | 0.137 |
| conformist | 1 | 0.9999 | 0.0000 | 1.8 | 0.999 | 0.158 |
| conformist | 4 | 0.9999 | 0.0000 | 1.7 | 0.999 | 0.153 |
| conformist | 10 | 0.9999 | 0.0000 | 1.8 | 0.999 | 0.172 |

### Finding 1 — the two rules disagree about direction

Against the compositional baseline of 0.850:

* **Homophilous copying erodes the resident culture** (≈0.73). Migrants pull
  residents partway towards them.
* **Conformist transmission assimilates the migrants almost completely** (0.9999).
  The majority wins, decisively and with zero variance across seeds.

Same city, same arrivals, same seeds, opposite outcomes. **No claim about whether
migration erodes or preserves resident culture can be made from one transmission
rule.** A-016 required two rules before any result; this is what that requirement
was for, and a single-rule study here would have been confidently wrong in
whichever direction its author happened to pick.

### Finding 2 — source count has no detectable effect

The project's central question, at this one parameter point:

| rule | retention at K=10 minus K=1 | se | z |
|---|---|---|---|
| null | +0.0000 | 0.0000 | — (arithmetic) |
| homophily | +0.0349 | 0.0608 | +0.57 |
| conformist | −0.0000 | 0.0000 | −0.06 |

Nothing. Under both rules, holding total migration constant, splitting the
incoming population into ten cultures instead of one made no detectable
difference to how much of the resident culture survived.

That is **H0-1**, and it contradicts H1, H2 *and* H3 — all three predict a K
effect, in various directions. A null here is a substantive outcome, not a failed
search.

### What this is not

Four seeds. One value each of M, D, drift, conformity, network configuration,
arrangement and neighbourhood size. The homophily arm at K = 4 has a standard
deviation of 0.22 against 0.04 at K = 10, which hints at bimodality — some runs
the residents hold, some they do not — and a mean is the wrong summary for a
bimodal outcome. H3 in particular is about a *rate*, and four runs cannot
estimate one.

So: a pilot pointing at a design, not a result. But it is the first time the
instrument has been asked its own central question and returned an answer, and
the answer was "no effect, under either mechanism".

---

## P-10 — The design, executed

**No longer a pilot.** P-9's four-seed comparison specified a design; this is that
design run at full replication. 240 runs, 0 failures, 8,786 s of compute:
three mechanisms × K ∈ {1, 2, 4, 10} × 20 seeds, all sharing a baseline and
scenario key so every arm faces a byte-identical city and byte-identical arrivals.
Configuration: `configs/sweeps/rq2_three_arm.json`. Compositional baseline 0.850.

| mechanism | K=1 | K=2 | K=4 | K=10 | sd |
|---|---|---|---|---|---|
| null (control) | 0.8501 | 0.8501 | 0.8501 | 0.8501 | 0.0000 |
| homophilous copying | 0.6959 | 0.7364 | 0.7892 | 0.7070 | ~0.11 |
| conformist | 0.9999 | 0.9999 | 0.9999 | 0.9999 | ~0.0001 |

**Effect of K on retention (K=10 minus K=1):**

| mechanism | difference | se | z |
|---|---|---|---|
| null | +0.0000 | 0.0000 | — (arithmetic) |
| homophilous copying | +0.0111 | 0.0322 | 0.35 |
| conformist | +0.0000 | 0.0000 | 0.88 |

### Both P-9 findings hold at five times the replication

1. **The mechanisms disagree about direction, by a lot.** Homophily lands 0.15
   *below* the compositional baseline; conformist transmission lands 0.15 *above* it,
   at near-total assimilation of the arrivals. The gap between the two mechanisms is
   0.30 — an order of magnitude larger than anything the migration variables did.

2. **Source count does nothing.** Under both active rules the K effect is well inside
   noise. The homophily arm wobbles non-monotonically across K (0.696, 0.736, 0.789,
   0.707), which is what a null looks like at sd ≈ 0.11 and se ≈ 0.03 — not a trend.

**H0-1 is not rejected**, now with twenty seeds per cell. H1, H2 and H3 each predict a
K effect and none appears.

### The control arm's own behaviour is worth noticing

The null arm returns 0.8501 with a standard deviation of **exactly zero** across all
80 of its runs. That is the compositional arithmetic reproducing itself perfectly, and
it is the sharpest available demonstration that the seeds, the arrivals and the city
really are matched: if anything differed between conditions, this number would move.

### What still limits it

One value each of M, D, drift rate, conformity exponent, network configuration,
arrangement and neighbourhood size. The conformist arm's variance is so small
(sd ≈ 0.0001) that its parameter is almost certainly saturating the outcome — A-030
says as much, and a saturated arm cannot show an effect of anything else. The
fragmentation hypothesis remains untestable here: no incoming culture became dominant
in any of the 240 runs.

So the honest summary is that the *migration* variables are not where the action is in
this model, and the thing that decides the outcome — the transmission mechanism — is
the one thing the project has no evidence about.

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
8. **Read S5 before anything else.** Its title points the opposite way from P-7's
   observation, so either the result or the implementation is not what it seems.
9. **Cross drift with the weak-tie weight.** Both govern the balance between
   mixing and regeneration and neither has been examined against the other.
10. **Time-average over a stationary window** wherever drift is non-zero. Single
    snapshots swing by a factor of ten there.
11. **State the regime.** Every result must say whether it is transmission- or
    drift-dominated (P-8). A sweep crossing that boundary reports two models.
12. **Report every arm.** The two rules disagree about the *direction* of the
    migration effect (P-9), so a single-rule result is not a result.
13. **Report distributions, not means, for the homophily arm.** Its variance
    across seeds is large and possibly bimodal.
