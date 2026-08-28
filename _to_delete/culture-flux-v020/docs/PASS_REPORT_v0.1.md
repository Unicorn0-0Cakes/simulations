# End-of-Pass Report — v0.1.0-skeleton

Framework pass completed 2026-08-22. **Stop and review before Phase 1.**

---

## CREATED

**68 files.** 4,230 lines of engine, 1,750 of tests, ~2,000 of documentation.

**Documentation (13 files)**
- `docs/literature/` — literature matrix (six papers, citations verified, all substantive columns NOT YET EXTRACTED, 12 open questions L-Q1…L-Q12); extraction protocol
- `docs/research/` — assumption registry (A-001…A-015); research questions (RQ1–RQ7); hypotheses (H1–H4 + 7 nulls); validation strategy; outcome typology
- `docs/model/` — architecture; stack decision; config schema; data outputs; roadmap (Phases 1–6 with entry/exit conditions)

**Engine (`src/culture_flux/`, 31 modules)**
`rng.py` (named deterministic streams) · `time.py` (step/year/generation) · `culture/` (feature schema, profiles, distance registry) · `agents/` (struct-of-arrays population, attribute registry) · `migration/` (source composition and geometry, arrival accounting) · `influence/` (cultural influence, separate from share) · `networks/` (multiplex abstractions) · `dynamics/` (transmission rules — null only) · `metrics/` (diversity indices, 21 registered metrics) · `experiment/` (config, run, sweep) · `io/` (manifests, writers, run dirs) · `cli.py`

**Configurations** — smoke (JSON + YAML, hashing identically), reference baseline, two sweeps including the central K-at-fixed-M contrast

**Tests** — 180 invariant tests across 8 files, plus a dependency-free runner

---

## IMPLEMENTED

Working, not stubbed:

- **Deterministic seeded randomness** with named streams and a baseline/condition split, so runs sharing a seed have byte-identical resident populations regardless of migration settings. Streams for unbuilt mechanisms are pre-declared so adding them later cannot shift existing draws.
- **Culture representation** — categorical feature/trait vectors with per-feature salience, transmission rate and resistance declared and carried through distance computation. Ordinal and continuous kinds raise rather than coerce.
- **Cultural distance** — a registry; `hamming` and `weighted_hamming`, both verified as true metrics.
- **Diversity metrics** — fractionalisation, Simpson/HHI, Shannon entropy, Pielou evenness, Hill numbers of arbitrary order, richness, max share.
- **Population initialisation** — struct-of-arrays, with within-group heterogeneity as a parameter and provenance held separate from culture.
- **Migration** — M/K/H/D/V independently manipulable; exact integer allocation by largest remainder; addition and replacement modes both reaching the same *final* migrant share; evenness targetable exactly at fixed K; three source-arrangement schemes controlling inter-source distance independently of distance-from-resident; realised geometry measured and stored, never assumed.
- **Metrics interface** — 16 implemented, 5 registered placeholders returning NaN with a stated blocker.
- **Experiment layer** — declarative config with strict validation and three derived hash keys; full run manifest; sweep expansion with condition hashing and dry-run.
- **CLI** — `status`, `metrics`, `validate`, `run`, `verify`, `sweep`. Headless; no GUI anywhere in the import graph.
- **Output** — parquet with CSV fallback, format recorded in the manifest.

Deliberately not implemented: any cultural transmission. `NullTransmission` is the only rule.

---

## TESTED

**180/180 passing**, under warnings-as-errors, on two environments.

Covered: RNG determinism and stream independence; the baseline/condition split; distance metric axioms (identity, symmetry, boundedness, triangle inequality); diversity closed forms and Hill-number identities; migration conservation at every tested size; population invariants; configuration rejection cases including unknown-key rejection; metric values against hand-computed answers; the null contract; the K-at-fixed-M contrast end to end.

