# Simulation Architecture Specification

**Stage 01 — Simulation Architect**
**Status:** Complete, pending Stage 02 (Research & Model Engineer)
**Date:** 2026-09-05

---

## 1. Working Title

**When the Towers Go Dark**
*Technical subtitle:* Resilience in Standalone Wireless Mesh Networks

---

## 2. Instrument ID

**Atlas slug:** `towers-dark`

The concept brief requested "next available `SIM-###`". **No such identifier convention exists in the Atlas.** `assets/catalogue.js` keys every instrument by a lowercase slug (`flask`, `universe-25`, `ferry-terminal`, `culture-flux`), and the slug is load-bearing: it is the record key, the directory name, the `preview` handle and the href stem. Introducing a parallel numeric ID would create a second identity space with nothing deriving from it.

**Decision:** use the established slug convention. `towers-dark` is unused and collides with no existing record.

If a numeric register is genuinely wanted across the Atlas, that is a catalogue-schema change affecting all eleven existing instruments and should be raised as its own piece of work, not smuggled in with a new simulation.

---

## 3. Primary Research Question

> When conventional infrastructure is unavailable, which of a community's own resources — device density, relay siting, stored energy, participation, and the decision to host services locally — most determines what a standalone wireless network can still deliver, and **at which layer does it fail first**?

### Why the original question was reframed

The submitted question was:

> *"Under what conditions can a wireless standalone mesh network remain connected, useful, and resilient when conventional internet and cellular infrastructure are unavailable?"*

Three problems, each of which would have propagated into the model:

1. **"Resilient" is a conclusion word, not a measurable.** It is the thing to be operationalised, so it cannot also appear in the question as a property the network either has or lacks. The reframed question forces resilience to be *defined by what is measured* rather than asserted.
2. **"Connected, useful, and resilient" bundles three distinct dependent variables** that the brief's own four-layer table separates. Bundling them at the question level would have licensed a single blended score and destroyed exactly the distinction the instrument exists to expose.
3. **"Under what conditions" is unbounded.** Any simulation answers *some* question about conditions. Naming the five candidate resources makes the question investigable and makes the comparison set finite.

The added clause — *at which layer does it fail first* — is the scientifically load-bearing part. It is genuinely non-obvious, it is not answerable by inspection, and it cannot be answered by a demonstration. It is the reason this is an instrument.

### Neutrality check

The question does not presuppose that a mesh network helps. It admits the finding that no configuration delivers usable service, that the binding constraint is participation rather than radio, or that the layer that fails first is the one nobody instruments. See §14 (null baseline) and §20(D).

---

## 4. Secondary Questions

**SQ1 — Do connectivity and usefulness decouple?**
Does structural connectivity predict service delivery, or can a fully connected mesh deliver nothing because no service is hosted inside it?

**SQ2 — Is energy depletion a form of targeted attack?**
Random node loss and targeted removal of highly connected nodes are known to affect networks differently. Busy relays draw more power. Does energy-driven failure therefore concentrate on high-centrality nodes, producing targeted-loss dynamics without an adversary?

**SQ3 — What does priority routing cost?**
Does emergency-class prioritisation improve emergency delivery, what does it cost routine traffic, and does that trade-off change shape under congestion?

**SQ4 — Is repositioning repair or disturbance?**
When the user moves a node to bridge a partition, does the gain at the destination exceed the loss at the origin, and under what geometry?

**SQ5 — Few strong nodes or many weak ones?**
At matched total provisioning cost, how does a small number of well-sited, well-powered relays compare with a large number of ordinary distributed devices?

**SQ6 — Who is unreachable regardless?**
What fraction of the population remains without service under every configuration tested, and is that fraction set by geography, by device ownership, or by energy?

---

## 5. Purpose

An instrument for investigating the conditions under which a community-scale standalone wireless network delivers usable service after infrastructure loss — and, equally, the conditions under which it does not.

**It is not** a mesh-networking demonstration, a radio-technology comparison, a product evaluation, or a preparedness advocacy tool.

The user's work is to make provisioning decisions under uncertainty about the damage, then live with them, then intervene as the situation degrades — and to read a layered set of outcome measures rather than a single verdict. The instrument's contribution is making visible a distinction that operational discussion routinely collapses: **a mesh that routes perfectly and hosts nothing provides no service at all.**

---

## 6. System Definition

### 6.1 Boundary

**Inside the boundary**

- One community-scale area and its population
- All wireless devices held by that population, plus any deliberately provisioned relays
- Stored energy and local charging capability (vehicle, generator, solar)
- Services hosted on nodes inside the network
- Message traffic generated inside the community
- Terrain, structures, water and elevation as they affect radio propagation
- Human participation decisions: who owns, powers, carries and keeps a device active

**Outside the boundary**

