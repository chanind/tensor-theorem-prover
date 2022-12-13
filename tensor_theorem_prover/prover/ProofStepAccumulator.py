from __future__ import annotations
from copy import copy
from typing import Optional

from tensor_theorem_prover.prover.ProofStats import ProofStats

from .ProofStep import ProofStep


class ProofStepAccumulator:
    """Helper class which accumulates successful proof steps and keeps track of the minimum proof similarity"""

    max_proofs: Optional[int]
    scored_proof_steps: list[tuple[float, ProofStep, ProofStats]]
    min_similarity: float

    def __init__(self, max_proofs: Optional[int] = None) -> None:
        self.max_proofs = max_proofs
        self.scored_proof_steps = []
        self.min_similarity = 0.0

    def is_full(self) -> bool:
        """Return True if the accumulator is full, i.e. it has enough proofs"""
        return (
            self.max_proofs is not None
            and len(self.scored_proof_steps) >= self.max_proofs
        )

    def add_proof(self, proof_step: ProofStep, stats: ProofStats) -> None:
        """Add a proof step to the accumulator"""

        # TODO: Make combining similarities customizable rather than always taking the minimum
        similarity = proof_step.similarity
        cur_step = proof_step
        while cur_step.parent:
            similarity = min(similarity, cur_step.parent.similarity)
            cur_step = cur_step.parent

        # make sure to clone the stats before appending, since the stats will continue to get mutated after this
        self.scored_proof_steps.append((similarity, proof_step, copy(stats)))
        self.scored_proof_steps.sort(key=lambda x: x[0], reverse=True)
        if self.max_proofs and len(self.scored_proof_steps) > self.max_proofs:
            # Remove the proof step with the lowest similarity
            self.scored_proof_steps.pop()
            stats.discarded_proofs += 1
        # Update the minimum similarity
        self.min_similarity = self.scored_proof_steps[-1][0]
