# Technology Stack Decision

Recorded before substantial code was written, per brief section 24.

## Decision

**Python 3.10+, NumPy for state, no agent-based-modelling framework.**

Optional and deferred: pyarrow (storage), PyYAML (configuration convenience),
NetworkX (network *construction and analysis*, from Phase 3), Polars/DuckDB/SciPy
(analysis, from Phase 2), Matplotlib (figures). None is a hard dependency; the
engine imports NumPy and the standard library only.

## Why not an ABM framework

Mesa is the obvious candidate and was rejected on four grounds, in order of
weight:

1. **The scheduler is the wrong shape.** Mesa's model is a scheduler stepping
   agent objects. This project needs several processes on *different* clocks —
   interaction per step, migration per year, reproduction per generation,
   measurement on its own cadence (brief section 10). Expressing that inside a
   scheduler designed around a uniform agent step means working against it, and
   the step/year/generation distinction the brief insists on is exactly what
   would get blurred.

2. **Per-agent Python objects do not survive the sweep requirement.** The design
   in section 14 is ~10⁴–10⁵ runs. At N = 10⁴ agents, an object-per-agent model
   spends most of its time in attribute lookup and garbage collection. A
   struct-of-arrays layout with vectorised NumPy operations is one to two orders
   of magnitude faster and makes the difference between a sweep that runs
   overnight and one that does not run.

3. **Determinism.** The reproducibility requirement (section 12) needs exact
   control over which stochastic process draws from which stream, in what order.
   Frameworks that own the RNG and the iteration order make that control
   indirect, and indirect control over randomness is how irreproducible results
   happen.

4. **The framework's main benefit does not apply.** Mesa's real value is its
   batteries — grid spaces, a visualisation server, a batch runner. This project
   needs multiplex networks rather than a grid, must not have a GUI driving the
   engine (section 15), and needs a batch runner with condition hashing and
   resume, which is roughly as much work to adapt as to write.

**What the choice costs.** Familiarity: reviewers who know Mesa will recognise a
Mesa model faster than a bespoke one. Mitigation: document the model in ODD
protocol form (a Phase 2 task), which is the actual lingua franca for ABM
reporting and is framework-independent. Also: everything a framework would have
provided must be written and tested here, which is why the test suite is large
relative to the engine.

**What would reverse the decision.** If the model acquires mechanisms that are
genuinely per-agent and irregular — heterogeneous decision rules that cannot be
vectorised — the performance argument weakens and the framework's structure
starts to pay. Revisit at the point where a transmission rule cannot be written
as array operations.

## Why NumPy rather than pure Python or a compiled core

NumPy is the floor for this kind of work and the ceiling for now. It gives
vectorised operations, a well-specified RNG (`PCG64` via `SeedSequence`) whose
stream is stable across platforms and versions, and no build step.

Compiled acceleration (Numba, Cython, Rust) is not needed and would be premature:
nothing has been profiled, because there is nothing substantial to profile yet.
The architecture does not block it — the hot loop, when it exists, will be one
function over contiguous arrays.

## Why NetworkX is deferred rather than adopted

NetworkX is the right tool for *building* structured graphs and computing
modularity, and it will be used for that. It is the wrong tool for the inner
loop: its graph objects are dictionaries of dictionaries and traversing them per
agent per step would undo the performance argument above. The intended split is
NetworkX to construct and analyse, adjacency in NumPy arrays to simulate. The
`NetworkLayer` interface is written so that this split is possible without the
engine knowing which library built the layer.

## Why JSON is the canonical configuration format

YAML is pleasanter to write and is supported. JSON is canonical because
configuration hashing requires a byte-stable serialisation, and JSON with sorted
keys gives one with no dependency. Both formats load, both hash identically, and
the test suite checks that the shipped pair agree.

One YAML trap worth knowing, since it bit this repository during construction:
unquoted `null` in YAML is a null *value*, not the string `"null"`. The
transmission rule named `null` must be quoted. The shipped `smoke.yaml` carries a
comment saying so.

## Why parquet with a CSV fallback

Parquet is columnar, typed and compressed — the right format for sweep output
that will be read by Polars or DuckDB. But a run must never fail because an
optional dependency is missing, so the writer falls back to CSV and records which
format it used in the manifest. A stored result always says how it was stored.

## Python version floor

3.10, for structural pattern matching availability and `X | Y` type syntax. The
code uses `from __future__ import annotations` throughout, so the annotations
themselves are not a constraint.
