"""Concrete network layers.

Two shapes cover everything the research programme needs:

``GroupLayer``
    Membership in a shared container -- a household, a neighbourhood, a
    workplace. Everyone in the group is adjacent to everyone else. Groups are
    disjoint and every agent belongs to exactly one, which is a simplification
    (people have one home but several workplaces over a life) recorded as A-020.

``AttentionTieLayer``
    Named ties. Each agent holds exactly ``degree`` outgoing ties to specific
    other agents: "whose culture I am exposed to". **Ties are directed**, not
    reciprocal friendships -- attention is not symmetric, and the fixed-degree
    (N, degree) array this permits makes rewiring O(1) per tie instead of a
    graph rebuild. Registered as A-021; the modularity metric symmetrises for
    measurement only.

Both expose ``sample_partners``, which is what the transmission rule actually
consumes. Neither materialises an adjacency matrix: a citywide layer at N = 10^5
would be 10^10 entries, and the rule only ever needs "one random neighbour of
each of these agents".

Why fixed degree, and why disjoint groups
-----------------------------------------
Both are chosen because they make the *sampling* operation a constant-time array
lookup, which is what allows a 10^5-run sweep. Degree heterogeneity and
overlapping memberships are both real and both excluded; A-020 and A-021 record
what that costs.
"""

from __future__ import annotations

import numpy as np

from ..agents.population import Population
from .base import NetworkLayer

#: Assignment schemes for placing arriving agents into groups.
ASSIGNMENT_SCHEMES = ("random", "clustered")


