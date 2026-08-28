# Culture Flux — User Manual

A guide to operating the instrument. Open `culture-flux.html` in a browser to follow
along. Nothing to install, no build step, no network access.

The page is a viewer over 240 stored simulation runs. It never runs the model — the model
is a headless Python engine in `src/`, and the page reads what that engine wrote.

## Getting started in 30 seconds

1. Open `culture-flux.html`.
2. Read the **Overview** tab, and specifically the paragraph about the control arm. Every
   number on this page is meaningless without it.
3. Go to **Results** and press **Resident cultural retention**.
4. Find the dashed orange line. That is what composition alone predicts. Any arm sitting
   on it has discovered nothing.

## Reading the strip plot

Each row is one experimental cell — a mechanism at one number of incoming cultures.

- **Each translucent dot is one complete simulation run.** Twenty per row. Overlap reads
  as density, so a tight cluster is a reproducible outcome and a spread is not.
- **The heavy vertical rule is the group mean.**
- **The dashed orange line** is the compositional prediction, `1 − M·D`. It is arithmetic,
  not a result.
- **Colour is the mechanism**: grey for the control, blue for homophilous copying, violet
  for conformist transmission.

Individual runs are drawn rather than error bars on purpose. One arm looked bimodal in
earlier work — some runs the residents hold, some they do not — and a mean with a standard
error would describe a shape the data does not have.

## Reading the line chart

The same measurement plotted against **K**, the number of distinct incoming cultures, with
total migration held constant. Bars are one standard error.

This is the project's central manipulation. A flat line means the number of incoming
cultures did not matter for that measurement.

## The measurements

| Measurement | What it means |
|---|---|
| Resident cultural retention | Share of cultural features on which a randomly chosen current resident still carries the founding trait. This is the headline. |
| Distinct cultures present | How many whole cultural configurations exist. Sensitive to single-agent variation. |
| Largest culture's share | Dominance. Says nothing about *which* culture dominates. |
| Effective number of cultures | Inverse Simpson — the diversity you would have if all cultures were equally common. Comparable across runs. |
| Spatial segregation | Theil's index over neighbourhoods. 0 = every neighbourhood mirrors the city, 1 = each is internally uniform. |
| Distance from any founding culture | How far agents have drifted from every culture anyone started with. The raw material for a hybridisation measure that is deliberately not yet defined. |

## The tabs

- **Overview** — the question, what is held identical, and why the control arm matters.
- **The three mechanisms** — what each assumption about influence actually does.
- **Results** — the stored runs.
- **What was retracted** — two findings this instrument produced and then overturned.
  Worth reading before the results, not after.
- **Method** — the shape of the model. Full detail is in `methods.html`.
- **Provenance** — every run's config and result hash, and the five assumptions most
  likely to change what you see.

Arrow keys move between tabs when one has focus. The URL fragment tracks the tab, so a
link to a particular tab works.

## What to try first

1. **Compare the two active mechanisms on retention.** They sit on opposite sides of the
   dashed line. That is the instrument's main finding, and it is a finding about how
   little the model can tell you without knowing which mechanism is right.
2. **Switch to "Distinct cultures present" and look at the control arm.** It rises with K
   for a purely bookkeeping reason: more source cultures means more founding profiles.
   That is what compositional change looks like when nothing is happening.
3. **Follow one measurement across all three arms at K=1**, then ask what would have been
   concluded from any single arm alone.
4. **Read the retractions tab, then look at the results again.** The runs behind those
   retracted claims looked exactly as convincing as these do.

## Regenerating the data

The page reads `culture-flux.data.js`, which is generated:

```bash
python3 -m culture_flux.cli sweep configs/sweeps/rq2_three_arm.json \
        --out results/rq2 --workers 0
python3 analysis/export_web_data.py --batch results/rq2
```

The sweep resumes: interrupt it and run it again and it continues. Editing the data file
by hand is not supported — the point of generating it is that a figure on the page can
always be traced to a run hash.
