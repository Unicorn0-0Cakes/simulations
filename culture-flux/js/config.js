/* culture-flux — copy and constants for the results explorer.
   Prose lives here rather than in the HTML so that the page structure stays
   readable and the wording can be revised without touching the layout. */

const TABS = [
  ["overview",   "Overview"],
  ["mechanisms", "The three mechanisms"],
  ["results",    "Results"],
  ["retracted",  "What was retracted"],
  ["method",     "Method"],
  ["provenance", "Provenance"]
];

const RULE_COLOUR = {
  "null":              "var(--cf-null)",
  "axelrod_homophily": "var(--cf-homophily)",
  "conformist":        "var(--cf-conformist)"
};

const RULE_SHORT = {
  "null":              "Control",
  "axelrod_homophily": "Homophily",
  "conformist":        "Conformist"
};

/* What each arm does, in one sentence each. The control is described first
   because every result on this page is read against it. */
const RULE_TEXT = {
  "null": {
    rule: "Nobody influences anybody",
    body: "The control arm. Agents arrive and stay exactly as they were. Any movement " +
          "in a measurement here is compositional — the mix of people changed, not " +
          "anyone's culture. Retention under this arm is exactly 1 − M·D, and that " +
          "number is arithmetic, not a finding. It is the floor every other arm is " +
          "measured against."
  },
  "axelrod_homophily": {
    rule: "You are influenced by people already like you",
    body: "Two agents interact with probability equal to how much culture they already " +
          "share, and the focal agent copies one feature it does not have. Agents with " +
          "nothing in common cannot influence each other at all, so cultural distance " +
          "is self-reinforcing. A rule in the family Axelrod introduced in 1997 — not a " +
          "verified reproduction of it, because that paper has not been read."
  },
  "conformist": {
    rule: "You are influenced by whatever most people around you do",
    body: "An agent samples several neighbours and adopts a trait with probability " +
          "proportional to its frequency among them, raised to a conformity exponent. " +
          "There is no similarity gate: an agent with nothing in common with its " +
          "neighbours is still influenced by them. A different family from homophily, " +
          "and the mechanism the diversity hypothesis actually depends on."
  }
};

/* Registered assumptions surfaced on the page. IDs match
   docs/research/assumption_registry.md, which is the authority. */
const KEY_ASSUMPTIONS = [
  ["A-016", "The transmission rules were specified in this codebase, not extracted from any paper. The literature review was skipped."],
  ["A-018", "Cultural drift is a free parameter. Every earlier result assumed it was zero, and that default decided the outcome."],
  ["A-019", "How encounters divide between household, neighbourhood, workplace and strangers. Invented numbers."],
  ["A-028", "A finite horizon can report a plateau as an equilibrium. It did, here, twice."],
  ["A-030", "The conformity exponent's default saturates the outcome and should be swept, not treated as a reference."]
];
