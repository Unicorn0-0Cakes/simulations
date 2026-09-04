# Data Outputs

## Principles

1. **Every stored result must be interpretable without the code that made it.**
   The manifest carries the full configuration, the model version, the RNG layout
   version, and the metric names in force.
2. **Nothing scales with N unless asked for.** The time series is one row per
   *measurement*. Only `final_population` is per-agent, and it can be switched off
   — which it is in the reference sweep configuration.
3. **Format is recorded, not assumed.** A run written as CSV because pyarrow was
   missing says so in its manifest.

## Files

| File | Rows | Purpose |
|---|---|---|
| `manifest.json` | — | Provenance: seed, versions, config, hashes, realised source geometry, migration accounting, environment, timing |
| `config.resolved.json` | — | The configuration as run, canonically ordered. Feeds `verify`. |
| `timeseries.parquet` / `.csv` | one per measurement | Step, year, generation, cumulative arrivals/displacements/trait-changes, and every configured metric |
| `culture_distribution.parquet` / `.csv` | one per distinct profile | Count and share of each cultural configuration present at the end |
| `final_population.parquet` / `.csv` | one per agent | Full final state. Optional. |
| `metrics_final.json` | — | The last measurement, for quick reading without a parquet reader |
| `run_hash.txt` | — | The reproducibility digest |

## Size

At the reference configuration (N₀ = 10,000, 100 years, monthly measurement,
`write_final_population: false`) a run stores roughly 100 measurement rows across
~27 columns plus a manifest — a few tens of kilobytes. A 10,000-run sweep is
therefore on the order of hundreds of megabytes, which is tractable without
special handling.

Turning `write_final_population` on adds ~13,000 rows × (5 + F) columns per run.
At F = 20 that is roughly 300 KB per run compressed — three orders of magnitude
more, and 3 TB across the same sweep. Hence the default is off, and it should be
turned on only for a deliberately chosen subset of conditions.

## Analysis path

The intended read path is Polars or DuckDB directly over the parquet files, with
run directories as the unit of grouping and `config_hash` as the condition key.
`manifest.json` files are small enough to load in bulk into a single table of
conditions, joined to the time series by `config_hash` and `seed`.

Every sweep writes two batch-level files alongside the run directories:

| File | Rows | Purpose |
|---|---|---|
| `batch_manifest.json` | — | Sweep summary, model version, worker count, resume setting, per-status counts, total compute, and **every failure listed individually** — a batch that quietly dropped 3% of its runs would still look complete in an aggregate table |
| `run_summary.csv` | one per run | The swept parameters plus every final metric. The table an analysis actually starts from |

Dict-valued axes (a whole network specification) are flattened to canonical JSON
strings so the summary stays rectangular and diffable.

## Reporting absorption

Every manifest carries an `absorption` block: whether the run ended absorbed, how
many quiescent years it had, and a confidence that is **never "certain" under an
active transmission rule**. The time series carries `steps_since_last_change`.

This is not bookkeeping. Pilot P-6 recorded an 1,800-year plateau of stable
cultural richness that then collapsed to monoculture, so a run whose metrics have
stopped moving is not thereby at equilibrium. No result may use "equilibrium",
"stable" or "persists" unless the runs behind it are absorbed (A-028).

## Rules for figures

Every published figure traces to run directories and their `run_hash` values,
recorded in the figure's source. A figure whose data cannot be traced to a run
hash is not a result.
