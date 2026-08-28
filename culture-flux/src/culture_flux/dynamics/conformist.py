"""Conformist transmission -- frequency-dependent bias.

A different family from homophilous copying, and the one hypothesis H2 actually
depends on. Where the homophily rule asks *am I similar enough to this person to
be influenced by them*, this rule asks *what is everyone around me doing*.

The rule, as specified here
---------------------------
Each event, for one focal agent:

1. Sample ``n_models`` other agents from the multiplex network -- the agent's
   observed neighbourhood, not the whole city.
2. Pick one feature at random (weighted by ``transmission_rate``).
3. Count how many of the sampled models carry each trait on that feature.
4. Adopt trait *t* with probability proportional to ``f_t ** conformity``, where
   ``f_t`` is its frequency among the models.
5. Refuse the change with probability equal to the feature's ``resistance``, and
   weight the adoption by the models' influence.

``conformity`` is the whole rule:

* ``= 0`` — every observed trait equally likely. Random copying, no bias.
* ``= 1`` — adopt in proportion to frequency. **Unbiased transmission**, the
  neutral null of cultural evolution: this is drift-in-the-population-genetic
  sense, not conformity at all.
* ``> 1`` — conformist. Common traits are adopted more often than their
  frequency warrants; the majority is amplified.
* ``< 1`` (and > 0) — anti-conformist. Rare traits are favoured.

So one parameter spans conformity, neutrality and anti-conformity, and the
neutral case is a *value* rather than a separate rule. That matters for the
hypotheses: H2 claims the resident culture's advantage comes from a conformity
asymmetry, which means H2 predicts an effect that should vanish at
``conformity = 1`` and reverse below it. That is a directly testable structure
and it is why this rule is parameterised this way (A-030).

What differs from the homophily rule, and why it is a real test
--------------------------------------------------------------
* **No similarity gate.** An agent with nothing in common with its neighbours is
  still influenced by them. Cultural distance is not self-reinforcing, so the
  frozen-apart absorbing states of the Axelrod family do not arise the same way.
* **Many models, not one.** Influence is aggregated over a neighbourhood rather
  than being a dyadic event.
* **Feature-by-feature, with no coupling between features.** Whole cultural
  profiles have no standing; only trait frequencies do.

If a result holds under both rules it is not an artefact of either. If it does
not, A-016's requirement has done its job.
"""

from __future__ import annotations

import numpy as np

from ..agents.population import Population
from ..influence.base import InfluenceModel
from ..networks.base import MultiplexNetwork
from .base import TransmissionRule
from .drift import apply_drift