- The wider internet. This is definitional, not a simplification: the instrument's subject is what a network can do *without* it. An internet gateway is a SECONDARY feature precisely so its absence is the default case.
- Cellular and ISP infrastructure. Assumed unavailable for the run horizon; staged restoration is SECONDARY.
- Commercial restoration logistics, emergency-management command structures, mutual-aid dispatch.
- Spectrum regulation, licensing and legal constraints.
- Physical rescue, medical outcomes, evacuation logistics. The instrument measures whether a message arrived, never what the recipient then achieved. See §19.
- Adversarial interference and jamming (FUTURE).

### 6.2 Time

**Two processes, one clock.** The system contains fast processes (message transmission, queueing) and slow ones (energy depletion, repositioning, participation change) separated by several orders of magnitude. Architecturally this is a single event-driven clock in seconds; slow processes are scheduled as coarse periodic events. The model must never mix a step-based slow loop with an event-based fast loop — that is the classic source of unreproducible ordering.

- **Run horizon:** a user control, on the order of days. *Default value: Pending Research & Model Engineer review* — it must follow documented outage durations, not intuition.
- **Phase structure:** Phase 1 (provisioning) occurs at t < 0 and consumes no simulated time. Phase 2 (event) runs from t = 0 to the horizon.
- **Censoring:** a message still undelivered at the horizon is a **lower bound on its delivery time, not a missing observation.** Reporting must be censoring-aware. This convention already exists in the Atlas (`ferry-terminal`) and must be inherited, not reinvented.

### 6.3 Space

Continuous 2D, abstract and parameterised — not georeferenced.

- A settlement-pattern generator producing habitation, with a preset expressing the linear road-and-water settlement geometry characteristic of South Louisiana coastal parishes.
- An **obstruction field** over the plane (structures, vegetation, open water, elevation) modifying propagation.
- **Charging-resource sites** as a spatial layer.

**Rationale for abstraction over real parish data:** georeferenced data would import an evidence burden the instrument cannot discharge — every propagation result would become a claim about a real place, defensible only with measurements that do not exist. The abstract landscape carries a preset that *resembles* South Louisiana without asserting it *is* South Louisiana, and the same model generalises to rural regions, expeditions, maritime operations and protests, as the brief intended.

---

## 7. Entities

**E1 — Node (device).** A radio-capable device.
Properties: position; mobility class (fixed / relocatable / carried); radio profile (an abstract power/sensitivity class, **never a named technology** — see §16 REJECT-1); energy store and state-dependent draw; role set (endpoint, relay, service host, charging-attached); transmit queue; routing state; liveness (active / asleep / depleted / failed / removed).

**E2 — Person / household.** A population unit. **Deliberately distinct from Node.** Properties: location; device ownership (may be zero); participation state; need profile by message class; current service-reachability status.

The separation is not bookkeeping. Every metric that matters to the brief's fourth layer is a statement about people, and a device-only model silently answers a different question — it measures the network's service to itself.

**E3 — Message.** Properties: class (emergency / coordination / routine / bulk); origin; destination (unicast, broadcast, or service-request); size; creation time; deadline (class-dependent); state (queued / in-flight / delivered / dropped / **undelivered-at-horizon = censored**).

**E4 — Link.** A derived, not stored, pairwise relation: exists when mutual received signal clears a threshold given range, radio profiles and the obstruction field. Carries a finite capacity and a loss rate. Recomputed on any positional or liveness change.

**E5 — Service.** A capability hosted on one or more nodes (bulletin, household roster, map, clinic triage queue, message store). Available to a person only if a host is *reachable* **and** *powered*. Replication factor and siting are provisioning decisions.

**E6 — Terrain cell.** Obstruction coefficient, elevation, water flag, charging availability.

---

## 8. Variables

### 8.1 User Controls — Phase 1 (Provisioning, before the event)

| Control | Description |
|---|---|
| Device budget | Total provisioning resource, spendable across the choices below |
| Device count and distribution policy | Random household distribution / strategic relay siting / hybrid |
| Radio profile mix | How many of each abstract power class |
| Relay siting | Explicit placement of dedicated relay nodes |
| Stored energy per class | Battery capacity provisioned per node class |
| Charging resource placement | Where vehicle / generator / solar charging exists |
| Service hosting | Which services exist, on which nodes, at what replication |
| Participation rate | Fraction of the population that owns and activates a device |

### 8.2 User Controls — Phase 2 (Intervention, during the event)

| Control | Description |
|---|---|
| Reposition node | Relocate a relocatable node; incurs travel time and transit outage |
| Allocate charging | Direct a limited charging resource to a chosen node |
| Routing policy | Flat (class-blind) vs emergency-priority scheduling |
| Traffic throttle | Suppress a routine/bulk class to protect capacity |
| Service relocation | Move or replicate a hosted service to another node |

Every Phase 2 action is logged with its timestamp so that outcomes remain attributable to decisions. See §20(B).

### 8.3 Model Parameters — require empirical grounding

All of the following are **Pending Research & Model Engineer Review**. No values are proposed here.

