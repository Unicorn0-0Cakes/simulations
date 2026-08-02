/* =====================================================================
   ORBITAL — the catalogue
   ---------------------------------------------------------------------
   One record per instrument. This file is the single source of truth for
   the homepage grid, the filter bar, each methods page and the status
   strip that appears on the simulation pages themselves.

   ADDING AN INSTRUMENT
     Append an object below. Every field marked (required) must be set or
     the card will render an obvious placeholder rather than fail quietly.

   THE TAXONOMIES  — use these exact strings, they drive the filters.

     domain      Physics · Biology · Ecology · Society · Earth · Cognition
     mode        Observe · Diagnose · Design · Measure · Infer
                 (what the person DOES — the most useful axis, list all
                  that genuinely apply, most important first)
     duration    "Under 10 minutes" · "10–30 minutes" · "Deep session"
     complexity  Introductory · Intermediate · Advanced
     model       Agent-based · Differential equation · Statistical ·
                 Historical reconstruction   (array; primary first)
     state       Playable · Research preview · Development
                 (can you use it right now?)

     evidence    THE TRUST-BEARING BADGE — deliberately left null.
                 Set each one yourself to exactly one of:
                   "Historical reconstruction"
                   "Established mathematical model"
                   "Exploratory agent-based model"
                   "Calibrated research model"
                   "Uncalibrated prototype"
                 Anything still null renders as a dashed "Status pending"
                 chip, which is honest and visibly unfinished.

   VERSION NUMBERS
     `version` is a placeholder except for CCE, which reports its own
     (0.1.0-milestone0) in its README. Set these to whatever you actually
     want to claim; nothing else derives from them.
   ===================================================================== */

const CATALOGUE = [

  /* ---------------------------------------------------------------- */
  {
    id: "flask",
    title: "Evolution in a Flask",
    href: "flask/flask.html",
    methods: "flask/methods.html",
    preview: "flask",
    thumb: null,

    domain: "Biology",
    mode: ["Measure", "Observe"],
    duration: "Deep session",
    complexity: "Intermediate",
    model: ["Differential equation", "Historical reconstruction"],
    state: "Playable",
    evidence: null,

    version: "1.0",
    updated: "Aug 2026",
    flags: [],

    question: "Run the same environment twelve times over — does evolution repeat itself?",
    role: "Spend a finite budget of bench hours deciding what is worth measuring, then live with what you chose not to look at.",

    /* kept for the methods page and the simulation's own header */
    blurb: "Twelve populations, the same thin sugar medium, one transfer a day, fifty thousand generations of nothing else happening. Fitness is never reported — it is a competition you set up against something you were careful enough to freeze.",
    chips: ["Twelve parallel worlds", "Muller plots", "Measurement costs time", "Replay experiments"]
  },

  /* ---------------------------------------------------------------- */
  {
    id: "universe-25",
    title: "Universe 25",
    href: "universe-25/universe25.html",
    methods: "universe-25/methods.html",
    preview: "universe25",
    thumb: null,

    domain: "Ecology",
    mode: ["Observe", "Design"],
    duration: "10–30 minutes",
    complexity: "Introductory",
    model: ["Agent-based", "Historical reconstruction"],
    state: "Playable",
    evidence: null,

    version: "1.4",
    updated: "Aug 2026",
    flags: ["Updated"],

    question: "Can abundance without space collapse a society — and can predation prevent it?",
    role: "Set the world's size, resources and predators, then watch the colony move through its phases.",

    blurb: "A living recreation of Calhoun's “mouse utopia” — unlimited resources, limited space. Watch a colony rise and collapse through Growth → Breakdown → Collapse, with predators, terrain, water, fish and birds all interacting.",
    chips: ["Mice & predators", "Terrain & water", "Live charts", "Presets"]
  },

  /* ---------------------------------------------------------------- */
  {
    id: "biosphere",
    title: "Biosphere: Closed World",
    href: "biosphere/biosphere.html",
    methods: "biosphere/methods.html",
    preview: "biosphere",
    thumb: null,

    domain: "Earth",
    mode: ["Diagnose", "Design"],
    duration: "Deep session",
    complexity: "Advanced",
    model: ["Differential equation", "Historical reconstruction"],
    state: "Playable",
    evidence: null,

    version: "1.0",
    updated: "Aug 2026",
    flags: [],

    question: "Why is oxygen disappearing when carbon dioxide is not rising to match?",
    role: "Diagnose a living machine through imperfect instruments, and decide what you will break to keep everyone breathing.",

    blurb: "Eight people, seven biomes and one atmosphere with nowhere to go, sealed inside three acres of glass. The central mechanic is causal diagnosis, not resource accumulation.",
    chips: ["Causal diagnosis", "Carbon & oxygen budget", "Hypothesis workbench", "Historically informed"]
  },

  /* ---------------------------------------------------------------- */
  {
    id: "commons",
    title: "The Commons",
    href: "commons/commons.html",
    methods: "commons/methods.html",
    preview: "commons",
    thumb: null,

    domain: "Society",
    mode: ["Design", "Observe"],
    duration: "10–30 minutes",
    complexity: "Intermediate",
    model: ["Agent-based"],
    state: "Playable",
    evidence: null,

    version: "1.1",
    updated: "Aug 2026",
    flags: [],

    question: "Can a shared system nobody is obliged to maintain survive the incentive not to?",
    role: "Write the society's rules — abundance, visibility, punishment, the accuracy of what people believe — then read what emerged and what it cost.",

    blurb: "Everyone gets their own resources, but survival depends on a shared system nobody is forced to maintain. The interesting question is not whether society survived, but what kind survived and what survival cost it.",
    chips: ["Public-goods game", "Emergent behaviour", "Trust & rumour", "Live dashboard"]
  },

  /* ---------------------------------------------------------------- */
  {
    id: "sentinel",
    title: "Sentinel: The Oversight Experiment",
    href: "sentinel/sentinel.html",
    methods: "sentinel/methods.html",
    preview: "sentinel",
    thumb: null,

    domain: "Society",
    mode: ["Infer", "Measure"],
    duration: "10–30 minutes",
    complexity: "Advanced",
    model: ["Differential equation", "Statistical"],
    state: "Playable",
    evidence: null,

    version: "1.0",
    updated: "Aug 2026",
    flags: ["New"],

    question: "Why did adding more oversight change nothing?",
    role: "Drive twelve levers and read a global sensitivity screen with three decoys wired into it, so the noise floor is measured rather than assumed.",

    blurb: "A spin-off built around the two metrics its parent simulation could not move. Detection delay and governance quality were white noise there — both structurally severed from anything the experiment varied.",
    chips: ["Live global sensitivity", "Decoy-validated ranking", "Bistable capture cascade", "Runs in the page"]
  },

  /* ---------------------------------------------------------------- */
  {
    id: "cce",
    title: "The Cognitive Civilization Experiment",
    href: "cce/cce.html",
    methods: "cce/methods.html",
    preview: "cce",
    thumb: null,

    domain: "Cognition",
    mode: ["Infer", "Observe"],
    duration: "10–30 minutes",
    complexity: "Advanced",
    model: ["Agent-based", "Statistical"],
    state: "Research preview",
    evidence: null,

    version: "0.1.0-milestone0",
    updated: "Aug 2026",
    flags: ["Experimental"],

    question: "Does the rule a society uses to allocate work, housing and office change how long its people live?",
    role: "Read matched-seed contrasts between three societies and judge whether any difference clears the threshold set before the runs.",

    blurb: "Three societies of a hundred thousand people, five hundred years, the same disasters in each. A research instrument rather than a game — matched seeds, preregistered effect sizes, and a model built so that no single number is allowed to explain a person.",
    chips: ["Matched-seed design", "500 simulated years", "Real run data", "Reproducible & checksummed"]
  }
];

