# Ferry Terminal

A queue at a ferry terminal is not a queue at a counter. Nothing is served between departures. The berth
sits empty, vehicles accumulate, and then a whole batch leaves at once — or as much of it as fits.

You set how vehicles arrive, how much deck there is, how often the boat goes, and the order in which the
queue is offered to it. Then you have to say who waited, how long, and who never sailed at all.

Open `ferry-terminal.html` in any modern browser. Nothing to install, no build step, no network access
beyond the web font.

---

## Purpose

To make the structure of **batch service** manipulable. Three things about it are counter-intuitive and
are hard to feel from an equation:

- Carry-over is a **threshold** phenomenon, not a gradual one.
- A loading policy's effect often lives in the **tail**, not the average.
- Whether capacity is counted in vehicles or in lane-metres is a **modelling choice with consequences**,
  not a technicality.

And one thing about measurement, which turned out to be the sharpest lesson the instrument teaches:
if you measure waiting time only over the vehicles that sailed, you are measuring the survivors of the
policy's own selection. See [Why the primary chart is a survival curve](#why-the-primary-chart-is-a-survival-curve).

## Current status

**Version 0.1.0.** The model is validated; the instrument is not yet registered in the catalogue, so the
badges on the methods page state their own absence rather than asserting a status.

## Evidence level

**Uncalibrated prototype** — internally consistent, with nothing fitted to data.

Every parameter is NOT ESTABLISHED and is supplied by the user. The starting configuration is a neutral
exploratory point, labelled as such in the interface, and carries no claim of typicality. One mechanism —
capacity-denied boarding — is directly evidenced; the structure is well grounded; no parameter is
empirically defaulted. Raising the badge would require calibration against a measured terminal, which
does not exist here.

**This is a browser research instrument. It is not an operational planning tool and cannot be inverted
to infer real parameters from observed waits.**

## What is modelled

| Element | Representation |
|---|---|
| Arrivals | Two-component mixture: a Poisson component indifferent to the timetable, and a component targeting a specific sailing at a drawn lead time. The mixing fraction ρ is a user control. |
| Service | Batch departure at deterministic epochs, headway *h*. |
| Capacity | Finite lane-metres, accumulated in integer centimetres. Equal vehicle lengths reproduce unit-count capacity exactly. |
| Loading | First-fit within an ordering set by the active policy. Three abstract disciplines: first-come, booked-first, shortest-first. |
| Carry-over | Unboarded vehicles stay queued with their accumulated wait. |
| Disruption | One sailing may be delayed, reduced or cancelled. |
| Time to service | **Right-censored.** Kaplan–Meier product-limit estimate is the primary measure. |

## Why the primary chart is a survival curve

An earlier build reported time to service over served vehicles only. Under shortest-first loading, that
made the policy look better than first-come — a lower observed median, a little more lane-metres moved.

Correcting the measure did not make that conclusion available. It made the bias visible. In the
validation run — the Python reference implementation, seed and settings recorded in the validation record —
shortest-first served **zero** long vehicles against first-come's 4.7 per run: a long-vehicle service rate
of 0.0000 against 0.0913, while moving one per cent more lane-metres. The shorter observed median was
survivorship bias measured on a subpopulation the policy itself had selected.

This instrument reproduces the same signature rather than the same numbers, as it must, since it runs a
different generator: in the regression suite here, first-come serves 16.1% of long vehicles and
shortest-first serves 0.0%.

So the instrument is built so that the misleading view **does not exist**:

- The primary time-to-service display is the Kaplan–Meier estimate, with censoring marks drawn.
- The served/censored composition is welded to it and cannot be collapsed, minimised or hidden behind
  progressive disclosure.
- There is no code path that renders the observed-only distribution without its composition, and no
  interaction path that compares two policies on observed-only distributions. Not discouraged —
  unreachable.

## Files

```
ferry-terminal.html      the instrument
methods.html             methods, sources, parameters, limitations, validation
css/ferry-terminal.css   instrument styles; all colour from the --rf-* tokens
js/config.js             control register, copy, thresholds. Nothing here is measured.
js/model.js              the model. No DOM, no presentation.
js/charts.js             canvas drawing. Enforces the two structural pairings above.
js/events.js             notices and interpretive safeguards, as pure rules over state
js/screens.js            panels, readouts, data tables
js/main.js               state, wiring, the comparison rule
tests/model-tests.html   the regression suite, in the browser
tests/model-tests.js     35 assertions; also runs under node
```

## Running the tests

In a browser: open `tests/model-tests.html`.

From a shell:

```
node -e "require('./js/model.js'); require('./tests/model-tests.js')"
```

Each assertion names the property it protects. **The arrival-count dispersion test must never be
removed** — it is the one that would have caught the original blocking defect at build time.

## Known limitations

- Loading takes no time. Per-vehicle loading time and turnaround dwell are absent because no source
  gives them, not because they are small.
- The arrival rate is constant within a run. Non-homogeneous rate profiles λ(t) — the form the
  literature actually recommends — are not implemented.
- Packing is one-dimensional. Real Ro-Ro capacity is constrained by area, weight and floor pressure
  together.
- The loading policies were not surveyed from practice. They are abstract disciplines and are labelled so.
- The mixed vehicle-length set spans a documented range; it is not a measured small-terminal distribution.
- The analytic bulk-service benchmark has not been compared numerically, because its primary sources were
  not retrieved.
- The model was specified and first validated in Python and is implemented here in JavaScript with a
  different generator. Reproducibility is a property of this instrument; the two are not bit-identical,
  and the validated properties are distributional and structural.

## Accessibility

Full keyboard operation, including step-to-epoch. Every chart has a data-table alternative carrying the
same numbers — the survival table includes event times, at-risk counts and censoring indicators. Nothing
is encoded by colour alone: censored blocks are also hatched and policies also differ by curve. The
comparison capability is preserved at every viewport width, including a 390 px phone.

## Licence and attribution

Part of the Orbital simulations catalogue. Candice Cantrelle, 2026.
