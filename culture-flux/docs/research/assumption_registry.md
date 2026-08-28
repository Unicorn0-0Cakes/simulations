# Assumption Registry

Every consequential modelling decision taken without literature support, in one
place, with the evidence needed to settle it.

The purpose is negative: to stop assumptions accumulating silently inside code.
A decision that is not here is either trivial or missing, and "missing" is a bug
in this file.

**Status values**

| Status | Meaning |
|---|---|
| `provisional` | Chosen for tractability. No literature support yet. Reversible. |
| `supported` | Backed by an extracted source, cited in `Evidence`. |
| `contradicted` | An extracted source argues against it. Must be changed or defended explicitly. |
| `structural` | Not an empirical claim: a scope decision defining what the model is about. |

**Sensitivity test values**

| Value | Meaning |
|---|---|
| `required` | A published result must include a sensitivity analysis over this. |
| `required-later` | Cannot be tested until a prerequisite mechanism exists. |
| `n/a` | Not a quantity that can be varied. |

---

## A-001 — Cultural features are interchangeable

**Description.** All F cultural features have equal salience, equal transmission
rate and zero resistance. No feature is more central to identity, more visible,
or harder to change than another.

**Justification.** The smallest representation that supports the research
question. Feature heterogeneity multiplies the parameter space before there is
any evidence about how to set it.

**Evidence.** None. Open question L-Q1.

**Implementation.** `culture/features.py` (`CultureSchema.uniform`); non-default
salience is carried through `distance.weighted_hamming` and is already testable.

**Expected effect.** Unknown in direction. Heterogeneous salience plausibly slows
change on core features and speeds it on peripheral ones, which could produce
partial retention states that a uniform schema cannot represent — and partial
retention is one of the outcomes the project exists to detect.

**Uncertainty.** High. This is among the most likely of the assumptions here to
be wrong in a way that changes conclusions.

**Sensitivity test.** `required`. The machinery exists: vary salience dispersion
at fixed mean.

**Status.** `provisional`

---

## A-002 — Origin never determines behaviour

**Description.** `source_id` is bookkeeping. No mechanism may branch on it except
measurement. Culture is a separate, mutable array, and residents and migrants are
initialised through the same code path.

**Justification.** The scientific-neutrality requirement, made structural. If
origin could drive behaviour, "ethnicity does not determine culture" would be a
claim in the README rather than a property of the program.

**Evidence.** A commitment of the project, not an empirical finding.

**Implementation.** `agents/population.py`; enforced by
`test_population.py::test_provenance_and_culture_are_separate_arrays`.

**Expected effect.** Prevents a class of results that would otherwise be
artefacts of the coding of identity.

**Uncertainty.** None about the choice. It does mean the model cannot represent
externally-imposed categorical treatment — discrimination, legal status,
residential steering — which are real mechanisms. Adding them later means adding
an explicit *treatment* layer, not relaxing this rule.

**Sensitivity test.** `n/a`

**Status.** `structural`

---

## A-003 — Cultural distance is normalised Hamming distance

**Description.** Distance between two profiles is the fraction of features on
which they differ. All differences count equally; trait identity beyond equality
is ignored.

**Justification.** The complement of Axelrod-style cultural overlap, and a true
metric, so triangle inequality arguments hold.

**Evidence.** None extracted. Open question L-Q4.

**Implementation.** `culture/distance.py`; axioms tested in `test_culture.py`.

**Expected effect.** Coarse. Two cultures differing on one feature by a small
amount and by a large amount are equidistant, so any gradual convergence
dynamic will be invisible until ordinal or continuous features exist.

**Uncertainty.** Moderate. Alternatives are registered rather than hard-coded, so
this is cheap to revisit.

**Sensitivity test.** `required-later` — needs a second implemented metric on a
different family (ordinal or continuous features).

**Status.** `provisional`

---

## A-004 — Within-group cultural variation is uniform random perturbation

**Description.** Agents in a group copy a modal profile, with per-feature
probability `within_source_noise` of an independent uniform redraw.

**Justification.** A one-parameter way to have any within-group variation at all.

**Evidence.** None. Open question L-Q7.

**Implementation.** `agents/population.py::draw_profiles`.

**Expected effect.** Independent perturbation produces no correlation structure
between features and no sub-clusters. Real populations have both, and a source
population with internal structure may behave like several smaller sources —
which would confound the K manipulation the whole project rests on.

