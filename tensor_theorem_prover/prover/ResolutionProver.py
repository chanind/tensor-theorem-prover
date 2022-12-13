from __future__ import annotations

from typing import Iterable, Optional

from tensor_theorem_prover.normalize import Skolemizer, CNFDisjunction, to_cnf
from tensor_theorem_prover.prover.Proof import Proof
from tensor_theorem_prover.prover.ProofStepAccumulator import ProofStepAccumulator
from tensor_theorem_prover.prover.operations.resolve import resolve
from tensor_theorem_prover.prover.ProofStep import ProofStep
from tensor_theorem_prover.similarity import (
    SimilarityCache,
    SimilarityFunc,
    cosine_similarity,
    similarity_with_cache,
)
from tensor_theorem_prover.types import Clause, Not


class ResolutionProver:
    base_knowledge: list[CNFDisjunction]
    max_proof_depth: int
    max_resolvent_width: Optional[int]
    min_similarity_threshold: float
    # MyPy freaks out if this isn't optional, see https://github.com/python/mypy/issues/708
    similarity_func: Optional[SimilarityFunc]
    skolemizer: Skolemizer
    similarity_cache: SimilarityCache

    def __init__(
        self,
        knowledge: Optional[Iterable[Clause]] = None,
        max_proof_depth: int = 10,
        max_resolvent_width: Optional[int] = None,
        similarity_func: Optional[SimilarityFunc] = cosine_similarity,
        min_similarity_threshold: float = 0.5,
        cache_similarity: bool = True,
    ) -> None:
        self.max_proof_depth = max_proof_depth
        self.max_resolvent_width = max_resolvent_width
        self.min_similarity_threshold = min_similarity_threshold
        self.skolemizer = Skolemizer()
        self.similarity_cache = {}
        if cache_similarity and similarity_func:
            self.similarity_func = similarity_with_cache(
                similarity_func, self.similarity_cache
            )
        else:
            self.similarity_func = similarity_func
        self.base_knowledge = []
        if knowledge is not None:
            self.extend_knowledge(knowledge)

    def extend_knowledge(self, knowledge: Iterable[Clause]) -> None:
        """Add more knowledge to the prover"""
        self.base_knowledge.extend(self._parse_knowledge(knowledge))

    def _parse_knowledge(self, knowledge: Iterable[Clause]) -> list[CNFDisjunction]:
        """Parse the knowledge into CNF form"""
        parsed_knowledge = []
        for clause in knowledge:
            parsed_knowledge.extend(to_cnf(clause, self.skolemizer))
        return parsed_knowledge

    def prove(
        self, goal: Clause, extra_knowledge: Optional[Iterable[Clause]] = None
    ) -> Optional[Proof]:
        """Find the best proof for the given goal"""
        proofs = self.prove_all(goal, extra_knowledge, max_proofs=1)
        if proofs:
            return proofs[0]
        return None

    def prove_all(
        self,
        goal: Clause,
        extra_knowledge: Optional[Iterable[Clause]] = None,
        max_proofs: Optional[int] = None,
    ) -> list[Proof]:
        """Find all possible proofs for the given goal, sorted by similarity score"""
        inverted_goals = to_cnf(Not(goal), self.skolemizer)
        parsed_extra_knowledge = self._parse_knowledge(extra_knowledge or [])
        proofs = []
        knowledge = self.base_knowledge + parsed_extra_knowledge + inverted_goals
        leaf_proof_steps_acc = ProofStepAccumulator(max_proofs)
        for inverted_goal in inverted_goals:
            self._prove_all_recursive(inverted_goal, knowledge, leaf_proof_steps_acc)
            for similarity, leaf_proof_step in leaf_proof_steps_acc.scored_proof_steps:
                proofs.append(Proof(inverted_goal, similarity, leaf_proof_step))

        return sorted(proofs, key=lambda proof: proof.similarity, reverse=True)

    def purge_similarity_cache(self) -> None:
        self.similarity_cache.clear()

    def reset(self) -> None:
        """Clear all knowledge from the prover and wipe the similarity cache"""
        self.base_knowledge = []
        self.purge_similarity_cache()

    def _prove_all_recursive(
        self,
        goal: CNFDisjunction,
        knowledge: Iterable[CNFDisjunction],
        leaf_proof_steps_acc: ProofStepAccumulator,
        depth: int = 0,
        parent_state: Optional[ProofStep] = None,
    ) -> None:
        if parent_state and depth >= self.max_proof_depth:
            return
        for clause in knowledge:
            # resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
            # so we know what the length of the resolvent will be before we even try to resolve
            if (
                self.max_resolvent_width
                and len(clause.literals) + len(goal.literals) - 2
                > self.max_resolvent_width
            ):
                continue
            min_similarity_threshold = self.min_similarity_threshold
            if leaf_proof_steps_acc.is_full():
                min_similarity_threshold = leaf_proof_steps_acc.min_similarity
            next_states = resolve(
                goal,
                clause,
                min_similarity_threshold=min_similarity_threshold,
                similarity_func=self.similarity_func,
                parent=parent_state,
            )
            for next_state in next_states:
                if next_state.resolvent is None:
                    raise ValueError("Resolvent was unexpectedly not present")
                if len(next_state.resolvent.literals) == 0:
                    leaf_proof_steps_acc.add_proof(next_state)
                else:
                    self._prove_all_recursive(
                        next_state.resolvent,
                        knowledge,
                        leaf_proof_steps_acc,
                        depth + 1,
                        next_state,
                    )
