from __future__ import annotations

from typing import Iterable, Optional

from tensor_theorem_prover.normalize import (
    Skolemizer,
    to_cnf,
)
from tensor_theorem_prover.prover.Proof import Proof
from tensor_theorem_prover.prover.ProofStats import ProofStats
from tensor_theorem_prover.similarity import (
    SimilarityFunc,
    cosine_similarity,
)
from tensor_theorem_prover.types import Clause, Not

from tensor_theorem_prover._rust import RsCNFDisjunction, RsResolutionProverBackend


class ResolutionProver:
    """
    Core theorem prover class that uses input resolution to prove a goal
    """

    skolemizer: Skolemizer
    backend: RsResolutionProverBackend

    def __init__(
        self,
        knowledge: Optional[Iterable[Clause]] = None,
        max_proof_depth: int = 10,
        max_resolvent_width: Optional[int] = None,
        max_resolution_attempts: Optional[int] = None,
        similarity_func: Optional[SimilarityFunc] = cosine_similarity,
        min_similarity_threshold: float = 0.5,
        cache_similarity: bool = True,
        skip_seen_resolvents: bool = False,
        find_highest_similarity_proofs: bool = True,
    ) -> None:
        self.skolemizer = Skolemizer()
        self.backend = RsResolutionProverBackend(
            max_proof_depth,
            max_resolvent_width,
            max_resolution_attempts,
            similarity_func,
            min_similarity_threshold,
            cache_similarity,
            skip_seen_resolvents,
            find_highest_similarity_proofs,
            set(),
        )
        if knowledge is not None:
            self.extend_knowledge(knowledge)

    def extend_knowledge(self, knowledge: Iterable[Clause]) -> None:
        """Add more knowledge to the prover"""
        self.backend.extend_knowledge(self._parse_knowledge(knowledge))

    def _parse_knowledge(self, knowledge: Iterable[Clause]) -> set[RsCNFDisjunction]:
        """Parse the knowledge into CNF form"""
        parsed_knowledge = set()
        for clause in knowledge:
            parsed_knowledge.update(to_cnf(clause, self.skolemizer))
        return set(cnf.to_rust() for cnf in parsed_knowledge)

    def prove(
        self, goal: Clause, extra_knowledge: Optional[Iterable[Clause]] = None
    ) -> Optional[Proof]:
        """Find the proof for the given goal with highest similarity score"""
        proofs = self.prove_all(
            goal, extra_knowledge, max_proofs=1, skip_seen_resolvents=True
        )
        if proofs:
            return proofs[0]
        return None

    def prove_all(
        self,
        goal: Clause,
        extra_knowledge: Optional[Iterable[Clause]] = None,
        max_proofs: Optional[int] = None,
        skip_seen_resolvents: Optional[bool] = None,
    ) -> list[Proof]:
        """Find all possible proofs for the given goal, sorted by similarity score"""
        proofs, _ = self.prove_all_with_stats(
            goal,
            extra_knowledge,
            max_proofs=max_proofs,
            skip_seen_resolvents=skip_seen_resolvents,
        )
        return proofs

    def prove_all_with_stats(
        self,
        goal: Clause,
        extra_knowledge: Optional[Iterable[Clause]] = None,
        max_proofs: Optional[int] = None,
        skip_seen_resolvents: Optional[bool] = None,
    ) -> tuple[list[Proof], ProofStats]:
        """
        Find all possible proofs for the given goal, sorted by similarity score.
        Return the proofs and the stats for the proof search.
        """
        inverted_goals = set(
            cnf.to_rust() for cnf in to_cnf(Not(goal), self.skolemizer)
        )
        parsed_extra_knowledge = self._parse_knowledge(extra_knowledge or [])
        (rust_proofs, rust_stats) = self.backend.prove_all_with_stats(
            inverted_goals, parsed_extra_knowledge, max_proofs, skip_seen_resolvents
        )
        proofs = [Proof.from_rust(rust_proof) for rust_proof in rust_proofs]
        stats = ProofStats.from_rust(rust_stats)
        return (proofs, stats)

    def purge_similarity_cache(self) -> None:
        pass

    def reset(self) -> None:
        """Clear all knowledge from the prover and wipe the similarity cache"""
        self.backend.reset()