**Uncertainty.** High, and it interacts with the central research question. Worth
early attention.

**Sensitivity test.** `required`.

**Status.** `provisional`

---

## A-005 — The founding resident culture is the all-zero profile

**Description.** The pre-migration city starts at trait 0 on every feature.

**Justification.** Trait labels are arbitrary and unordered, so any fixed profile
is equivalent to any other up to relabelling. Fixing it makes retention metrics
comparable across runs without extra bookkeeping.

**Evidence.** Follows from A-003 (labels carry no meaning). Independent of the
literature.

**Implementation.** `agents/population.py::initialise_resident_population`.

**Expected effect.** None, given A-003. It stops being harmless the moment
ordinal or continuous features exist, because then trait 0 is an endpoint rather
than a label.

**Uncertainty.** Low now, high after ordinal features arrive. Flag for revisit at
that point.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-006 — Source cultural geometry is set by choosing which features differ

**Description.** A source at target distance d differs from the resident profile
on `round(d · F)` features, chosen according to `arrangement`
(`independent` / `nested` / `disjoint`), with the differing trait drawn from the
non-resident traits. Realised distances are measured and stored, never assumed.

**Justification.** Gives independent control of distance-from-resident and
distance-between-sources, which hypotheses H2–H4 require. `independent` is the
neutral default; the other two bracket it.

**Evidence.** None. No extracted source describes how to arrange multiple source
cultures in a shared space — plausibly because L-Q6 is the gap this project fills.

**Implementation.** `migration/sources.py::generate_source_set`.

**Expected effect.** Direct and large. `nested` makes multiple sources behave
more like one; `disjoint` maximises their mutual distinctness. If K has an effect
at all, it will depend on arrangement.

**Uncertainty.** High, and structural rather than parametric: an entirely
different way of laying out culture space (e.g. sampling from a metric embedding)
may be better.

**Sensitivity test.** `required`. Every K result must be reported across all
three arrangements.

**Status.** `provisional`

---

## A-007 — Cultural-distance presets

**Description.** `near = 0.25`, `medium = 0.50`, `far = 0.75`, `maximal = 1.00`.

**Justification.** Round numbers spanning the achievable range. Nothing more.

**Evidence.** None. These are labels for convenience, not estimates.

**Implementation.** `migration/sources.py::DISTANCE_PRESETS`.

**Expected effect.** None on results, provided analyses report realised numeric
distances rather than preset names. The risk is rhetorical: writing "far
cultural distance" in a paper implies a calibration that does not exist.

**Uncertainty.** n/a — this is naming, not modelling.

**Sensitivity test.** `n/a`. **Reporting rule:** publications state realised
numeric distances; preset names never appear in results.

**Status.** `provisional`

---

## A-008 — Migration magnitude M is the migrant share of the FINAL population

**Description.** M is defined on the end state. `addition` grows the city
(`n = M·N₀/(1−M)` arrivals); `replacement` holds it constant (`n = M·N₀`
arrivals, an equal number of residents removed). Both end at migrant share M.

**Justification.** Makes the two modes comparable: a contrast between them
isolates whether residents left, not how big the city got. Defining M on the
initial population instead would make "30% migration" mean different end states
in the two modes.

**Evidence.** None. Open question L-Q5 — predecessor models may define it
differently, which would matter for internal validation.

**Implementation.** `migration/schedule.py::total_migrants`.

**Expected effect.** Large on cross-model comparison, small within this model.

**Uncertainty.** Low as a definition; the risk is mismatch with predecessors.

**Sensitivity test.** `required` — report both modes.

**Status.** `provisional`

---

## A-008b — Displacement under replacement is uniform among residents

**Description.** In `replacement` mode the residents removed are drawn uniformly
at random from those present.

**Justification.** The neutral placeholder. Real out-migration selects on age,
tenure, income and culture; each of those would push the result in a direction
the model has no warrant for.

**Evidence.** None.

**Implementation.** `experiment/run.py::ExperimentRun._displace`.

**Expected effect.** Culture-correlated departure ("white flight" and its
analogues) is a well-documented mechanism that this deliberately excludes.
Excluding it likely *understates* resident-culture loss under replacement.

**Uncertainty.** High if replacement mode becomes central; low while `addition`
is the default.