- Range-versus-obstruction relation (path-loss form and coefficients over vegetation, structures, open water, elevation)
- Per-state energy draw: idle, receive, transmit, sleep — and the relationship between relay traffic volume and drain
- Effective link capacity and protocol overhead fraction under multi-hop contention
- Message generation rates and size distributions by class, and how they change during an emergency
- Deadline conventions per message class
- Repositioning travel speeds under obstructed conditions
- Node failure hazard rates (non-energy causes: water, damage, loss)
- Charging rates by resource type and fuel/insolation availability over a multi-day horizon
- Participation dynamics: initial ownership, activation, and abandonment
- Failure thresholds for I1, I2 and I3, used by the layer-of-first-failure marker (§13.3)

### 8.4 State Variables

Node energy; node liveness; node position; queue depth per node and class; routing state; message state vector; the dynamic link set; connected-component structure and partition membership; service-reachability set per person; population reachability over time; cumulative energy consumed.

### 8.5 Outputs

See §13.

---

## 9. Candidate Model Architecture

```
MODEL FAMILY DECISION: Pending Research & Model Engineer review.

Research question the engineer must answer:
  Is deliverability in a community-scale standalone mesh dominated by
  (a) queueing and contention for finite capacity, or
  (b) topology dynamics driven by energy, loss and human participation?

Alternatives:
  A. Discrete-event network simulation over a dynamic graph, with explicit
     message queueing and scheduling. Strongest if (a) dominates.
  B. Agent-based model: nodes and people as agents, forwarding as behaviour.
     Strongest if (b) dominates; natural home for participation and mobility.
  C. Hybrid: ABM for people, participation, energy and position; DES for the
     traffic layer. Highest fidelity, highest complexity, hardest to validate.
  D. Analytic percolation / graph-robustness layer — as a validation benchmark
     against which the simulation engine is checked, not as the engine.

Decision criteria:
  - Whether published mesh-resilience results attribute failure primarily to
    congestion collapse or to topological partition
  - Whether emergency-class delivery is deadline-bound (favours A) or
    reachability-bound (favours B)
  - Computational budget for in-browser execution at the population scale of §6
  - Availability of a published benchmark the model can be checked against;
    D should be available regardless, as the check on A/B/C
```

### Atlas taxonomy conflict — must be resolved before publication

`assets/catalogue.js` declares `TAXONOMY.model` as exactly:

```
["Agent-based", "Differential equation", "Statistical", "Historical reconstruction"]
```

**There is no "Network model" and no "Discrete-event" entry.** Whichever of A–D is selected, the instrument's honest model family is not currently expressible in the Atlas vocabulary.

**Taxonomy fit unresolved.** Two admissible resolutions, to be decided at Stage 06 (Atlas Curator), not invented here:

1. Extend `TAXONOMY.model` with `"Network model"` (and, if C is chosen, `"Discrete-event"`), updating the filter bar. This is a schema change affecting the homepage.
2. Classify as `"Agent-based"` if alternative B or C is selected, which is defensible but understates the network-structural core.

Option 2 is **not** available if alternative A is selected. Do not paper over this by labelling a discrete-event network simulation "Agent-based".

---

## 10. Mechanisms to Represent

| # | Mechanism | Layer | v1 |
|---|---|---|---|
| M1 | Link formation from range, radio profile and the obstruction field | Physical | CORE |
| M2 | Multi-hop routing and rerouting over a dynamic graph | Routing | CORE |
| M3 | Finite capacity, queueing, congestion; message classes; scheduling policy as a *comparable* choice, not a fixed rule | Routing | CORE |
| M4 | Energy: state-dependent draw, depletion, charging | Physical / participation | CORE |
| M5 | Node loss: random failure versus targeted removal of high-centrality nodes | Physical | CORE |
| M6 | Service hosting, replication and availability | Service | CORE |
| M7 | Participation: population-to-device mapping, activation, abandonment | Human | CORE |
| M8 | User repositioning of a relocatable node, with travel time | Physical | CORE (see note) |
| M9 | Autonomous stochastic mobility of many carried nodes; store-carry-forward routing across partitions | Routing | SECONDARY |

**Note on M8/M9.** Mobility was not selected for v1, but the two-phase design requires the user to be able to move a node. These are separated: v1 contains **discrete, user-initiated relocation with travel time and transit outage** (M8) — a decision, not a process. Continuous stochastic mobility of a population of carried devices, and the delay-tolerant store-carry-forward routing it enables, is a different and much larger mechanism (M9) and is SECONDARY. This split is stated explicitly so that Stage 02 does not quietly implement M9 while believing it is implementing M8.

M3 carries a design constraint: the scheduling policy must be **selectable and comparable**, never hardcoded. Hardcoding emergency priority would answer SQ3 by construction.

M5 carries a design constraint: targeted loss must be definable by a **stated centrality criterion** (degree, betweenness, or traffic volume) exposed to the user, because SQ2 asks whether energy depletion *reproduces* targeted loss — which is unanswerable if "targeted" is not independently defined.

---

## 11. Assumption Register