**Verified behaviour worth stating:**
- Retention equals `1 − M·D̄` to machine precision — the compositional baseline, exact.
- Source count has **exactly zero** effect on retention under the null (< 1e-12 across K ∈ {1,2,5,10}) while composition diversity does move. Any future K effect is attributable to the mechanism.
- Velocity has **exactly zero** effect on the endpoint under the null.
- Source cultures *do* differ across seeds even though null metrics do not — so zero replicate variance is a property of the null, not a dead RNG.
- Cross-environment: identical `run_hash` on Python 3.11/NumPy 2.4.4 and Python 3.10/NumPy 2.2.6. Pinned as a regression tripwire.

**Not verified:** the parquet writer (pyarrow absent in the build environment — only the CSV path ran); behaviour above N = 20,000; a second CPU architecture; any transmission rule.

**Performance:** a 100-year run at N₀ = 10,000 takes 0.9 s after profiling removed a 25× overhead (repeated lexsort in profile grouping, fixed by mixed-radix encoding and per-measurement memoisation). A 8,100-run design is therefore ~2 CPU-hours single-threaded.

---

## PROVISIONAL ASSUMPTIONS

Fifteen registered. The five most likely to change conclusions:

| ID | Assumption | Why it matters |
|---|---|---|
| **A-001** | All cultural features are interchangeable | Heterogeneous salience could produce partial-retention states a uniform schema cannot represent — and partial retention is an outcome the project exists to detect |
| **A-006** | Source cultures are arranged by choosing which features differ | Directly controls inter-source distance. If K has any effect, it will depend on arrangement |
| **A-009** | Cultural influence is uniform across agents | Under it, share *is* influence. Any percentage threshold found is a result about a world where influence is uniform |
| **A-010** | The city is one well-mixed pool | Enclaves, spatial segregation and network modularity are **impossible** under it. A null on those is an artefact, not a finding |
| **A-013** | F = 20 features, Q = 5 traits | In Axelrod-family models, traits-per-feature strongly affects whether populations converge or polarise |

Also registered: A-002 origin never determines behaviour (structural); A-003 Hamming distance; A-004 within-group variation as uniform perturbation; A-005 all-zero founding profile; A-007 distance preset labels; A-008/A-008b M defined on the final population, uniform displacement; A-011 no transmission (structural); A-012 "hybrid" undefined; A-014 uniform arrivals; A-015 no demography (structural).

---

## LITERATURE GAPS

None of the six papers is on disk. Citations were verified (venue, year, DOI); nothing about their content was inferred, and no number in this codebase came from any of them.

Twelve questions block modelling decisions. The two that block the most:

- **L-Q3 — which transmission rule, and on what stated grounds?** At least four plausible candidates sit in the corpus. This blocks the entire dynamics layer, and choosing before reading would mean choosing arbitrarily.
- **L-Q6 — does any predecessor vary source count at fixed total migration?** This determines whether the project's central claim is novel. If one does, the framing needs rework; if none does, that gap *is* the contribution and must be stated as such.

Also open: culture representation and its justification (L-Q1); F and Q values and whether behaviour depends on them (L-Q2); distance definition (L-Q4); migration operationalisation (L-Q5); within-group variation (L-Q7); network structures (L-Q8); acculturation orientations as agent strategies (L-Q9); outcome measures and how qualitative regimes are identified (L-Q10); replication practice (L-Q11); whether majority-group change is modelled at all (L-Q12).

Two partial-verification notes: Mesoudi 2018 has a published correction that must be read alongside it; Chuang et al. 2019's volume/issue/pages could not be verified and are marked as such.

---

## ARCHITECTURAL DECISIONS

