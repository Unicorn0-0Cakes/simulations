/* =====================================================================
   FERRY TERMINAL — configuration, control register and copy
   ---------------------------------------------------------------------
   Everything the interface says about the model lives here, so a control
   can never drift from the scientific meaning Stage 03 specified.

   NOTHING IN THIS FILE IS MEASURED. Every default is a neutral
   exploratory starting point, explicitly labelled as such, and carries
   no claim of typicality.
   ===================================================================== */
(function (global) {
  "use strict";

  /* The neutral exploratory starting point (§9). Not empirical, not
     calibrated, not historical, not "typical". */
  var BASELINE = {
    lam: 40,
    rho: 0.5,
    leadTimeMean: 10,
    headway: 30,
    capacityM: 60,
    horizon: 300,
    warmup: 30,
    lengthDist: "ALL_EQUAL",
    equalLengthM: 5,
    bookedFraction: 0,
    policy: "FCFS",
    seed: 1,
    disruption: null
  };

  /* §7 Control Register. `key` matches the model config exactly. */
  var CONTROLS = [
    { key: "rho", group: "Arrivals", label: "Arrival mixture", symbol: "ρ", unit: "",
      kind: "range", min: 0, max: 1, step: 0.01,
      meaning: "The share of vehicles arriving indifferent to the timetable.",
      ends: ["fully timetable-targeted", "fully random"],
      note: "The central investigable question. The assumption that arrivals are simply Poisson was rejected on published evidence at Stage 02." },

    { key: "lam", group: "Arrivals", label: "Mean arrival rate", symbol: "λ", unit: "vehicles / hour",
      kind: "number", min: 0.1, max: 400, step: 0.1,
      meaning: "How many vehicles reach the terminal per hour, on average.",
      note: "Sets the load ratio with headway and capacity." },

    { key: "leadTimeMean", group: "Arrivals", label: "Targeted lead time", symbol: "D", unit: "minutes",
      kind: "range", min: 0, max: 60, step: 1,
      meaning: "How early, on average, a timetable-targeted vehicle appears before its sailing.",
      note: "Clamped below the headway. Determines where waiting accrues." },

    { key: "bookedFraction", group: "Arrivals", label: "Booked share", symbol: "", unit: "",
      kind: "range", min: 0, max: 1, step: 0.01,
      meaning: "The share of vehicles holding a reservation.",
      note: "Only affects the run under the class-priority discipline. No-show behaviour is not modelled." },

    { key: "headway", group: "Service", label: "Headway", symbol: "h", unit: "minutes",
      kind: "number", min: 1, max: 240, step: 1,
      meaning: "Minutes between scheduled departures.",
      note: "Rescales the bound on targeted lead time." },

    { key: "capacityM", group: "Service", label: "Capacity", symbol: "C", unit: "lane-metres",
      kind: "number", min: 1, max: 600, step: 1,
      meaning: "Lane-metres available on each sailing.",
      note: "Below the longest vehicle nothing can board, and the run is blocked rather than looped." },

    { key: "lengthDist", group: "Service", label: "Length distribution", symbol: "ℓ", unit: "",
      kind: "select",
      options: [
        { v: "ALL_EQUAL", t: "All equal — reproduces unit-count capacity exactly" },
        { v: "MIXED", t: "Mixed — an exploratory set spanning the documented Ro-Ro range" }
      ],
      meaning: "How vehicle lengths are distributed.",
      note: "The mixed set is unvalidated at small-terminal scale. Neither representation is marked correct." },

    { key: "equalLengthM", group: "Service", label: "Equal vehicle length", symbol: "", unit: "metres",
      kind: "number", min: 1, max: 30, step: 0.1, showWhen: function (c) { return c.lengthDist === "ALL_EQUAL"; },
      meaning: "The single length used when every vehicle is the same." },

    { key: "policy", group: "Policy", label: "Loading policy", symbol: "π", unit: "",
      kind: "segmented",
      options: [
        { v: "FCFS", t: "First come" },
        { v: "CLASS_PRIORITY", t: "Booked first" },
        { v: "SIZE_AWARE", t: "Shortest first" }
      ],
      meaning: "The order in which the queue is offered to the deck.",
      note: "These are abstract disciplines, not a surveyed taxonomy of practice." },

    { key: "horizon", group: "Run", label: "Horizon", symbol: "T", unit: "minutes",
      kind: "number", min: 10, max: 3000, step: 10,
      meaning: "How long the terminal is observed.",
      note: "A vehicle still queueing at the horizon has a censored, not a missing, time to service." },

    { key: "warmup", group: "Run", label: "Warm-up", symbol: "", unit: "minutes",
      kind: "number", min: 0, max: 1000, step: 5,
      meaning: "Statistics start after this point.",
      note: "Excludes the empty-terminal start. Must be below the horizon." },

    { key: "seed", group: "Run", label: "Seed", symbol: "", unit: "",
      kind: "number", min: 1, max: 999999, step: 1,
      meaning: "Every random decision in the run comes from this number.",
      note: "A scientific control, not a developer setting. Changing it clears the comparison, because a different random stream makes the contrast uninterpretable." }
  ];

  /* Parameters deliberately NOT exposed (§7). Shown in the methods view
     so their absence is legible rather than silent. */
  var NOT_EXPOSED = [
    ["Per-vehicle loading time τ", "NOT ESTABLISHED. An ungrounded control invites false precision."],
    ["Turnaround dwell δ", "NOT ESTABLISHED. Excluded with τ."],
    ["No-show rate ν", "Deferred with the booked / standby distinction."],
    ["Event-queue ordering, warm-up collection flag, generator internals", "Implementation, not science."]
  ];

  var DISRUPTIONS = [
    { v: "NONE", t: "No disruption" },
    { v: "DELAYED", t: "Delay one sailing" },
    { v: "REDUCED", t: "Reduce one sailing's capacity" },
    { v: "CANCELLED", t: "Cancel one sailing" }
  ];

  /* Categorical hues only. No good/bad semantics anywhere (§15). */
  var POLICY_HUE = { FCFS: "teal", CLASS_PRIORITY: "violet", SIZE_AWARE: "gold" };
  /* Policies also differ by marker, so nothing is encoded by colour alone. */
  var POLICY_MARK = { FCFS: "circle", CLASS_PRIORITY: "square", SIZE_AWARE: "triangle" };

  var LENGTH_CLASS_LABEL = { short: "Short (≤ 5.0 m)", medium: "Medium (5.0–8.0 m)", long: "Long (> 8.0 m)" };

  /* Threshold above which the heavy-censoring notice is raised. A display
     threshold, not a model parameter, and stated wherever it fires. */
  var HEAVY_CENSORING_THRESHOLD = 0.25;

  var COPY = {
    question: "How do vehicle arrival patterns and ferry loading policies jointly affect time to service, queue length, throughput, and missed departures at a small single-berth ferry terminal?",
    exploratoryMarker: "Exploratory instrument — all parameters user-specified, none empirical.",
    exploratoryBody: "Every value on this page was chosen by you. Nothing here is measured from a real port, and no result describes one.",
    baselineLabel: "Neutral exploratory starting point — not a typical terminal, not a measured one.",
    firstChange: "Try shifting arrivals from random toward timetable-targeted.",
    seedCleared: "Comparison cleared. The seed changed, so the two runs no longer share an arrival realisation and the difference between them cannot be attributed to the control you moved.",
    seedClearedBody: "The two runs no longer share an arrival realisation, so the difference between them cannot be attributed to the control you moved.",
    singleRun: "One replicate. This is a single run, not an estimate of what these settings usually produce.",
    singleRunBody: "This is one run, not an estimate of what these settings usually produce.",
    warmupNotice: "Statistics begin after the warm-up point. Vehicles arriving before it are simulated but not counted.",
    heavyCensoring: "Heavy censoring. More than a quarter of vehicles never sailed within the horizon, so the observed distribution describes a minority of arrivals and the upper tail of the survival estimate is unreliable.",
    heavyCensoringBody: "The observed distribution describes a minority of arrivals, and the upper tail of the survival estimate is unreliable.",
    unstable: "The queue grows without bound at these settings, so steady-state statistics are not meaningful.",
    censoringPrimer: "Time to service is right-censored: a vehicle still queueing at the horizon has a time to service of at least the time it has already waited. Dropping those vehicles would measure only the ones a policy chose to serve."
  };

  global.FerryConfig = {
    BASELINE: BASELINE,
    CONTROLS: CONTROLS,
    NOT_EXPOSED: NOT_EXPOSED,
    DISRUPTIONS: DISRUPTIONS,
    POLICY_HUE: POLICY_HUE,
    POLICY_MARK: POLICY_MARK,
    LENGTH_CLASS_LABEL: LENGTH_CLASS_LABEL,
    HEAVY_CENSORING_THRESHOLD: HEAVY_CENSORING_THRESHOLD,
    COPY: COPY,
    clone: function (c) { return JSON.parse(JSON.stringify(c)); }
  };
})(typeof window !== "undefined" ? window : globalThis);
