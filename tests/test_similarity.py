import pytest
import numpy as np
from tensor_theorem_prover.prover.ProofStats import ProofStats

from tensor_theorem_prover.similarity import (
    SimilarityCache,
    cosine_similarity,
    similarity_with_cache,
    symbol_compare,
    max_similarity,
)
from tensor_theorem_prover.types.Constant import Constant


def test_cosine_similarity_uses_the_provided_similarity_metric() -> None:
    assert cosine_similarity(
        Constant("a", np.array([1, 0, 1])),
        Constant("b", np.array([0, 1, 1])),
    ) == pytest.approx(0.5)


def test_cosine_similarity_compares_symbols_if_either_const_is_missing_a_embedding() -> None:
    assert cosine_similarity(
        Constant("a", np.array([1, 0, 1])),
        Constant("b"),
    ) == pytest.approx(0.0)
    assert cosine_similarity(
        Constant("same"),
        Constant("same"),
    ) == pytest.approx(1.0)


def test_symbol_compare_compares_symbols_directly() -> None:
    assert symbol_compare(
        Constant("a", np.array([1, 0, 1])),
        Constant("b", np.array([0, 1, 1])),
    ) == pytest.approx(0.0)
    assert symbol_compare(
        Constant("same", np.array([1, 0, 1])),
        Constant("same", np.array([0, 1, 1])),
    ) == pytest.approx(1.0)


def test_max_similarity_takes_the_max_of_all_passed_similarity_measures() -> None:
    combined_similarity = max_similarity([symbol_compare, cosine_similarity])
    assert combined_similarity(
        Constant("a", np.array([1, 0, 1])),
        Constant("b", np.array([0, 1, 1])),
    ) == pytest.approx(0.5)
    assert (
        combined_similarity(
            Constant("b", np.array([1, 0, 1])),
            Constant("b", np.array([0, 1, 1])),
        )
        == 1.0
    )


def test_similarity_with_cache() -> None:
    stats = ProofStats()
    item1 = Constant("a", np.array([1, 0, 1]))
    item2 = Constant("b", np.array([0, 1, 1]))
    cache: SimilarityCache = {(id(item1), id(item2)): 0.75}
    similarity = similarity_with_cache(cosine_similarity, cache, stats)
    assert similarity(item1, item2) == pytest.approx(0.75)
    assert stats.similarity_cache_hits == 1
    cache.clear()
    assert similarity(item1, item2) == pytest.approx(0.5)
    assert cache[(id(item1), id(item2))] == pytest.approx(0.5)
    assert stats.similarity_cache_hits == 1
