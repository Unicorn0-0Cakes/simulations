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

**Expected effect.** Large and one-directional. Well-mixed populations converge;
structured ones sustain local diversity. Under a well-mixed assumption the model
*cannot* produce enclaves, spatial segregation, or network modularity — three of
the outcomes in the research brief. Any null result on those is an artefact of
this assumption, not a finding.

**Uncertainty.** Low that it matters; high about which structure to use.

**Sensitivity test.** `required-later`.

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

**Status.** `structural`

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
correct state to be in.

**Uncertainty.** High. Likely resolved by reporting the full distance-to-nearest-
founder distribution rather than any scalar index.

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

## Registry maintenance

- A new assumption gets the next free ID. IDs are never reused.
- Changing an assumption's `Status` requires a citation in `Evidence`.
- Removing an assumption requires removing the code that embodies it.
- Every `required` sensitivity test must appear in the analysis plan before any
  result derived from that assumption is published.
