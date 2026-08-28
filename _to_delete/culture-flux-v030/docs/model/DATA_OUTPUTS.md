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

Nothing writes an aggregated cross-run summary yet. That belongs with the
analysis layer in Phase 2, and writing it before there is anything to aggregate
would fix a schema around guesses.

## Rules for figures

Every published figure traces to run directories and their `run_hash` values,
recorded in the figure's source. A figure whose data cannot be traced to a run
hash is not a result.