**Sensitivity test.** `required-later` — needs a selective-departure rule.

**Status.** `provisional`

---

## A-009 — Cultural influence is uniform across agents

**Description.** Every agent carries influence weight 1, so group influence
equals group population share.

**Justification.** The explicit null. The project's premise is that share and
influence are different things; the way to test that is to run the model where
they coincide and compare against models where they do not.

**Evidence.** None, and the point is that the equality is the thing under test.

**Implementation.** `influence/base.py::UniformInfluence`. Divergence between
influence and share is measured every run
(`metrics.influence_share_divergence`), so the null is visible in the output.

**Expected effect.** Under this model, "30% of the population" and "30% of the
cultural influence" are the same statement. Any result showing a percentage
threshold under it is a result about a world where influence is uniform, and must
be reported as such.

**Uncertainty.** High — almost certainly false of real societies. It is here to
be replaced.

**Sensitivity test.** `required`. The first non-uniform model (network-degree
weighting is the cheapest) is a Phase 3 priority.

**Status.** `provisional`

---

## A-010 — The city is a single well-mixed pool

**Description.** The only implemented network layer is a complete graph.

**Justification.** Structure is a Phase 3 concern and would be premature before a
transmission rule exists to run over it.

**Evidence.** None. Open question L-Q8. Enclave formation (P5) and network
formation (P2) both suggest this is consequential.

**Implementation.** `networks/base.py::WellMixedLayer`.

**Expected effect.** **Outcome-determining, and now measured.** Pilot P-1
(docs/research/pilot_notes.md) ran the homophily rule to 2,000 simulated years
with no migration at Q ∈ {2, 3, 5, 10}: *every* configuration converged to a
single culture and froze. Only the time to convergence differed.

Under this assumption the model appears to have exactly one long-run outcome —
monoculture — with the only open question being which culture wins. That removes
"multicultural equilibrium" and "cultural fragmentation" from the set of
reachable states, on top of the enclaves, spatial segregation and network
modularity that were already impossible. Six of the nine outcomes named in the
research brief are unavailable under A-010.

It also means finite-horizon results describe transients. At 200 years, Q = 5
showed 379 distinct profiles and `interactable_pair_fraction` = 0.998, which
reads as sustained diversity and is in fact a way-station to monoculture.

**Uncertainty.** None that it matters — measured. High about which structure to
replace it with.

**Superseded in v0.3, and the replacement is worse than expected.** Structured
layers now exist, and pilot P-4 shows they do not fix the problem: households,
neighbourhoods and workplaces with random overlapping memberships still collapse
to monoculture, because they stitch the city into one connected component. What
sustains diversity is *disconnection*, not locality. See A-019 and A-027.

**Sensitivity test.** `required`. **Reporting rule:** any result must report
`interactable_pair_fraction`, and must state whether it concerns an equilibrium
or a transient.

**Status.** `provisional`

---

## A-016 — The transmission rule is specified here, not extracted

**Description.** `axelrod_homophily` implements a rule *in the family* Axelrod
(1997) introduced: interaction probability equal to cultural overlap, one-way
copying of a single differing feature, no innovation. Every detail — one-way
copying, the feature-choice weighting, the treatment of overlap 0 and 1, the
interaction rate — is specified in `dynamics/homophily.py` and nowhere else.

**Justification.** None from the literature. The rule was implemented at the
user's direction ahead of Phase 1, on the grounds that it is the family the
current culture representation descends from. That is a reason to try it, not
evidence that it is right.

**Evidence.** **None.** Axelrod (1997) has not been read; open question L-Q3 is
open. Where the published model differs from this one, this implementation is
wrong about Axelrod and right about itself.

**Implementation.** `dynamics/homophily.py`.

**Expected effect.** Determines every dynamic result the model produces. It is
the single most consequential choice in the codebase and the one with the least
support behind it.

**Uncertainty.** Maximal. At least four alternative rules sit in the core corpus
(conformist, prestige-biased, payoff-biased, acculturation-orientation), and the
answer to RQ2 may depend more on which is chosen than on K.

**Sensitivity test.** `required`. No substantive result may rest on a single
transmission rule; at least two from different families must agree.

**Reporting rule.** This rule is never to be described as "Axelrod's model" in
any output until the paper has been read and the correspondence checked. The
configuration layer emits this warning on every run that uses it.

**Status.** `provisional`

