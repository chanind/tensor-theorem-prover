from __future__ import annotations

from typing import Iterable, Optional

from tensor_theorem_prover.normalize import Skolemizer, CNFDisjunction, to_cnf
from tensor_theorem_prover.prover.Proof import Proof
from tensor_theorem_prover.prover.ProofStats import ProofStats
from tensor_theorem_prover.prover.ProofContext import ProofContext
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
    cache_similarity: bool

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
        self.cache_similarity = cache_similarity
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
        proofs, _ = self.prove_all_with_stats(
            goal, extra_knowledge, max_proofs=max_proofs
        )
        return proofs

    def prove_all_with_stats(
        self,
        goal: Clause,
        extra_knowledge: Optional[Iterable[Clause]] = None,
        max_proofs: Optional[int] = None,
    ) -> tuple[list[Proof], ProofStats]:
        """
        Find all possible proofs for the given goal, sorted by similarity score.
        Return the proofs and the stats for the proof search.
        """
        inverted_goals = to_cnf(Not(goal), self.skolemizer)
        parsed_extra_knowledge = self._parse_knowledge(extra_knowledge or [])
        proofs = []
        knowledge = self.base_knowledge + parsed_extra_knowledge + inverted_goals
        ctx = ProofContext(
            initial_min_similarity_threshold=self.min_similarity_threshold,
            max_proofs=max_proofs,
        )
        similarity_func = self.similarity_func
        if self.cache_similarity and self.similarity_func:
            similarity_func = similarity_with_cache(
                self.similarity_func, self.similarity_cache, ctx.stats
            )

        for inverted_goal in inverted_goals:
            self._prove_all_recursive(
                inverted_goal,
                knowledge,
                similarity_func,
                ctx,
            )
            for (
                similarity,
                leaf_proof_step,
                leaf_proof_stats,
            ) in ctx.scored_proof_steps:
                proofs.append(
                    Proof(
                        inverted_goal,
                        similarity,
                        leaf_proof_step,
                        leaf_proof_stats,
                    )
                )

        return (
            sorted(proofs, key=lambda proof: proof.similarity, reverse=True),
            ctx.stats,
        )

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
        similarity_func: Optional[SimilarityFunc],
        ctx: ProofContext,
        depth: int = 0,
        parent_state: Optional[ProofStep] = None,
    ) -> None:
        if parent_state and depth >= self.max_proof_depth:
            return
        if depth >= ctx.stats.max_depth_seen:
            # add 1 to match the depth stat seen in proofs. It's strange if the proof has depth 12, but max_depth_seen is 11
            ctx.stats.max_depth_seen = depth + 1
        for clause in knowledge:
            # resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
            # so we know what the length of the resolvent will be before we even try to resolve
            if (
                self.max_resolvent_width
                and len(clause.literals) + len(goal.literals) - 2
                > self.max_resolvent_width
            ):
                continue
            ctx.stats.attempted_resolutions += 1
            next_states = resolve(
                goal,
                clause,
                similarity_func=similarity_func,
                parent=parent_state,
                ctx=ctx,
            )
            if len(next_states) > 0:
                ctx.stats.successful_resolutions += 1
            for next_state in next_states:
                if next_state.resolvent is None:
                    raise ValueError("Resolvent was unexpectedly not present")
                if len(next_state.resolvent.literals) == 0:
                    ctx.record_leaf_proof(next_state)
                else:
                    resolvent_width = len(next_state.resolvent.literals)
                    if resolvent_width >= ctx.stats.max_resolvent_width_seen:
                        ctx.stats.max_resolvent_width_seen = resolvent_width
                    self._prove_all_recursive(
                        next_state.resolvent,
                        knowledge,
                        similarity_func,
                        ctx,
                        depth + 1,
                        next_state,
                    )
