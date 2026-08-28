"""Cultural drift: change that does not come from anybody.

Copying-only transmission has a structural consequence that took a pilot to
notice: the set of traits present at each feature can shrink but never grow, so
cultural diversity is a non-renewable resource and monoculture is the only
absorbing state a connected population can reach. Assumption A-018 recorded that;
pilot P-6 showed what it costs.

Drift is the one-parameter repair. With probability ``drift_rate`` per agent per
step, an agent changes one randomly chosen feature to a randomly chosen different
trait. It is variously called copying error, innovation, or noise depending on
which literature is speaking; the mechanism is the same and this module stays
agnostic about which story it tells (A-029).

Why it lives here rather than inside a rule
-------------------------------------------
Drift is not a property of *how people learn from each other* — it is what
happens when nobody is learning. Every transmission rule should be able to have
it, so it is a shared helper any rule can call rather than a feature of one.

Why it is not applied by the engine to every rule
-------------------------------------------------
Because ``NullTransmission`` must stay null. A control arm that quietly drifted
would no longer be a control arm, and every "the null does nothing" invariant in
the test suite would have to be weakened. Rules opt in.
"""

from __future__ import annotations

import numpy as np

from ..agents.population import Population


def apply_drift(
    population: Population, drift_rate: float, rng: np.random.Generator
) -> int:
    """Re-draw one feature for each of a Binomial(N, drift_rate) sample of agents.

    Returns the number of trait changes applied.

    Two details that decide whether ``drift_rate`` means what it says:

    * The drifting agents are drawn **without replacement**, so exactly
      ``n_drifting`` distinct agents change and the realised per-agent rate is
      ``drift_rate``. Sampling with replacement would let one agent absorb
      several draws and quietly depress the effective rate.
    * The replacement trait always **differs** from the current one, so the rate
      is at which culture changes, not at which a change is attempted. Same
      discipline as within-group initialisation noise, for the same reason.

    Drawing the count from a Binomial and then choosing that many agents is
    equivalent in distribution to an independent Bernoulli trial per agent, and
    costs O(k) rather than O(N) draws -- which matters at the low rates this
    parameter is interesting at.
    """
    if not 0.0 <= drift_rate <= 1.0:
        raise ValueError("drift_rate must lie in [0, 1]")
    n = population.size
    if n == 0 or drift_rate == 0.0:
        return 0
    n_drifting = int(rng.binomial(n, drift_rate))
    if n_drifting == 0:
        return 0
    agents = rng.choice(n, size=n_drifting, replace=False)
    features = rng.integers(0, population.n_features, size=n_drifting)
    limits = population.schema.n_traits[features]
    current = population.culture[agents, features].astype(np.int64)
    offsets = (rng.random(n_drifting) * (limits - 1)).astype(np.int64) + 1
    population.culture[agents, features] = ((current + offsets) % limits).astype(
        population.culture.dtype
    )
    return int(n_drifting)
