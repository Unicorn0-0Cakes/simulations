# Configuration Schema

Canonical format JSON; YAML supported and hashes identically. Validated on load;
unknown keys are **rejected**, because a silently-ignored typo produces a run
that looks like a null result.

## Sections

### `population`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `initial_size` | int ≥ 1 | 2000 | Pre-migration city size, N₀ |
| `within_source_noise` | float [0,1] | 0.0 | Per-feature probability an agent departs from its group's modal profile. 0 = perfectly homogeneous groups (A-004) |

### `culture`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `features` | int ≥ 1 | 10 | F. Achievable distances are multiples of 1/F; F < 10 warns (A-013) |
| `traits_per_feature` | int ≥ 2 | 5 | Q |
| `distance_metric` | registered name | `hamming` | A-003 |

### `migration`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `mode` | `addition` \| `replacement` | `addition` | A-008 |
| `total_share` | float [0,1) | 0.30 | **M** — migrant share of the *final* population |
| `source_count` | int ≥ 1 | 1 | **K** |
| `source_distribution` | `single`\|`even`\|`geometric`\|`dirichlet`\|`explicit` | `even` | shape of the incoming size distribution |
| `decay` | float (0,1] | 0.5 | geometric only |
| `concentration` | float > 0 | 1.0 | dirichlet only |
| `explicit_shares` | list[float] | null | explicit only; length must equal K |
| `target_evenness` | float (0,1] \| null | null | **H** — when set, overrides `source_distribution` with geometric shares at exactly this Pielou evenness |
| `cultural_distance` | float [0,1] \| preset \| list | `medium` | **D**. Presets are labels, not estimates (A-007) |
| `arrangement` | `independent`\|`nested`\|`disjoint` | `independent` | distance *between* sources at fixed distance from residents (A-006) |
| `start_year` | float ≥ 0 | 0.0 | when arrivals begin |
| `duration_years` | float > 0 | 10.0 | **V** — the same total arrivals spread over this many years |
| `arrival_profile` | `uniform` (others declared) | `uniform` | A-014 |

### `network`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `layers` | list[str] | `["citywide"]` | Declared: household, neighbourhood, workplace, friendship, citywide. Only `citywide` implemented (A-010) |

### `dynamics`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `transmission_rule` | declared name | `null` | Only `null` implemented (A-011). **In YAML, quote it** — bare `null` is a YAML null |
| `influence_model` | registered name | `uniform` | A-009 |

### `runtime`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `total_years` | float > 0 | 50.0 | run length in simulated years |
| `steps_per_year` | int ≥ 1 | 12 | 1 warns: step and year become indistinguishable |
| `years_per_generation` | float > 0 | 25.0 | generation length |
| `measure_every_steps` | int ≥ 1 | 12 | measurement cadence; the final step always measures |

### `metrics`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `include` | list[str] \| null | null | null = every implemented metric |
| `include_placeholders` | bool | true | placeholders return NaN and are reported as NaN |

### `output`
| Key | Type | Default | Meaning |
|---|---|---|---|
| `directory` | str | `results` | results root |
| `write_final_population` | bool | true | the only per-agent output; off for large sweeps |
| `write_timeseries` | bool | true | |
| `format` | `auto`\|`parquet`\|`csv` | `auto` | `auto` = parquet when pyarrow imports |

## Derived keys

| Key | Covers | Used for |
|---|---|---|
| `config_hash` | everything scientific (excludes name, description, output) | identifies a condition |
| `baseline_key` | `population` + `culture` | runs sharing (seed, baseline_key) have byte-identical resident populations |
| `condition_key` | everything else | condition-dependent RNG streams |

Renaming an experiment or moving its output does not change any of them.

## Warnings

Wrong raises; questionable warns and is carried into the run manifest. Current
warnings: migration window extending past the end of the run; F < 10; one step
per year; a declared-but-unimplemented transmission rule; the null rule (always);
too few migrants per source for the requested share distribution to survive
integer rounding.

## Sweeps

A sweep file names a `base` (inline or a path) and `axes` — dotted configuration
paths mapped to value lists — plus `replicates` and `seed_start`. Axes naming
non-existent fields are rejected. `sweep --dry-run` expands and reports without
running, and warns if the number of distinct condition hashes does not match the
number of conditions, which would mean an axis has no scientific effect.