---

## A-017 — Batched updating approximates asynchronous updating

**Description.** By default, interaction events are applied in conflict-free
batches: within a batch no agent is a focal agent twice, and every event reads
the pre-batch state. The exact asynchronous process is available as
`update_scheme: "asynchronous"`.

**Justification.** Speed — 12.6× measured. Asynchronous updating costs one Python
iteration per event, which at 10^7 events per run makes sweeps impractical.

**Evidence.** Weak, and deliberately labelled so. Eight seeds at N = 200
comparing the two schemes on retention and off-founding share found no difference
beyond noise (|z| < 0.6 on all four quantities compared;
`test_batched_and_asynchronous_schemes_agree_within_noise`). That has low power:
it rules out a gross discrepancy, not a subtle one, and in a model where
convergence is driven by rare events a subtle difference in event ordering is
exactly the kind that could matter.

**Implementation.** `dynamics/homophily.py::_apply_batch`.

**Expected effect.** A batched process is a different stochastic process, not a
faster version of the same one. Its likely direction is towards slightly slower
convergence, since events cannot chain within a batch.

**Uncertainty.** Moderate.

**Sensitivity test.** `required`. Before any published result, re-run a
representative subset asynchronously and compare distributions, not means, at a
sample size with real power.

**Status.** `provisional`

---

## A-017b — Influence weights are computed once per step

**Description.** The influence model is consulted once per simulation step; every
event within that step uses the same weights.

**Justification.** Under `UniformInfluence` this is exact. Under a
state-dependent influence model it is a within-step approximation.

**Evidence.** None needed while influence is uniform; becomes live the moment it
is not.

**Implementation.** `dynamics/homophily.py::step`.

**Expected effect.** None currently. Under a network-position or prestige model
it would damp feedback between cultural change and influence within a step.

**Uncertainty.** Low now, moderate from Phase 3.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-018 — No innovation, error or drift

**Description.** Traits are only ever copied. No mechanism creates a trait nobody
holds. Enforced as a test invariant: the set of traits present at each feature
can shrink but never grow.

**Justification.** The rule family's convention, and one fewer parameter.

**Evidence.** None. Cultural drift and innovation are named in the project's
secondary corpus and are not yet extracted.

**Implementation.** `dynamics/homophily.py`; invariant tested in
`test_copying_can_never_introduce_a_trait_nobody_held`.

**Expected effect.** Substantial and one-directional. Without innovation the
reachable culture space is bounded by the founding profiles, so the only route to
novelty is recombination across features — which pilot P-2 shows is the usual
outcome, but which is a much weaker form of novelty than the "emergent synthesis"
H4 describes. It also guarantees absorbing states exist: with no innovation,
diversity can only ever decrease.

**Uncertainty.** High. A copying-error rate is one parameter and would change
whether absorbing states are reachable at all.

**Sensitivity test.** `required`.

**Status.** `provisional`

---

## A-011 — No cultural transmission occurs (v0.1 only)

**Description.** The only transmission rule is the null. Nobody changes culture.

**Justification.** Building measurement before mechanism means the mechanism can
be judged against a working baseline. It also makes the compositional component
of every metric visible and quantified, so a later transmission result can be
reported net of it.

**Evidence.** n/a — a release-scope decision.

**Implementation.** `dynamics/base.py::NullTransmission`.

**Expected effect.** All v0.1 trajectories are compositional. `NullTransmission`
is permanent, not temporary: it stays as the control arm.

**Uncertainty.** n/a

**Sensitivity test.** `n/a`

**Status.** `structural` — superseded as the default in v0.2 by A-016, but
`NullTransmission` remains the control arm and every experiment must run it.

---

## A-012 — "Hybrid" is undefined

**Description.** The hybridisation metric is registered as a placeholder
returning NaN, because two definitions are available and they disagree: (a) a
profile matching no founding profile exactly; (b) a profile beyond distance d
from every founding profile.

**Justification.** Definition (a) is trivially satisfied by a single copied trait
and would make hybridisation look ubiquitous. Definition (b) needs a threshold
that would prejudge RQ6. Neither is defensible yet, so the metric returns NaN
rather than a number that would be quoted.

**Evidence.** None. Open question L-Q10.

**Implementation.** `metrics/cultural.py::hybridization_index`.

