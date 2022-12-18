from __future__ import annotations
from copy import copy
from typing import Optional

from tensor_theorem_prover.prover.ProofStats import ProofStats

from .ProofStep import ProofStep


class ProofContext:
    """Helper class which accumulates successful proof steps and keeps track of stats during the proof process"""

    max_proofs: Optional[int]
    scored_proof_steps: list[tuple[float, int, ProofStep, ProofStats]]
    min_similarity_threshold: float
    stats: ProofStats
    seen_resolvents_hash: dict[int, tuple[int, float]]
    skip_seen_resolvents: bool

    def __init__(
        self,
        initial_min_similarity_threshold: float = 0.0,
        max_proofs: Optional[int] = None,
        skip_seen_resolvents: bool = False,
    ) -> None:
        self.stats = ProofStats()
        self.min_similarity_threshold = initial_min_similarity_threshold
        self.max_proofs = max_proofs
        self.scored_proof_steps = []
        self.seen_resolvents_hash = {}
        self.skip_seen_resolvents = skip_seen_resolvents

    def record_leaf_proof(self, proof_step: ProofStep) -> None:
        """Add a leaf proof step to the accumulator"""

        # make sure to clone the stats before appending, since the stats will continue to get mutated after this
        self.scored_proof_steps.append(
            (
                proof_step.running_similarity,
                proof_step.depth,
                proof_step,
                copy(self.stats),
            )
        )
        self.scored_proof_steps.sort(key=lambda x: (x[0], -1 * x[1]), reverse=True)
        if self.max_proofs and len(self.scored_proof_steps) > self.max_proofs:
            # Remove the proof step with the lowest similarity
            self.scored_proof_steps.pop()
            self.stats.discarded_proofs += 1
            # Update the minimum similarity threshold to the new lowest similarity
            self.min_similarity_threshold = self.scored_proof_steps[-1][0]

    def leaf_proof_steps_with_stats(self) -> list[tuple[ProofStep, ProofStats]]:
        return [
            (proof_step, stats) for _, _, proof_step, stats in self.scored_proof_steps
        ]

    def check_resolvent(
        self,
        proof_step: ProofStep,
    ) -> bool:
        """
        Check if the resolvent has already been seen at the current depth or below and if so, return False.
        Otherwise, add it to the seen set and return True
        """
        if not self.skip_seen_resolvents:
            return True
        self.stats.resolvent_checks += 1
        resolvent_hash = hash(proof_step.resolvent)
        if resolvent_hash in self.seen_resolvents_hash:
            prev_depth, prev_similarity = self.seen_resolvents_hash[resolvent_hash]
            if (
                prev_depth <= proof_step.depth
                and prev_similarity >= proof_step.running_similarity
            ):
                self.stats.resolvent_check_hits += 1
                return False
        self.seen_resolvents_hash[resolvent_hash] = (
            proof_step.depth,
            proof_step.running_similarity,
        )
        return True
