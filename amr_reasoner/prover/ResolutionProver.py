from __future__ import annotations
from typing import Iterable, Optional

from amr_reasoner.normalize.to_cnf import CNFDisjunction, to_cnf
from amr_reasoner.prover.Proof import Proof
from amr_reasoner.prover.operations.resolve import resolve
from amr_reasoner.prover.ProofStep import ProofStep
from amr_reasoner.similarity import SimilarityFunc
from amr_reasoner.types import Clause, Not


class ResolutionProver:
    base_knowledge: frozenset[CNFDisjunction]
    max_proof_depth: int
    min_similarity_threshold: float
    # MyPy freaks out if this isn't optional, see https://github.com/python/mypy/issues/708
    similarity_func: Optional[SimilarityFunc]

    def __init__(
        self,
        knowledge: Iterable[Clause],
        max_proof_depth: int = 10,
        similarity_func: Optional[SimilarityFunc] = None,
        min_similarity_threshold: float = 0.5,
    ) -> None:
        self.max_proof_depth = max_proof_depth
        self.similarity_func = similarity_func
        self.min_similarity_threshold = min_similarity_threshold
        parsed_knowledge = set()
        for clause in knowledge:
            parsed_knowledge.update(to_cnf(clause))
        self.base_knowledge = frozenset(parsed_knowledge)

    def prove(self, goal: Clause) -> Optional[Proof]:
        """Find the best proof for the given goal"""
        proofs = self.prove_all(goal)
        if proofs:
            return proofs[0]
        return None

    def prove_all(self, goal: Clause) -> list[Proof]:
        """Find all possible proofs for the given goal, sorted by similarity score"""
        inverted_goals = to_cnf(Not(goal))
        proofs = []
        knowledge = self.base_knowledge | inverted_goals
        for inverted_goal in inverted_goals:
            leaf_proof_steps = self._prove_all_recursive(inverted_goal, knowledge)
            for leaf_proof_step in leaf_proof_steps:
                # TODO: Make combining similarities customizable rather than always taking the minimum
                similarity = leaf_proof_step.similarity
                cur_state = leaf_proof_step
                while cur_state.parent:
                    similarity = min(similarity, cur_state.parent.similarity)
                    cur_state = cur_state.parent
                proofs.append(Proof(inverted_goal, similarity, leaf_proof_step))

        return sorted(proofs, key=lambda proof: proof.similarity, reverse=True)

    def _prove_all_recursive(
        self,
        goal: CNFDisjunction,
        knowledge: frozenset[CNFDisjunction],
        depth: int = 0,
        parent_state: Optional[ProofStep] = None,
    ) -> list[ProofStep]:
        if parent_state and depth >= self.max_proof_depth:
            return []
        successful_proof_leaf_steps = []
        for clause in knowledge:
            next_states = resolve(
                goal,
                clause,
                min_similarity_threshold=self.min_similarity_threshold,
                similarity_func=self.similarity_func,
                parent=parent_state,
            )
            for next_state in next_states:
                if next_state.resolvent is None:
                    raise ValueError("Resolvent was unexpectedly not present")
                if len(next_state.resolvent.literals) == 0:
                    successful_proof_leaf_steps.append(next_state)
                else:
                    successful_proof_leaf_steps += self._prove_all_recursive(
                        next_state.resolvent, knowledge, depth + 1, next_state
                    )

        return successful_proof_leaf_steps