class GroupLayer(NetworkLayer):
    """Disjoint groups; everyone in a group is adjacent to everyone else."""

    def __init__(
        self,
        name: str,
        n_agents: int,
        target_size: float,
        rng: np.random.Generator,
        *,
        assignment: str = "random",
        clustering: float = 0.0,
    ) -> None:
        if target_size < 1:
            raise ValueError(f"layer {name!r}: target_size must be >= 1")
        if assignment not in ASSIGNMENT_SCHEMES:
            raise ValueError(
                f"layer {name!r}: unknown assignment {assignment!r}; known: {ASSIGNMENT_SCHEMES}"
            )
        if not 0.0 <= clustering <= 1.0:
            raise ValueError(f"layer {name!r}: clustering must lie in [0, 1]")
        self.name = name
        self.target_size = float(target_size)
        self.assignment = assignment
        self.clustering = float(clustering)
        self.n_groups = max(1, int(round(n_agents / self.target_size)))
        self.membership = rng.integers(0, self.n_groups, size=n_agents).astype(np.int32)
        self._index_dirty = True
        self._order = np.zeros(0, dtype=np.int64)
        self._starts = np.zeros(0, dtype=np.int64)
        self._counts = np.zeros(0, dtype=np.int64)

    # -- structure ---------------------------------------------------------
    def size(self) -> int:
        return int(self.membership.shape[0])

    def _reindex(self) -> None:
        """Group members into a contiguous block per group, for O(1) sampling."""
        self._order = np.argsort(self.membership, kind="stable").astype(np.int64)
        self._counts = np.bincount(self.membership, minlength=self.n_groups).astype(np.int64)
        self._starts = np.concatenate([[0], np.cumsum(self._counts)[:-1]]).astype(np.int64)
        self._index_dirty = False

    def neighbours(self, agent_index: int) -> np.ndarray:
        if self._index_dirty:
            self._reindex()
        g = int(self.membership[agent_index])
        block = self._order[self._starts[g] : self._starts[g] + self._counts[g]]
        return block[block != agent_index]

    def sample_partners(self, focal: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """One random co-member per focal agent.

        Returns the focal index itself when the agent is alone in its group; the
        caller drops self-pairs, so a lone agent simply has no interaction that
        event rather than being silently reassigned.
        """
        if self._index_dirty:
            self._reindex()
        g = self.membership[focal]
        counts = self._counts[g]
        offsets = (rng.random(focal.shape[0]) * counts).astype(np.int64)
        offsets = np.minimum(offsets, np.maximum(counts - 1, 0))
        return self._order[self._starts[g] + offsets]

    # -- growth ------------------------------------------------------------
    def add_agents(self, n: int, rng: np.random.Generator, source_id: int = 0) -> None:
        if n < 0:
            raise ValueError("cannot add a negative number of agents")
        if n == 0:
            return
        if self.assignment == "random" or self.clustering == 0.0:
            new = rng.integers(0, self.n_groups, size=n).astype(np.int32)
        else:
            # Clustered placement: with probability `clustering` an arrival joins
            # a group that already contains someone from its own source; with the
            # remaining probability it lands anywhere. This is the residential
            # sorting mechanism, and it is a parameter rather than a default
            # because assuming it would build enclave formation into the
            # initialisation instead of letting it emerge (A-022).
            occupied = self._groups_containing_source(source_id)
            new = rng.integers(0, self.n_groups, size=n).astype(np.int32)
            if occupied.size:
                pick = rng.random(n) < self.clustering
                new[pick] = occupied[rng.integers(0, occupied.size, size=int(pick.sum()))]
        self.membership = np.concatenate([self.membership, new])
        self._index_dirty = True

    def _groups_containing_source(self, source_id: int) -> np.ndarray:
        cache = getattr(self, "_source_groups", None)
        if cache is None:
            cache = {}
            self._source_groups = cache
        return cache.get(source_id, np.zeros(0, dtype=np.int32))

    def note_source_placement(self, source_id: int, groups: np.ndarray) -> None:
        cache = getattr(self, "_source_groups", None)
        if cache is None:
            cache = {}
            self._source_groups = cache
        prior = cache.get(source_id)
        cache[source_id] = groups if prior is None else np.unique(np.concatenate([prior, groups]))

    def describe(self) -> dict:
        d = super().describe()
        d.update(
            {
                "kind": "group",
                "target_size": self.target_size,
                "n_groups": self.n_groups,
                "assignment": self.assignment,
                "clustering": self.clustering,
            }
        )
        return d


class AttentionTieLayer(NetworkLayer):
    """Fixed out-degree directed ties: whose culture each agent is exposed to."""

    def __init__(
        self,
        name: str,
        n_agents: int,
        degree: int,
        rng: np.random.Generator,
        *,
        rewire_rate: float = 0.0,
        rewire_candidates: int = 4,
    ) -> None:
        if degree < 1:
            raise ValueError(f"layer {name!r}: degree must be >= 1")
        if not 0.0 <= rewire_rate <= 1.0:
            raise ValueError(f"layer {name!r}: rewire_rate must lie in [0, 1]")
        if rewire_candidates < 1:
            raise ValueError(f"layer {name!r}: rewire_candidates must be >= 1")
        self.name = name
        self.degree = int(degree)
        self.rewire_rate = float(rewire_rate)
        self.rewire_candidates = int(rewire_candidates)
        self.ties = self._random_ties(n_agents, self.degree, rng)

    @staticmethod
    def _random_ties(n: int, degree: int, rng: np.random.Generator) -> np.ndarray:
        if n == 0:
            return np.zeros((0, degree), dtype=np.int64)
        ties = rng.integers(0, max(n, 1), size=(n, degree)).astype(np.int64)
        if n > 1:
            # Remove self-ties by shifting; leaves the distribution uniform over
            # the other n-1 agents.
            self_idx = np.arange(n)[:, None]
            clash = ties == self_idx
            ties[clash] = (ties[clash] + 1) % n
        return ties

    def size(self) -> int:
        return int(self.ties.shape[0])

    def neighbours(self, agent_index: int) -> np.ndarray:
        return np.unique(self.ties[agent_index])

    def sample_partners(self, focal: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        slot = rng.integers(0, self.degree, size=focal.shape[0])
        return self.ties[focal, slot]

    def add_agents(self, n: int, rng: np.random.Generator, source_id: int = 0) -> None:
        if n < 0:
            raise ValueError("cannot add a negative number of agents")
        if n == 0:
            return
        total = self.size() + n
        new = rng.integers(0, total, size=(n, self.degree)).astype(np.int64)
        self.ties = np.vstack([self.ties, new])

    def rewire(self, population: Population, rng: np.random.Generator) -> int:
        """Homophilous rewiring: drop a tie, replace it with a more similar agent.

        Each agent, with probability ``rewire_rate``, drops one random tie and
        forms a new one with the most culturally similar of ``rewire_candidates``
        randomly drawn agents. This is the mechanism by which enclaves can form:
        structure follows culture, which then reinforces structure.

        Best-of-k rather than a similarity-proportional draw because k is a
        legible dial for homophily strength (k = 1 is no homophily at all) and
        because it costs one comparison pass instead of a normalisation over N
        (A-023).
        """
        n = self.size()
        if n < 2 or self.rewire_rate == 0.0:
            return 0
        active = np.flatnonzero(rng.random(n) < self.rewire_rate)
        if active.size == 0:
            return 0
        k = self.rewire_candidates
        candidates = rng.integers(0, n, size=(active.size, k))
        culture = population.culture
        # Similarity = number of features shared, computed against each candidate.
        agree = np.stack(
            [(culture[active] == culture[candidates[:, c]]).sum(axis=1) for c in range(k)],
            axis=1,
        )
        best = candidates[np.arange(active.size), np.argmax(agree, axis=1)]
        slot = rng.integers(0, self.degree, size=active.size)
        keep = best != active  # never tie an agent to itself
        self.ties[active[keep], slot[keep]] = best[keep]
        return int(keep.sum())

    def symmetric_edges(self) -> tuple[np.ndarray, np.ndarray]:
        """Undirected edge list, for measurement only.

        Modularity is defined on undirected graphs; the ties themselves stay
        directed because attention is not reciprocal.
        """
        n = self.size()
        src = np.repeat(np.arange(n, dtype=np.int64), self.degree)
        dst = self.ties.ravel()
        lo = np.minimum(src, dst)
        hi = np.maximum(src, dst)
        keep = lo != hi
        return lo[keep], hi[keep]

    def describe(self) -> dict:
        d = super().describe()
        d.update(
            {
                "kind": "directed_ties",
                "degree": self.degree,
                "rewire_rate": self.rewire_rate,
                "rewire_candidates": self.rewire_candidates,
            }
        )
        return d