**Expected effect.** RQ6 cannot be answered until this is settled. That is the
correct state to be in — and it is now a live risk rather than a theoretical one,
because with an active rule the metric would return a plausible-looking number
that would be quoted. A test asserts it still returns NaN.

**Uncertainty.** High. Partly addressed in v0.2 by reporting the
distance-to-nearest-founding-culture distribution directly
(`mean_`/`max_distance_to_nearest_founding_culture`,
`share_off_founding_profiles`) instead of a scalar index. Pilot P-2 shows why the
naive definition fails: 50–80% of converged runs end on a profile no founding
population held, which the naive index would call universal hybridisation when it
is ordinary recombination.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-013 — Default schema size: F = 20 features, Q = 5 traits

**Description.** The reference configuration uses 20 features of 5 traits each
(10 × 5 in the smoke test).

**Justification.** F = 20 makes achievable distances multiples of 0.05, fine
enough that rounding does not distort the D manipulation. Q = 5 is Axelrod's
conventional order of magnitude. Both are convenience.

**Evidence.** None. Open question L-Q2 — and whether qualitative behaviour
depends on F and Q is itself a known-important question in this literature.

**Implementation.** `configs/baseline_v0.json`. Configurations with F < 10 emit
a warning that is carried into every run manifest.

**Expected effect.** In Axelrod-family models the number of traits per feature
strongly affects whether a population converges or polarises. Any result here is
conditional on Q until shown otherwise.

**Uncertainty.** High.

**Sensitivity test.** `required`. F ∈ {10, 20, 40} × Q ∈ {2, 5, 10} at minimum.

**Status.** `provisional`

---

## A-014 — Arrivals are uniform within the migration window

**Description.** The same number of arrivals lands in each step of the window,
allocated by largest remainder.

**Justification.** The neutral velocity profile. Front-loaded, back-loaded and
pulse profiles are declared and raise `NotImplementedError` rather than being
approximated.

**Evidence.** None.

**Expected effect.** Under the null rule, none — the endpoint is identical at any
velocity (tested). Once transmission exists, arrival timing is exactly where path
dependence and hysteresis would appear, so this becomes consequential precisely
when RQ5 becomes answerable.

**Uncertainty.** Low now, high later.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-015 — No births, deaths, ageing or onward emigration

**Description.** The population changes only through the migration schedule.

**Justification.** Vertical transmission is meaningless without a transmission
rule, and demography would add parameters with no way to judge them.

**Evidence.** n/a — scope.

**Expected effect.** The model cannot represent generational replacement, which
is the timescale on which acculturation is usually observed. `migration_generation`
is recorded but only ever takes values 0 and 1. The reserved `vital_events` RNG
stream means adding demography later will not shift any existing stream's draws.

**Uncertainty.** n/a as scope; high as a limitation on what can be claimed.

**Sensitivity test.** `n/a`

**Status.** `structural`

---

## A-019 — How encounters divide across social settings

**Description.** Each interaction event draws its layer in proportion to a fixed
weight. Defaults: household 0.30, neighbourhood 0.20, workplace 0.30, friendship
0.15, citywide 0.05.

**Justification.** None. These are placeholders expressing the ordering the
project brief itself proposed as its example assumption — that people interact
more with household members than with random city residents. The *ordering* is
uncontroversial; the *numbers* are invented.

**Evidence.** None. No time-use or contact-survey source has been extracted.

**Implementation.** `networks/base.py::DEFAULT_LAYER_SPECS`.

**Expected effect.** **Decisive, and measured — but not in the way P-5 first
reported.** Pilot P-6 retracts the threshold: extending the runs shows the
citywide weight governs *how long* cultural diversity lasts, not whether it
survives. At N = 1000 the weight that produced monoculture at N = 500 sustains
~30 cultures for 1,800 years before collapsing anyway. Every connected
configuration tested ends in monoculture.

**The default of 0.05 still sits deep in the fast-collapse regime.** And plateau
duration is now the thing this parameter controls, which makes it *harder* to
reason about than a threshold would have been, not easier.

**Uncertainty.** Maximal. A migration result could appear, move or vanish purely
as a function of this number *and* of the observation horizon, which interact:
this parameter sets how long a plateau lasts, and the horizon decides whether the
plateau or the collapse is what gets measured.