| # | Assumption | Importance | Research needed |
|---|---|---|---|
| A1 | Radio behaviour can be abstracted to a range/obstruction/capacity triple without naming a technology | **Critical** | Yes — bounds within which the abstraction holds |
| A2 | An abstract landscape with a regional preset is sufficient; georeferenced data is not required | High | No — architectural decision, recorded |
| A3 | Cellular and internet infrastructure remain unavailable for the whole horizon unless restoration is enabled | High | Yes — documented outage durations |
| A4 | Relay traffic volume drives energy drain enough for depletion to correlate with centrality | **Critical** (SQ2 depends on it) | Yes — per-state draw and duty cycle |
| A5 | A message is "delivered" on arrival at the destination node; human receipt is not modelled | High | No — boundary decision, see §19 |
| A6 | Message classes have distinct deadlines and those deadlines are meaningful | Medium | Yes — operational conventions |
| A7 | Participation is exogenous in v1: people do not join or abandon in response to whether the network is working | **Critical** | Yes — the feedback loop is real; see §20(F) |
| A8 | Charging resources have finite, exhaustible supply (fuel, insolation) over a multi-day horizon | High | Yes — realistic multi-day availability |
| A9 | Population and device positions are fixed except for M8 relocation | Medium | No — v1 scope decision |
| A10 | Provisioning costs are commensurable on a single budget axis | Medium | Yes — relative cost of relays vs devices vs batteries |
| A11 | Terrain does not change during the run (no ongoing flooding, no debris) | Medium | Yes — whether post-event landscape change is material |
| A12 | Protocol overhead can be represented as a capacity fraction rather than simulated | High | Yes — whether this holds under multi-hop contention |
| A13 | Interference is limited to obstruction and self-contention; no adversarial or external interference | Medium | No — FUTURE scope |

---

## 12. User Investigation Loop

Each loop states what the user does, what the model runs, what is observed, and what question it illuminates. **No loop states what the model will produce.**

### Loop 1 — Does connectivity buy usefulness? (SQ1)

1. **User action:** Provision a configuration and set service hosting to *none*. Commit and run.
2. **Model operation:** Simulate the full horizon; record structural connectivity and service availability separately.
3. **Observable:** The connectivity indicator and the service-access indicator on the same timeline; then re-run at identical seed with one hosted, replicated service and compare the two indicators pairwise.
4. **Question:** Does structural connectivity constrain, predict, or fail to predict what people can actually do?

### Loop 2 — Is depletion targeted? (SQ2)

1. **User action:** Run the baseline with energy depletion enabled and no imposed failures. Then, at the same seed, disable depletion and impose (a) random loss and (b) centrality-targeted loss, matched on total nodes lost.
2. **Model operation:** Three runs on a shared realisation; record the centrality distribution of lost nodes and the timing of loss.
3. **Observable:** Compare the centrality profile of energy-depleted nodes against the two imposed-loss profiles, and compare the resulting delivery indicators.
4. **Question:** Does energy depletion select nodes the way a targeted attack does?

### Loop 3 — What does priority cost? (SQ3)

1. **User action:** Hold provisioning and seed fixed. Run under flat scheduling, then under emergency-priority scheduling. Repeat both at an elevated routine-traffic setting.
2. **Model operation:** Four runs on a shared realisation.
3. **Observable:** Emergency delivery-within-deadline and routine delivery-within-deadline, each reported with its censored fraction, across the 2 × 2 grid.
4. **Question:** What is the exchange rate between emergency and routine service, and is it constant across congestion levels?

### Loop 4 — Repair or disturbance? (SQ4)

1. **User action:** During a run, identify a partition and reposition a relocatable node toward it.
2. **Model operation:** Continue the run with travel time and transit outage applied; a counterfactual run continues from the same state with no intervention.
3. **Observable:** Population service access at the origin and destination regions separately, before and after the move, against the no-intervention counterfactual.
4. **Question:** Under what geometry does the gain at the destination exceed the loss at the origin?

### Loop 5 — Few strong or many weak? (SQ5)

1. **User action:** Build two provisionings at equal budget: one favouring few high-power, well-powered, sited relays; one favouring many ordinary distributed devices. Run each across a set of seeds.
2. **Model operation:** Matched-budget comparison across a seed set; damage realisation shared within each seed.
3. **Observable:** The three-layer indicator profile for each provisioning, with dispersion across seeds shown, not just the central tendency.
4. **Question:** Which provisioning strategy is better, and — as importantly — which is more *variable*?

---

## 13. Required Outputs and Visualizations

### 13.1 The three primary indicators — reported as a profile, never collapsed

The instrument's headline is a **resilience profile of three layer-resolved indicators shown together**, on a shared timeline:

- **I1 — Structural connectivity.** Largest connected component as a share of active nodes; partition count; isolated-household count.
- **I2 — Priority delivery.** Fraction of emergency-class messages delivered within deadline, reported with the censored fraction shown explicitly. Reported separately for each class; never averaged across classes.
- **I3 — Population service access.** Fraction of *people* (not devices) able to reach at least one powered, hosted service.

### 13.2 The composite index — accepted, with a recorded objection

A composite resilience index over I1–I3 was requested and is included, under three binding constraints:

