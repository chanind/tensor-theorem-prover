from __future__ import annotations
from typing import Callable, Dict, Iterable, Tuple, Union
import numpy as np
from numpy.linalg import norm
from tensor_theorem_prover.prover.ProofStats import ProofStats

from tensor_theorem_prover.types.Constant import Constant
from tensor_theorem_prover.types.Predicate import Predicate


SimilarityFunc = Callable[
    [Union[Constant, Predicate], Union[Constant, Predicate]], float
]

SimilarityCache = Dict[Tuple[Union[str, int], Union[str, int]], float]


def similarity_with_cache(
    similarity: SimilarityFunc,
    cache: SimilarityCache,
    proof_stats: ProofStats,
) -> SimilarityFunc:
    """cache all similarity scores by the object id of the items being compared"""

    def _similarity_with_cache(
        item1: Constant | Predicate, item2: Constant | Predicate
    ) -> float:
        key1: str | int = item1.symbol if item1.embedding is None else id(item1)
        key2: str | int = item2.symbol if item2.embedding is None else id(item2)
        key = (key1, key2)
        if key in cache:
            proof_stats.similarity_cache_hits += 1
        else:
            cache[key] = similarity(item1, item2)
        return cache[key]

    return _similarity_with_cache


def symbol_compare(item1: Constant | Predicate, item2: Constant | Predicate) -> float:
    """
    directly compares the symbol strings of the two items, doesn't do any fuzzy matching
    """
    return 1.0 if item1.symbol == item2.symbol else 0.0


def cosine_similarity(
    item1: Constant | Predicate, item2: Constant | Predicate
) -> float:
    """
    use cosine similarity to calculate a similarity score between the items.
    falls back to symbol comparison if either item is missing a embedding
    """
    if item1.embedding is None or item2.embedding is None:
        return symbol_compare(item1, item2)
    return np.dot(item1.embedding, item2.embedding) / (
        norm(item1.embedding) * norm(item2.embedding)
    )


def max_similarity(funcs: Iterable[SimilarityFunc]) -> SimilarityFunc:
    """
    returns a function that calls all the given functions and returns the maximum similarity score
    """
    return lambda item1, item2: max(func(item1, item2) for func in funcs)
