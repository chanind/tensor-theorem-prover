from __future__ import annotations

from typing import Any, Optional, Union

from tensor_theorem_prover.similarity import SimilarityFunc

# The _rust module is just a flat module, since submodules using pyO3 seems finicky.

class RsAtom:
    predicate: RsPredicate
    terms: list[RsTerm]

    def __init__(self, predicate: RsPredicate, terms: list[RsTerm]) -> None: ...

class RsPredicate:
    symbol: str
    embedding: Optional[Any]

    def __init__(self, symbol: str, embedding: Optional[Any]) -> None: ...

class RsConstant:
    symbol: str
    embedding: Optional[Any]

    def __init__(self, symbol: str, embedding: Optional[Any]) -> None: ...

class RsVariable:
    name: str

    def __init__(self, name: str) -> None: ...

class RsFunction:
    symbol: str

    def __init__(self, symbol: str) -> None: ...

class RsBoundFunction:
    function: RsFunction
    terms: list[RsTerm]

    def __init__(self, function: RsFunction, terms: list[RsTerm]) -> None: ...

RsTerm = Union[RsConstant, RsVariable, RsBoundFunction]

class RsCNFLiteral:
    atom: RsAtom
    polarity: bool

    def __init__(self, atom: RsAtom, polarity: bool) -> None: ...

class RsCNFDisjunction:
    literals: set[RsCNFLiteral]

    def __init__(self, literals: set[RsCNFLiteral]) -> None: ...

class RsProofStep:
    source: RsCNFDisjunction
    target: RsCNFDisjunction
    source_unification_literal: RsCNFLiteral
    target_unification_literal: RsCNFLiteral
    source_substitutions: dict[RsVariable, RsTerm]
    target_substitutions: dict[RsVariable, RsTerm]
    resolvent: RsCNFDisjunction
    similarity: float
    running_similarity: float
    depth: int

class RsProofStats:
    attempted_unifications: int
    successful_unifications: int
    similarity_comparisons: int
    similarity_cache_hits: int
    attempted_resolutions: int
    successful_resolutions: int
    max_resolvent_width_seen: int
    max_depth_seen: int
    discarded_proofs: int
    resolvent_checks: int
    resolvent_check_hits: int

class RsProof:
    goal: RsCNFDisjunction
    similarity: float
    stats: RsProofStats
    leaf_proof_step: RsProofStep
    substitutions: dict[RsVariable, RsTerm]
    depth: int
    proof_steps: list[RsProofStep]

class RsResolutionProverBackend:
    max_proof_depth: int
    max_resolution_attempts: Optional[int]
    max_resolvent_width: Optional[int]
    min_similarity_threshold: float
    py_similarity_fn: Optional[SimilarityFunc]
    cache_similarity: bool
    skip_seen_resolvents: bool
    find_highest_similarity_proofs: bool
    base_knowledge: set[RsCNFDisjunction]

    def __init__(
        self,
        max_proof_depth: int,
        max_resolvent_width: Optional[int],
        max_resolution_attempts: Optional[int],
        py_similarity_fn: Optional[SimilarityFunc],
        min_similarity_threshold: float,
        cache_similarity: bool,
        skip_seen_resolvents: bool,
        find_highest_similarity_proofs: bool,
        base_knowledge: set[RsCNFDisjunction],
    ) -> None: ...
    def extend_knowledge(self, knowledge: set[RsCNFDisjunction]) -> None: ...
    def prove_all_with_stats(
        self,
        inverted_goals: set[RsCNFDisjunction],
        extra_knowledge: Optional[set[RsCNFDisjunction]],
        max_proofs: Optional[int],
        skip_seen_resolvents: Optional[bool],
    ) -> tuple[list[RsProof], RsProofStats]: ...
    def reset(self) -> None: ...
    def purge_similarity_cache(self) -> None: ...