1. **The weights are user-visible and user-editable.** No fixed weighting is asserted, because none is defensible.
2. **The composite is never displayed without its three components adjacent to it.**
3. **Run comparison is reported on the profile.** The composite may order runs; it may not be the only thing shown when they are ordered.

*Recorded architectural objection:* a composite is precisely the mechanism by which the layer distinction — the instrument's stated reason to exist — becomes invisible. A network that routes perfectly and hosts nothing produces a mid-range composite that looks like partial success and is in fact total service failure. The constraints above are what make the composite admissible rather than harmful. Stage 03 (Experience Designer) must treat constraint 2 as non-negotiable.

### 13.3 Supporting outputs

- Message latency distributions by class, with censored observations retained
- Energy consumed and energy remaining, per node class and in aggregate
- Node liveness timeline: alive / asleep / depleted / failed
- Coverage over time: fraction of population within any active link
- **Isolated-population trace:** who was unreachable, for how long, and where — a distribution over people, not an average
- Queue-depth and drop counts, by node and class
- Layer-of-first-failure marker: which of I1/I2/I3 crossed its threshold first, and when.
  *The threshold definitions for each indicator are Pending Research & Model Engineer Review* — they determine what "failure" means and may not be set by intuition.

### 13.4 Visualizations

- Live network view over the landscape: nodes by liveness and energy, links by capacity/load, partitions distinguished, service hosts marked, people without access marked
- The three-indicator timeline, always co-plotted
- Run-comparison view for shared-realisation contrasts
- A layer diagram making the four-layer distinction explicit and clickable, since it is the instrument's central conceptual claim

---

## 14. Baseline & Comparison Scenarios

All comparisons are **shared-realisation**: same seed, same generated landscape, same damage, same traffic demand. Only the named factor differs. This convention is inherited from `ferry-terminal`.

**Baseline B0 — reference configuration.** A committed provisioning under default landscape and damage. Reference condition only; no expected outcome is stated.

**Null baseline B-null — no network at all.** All devices inactive. Establishes the floor. *This scenario is CORE and mandatory.* Without it the instrument cannot express the finding that a mesh added nothing, and becomes an advertisement rather than an instrument. See §20(D).

| # | Contrast | Isolates | From brief |
|---|---|---|---|
| C1 | Random device distribution vs strategically sited relays | Siting policy | ✓ scenario 1 |
| C2 | All nodes fixed vs relocation permitted in Phase 2 | Intervention value | ✓ scenario 2 (partial — see M8/M9) |
| C3 | Random node loss vs centrality-targeted loss, matched count | Loss regime | ✓ scenario 3 |
| C4 | Flat scheduling vs emergency-priority scheduling | Routing policy | ✓ scenario 4 |
| C5 | Fixed battery stock vs charging resources available | Energy regime | ✓ scenario 5 |
| C6 | Fully decentralised routing vs a small number of high-capacity hub nodes | Topology strategy | ✓ scenario 6 |
| C7 | High participation with low-capability devices vs low participation with high-capability devices, at matched budget | Participation vs capability | ✓ scenario 7 |
| C8 | Services hosted inside the network vs no hosted services | Service layer | New — required by SQ1 |
| C9 | B0 vs B-null | Whether the network helps at all | New — required for honesty |

Each contrast states **what changes**. None states what the model will produce.

---

## 15. Reproducibility Requirements

- **Single seed governs everything stochastic:** landscape generation, damage realisation, traffic generation, failure draws, and any routing tie-breaks.
- **Shared realisation across compared runs** is a first-class feature, not an option buried in settings: two runs differing in one factor must be able to share the identical world.
- **Deterministic event ordering.** Simultaneous events must resolve by a stated, seeded rule. Without this, the two-clock structure of §6.2 will produce runs that do not reproduce.
- **Run manifest** capturing every Phase 1 control, every timestamped Phase 2 intervention, the seed, the parameter set version, and the instrument version.
- **Export** of the manifest plus indicator time series, sufficient to reconstruct any reported figure.
- **Reset** returns to the committed provisioning, not to factory defaults, so a scenario can be re-run after intervention.
- **Phase 2 interventions are part of the manifest,** because in a two-phase design the intervention log *is* part of the experimental condition.

---

## 16. Scope

Every element proposed in the originating concept receives an explicit disposition below. Nothing is silently dropped.

### CORE (v1)

