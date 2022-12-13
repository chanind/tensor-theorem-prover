from __future__ import annotations
from typing import Optional

from .ProofStep import ProofStep


class ProofStepAccumulator:
    """Helper class which accumulates successful proof steps and keeps track of the minimum proof similarity"""

    max_proofs: Optional[int]
    scored_proof_steps: list[tuple[float, ProofStep]]
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

    def add_proof(self, proof_step: ProofStep) -> None:
        """Add a proof step to the accumulator"""

        # TODO: Make combining similarities customizable rather than always taking the minimum
        similarity = proof_step.similarity
        cur_step = proof_step
        while cur_step.parent:
            similarity = min(similarity, cur_step.parent.similarity)
            cur_step = cur_step.parent

        self.scored_proof_steps.append((similarity, proof_step))
        self.scored_proof_steps.sort(key=lambda x: x[0], reverse=True)
        if self.max_proofs and len(self.scored_proof_steps) > self.max_proofs:
            # Remove the proof step with the lowest similarity
            self.scored_proof_steps.pop()
        # Update the minimum similarity
        self.min_similarity = self.scored_proof_steps[-1][0]
