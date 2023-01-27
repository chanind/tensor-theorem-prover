import pytest
import numpy as np

from tensor_theorem_prover.similarity import (
    cosine_similarity,
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