| Element | Source |
|---|---|
| Fixed nodes: homes, shelters, clinics, command posts, repeaters | Brief |
| Radio range and signal degradation (abstracted, technology-neutral) | Brief |
| Terrain and structural interference | Brief + user selection |
| Message routing and rerouting over a dynamic graph | Brief |
| Bandwidth, congestion and queueing | Brief + user selection |
| Message priority classes and selectable scheduling policy | Brief + user selection |
| Battery capacity and charging availability | Brief + user selection |
| Node failure, random and centrality-targeted | Brief + user selection |
| Service hosting and availability (the third layer) | Brief |
| Human participation: population-to-device mapping | Brief (fourth layer) |
| Person entity distinct from Node | Architect |
| Two-phase play: provisioning then intervention | User selection |
| User repositioning with travel time (M8) | Required by two-phase design |
| Delivery rate, latency, coverage, isolated populations, energy consumption | Brief |
| Three-layer indicator profile (I1/I2/I3) | Brief's four-layer framing |
| User-weighted composite index, constrained per §13.2 | User selection |
| Censoring-aware reporting of undelivered messages | Atlas convention |
| Null baseline B-null | Architect — required for outcome neutrality |
| Shared-realisation run comparison | Atlas convention |
| Contrasts C1–C9 | Brief scenarios 1–7 plus SQ1 and honesty |

### SECONDARY (post-v1, valuable)

- **Autonomous stochastic mobility and store-carry-forward routing (M9).** The brief's mobile nodes — people, vehicles, boats, drones — as a *process* rather than a user action. Deferred because it is a second routing paradigm (delay-tolerant networking), not an increment on the first.
- **Internet gateway.** A single node with outside connectivity. Deferred deliberately: making it SECONDARY keeps "no internet" the default and prevents the instrument drifting into a backhaul study.
- **Staged infrastructure restoration** during the horizon.
- **Endogenous participation** — people joining or abandoning in response to whether the network works (relaxes A7).
- **Multi-community / inter-settlement bridging.**
- **Ongoing landscape change** during the run: continued flooding, debris (relaxes A11).

### FUTURE

- **Evidence-grounded radio-technology parameter profiles.** Once the general model is validated, LoRa, Wi-Fi HaLow, Bluetooth Mesh and Meshtastic may be expressed as *parameter profiles with citations* — the brief's own sequencing, and correct.
- Adversarial interference and jamming (relaxes A13).
- Cost/logistics realism: procurement lead times, supply constraints.
- Sensor and telemetry traffic as a distinct class.
- Georeferenced landscape import as an optional layer, once the abstract model is validated.

### REJECT (v1)

- **REJECT-1 — Selecting a specific radio technology at architecture time.** Explicitly excluded, per the brief's own strongest caution. Naming a technology converts the instrument into a product comparison and imports parameter commitments the model cannot yet defend.
- **REJECT-2 — Protocol-accurate MAC-layer simulation.** Belongs to ns-3 or equivalent, not to a browser instrument. The abstracted capacity model (A12) is the correct level; if Stage 02 finds A12 untenable, that is a return-loop to this specification, not a licence to build a packet simulator.
- **REJECT-3 — Real georeferenced parish data in v1.** See §6.3. Available later as FUTURE once the abstraction is validated.
- **REJECT-4 — Spectrum, licensing and regulatory modelling.** Outside the boundary; adds no discriminating power for the research question.
- **REJECT-5 — A single unlabelled resilience score as the sole headline output.** Superseded by §13.2. The composite survives only with its components visible.
- **REJECT-6 — Modelling outcomes downstream of message delivery** (whether help arrived, whether anyone was saved). The instrument measures communication, not rescue. See §19.

### RESEARCH-DEPENDENT (routed to Stage 02)

- Final model family: A / B / C / D per §9
- Whether A12 (overhead as a capacity fraction) survives contact with multi-hop contention evidence
- Whether A4 (traffic-driven drain correlating with centrality) is supported — SQ2 collapses if it is not
- Run-horizon default, deadline conventions, and all §8.3 parameters

---

## 17. Atlas Classification

Draft record for `assets/catalogue.js`, using the schema that file actually declares:

```
id:          "towers-dark"
title:       "When the Towers Go Dark"
href:        "towers-dark/towers-dark.html"
methods:     "towers-dark/methods.html"
preview:     "towersdark"
thumb:       null

domain:      "Society"
mode:        ["Design", "Diagnose", "Measure"]
duration:    "Deep session"
complexity:  "Advanced"
model:       TAXONOMY FIT UNRESOLVED — see §9
state:       "Development"
evidence:    null      (renders as the dashed "Status pending" chip)
basis:       null      (no published work identified yet; must not be invented)

version:     "0.1.0"
updated:     Pending build
flags:       ["New", "Experimental"]

question:    "When the towers go dark, what can a community's own devices still deliver — and which layer gives out first?"
role:        Pending Stage 03 (Experience Designer)
blurb:       Pending Stage 03
chips:       Pending Stage 03
```

**Schema note.** The catalogue has no `subtitle` field. *Resilience in Standalone Wireless Mesh Networks* is a document-level technical subtitle for the methods page and README; it must not be appended to `title`, which is the card heading and the filter label.

**Notes on classification choices**

