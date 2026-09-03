# Ferry Terminal — User Manual

A hands-on guide to operating the instrument. Open `ferry-terminal.html` in a browser to follow along.

## Getting started in 30 seconds

1. Press **Open the terminal**. A neutral exploratory configuration loads and runs once.
2. Move **Arrival mixture** from 0.5 toward 0 — fully timetable-targeted. The previous run stays on
   screen as a faint ghost, on the *same* arrivals, so the difference is the control and not the dice.
3. Look at the **composition bar** under the survival curve before you read the curve. It tells you what
   fraction of vehicles the curve is even describing.
4. Press **Compare policies**. Watch the shortest-first curve and then look at the bars underneath it.

## The one habit worth building

**Read the composition first, then the curve.** A time-to-service curve that looks excellent while 47%
of vehicles never sailed is not describing a fast terminal. It is describing whoever the policy chose.

The instrument will not let you forget this — the composition is welded to every distribution and cannot
be collapsed — but the habit is what makes the display useful rather than decorative.

## Reading the scopes

### Time to service — censoring-aware *(primary)*

The vertical axis is the probability that a vehicle is **still waiting**; the horizontal axis is time
since it arrived. The curve starts at 1 and steps down each time a vehicle sails.

- **Short vertical ticks** on the curve are censored vehicles — still queueing when the horizon ended.
  They are drawn, never hidden. Each one is a vehicle whose true time to service is unknown but is known
  to be *at least* that long.
- **The hatched region** marks where fewer than one vehicle in ten remains at risk. The estimate there is
  unreliable and is shown as unreliable rather than smoothed into a continuous-looking line.
- **The faint dashed curve**, when present, is the previous run on the same arrivals.

Beneath it, always, is the composition bar: teal for vehicles that sailed, hatched red for vehicles that
never did.

### Queue length, with departure epochs

Vertical rules are scheduled departures — grey normal, amber delayed or reduced, dashed red cancelled.
The queue climbs between them and drops at each one. **If the drops stop reaching the previous floor, you
are watching carry-over accumulate.** That is the threshold, and it is visible before any statistic says so.

### Per-sailing load against capacity

Each sailing is drawn as an outline showing its capacity with the loaded lane-metres filled in. **The gap
is real deck left empty.** With mixed vehicle lengths and vehicles still queueing, a visible gap is the
packing constraint made visible: the next vehicle in the queue order simply did not fit.

### Throughput against the analytic bound

Cumulative vehicles sailed, with a dashed reference line at min(λ, C/h). Below the stability boundary the
run tracks the arrival rate; above it, the run tracks the service bound and the gap between them is the
queue.

### Denied boarding · Never sailed

Two cards, deliberately unlike each other, because they count different things.

- **Denied boarding** counts *events*: a vehicle present at a sailing that did not board it. One vehicle
  waiting through four sailings contributes four.
- **Never sailed** counts *vehicles*: distinct vehicles still queueing at the horizon. That same vehicle
  contributes one.

Adding them would be meaningless, and no view in the instrument does.

### Observed time to service *(secondary)*

The histogram of waits among vehicles that sailed. It answers a real question — how long did the served
wait — and it is kept for that. It is drawn with a dashed border and its own composition bar, because on
its own it is the chart that misleads.

## The controls

### Arrivals

| Control | What it does |
|---|---|
| **Arrival mixture ρ** | 1 = every vehicle arrives indifferent to the timetable. 0 = every vehicle targets a sailing. This is the instrument's central question; it exists as a control because the assumption that arrivals are simply Poisson did not survive the evidence. |
| **Mean arrival rate λ** | Vehicles per hour. With headway and capacity it sets the load ratio. |
| **Targeted lead time D** | How early a targeted vehicle appears before its sailing. Clamped below the headway. Small D concentrates arrivals just before departure; large D spreads them. |
| **Booked share** | The fraction holding a reservation. It changes nothing unless the loading policy is booked-first. |

### Service

| Control | What it does |
|---|---|
| **Headway h** | Minutes between departures. |
| **Capacity C** | Lane-metres per sailing. Below the longest vehicle nothing could ever board, and the run is blocked with an explanation rather than looping. |
| **Length distribution** | *All equal* reproduces unit-count capacity exactly, so the unit-count model is a selectable special case rather than a discarded rival. *Mixed* is an exploratory set spanning the documented Ro-Ro range and is not a measured distribution. Neither is marked correct. |

### Policy

Three **abstract disciplines**, not a survey of practice:

- **First come** — queue order by arrival.
- **Booked first** — reservations ahead of standby, then arrival order.
- **Shortest first** — shortest vehicle first among those waiting.

Shortest first fills the deck more densely. Whether that is operationally desirable is not a claim this
model makes, and the comparison view is built to show you why.

### Run

Horizon, warm-up, seed and disruption. **The seed is a scientific control, not a developer setting.**

## The comparison rule

Change any control except the seed and the previous run is kept as a ghost baseline, on the same arrival
realisation. The difference you see is the control you moved.

Change the seed and the comparison is **cleared, with a message saying why**. Two runs on different random
streams produce a contrast that cannot be attributed to anything. The instrument will not display one.

The **changed** control is marked with an orange edge until the next run, so you always know what moved.

## Keyboard

| Key | Action |
|---|---|
| `Space` | Run or pause |
| `S` | Step to the next departure |
| `T` | Switch between day and night |
| `Esc` | Close a dialog |
| `Tab` | Every control, chart alternative and table is reachable |

Charts have data-table alternatives at the bottom of the centre column. The survival table carries event
times, at-risk counts and censoring indicators — the same numbers the curve is drawn from.

## Reproducibility

**Export configuration** writes JSON including the seed. **Import configuration** restores the run
exactly. **Replay this seed** reruns without changing anything. **New seed** draws a fresh stream and
clears the comparison.

## Three things to try

1. **Find the threshold.** Fix everything, raise λ slowly, and watch the queue-length chart. Carry-over
   does not creep in. It arrives.
2. **Make timetable coupling matter.** Set ρ = 1 and note the survival curve. Set ρ = 0 with a short lead
   time. Same load, very different distribution of who waits — and the composition bar tells you whether
   the comparison is even about the same population.
3. **Try to make shortest-first look good.** It is easy on the secondary histogram and impossible on the
   comparison view. That difference is the point of the instrument.

## What this cannot tell you

Nothing about a real terminal. Every parameter is user-specified, none is measured, and different
combinations of ρ, λ and C produce similar waiting distributions — so the model cannot be run backwards
to infer what a real port's parameters are. See [methods.html](methods.html) §05.
