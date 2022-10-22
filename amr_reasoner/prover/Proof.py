from __future__ import annotations
from collections import deque

from dataclasses import dataclass
from textwrap import indent

from amr_reasoner.normalize.to_cnf import CNFDisjunction
from .ProofState import ProofState


@dataclass(frozen=True, eq=True)
class Proof:
    goal: CNFDisjunction
    similarity: float
    leaf_proof_state: ProofState

    @property
    def proof_states(self) -> list[ProofState]:
        proof_states: deque[ProofState] = deque()
        cur_proof_state = self.leaf_proof_state
        while True:
            proof_states.appendleft(cur_proof_state)
            if not cur_proof_state.parent:
                break
            cur_proof_state = cur_proof_state.parent
        return list(proof_states)

    def __str__(self) -> str:
        output = f"Goal: {self.goal}\n"
        output += f"Similarity: {self.similarity}\n"
        output += f"Depth: {len(self.proof_states)}\n"
        output += "Steps:\n"
        output += "\n---\n".join(
            indent(str(proof_state), "  ") for proof_state in self.proof_states
        )
        return output