- **Mode.** `Design` leads, because Phase 1 is a provisioning decision. `Diagnose` and `Measure` are added because Phase 2 is diagnostic and the whole apparatus is measurement. The brief's proposed secondary domain "engineering/communications" **does not exist in the Atlas domain vocabulary** (`Physics · Biology · Ecology · Society · Earth · Cognition`) and the catalogue schema has no secondary-domain field. `Society` alone is correct, and it is the honest one: the fourth layer is the reason.
- **Evidence.** `null`, per the catalogue's documented convention — visibly unfinished rather than quietly overclaiming. Any evidence class before Stage 05 would be fabricated.
- **Complexity.** `Advanced`. The v1 mechanism set is large (M1–M8) and the instrument's central point requires the user to read four layers at once.
- **Duration.** `Deep session`. Two-phase play with shared-realisation comparison is not a ten-minute instrument.

---

## 18. Scientific Work Required (Stage 02)

1. **Propagation abstraction.** Literature on range versus obstruction for low-power community wireless; establish the bounds within which a range/obstruction/capacity triple substitutes for a link budget (A1).
2. **Energy.** Per-state draw and duty-cycle behaviour; the empirical relationship between forwarding load and drain (A4 — SQ2 depends entirely on this).
3. **Capacity and overhead.** Whether multi-hop contention permits representation as a capacity fraction (A12, REJECT-2).
4. **Outage durations.** Documented restoration timelines after major coastal storms, to ground the horizon.
5. **Traffic.** Message generation rates, sizes and class mix during emergencies; deadline conventions per class.
6. **Network robustness benchmarks.** Published random-versus-targeted removal results against which the model's D-layer check can be validated.
7. **Mesh field evidence.** Documented deployments of community mesh networks during infrastructure outages — what was delivered, what failed, and at which layer.
8. **Charging realism.** Multi-day availability of vehicle, generator and solar charging under post-storm fuel and weather constraints (A8).
9. **Participation.** Device ownership, activation and abandonment in affected populations (A7).
10. **Costs.** Relative provisioning costs to make the single budget axis commensurable (A10).
11. **Model family decision.** Resolve §9 A/B/C/D against criteria stated there.
12. **Evidence class recommendation** for Stage 05/06, with the specific work that would justify it.

---

## 19. Known Limitations

**This instrument will not establish:**

- That any particular radio technology is suitable for disaster communication. It is technology-neutral by construction (REJECT-1).
- Whether a real community would have this network, these devices, or this participation. Provisioning is a user decision, not a forecast.
- Any outcome downstream of message delivery. A message arriving at a node is not a person reading it, not help dispatched, and not a life saved (A5, REJECT-6). The instrument measures communication and stops there — deliberately, because the alternative is a model that implies rescue outcomes it cannot support.
- Quantitative predictions for a named place. The landscape is abstract (A2, REJECT-3).
- Protocol-level performance figures. The capacity model is abstracted (A12, REJECT-2).
- Behaviour under adversarial interference (A13).
- Whether people would participate. Participation is exogenous in v1 (A7).

**Survivorship boundary.** The instrument models a community that has some devices, some energy and some willingness. It is silent on communities that have none, and its results must not be read as generalising to them.

---

## 20. Assumption Challenge

**(A) "Resilient" was doing work no measurement could support.** Addressed in §3 by refusing to let resilience be a property in the question, and in §13 by making it a three-part profile. The word survives in the title, where it belongs, and nowhere in the model.

**(B) Two-phase play weakens attribution.** The user chose provisioning *and* intervention. This is scientifically richer and it makes outcomes harder to attribute: a good result may come from good provisioning, good intervention, or a mild damage draw. Mitigations are structural, not cosmetic — timestamped intervention logs (§8.2), the intervention log as part of the run manifest (§15), and the counterfactual continuation in Loop 4. **Stage 03 must not let Phase 2 become continuous fiddling**, or every run becomes an uncontrolled trial. A bounded intervention budget is the natural instrument-side answer and is recommended to the Experience Designer.

**(C) The composite index is the single most dangerous element in this specification.** Recorded in full at §13.2. Retained on the user's decision, constrained so that it cannot hide the layer distinction. Flagged again here so it cannot be quietly deconstrained downstream.

**(D) The concept assumes a mesh is the right response.** The brief's framing — "how much infrastructure can a community reconstruct" — presumes reconstruction is possible and worthwhile. An instrument that can only show degrees of mesh success is an advertisement. Hence B-null (no network at all) is CORE and mandatory (§14). The instrument must be able to conclude that the network delivered nothing that mattered.

**(E) "Community reconstructs infrastructure" attributes agency where damage may dominate.** If the damage realisation determines the outcome and provisioning barely moves it, that is a finding, not a failure — and the dispersion-across-seeds requirement in Loop 5 is what makes it visible. Reporting central tendency alone would hide it.

**(F) Participation is a feedback loop that v1 cuts.** A7 fixes participation exogenously, but people abandon a network that is not working, which degrades it further — a plausible collapse mechanism the v1 model cannot exhibit. This is an honest simplification, not an oversight, and it is the strongest candidate for v1.1. It must appear in the methods page's limitations, not only here.

**(G) The abstraction may make range dominant by construction.** If links are a range threshold modified by obstruction, and everything else is downstream of link existence, the model may find range decisive because it was built to be. Stage 02 must include a sensitivity check that would detect this — if I1, I2 and I3 all move monotonically with one parameter, the model is an elaborate restatement of that parameter.

