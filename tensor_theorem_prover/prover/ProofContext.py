from __future__ import annotations
from copy import copy
from typing import Optional

from tensor_theorem_prover.prover.ProofStats import ProofStats

from .ProofStep import ProofStep


class ProofContext:
    """Helper class which accumulates successful proof steps and keeps track of stats during the proof process"""

    max_proofs: Optional[int]
    scored_proof_steps: list[tuple[float, ProofStep, ProofStats]]
    min_similarity_threshold: float
    stats: ProofStats

    def __init__(
        self,
        initial_min_similarity_threshold: float = 0.0,
        max_proofs: Optional[int] = None,
    ) -> None:
        self.stats = ProofStats()
        self.min_similarity_threshold = initial_min_similarity_threshold
        self.max_proofs = max_proofs
        self.scored_proof_steps = []

    def record_leaf_proof(self, proof_step: ProofStep) -> None:
        """Add a leaf proof step to the accumulator"""

        similarity = proof_step.running_similarity
        # make sure to clone the stats before appending, since the stats will continue to get mutated after this
        self.scored_proof_steps.append((similarity, proof_step, copy(self.stats)))
        self.scored_proof_steps.sort(key=lambda x: x[0], reverse=True)
        if self.max_proofs and len(self.scored_proof_steps) > self.max_proofs:
            # Remove the proof step with the lowest similarity
            self.scored_proof_steps.pop()
            self.stats.discarded_proofs += 1
            # Update the minimum similarity threshold to the new lowest similarity
            self.min_similarity_threshold = self.scored_proof_steps[-1][0]