1. **NumPy, no ABM framework.** Mesa's scheduler is the wrong shape for four different clocks; per-agent Python objects do not survive a 10⁵-run design; framework-owned RNG makes stream control indirect; and its main benefits (grid space, visualisation server) are things this project must not use. Reversal condition documented.
2. **Layer separation by import direction.** A layer imports downward only. The engine has no GUI or plotting import, so a UI cannot be inserted into the loop. Metrics receive a context and return floats — a metric that mutated state would be a mechanism wearing a measurement's name.
3. **Baseline/condition RNG split.** The mechanism that makes "same M, different K" a controlled contrast rather than a comparison of two different cities.
4. **Declared-versus-implemented, machine-readable.** 19 agent attributes declared / 5 implemented; 7 rules / 1; 5 layers / 1; 3 feature kinds / 1; 21 metrics / 16. Requesting anything unimplemented raises with a roadmap pointer. `culture-flux status` prints both columns; the counts are pinned in tests so the gap cannot drift.
5. **The null is permanent.** Not a placeholder awaiting deletion — the control arm, and a sharp falsifiable check most simulation work lacks.
6. **Placeholder metrics return NaN, never a plausible zero,** and each states its blocker.
7. **Targets requested, realised values measured.** Cultural distance is a target; achievable values are multiples of 1/F; the realised pairwise matrix goes in the manifest and analysis uses that.
8. **Unknown configuration keys are rejected.** A silently-ignored typo looks exactly like a null result.
9. **JSON canonical for byte-stable hashing;** YAML supported and hashing identically.
10. **`run_hash` covers scientific content only** — final culture matrix, provenance, full metric series — excluding timestamps, paths and machine names, so `verify` tests reproducibility rather than environment.

---

## RISKS

**Scientific**

1. **The transmission rule will dominate everything.** Whichever rule is chosen may determine the answer to RQ2 more than K does. Mitigation: implement at least two rules from different families before drawing conclusions, and report results under both.
2. **A-001, A-003 and A-013 may be doing the work.** An apparent K effect could be an artefact of the culture representation. Mitigation: the `required` sensitivity analyses, run *before* any substantive result.
3. **RQ7 invites the classification trap.** Naming five outcome states and sorting runs into them would impose the answer. The engine is built to resist this and a test enforces it, but the discipline has to hold in the analysis layer too, where it is not enforceable by code.
4. **H2 and H3 are not mutually exclusive and could easily be tested as if they were.** Both can hold — the resident culture erodes while nothing replaces it. Testing them together needs the full outcome *distribution* across replicates, not means.
5. **The dependent variable may have no empirical counterpart.** No real dataset measures cultural-profile distributions over synthetic features. The empirical-validation path may have to step down to a much coarser comparison, and deciding that is itself unscheduled research.
6. **A-010 makes three named outcomes impossible.** Enclaves, spatial segregation and network modularity cannot appear before Phase 3. A null on those in Phase 2 must not be reported as a finding.

**Engineering**

7. **NumPy NEP 19 does not guarantee `Generator` stream stability across major versions.** A future NumPy could silently break replay of stored runs. Mitigated by the pinned-hash tripwire, not eliminated.
8. **The parquet path is untested.** Only CSV has run. Install pyarrow and add a round-trip test before any large sweep.
9. **Sweep execution is serial and has no resume.** 8,100 runs is ~2 CPU-hours, which is fine; 10⁵ is not. Condition hashing makes resume straightforward, but it is not written.
10. **`final_population` output is three orders of magnitude larger than everything else.** Default off; turning it on across a large sweep would produce terabytes.

---

## NEXT RECOMMENDED BUILD

**Phase 1: literature extraction. No code.**

Fill the matrix from the full texts, in the order given in the extraction protocol — Axelrod first (it is the ancestor of the current representation, so its assumptions are the ones most likely to have been inherited unexamined), then Mesoudi 2018, then the orientation strand, then the network strand.

**Exit condition:** L-Q3 answered with a page reference, and L-Q6 answered.

Building the transmission rule first would mean choosing the model's single most consequential mechanism from memory — precisely the thing that cannot be defended in review.

**Stopping here for review, as instructed.**
