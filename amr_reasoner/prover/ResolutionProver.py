from __future__ import annotations
from typing import Iterable, Optional

from amr_reasoner.normalize.to_cnf import CNFDisjunction, to_cnf
from amr_reasoner.prover.operations.resolve import resolve
from amr_reasoner.prover.types import ProofState
from amr_reasoner.similarity import SimilarityFunc
from amr_reasoner.types import Clause, Not


class ResolutionProver:

    knowledge: frozenset[CNFDisjunction]
    max_proof_depth: int
    min_similarity_threshold: float
    # MyPy freaks out if this isn't optional, see https://github.com/python/mypy/issues/708
    similarity_func: Optional[SimilarityFunc]

    def __init__(
        self,
        knowledge: Iterable[Clause],
        max_proof_depth: int = 10,
        similarity_func: Optional[SimilarityFunc] = None,
    ) -> None:
        self.max_proof_depth = max_proof_depth
        self.similarity_func = similarity_func
        parsed_knowledge = set()
        for clause in knowledge:
            parsed_knowledge.update(to_cnf(clause))
        self.knowledge = frozenset(parsed_knowledge)

    def prove(self, goal: Clause) -> list[ProofState]:
        inverted_goals = to_cnf(Not(goal))
        knowledge = self.knowledge | inverted_goals
        initial_state = ProofState(knowledge=knowledge)
        successful_proof_states = []
        for inverted_goal in inverted_goals:
            successful_proof_states += self._prove(inverted_goal, initial_state)
        return successful_proof_states

    def _prove(self, goal: CNFDisjunction, state: ProofState) -> list[ProofState]:
        if state.depth >= self.max_proof_depth:
            return []
        successful_states = []
        for clause in state.knowledge:
            next_states = resolve(clause, goal, state)
            for next_state in next_states:
                if next_state.resolvent is None:
                    raise ValueError("Resolvent was unexpectedly not present")
                if len(next_state.resolvent.literals) == 0:
                    successful_states.append(next_state)
                else:
                    successful_states += self._prove(next_state.resolvent, next_state)

        return successful_states
