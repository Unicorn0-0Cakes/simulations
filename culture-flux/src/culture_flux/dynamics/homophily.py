"""Homophilous trait copying -- an Axelrod-family transmission rule.

WHAT THIS IS, PRECISELY
-----------------------
This implements a rule *in the family* introduced by Axelrod (1997). It is
**not** a reproduction of the model as published in that paper: the paper has not
been read (see docs/literature/literature_matrix.md, open question L-Q3), so
every detail below is specified here, from this file, and must be checked against
the source before any claim of correspondence is made. Where the published model
differs, this implementation is wrong about Axelrod and right about itself.

The rule, as specified here
---------------------------
One *interaction event* is:

1. Draw a focal agent i uniformly from the population.
2. Draw a partner j from i's neighbours, with probability proportional to j's
   cultural influence weight. Under ``UniformInfluence`` this is uniform, and the
   rule reduces to the conventional form.
3. Compute their cultural overlap -- the salience-weighted fraction of features
   on which they agree, i.e. ``1 - distance(i, j)``.
4. With probability equal to that overlap, the interaction succeeds. Similar
   agents interact readily; agents with nothing in common do not interact at all.
   This is the homophily.
5. On success, pick one feature on which they differ (weighted by that feature's
   ``transmission_rate``) and set i's trait on it to j's.
6. That copy is refused with probability equal to the feature's ``resistance``.

Consequences that follow from the specification and are worth stating because
they bound what the rule can show:

- **Copying is one-way.** i adopts from j; j is unchanged. Influence is
  asymmetric per event, symmetric in expectation under uniform influence.
- **Overlap 0 blocks interaction entirely.** Two agents sharing no feature can
  never influence each other, so cultural distance is self-reinforcing. This is
  the mechanism that permits stable diversity, and it is also the reason a
  configuration can freeze: once every adjacent pair has overlap 0 or 1, nothing
  further can happen and the population is in an absorbing state.
- **No novel traits are created.** Traits are only ever copied, so the reachable
  culture space is bounded by the founding profiles. Recombination ACROSS
  features can produce profiles no founding population held -- which is the only
  route to hybridisation this rule offers, and it is a weak one. A rule allowing
  innovation or error would be a different rule; see A-018.

Update scheme
-------------
Axelrod-family dynamics are conventionally asynchronous: one event at a time, so
each event sees the results of all previous ones. That is the reference and is
implemented as ``update_scheme="asynchronous"``. It is also slow -- one Python
iteration per event, which at 10^7 events per run makes sweeps impractical.

``update_scheme="batched"`` (the default) applies events in conflict-free
batches: within a batch no agent is a focal agent twice, and every event reads
the pre-batch state. This is a genuinely different stochastic process, not an
optimisation, and it is registered as assumption A-017. The two schemes are
compared in the test suite on aggregate outcomes at small N; that comparison is
the evidence for using the fast path, and it is not strong evidence yet.
"""

from __future__ import annotations

import numpy as np

from ..agents.population import Population
from ..influence.base import InfluenceModel
from ..networks.base import MultiplexNetwork
from .base import TransmissionRule

UPDATE_SCHEMES = ("batched", "asynchronous")