/* ---------------------------------------------------------------------
   Featured entry points. Three doors, so nobody has to choose from six.
   ------------------------------------------------------------------ */
const FEATURED = [
  { id: "flask",       kind: "Start here",     why: "The clearest single idea on the site, and the one whose constraint you feel immediately: you cannot measure everything." },
  { id: "universe-25", kind: "Most visual",    why: "A live colony moving on a scope — terrain, predators, phases. Legible in about fifteen seconds without reading anything." },
  { id: "cce",         kind: "Research depth", why: "Twenty-five design documents, 92 registered parameters, matched seeds and a preregistration draft. The strongest apparatus here." }
];

/* ---------------------------------------------------------------------
   Filter vocabularies, in display order.
   ------------------------------------------------------------------ */
const TAXONOMY = {
  domain:     ["Physics", "Biology", "Ecology", "Society", "Earth", "Cognition"],
  mode:       ["Observe", "Diagnose", "Design", "Measure", "Infer"],
  duration:   ["Under 10 minutes", "10–30 minutes", "Deep session"],
  complexity: ["Introductory", "Intermediate", "Advanced"],
  model:      ["Agent-based", "Differential equation", "Statistical", "Historical reconstruction"],
  state:      ["Playable", "Research preview", "Development"]
};

const EVIDENCE_LEVELS = [
  "Historical reconstruction",
  "Established mathematical model",
  "Exploratory agent-based model",
  "Calibrated research model",
  "Uncalibrated prototype"
];

if (typeof window !== "undefined") {
  window.CATALOGUE = CATALOGUE;
  window.FEATURED = FEATURED;
  window.TAXONOMY = TAXONOMY;
  window.EVIDENCE_LEVELS = EVIDENCE_LEVELS;
  window.byId = id => CATALOGUE.find(s => s.id === id);
}
if (typeof module !== "undefined") {
  module.exports = { CATALOGUE, FEATURED, TAXONOMY, EVIDENCE_LEVELS };
}