**(H) Terminology.** "Standalone" is preferred to "off-grid" and "resilient" throughout: it states the technical condition (no upstream infrastructure) without implying virtue or self-sufficiency.

---

## 21. Acceptance Criteria

The architecture is satisfied when the built instrument can:

1. Report I1, I2 and I3 **on one timeline, simultaneously**, for any run.
2. Produce a run in which structural connectivity is high and population service access is at or near zero — demonstrating the layer distinction is real in the model, not only in the prose (SQ1).
3. Run two configurations against an **identical** landscape, damage and traffic realisation, differing in exactly one named factor, and report both (C1–C9).
4. Report undelivered messages as **censored observations**, never dropped from latency statistics.
5. Report the isolated population as a **distribution over people**, with location and duration — not as an average.
6. Execute B-null and report it alongside B0 without special-casing.
7. Reproduce any run exactly from its manifest, including Phase 2 interventions.
8. Display the composite index only with I1, I2 and I3 adjacent, with user-editable weights.
9. Show the layer at which a run first failed.
10. Contain **no named radio technology** anywhere in the model, the controls or the copy.
11. State every unresolved assumption from §11 on its methods page.
12. Run entirely offline, day and night themed, per Atlas convention.

---

## 22. Handoff Contract

```
CONTRACT_TYPE: EXECUTION_HANDOFF
GATE_STATUS: PASS
NEXT_STAGE: 02_RESEARCH_MODEL_ENGINEER
RETURN_STAGE: NONE
BLOCKERS: NONE

PRIMARY_RESEARCH_QUESTION:
  When conventional infrastructure is unavailable, which of a community's own
  resources — device density, relay siting, stored energy, participation, and
  the decision to host services locally — most determines what a standalone
  wireless network can still deliver, and at which layer does it fail first?

SYSTEM_BOUNDARY:
  One community-scale area over a horizon of days. Inside: devices, people,
  energy, hosted services, local traffic, terrain, participation. Outside: the
  internet, cellular infrastructure, emergency-management structures, spectrum
  regulation, adversarial interference, and all outcomes downstream of message
  delivery.

REQUIRED_MECHANISMS:
  M1 link formation (range × obstruction); M2 multi-hop routing and rerouting;
  M3 capacity, queueing, message classes, selectable scheduling policy;
  M4 energy draw, depletion and charging; M5 random vs centrality-targeted
  node loss; M6 service hosting and availability; M7 participation and the
  population-to-device mapping; M8 user repositioning with travel time.
  (M9 autonomous mobility and store-carry-forward: SECONDARY, not v1.)

CANDIDATE_MODEL_FAMILY:
  UNRESOLVED — A discrete-event network simulation / B agent-based /
  C hybrid / D analytic percolation as validation benchmark. Criteria in §9.
  NOTE: Atlas TAXONOMY.model has no "Network model" or "Discrete-event"
  entry; taxonomy fit unresolved, to be settled at Stage 06.

VARIABLES_REQUIRING_EMPIRICAL_GROUNDING:
  Range/obstruction relation; per-state energy draw and load-to-drain
  relationship; effective link capacity and overhead fraction; message
  generation rates, sizes and class mix; per-class deadlines; repositioning
  travel speeds; non-energy failure hazards; charging rates and multi-day
  availability; participation rates; relative provisioning costs; run horizon.

ASSUMPTIONS_REQUIRING_VALIDATION:
  A1 technology-neutral radio abstraction (critical)
  A3 outage persists for the horizon
  A4 traffic-driven drain correlates with centrality (critical — SQ2 depends)
  A6 class deadlines are meaningful
  A7 exogenous participation (critical — cuts a real feedback loop)
  A8 finite exhaustible charging supply
  A10 commensurable provisioning costs
  A11 static terrain during the run
  A12 overhead as a capacity fraction (critical — REJECT-2 depends)

REQUIRED_DATASETS:
  Post-storm infrastructure restoration timelines; emergency traffic
  characterisation; low-power wireless propagation measurements in vegetated,
  built and over-water settings; device energy profiles; documented community
  mesh deployments during outages; published network-robustness benchmarks
  for random vs targeted removal.

REQUIRED_EVIDENCE:
  Sufficient grounding to justify an evidence class at Stage 05. Until then
  evidence remains null ("Status pending"). No basis record may be asserted.

UNRESOLVED_SCIENTIFIC_QUESTIONS:
  1. Is deliverability dominated by congestion or by topological partition?
  2. Does energy depletion reproduce targeted-attack loss dynamics? (SQ2)
  3. Is the abstracted capacity model defensible under multi-hop contention?
  4. What is the operational definition of "usable service" in documented
     outages, and does the three-layer decomposition match it?
  5. Is there published evidence discriminating the few-strong-nodes and
     many-weak-nodes provisioning strategies? (SQ5)
```

---

*Stage 01 complete. This specification is a contract, not a summary. Downstream stages may return it upstream with cause; they may not reinterpret it silently.*