class ConformistTransmission(TransmissionRule):
    """Frequency-dependent copying from a sample of network neighbours."""

    name = "conformist"
    changes_culture = True

    def __init__(
        self,
        *,
        conformity: float = 1.0,
        n_models: int = 5,
        events_per_agent_per_step: float = 1.0,
        drift_rate: float = 0.0,
        batch_size: int | None = None,
    ) -> None:
        if conformity < 0:
            raise ValueError("conformity must be >= 0")
        if n_models < 1:
            raise ValueError("n_models must be >= 1")
        if events_per_agent_per_step < 0:
            raise ValueError("events_per_agent_per_step must be >= 0")
        if not 0.0 <= drift_rate <= 1.0:
            raise ValueError("drift_rate must lie in [0, 1]")
        if batch_size is not None and batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.conformity = float(conformity)
        self.n_models = int(n_models)
        self.events_per_agent_per_step = float(events_per_agent_per_step)
        self.drift_rate = float(drift_rate)
        self.batch_size = batch_size
        self.encounters = 0
        self.cross_cultural_encounters = 0
        self.successful_interactions = 0

    def describe(self) -> dict:
        d = super().describe()
        d.update(
            {
                "conformity": self.conformity,
                "regime": self._regime(),
                "n_models": self.n_models,
                "events_per_agent_per_step": self.events_per_agent_per_step,
                "drift_rate": self.drift_rate,
                "creates_novel_traits": self.drift_rate > 0.0,
                "similarity_gate": False,
            }
        )
        return d

    def _regime(self) -> str:
        if self.conformity == 0:
            return "unbiased random copying (no frequency dependence)"
        if abs(self.conformity - 1.0) < 1e-12:
            return "neutral / unbiased transmission (copy in proportion to frequency)"
        return "conformist" if self.conformity > 1 else "anti-conformist"

    def reset_counters(self) -> None:
        self.encounters = 0
        self.cross_cultural_encounters = 0
        self.successful_interactions = 0

    def step(
        self,
        population: Population,
        network: MultiplexNetwork,
        influence: InfluenceModel,
        step: int,
        rng: np.random.Generator,
    ) -> int:
        n = population.size
        if n < 2:
            return 0
        changes = apply_drift(population, self.drift_rate, rng)
        if self.events_per_agent_per_step == 0:
            return changes

        exact = self.events_per_agent_per_step * n
        n_events = int(exact)
        if rng.random() < exact - n_events:
            n_events += 1
        if n_events == 0:
            return changes

        weights = influence.weights(population, step)
        attention = None if bool(np.all(weights == weights[0])) else weights / weights.max()

        self.reset_counters()
        batch = self.batch_size or max(1, min(n // 10, 4096))
        remaining = n_events
        while remaining > 0:
            b = min(batch, remaining)
            changes += self._apply_batch(population, network, rng, attention, b)
            remaining -= b
        return changes

    def _apply_batch(
        self,
        population: Population,
        network: MultiplexNetwork,
        rng: np.random.Generator,
        attention: np.ndarray | None,
        size: int,
    ) -> int:
        n = population.size
        culture = population.culture
        schema = population.schema

        focal = rng.integers(0, n, size=size)
        if size > 1:
            _, first = np.unique(focal, return_index=True)
            focal = focal[np.sort(first)]
        m = focal.shape[0]
        if m == 0:
            return 0

        # One model set per focal agent, drawn through the network so that the
        # observed frequencies are LOCAL frequencies. Sampling from the whole
        # population instead would make every agent see the same distribution and
        # turn the rule into a global mean-field process.
        models = np.stack(
            [network.sample_partners(focal, rng) for _ in range(self.n_models)], axis=1
        )

        feature = self._choose_feature(schema.transmission_rate, m, rng)
        own = culture[focal, feature]
        model_traits = culture[models, feature[:, None]]  # (m, n_models)

        self.encounters += int(m * self.n_models)
        self.cross_cultural_encounters += int((model_traits != own[:, None]).sum())

        chosen = self._weighted_choice(
            model_traits,
            schema.n_traits[feature],
            attention[models] if attention is not None else None,
            rng,
        )

        resist = rng.random(m) >= schema.resistance[feature]
        changed = (chosen != own) & resist & (chosen >= 0)
        if not bool(changed.any()):
            return 0
        culture[focal[changed], feature[changed]] = chosen[changed].astype(culture.dtype)
        self.successful_interactions += int(changed.sum())
        return int(changed.sum())

    @staticmethod
    def _choose_feature(
        transmission_rate: np.ndarray, m: int, rng: np.random.Generator
    ) -> np.ndarray:
        total = float(transmission_rate.sum())
        if total <= 0:
            raise ValueError("at least one feature must have a positive transmission rate")
        cdf = np.cumsum(transmission_rate / total)
        return np.searchsorted(cdf, rng.random(m), side="right").clip(
            0, transmission_rate.shape[0] - 1
        )

    def _weighted_choice(
        self,
        model_traits: np.ndarray,
        n_traits: np.ndarray,
        model_attention: np.ndarray | None,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Adopt trait t with probability proportional to f_t ** conformity.

        Frequencies are tallied per row into a (m, max_traits) table. The table
        is dense because the trait count per feature is small by construction
        (assumption A-013 puts it at 5); a sparse tally would cost more than it
        saved.
        """
        m, k = model_traits.shape
        width = int(n_traits.max())
        counts = np.zeros((m, width), dtype=np.float64)
        rows = np.repeat(np.arange(m), k)
        cols = model_traits.ravel()
        contrib = np.ones(m * k) if model_attention is None else model_attention.ravel()
        np.add.at(counts, (rows, cols), contrib)

        totals = counts.sum(axis=1, keepdims=True)
        freq = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)
        weights = freq if self.conformity == 1.0 else np.power(freq, self.conformity)
        # A trait absent from the sample must stay absent: 0 ** 0 is 1 in NumPy,
        # which at conformity = 0 would otherwise let an agent adopt a trait
        # nobody it observed was carrying.
        weights = np.where(freq > 0, weights, 0.0)
        # Traits outside this feature's admissible range can never be selected.
        admissible = np.arange(width)[None, :] < n_traits[:, None]
        weights = np.where(admissible, weights, 0.0)

        w_total = weights.sum(axis=1)
        out = np.full(m, -1, dtype=np.int64)
        usable = w_total > 0
        if not bool(usable.any()):
            return out
        cdf = np.cumsum(weights[usable], axis=1)
        target = rng.random(int(usable.sum())) * w_total[usable]
        out[usable] = (cdf < target[:, None]).sum(axis=1)
        return out