**Sensitivity test.** `required`, and stronger than that: **the citywide weight
must be treated as an experimental variable alongside M, K, D, H and V**, not as
a setting. No threshold claim is meaningful without it on an axis.

**Note on prior art.** The transition itself is established in the literature
(secondary corpus S1, S2). That does not weaken the requirement — it strengthens
it, because it means the sensitivity of this project's results to a known-critical
parameter is a thing reviewers will expect to see addressed.

**Status.** `provisional`

---

## A-020 — Group memberships are disjoint and singular

**Description.** Every agent belongs to exactly one household, one neighbourhood
and one workplace, and groups do not overlap within a layer.

**Justification.** Makes partner sampling a constant-time array lookup, which is
what permits large sweeps.

**Evidence.** None.

**Implementation.** `networks/layers.py::GroupLayer`.

**Expected effect.** Excludes people belonging to several workplaces, changing
household over a life, or living between neighbourhoods. Note that this
assumption does *not* protect the city from being connected: P-4 shows random
overlapping *memberships across layers* already do that.

**Uncertainty.** Moderate.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-021 — Attention ties are directed and of fixed degree

**Description.** Each agent holds exactly `degree` outgoing ties — "whose culture
I am exposed to". Ties are not reciprocal, and every agent has the same
out-degree.

**Justification.** Attention genuinely is asymmetric. Fixed degree makes rewiring
O(1) per tie instead of a graph rebuild.

**Evidence.** None.

**Implementation.** `networks/layers.py::AttentionTieLayer`.

**Expected effect.** Excludes degree heterogeneity, which is one of the most
robust findings about real social networks and is the natural substrate for a
prestige-based influence model. The `network_degree` influence model reads
*in*-degree, which does vary, so some heterogeneity survives — but it is
generated by random tie formation rather than by any process.

**Uncertainty.** High for anything about influence; low for transmission.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-022 — Arrivals are placed at random by default

**Description.** Arriving agents join groups uniformly at random. `clustered`
assignment, in which an arrival joins a group already holding someone from its
own source with probability `clustering`, is available and off by default.

**Justification.** Random placement is the neutral choice. Turning clustering on
by default would build residential sorting into the initialisation, and enclave
formation is meant to be a thing the model can produce or fail to produce, not a
thing it starts with.

**Evidence.** None. Real migration is strongly chain-structured, so random
placement is very likely wrong — but wrong in a direction that makes enclaves
*harder* to obtain, which is the conservative error.

**Implementation.** `networks/layers.py::GroupLayer.add_agents`.

**Expected effect.** Understates enclave formation and residential segregation.

**Uncertainty.** High.

**Sensitivity test.** `required`. Report every segregation result at both
`clustering = 0` and a positive value.

**Status.** `provisional`

---

## A-023 — Homophilous rewiring is best-of-k

**Description.** A rewiring agent draws `rewire_candidates` agents at random and
ties to the most culturally similar.

**Justification.** k is a legible dial for homophily strength — k = 1 is exactly
no homophily, and is used as the control in the test suite — and it costs one
comparison pass rather than a normalisation over N.

**Evidence.** None.

**Implementation.** `networks/layers.py::AttentionTieLayer.rewire`.

**Expected effect.** Best-of-k is a rank-based rule, so it is insensitive to
*how much* more similar the winner is. A similarity-proportional rule would
behave differently near indifference.

**Uncertainty.** Moderate.

**Sensitivity test.** `required-later`.

**Status.** `provisional`

---

## A-024 — Influence multiplies the chance of being copied

**Description.** An interaction succeeds with probability
`overlap x attention(partner)`, where attention is the partner's influence weight
divided by the maximum weight. Influence therefore acts on *being copied*, not on
*being encountered*.

**Justification.** It composes with any network structure instead of competing
with it: partner selection belongs to the network, influence belongs to the
adoption decision. Normalising by the maximum bounds attention at 1, so influence
can never raise a probability above the overlap. Under uniform influence the term
is exactly 1, which reproduces v0.2 including its random draw sequence.

**Evidence.** None. Prestige bias in cultural evolution is often modelled as
biased *choice of model* — i.e. on encounter — which is the alternative this
rejects without evidence. Open question L-Q3 bears on it.

**Implementation.** `dynamics/homophily.py`.

**Expected effect.** Under encounter-weighting, a high-influence agent's culture
spreads by being met more often, which interacts with network position twice.
Under adoption-weighting it spreads by being adopted more readily once met. The
two differ most in sparse networks.

