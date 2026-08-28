# Hypothesis Registry

Four substantive hypotheses, stated as the project brief gives them, with their
nulls. **None is endorsed.** H1 and H2 predict opposite signs; H3 predicts the
opposite of H2 for the same manipulation. That is intentional — the design is
worth running precisely because competent people expect different answers.

Each entry records the prediction, the mechanism that would generate it, what
would falsify it, and what would make the test invalid.

---

## H1 — Concentration

**A single large incoming cultural population produces greater transformation
than the same total arriving as several smaller ones, because cultural
reinforcement is concentrated.**

- **Prediction.** At fixed M and D̄, retention increases with K.
- **Mechanism.** A large co-cultural group sustains its own culture internally:
  members reinforce each other, so their culture resists absorption and persists
  as a viable alternative to the resident configuration.
- **Falsified by.** Retention flat or decreasing in K.
- **Test invalid if.** `arrangement` is not held fixed — otherwise increasing K
  also changes distance-between-sources, and the effect is unattributable (A-006).
- **Depends on.** Any mechanism with frequency-dependent reinforcement. Under the
  null rule H1 is untestable, since retention is `1 − M·D̄` regardless of K.

---

## H2 — Diversity

**Multiple source cultures produce greater transformation, because the resident
culture's conformity advantage weakens and cultural variation increases.**

- **Prediction.** At fixed M and D̄, retention decreases with K.
- **Mechanism.** Under conformist transmission, the resident culture's advantage
  comes from being the single largest configuration. Fragmenting the incoming
  population does not reduce the total non-resident share, but it increases the
  variety of alternatives an agent encounters, weakening the conformity
  asymmetry that protects the resident culture.
- **Falsified by.** Retention flat or increasing in K.
- **Test invalid if.** Higher K is confounded with higher realised D̄ — check the
  realised distance-to-resident distribution, not the requested one.
- **Depends on.** A frequency-dependent (conformist) transmission rule.
  Distinguishing H1 from H2 will likely require varying conformity strength,
  since they plausibly hold in different regions of the same parameter.

---

## H3 — Fragmentation

**Increasing source diversity reduces the probability that any alternative
configuration becomes dominant, thereby increasing persistence of the original
culture.**

- **Prediction.** At fixed M, the probability that a *non-resident* configuration
  becomes dominant falls as K rises — even if mean retention also falls.
- **Mechanism.** Dominance requires a coalition. Ten cultures at 3% each have no
  route to majority; one at 30% does.
- **Note on the relationship to H2.** H2 and H3 are *not* mutually exclusive and
  must not be tested as if they were. H2 predicts lower mean retention at high K;
  H3 predicts a lower rate of incoming-culture dominance at high K. Both can
  hold: the resident culture erodes but nothing replaces it — a fragmentation
  outcome, which is one of the states RQ7 is looking for. Testing them together
  requires reporting the full outcome *distribution* across replicates, not the
  mean.
- **Falsified by.** Dominance-by-an-incoming-culture rates flat or rising in K.
- **Depends on.** Enough replicates per condition to estimate a rate, not a mean.
  This is the hypothesis with the largest compute requirement.

---

## H4 — Emergent synthesis

**Under sufficiently high cross-cultural interaction, multiple source cultures
increase the probability of a novel hybrid equilibrium rather than dominance by
any founding culture.**

- **Prediction.** At high K and high interaction, the modal outcome is a
  configuration far from every founding profile.
- **Mechanism.** Trait-level recombination across many sources explores regions
  of culture space no founding population occupies.
- **Falsified by.** Outcomes remaining near a founding profile regardless of K
  and interaction rate.
- **Blocked on.** A-012 — "novel hybrid" is currently undefined, and the two
  candidate definitions would give different answers. **H4 cannot be tested until
  that is settled**, and settling it after seeing results would be
  indistinguishable from choosing the definition that gives an answer.
- **Also depends on.** A transmission rule permitting trait-level recombination.
  Rules that copy whole profiles cannot produce H4 by construction, so a negative
  result under such a rule is uninformative.

---

## Null hypotheses

| ID | Statement |
|---|---|
| H0-1 | Source count K has no effect on cultural retention at fixed M, D̄ and arrangement. |
| H0-2 | Source evenness H has no effect at fixed K and M. |
| H0-3 | Cultural distance D and magnitude M do not interact: the retention surface over (M, D) is additive. |
| H0-4 | Velocity V has no effect on final-state outcomes when cumulative migration is held constant. |
| H0-5 | No parameter region produces a discontinuous change in outcome: the response surface is everywhere smooth. |
| H0-6 | Hybrid configurations do not arise at a rate distinguishable from the founding-profile baseline. |
| H0-7 | Outcome variance between replicates is constant across the parameter space (no critical slowing, no bistability). |

**On H0-5 and H0-7.** These are the interesting nulls. H0-5 says there is no
threshold — that the premise of "a tipping point at X% migration" is wrong, and
change is smooth and proportional. H0-7 says stochastic variation does not peak
anywhere, which would independently indicate no critical region. Both are
plausible, both are publishable, and finding them would be a substantive result
about a widely-assumed phenomenon.

---

## Status against the pilots

**Nothing below is a test.** These are exploratory runs at a single parameter
point with four seeds, recorded so that a later pre-registered test cannot be
mistaken for the first look. Every row is provisional and several are close to
uninformative.

| Hypothesis | Predicted | Pilot P-9 observed | Status |
|---|---|---|---|
| H1 Concentration | retention **rises** with K | +0.03 ± 0.06 (homophily); 0.00 (conformist) | not supported; not excluded |
| H2 Diversity | retention **falls** with K | same | not supported; not excluded |
| H3 Fragmentation | dominance-by-an-incoming-culture **falls** with K | untested — no incoming culture became dominant in any arm | **untestable at this parameter point** |
| H4 Emergent synthesis | novel hybrid equilibrium at high K and interaction | untested — "hybrid" still undefined (A-012) | blocked |
| **H0-1** K has no effect at fixed M | — | consistent with both rules | **not rejected** |

Three things worth stating plainly:

1. **H1 and H2 predict opposite signs and the pilot separates neither.** The
   homophily estimate is +0.57 standard errors from zero. That is not weak
   evidence for H1; it is no evidence about either.
2. **H3 could not be tested.** It concerns the *probability* that an incoming
   culture becomes dominant, and that happened zero times in 36 runs. Estimating
   a rate needs hundreds of runs per condition, which the design must budget for.
3. **The mechanism matters more than K did.** The two rules disagreed about
   whether the resident culture erodes (homophily, 0.73) or absorbs the migrants
   (conformist, 0.9999) against a compositional baseline of 0.850 — a much larger
   effect than anything K produced. If that survives a proper design, the
   headline is about transmission mechanism, not source diversity, and the
   research questions would need reframing around it.

## Pre-registration discipline

These hypotheses are recorded **before** any transmission mechanism exists, so
none of them can have been reverse-engineered from a result.

Before the first substantive experiment:

1. Freeze this file and record its git commit hash in the analysis plan.
2. Specify the analysis — the test, the effect-size measure, the replicate count,
   the correction for multiple comparisons — in advance.
3. Any hypothesis added after seeing data is labelled **exploratory** in this
   file and stays labelled that way in publication.