class HomophilousTraitCopying(TransmissionRule):
    """Interaction probability proportional to cultural overlap; one-way copy."""

    name = "axelrod_homophily"
    changes_culture = True

    def __init__(
        self,
        *,
        events_per_agent_per_step: float = 1.0,
        update_scheme: str = "batched",
        batch_size: int | None = None,
        distance_metric: str = "hamming",
    ) -> None:
        if events_per_agent_per_step < 0:
            raise ValueError("events_per_agent_per_step must be >= 0")
        if update_scheme not in UPDATE_SCHEMES:
            raise ValueError(
                f"unknown update_scheme {update_scheme!r}; known: {UPDATE_SCHEMES}"
            )
        if batch_size is not None and batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.events_per_agent_per_step = float(events_per_agent_per_step)
        self.update_scheme = update_scheme
        self.batch_size = batch_size
        self.distance_metric = distance_metric

    # -- configuration reporting ------------------------------------------
    def describe(self) -> dict:
        d = super().describe()
        d.update(
            {
                "events_per_agent_per_step": self.events_per_agent_per_step,
                "update_scheme": self.update_scheme,
                "batch_size": self.batch_size,
                "distance_metric": self.distance_metric,
                "copying": "one-way (focal adopts from partner)",
                "creates_novel_traits": False,
            }
        )
        return d

    # -- the step ----------------------------------------------------------
    def step(
        self,
        population: Population,
        network: MultiplexNetwork,
        influence: InfluenceModel,
        step: int,
        rng: np.random.Generator,
    ) -> int:
        n = population.size
        if n < 2 or self.events_per_agent_per_step == 0:
            return 0

        # Expected events per step; the fractional part is resolved by a
        # Bernoulli draw so that a rate of 0.5 means half a round per step in
        # expectation rather than being silently floored to zero.
        exact = self.events_per_agent_per_step * n
        n_events = int(exact)
        if rng.random() < exact - n_events:
            n_events += 1
        if n_events == 0:
            return 0

        # Influence weights are computed once per step, not once per event. At
        # uniform influence this is exact; under a state-dependent influence
        # model it is a within-step approximation (assumption A-017b).
        weights = influence.weights(population, step)
        cumulative = self._partner_cdf(weights)

        if self.update_scheme == "asynchronous":
            batch = 1
        else:
            batch = self.batch_size or max(1, min(n // 10, 4096))

        changes = 0
        remaining = n_events
        while remaining > 0:
            b = min(batch, remaining)
            changes += self._apply_batch(population, rng, cumulative, b)
            remaining -= b
        return changes

    @staticmethod
    def _partner_cdf(weights: np.ndarray) -> np.ndarray | None:
        """Cumulative distribution for partner choice, or None when uniform.

        Returning None for the uniform case is not only faster -- it keeps the
        RNG draw sequence identical to a rule that never consulted an influence
        model, so introducing the influence layer did not perturb the null.
        """
        w = np.asarray(weights, dtype=np.float64)
        if w.size == 0:
            return None
        first = w[0]
        if bool(np.all(w == first)):
            return None
        total = w.sum()
        if total <= 0:
            raise ValueError("total cultural influence must be positive")
        return np.cumsum(w) / total

    def _draw_partners(
        self, rng: np.random.Generator, cumulative: np.ndarray | None, n: int, size: int
    ) -> np.ndarray:
        if cumulative is None:
            return rng.integers(0, n, size=size)
        return np.searchsorted(cumulative, rng.random(size), side="right").clip(0, n - 1)

    def _apply_batch(
        self,
        population: Population,
        rng: np.random.Generator,
        cumulative: np.ndarray | None,
        size: int,
    ) -> int:
        n = population.size
        culture = population.culture
        schema = population.schema

        focal = rng.integers(0, n, size=size)
        partner = self._draw_partners(rng, cumulative, n, size)
        accept_u = rng.random(size)
        feature_u = rng.random(size)
        resist_u = rng.random(size)

        alive = focal != partner
        if size > 1:
            # Conflict-free: at most one event per focal agent per batch, so
            # every event in the batch reads the same pre-batch state.
            _, first = np.unique(focal, return_index=True)
            keep = np.zeros(size, dtype=bool)
            keep[first] = True
            alive &= keep
        if not bool(alive.any()):
            return 0

        f_idx = focal[alive]
        p_idx = partner[alive]
        differs = culture[f_idx] != culture[p_idx]  # (m, F)

        salience = schema.salience
        total_salience = float(salience.sum())
        overlap = 1.0 - (differs * salience[None, :]).sum(axis=1) / total_salience

        active = (accept_u[alive] < overlap) & (differs.sum(axis=1) > 0)
        if not bool(active.any()):
            return 0

        f_idx = f_idx[active]
        p_idx = p_idx[active]
        differs = differs[active]

        feature = self._choose_feature(differs, schema.transmission_rate, feature_u[alive][active])
        ok = feature >= 0
        if not bool(ok.any()):
            return 0
        f_idx, p_idx, feature = f_idx[ok], p_idx[ok], feature[ok]

        resistance = schema.resistance[feature]
        allowed = resist_u[alive][active][ok] >= resistance
        f_idx, p_idx, feature = f_idx[allowed], p_idx[allowed], feature[allowed]
        if f_idx.size == 0:
            return 0

        culture[f_idx, feature] = culture[p_idx, feature]
        return int(f_idx.size)

    @staticmethod
    def _choose_feature(
        differs: np.ndarray, transmission_rate: np.ndarray, u: np.ndarray
    ) -> np.ndarray:
        """One differing feature per row, weighted by transmission rate.

        Returns -1 for rows whose differing features all carry zero transmission
        rate -- a legitimate configuration in which those differences simply
        cannot be transmitted, rather than an error.
        """
        weights = differs * transmission_rate[None, :]
        totals = weights.sum(axis=1)
        out = np.full(differs.shape[0], -1, dtype=np.int64)
        usable = totals > 0
        if not bool(usable.any()):
            return out
        cum = np.cumsum(weights[usable], axis=1)
        target = u[usable] * totals[usable]
        out[usable] = (cum < target[:, None]).sum(axis=1)
        return out