**Uncertainty.** High.

**Sensitivity test.** `required` once a non-uniform influence model is used in
anger.

**Status.** `provisional`

---

## A-025 — Modularity under rewiring is partly tautological

**Description.** `network_modularity` measures whether ties run between
culturally similar agents. When homophilous rewiring is enabled, the rewiring
rule *creates* that alignment directly.

**Justification.** n/a — this is a caveat on interpretation, not a modelling
choice.

**Implementation.** `metrics/structure.py::network_modularity`.

**Expected effect.** Modularity is evidence of emergent enclave formation only
against a matched run with `rewire_rate = 0`. Reported alone it measures the
rewiring parameter.

**Sensitivity test.** `n/a`. **Reporting rule:** always report modularity in
matched pairs with rewiring off.

**Status.** `structural`

---

## A-026 — Influence has a floor

**Description.** `NetworkDegreeInfluence` maps influence into
`[floor, 1]` with `floor = 0.1`, so an agent nobody attends to still has some
chance of being copied.

**Justification.** Zero influence would make an agent unlearnable-from rather
than merely obscure, creating a class of agents who are permanently culturally
inert — a strong claim smuggled in as a numerical edge case.

**Evidence.** None. The value 0.1 is arbitrary.

**Implementation.** `influence/base.py::NetworkDegreeInfluence`.

**Expected effect.** Sets how sharply influence can concentrate. A lower floor
approaches winner-take-all.

**Uncertainty.** Moderate.

**Sensitivity test.** `required` whenever the model is used.

**Status.** `provisional`

---

## A-027 — Connectivity, not locality, is the operative structural variable

**Description.** Not a parameter but a finding that now constrains
interpretation: whether cultural diversity persists depends on whether the union
of interaction layers leaves the city disconnected, not on whether individual
interactions are local.

**Evidence.** Pilots P-4 and P-5. Every configuration whose layers formed one
connected component converged to monoculture, including one with no citywide
layer at all. Only genuinely disconnected islands sustained diversity, and adding
a 1% rate of stranger encounters destroyed it.

**Implementation.** n/a — a property of the model, recorded so that a future
change is not read as unrelated.

**Expected effect.** Any statement of the form "we added realistic social
structure, therefore the model can now represent cultural diversity" is false
here. Structure must be checked for connectivity, not assumed to imply it.

**Sensitivity test.** `n/a`. **Reporting rule:** report the effective weak-tie
weight alongside any diversity outcome.

**Status.** `structural`

---

## A-028 — A finite horizon may report a plateau as an equilibrium

**Description.** Not a parameter — a hazard, recorded so that it constrains every
result the project produces.

**Evidence.** Pilot P-6. Two seeds at N = 1000 held ~30 distinct cultures for
1,600 simulated years, with richness stable and drifting slightly upward, before
collapsing to a single culture. Anyone reporting the year-1,000 state of those
runs would have reported a robust multicultural equilibrium and been wrong.

**Implementation.** `experiment/run.py::_absorption_report` writes
`absorption.absorbed`, `quiescent_years`, `quiescent_fraction_of_run` and a
confidence into every manifest; the time series carries
`steps_since_last_change`. Absorption is tracked by **trait changes**, never by
metric stability — in P-6 the metrics were flat while traits changed continuously
underneath them.

**Expected effect.** Every outcome state in the research brief is exposed to
this: multicultural equilibrium, integration and fragmentation could each be a
plateau. So could a migration threshold.

**Uncertainty.** The existence of the hazard is established. Its magnitude —
how long plateaus last as a function of the parameters — is not characterised at
all.

**Sensitivity test.** `required`, and it is a *design* requirement rather than a
post-hoc check: either run every cell to absorption, or state the horizon and
report every result as conditional on it.

**Reporting rule.** No result may use the words "equilibrium", "stable" or
"persists" unless the runs behind it are absorbed. Confidence is never reported
as certain under an active rule, because a long plateau can still break.

**Status.** `structural`

---

## Registry maintenance

- A new assumption gets the next free ID. IDs are never reused.
- Changing an assumption's `Status` requires a citation in `Evidence`.
- Removing an assumption requires removing the code that embodies it.
- Every `required` sensitivity test must appear in the analysis plan before any
  result derived from that assumption is published.
