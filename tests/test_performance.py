from __future__ import annotations

import pytest
import pickle
import re

from tensor_theorem_prover import (
    Clause,
    ResolutionProver,
    Constant,
    Predicate,
    max_similarity,
    cosine_similarity,
    symbol_compare,
)


STRIP_FRAME_NUMBER_RE = re.compile(r"-\d+$")


symbols_sans_frame_numbers: dict[str, str] = {}


def strip_frame_number(symbol: str) -> str:
    if symbol not in symbols_sans_frame_numbers:
        stripped_symbol = re.sub(STRIP_FRAME_NUMBER_RE, "", symbol)
        symbols_sans_frame_numbers[symbol] = stripped_symbol
    return symbols_sans_frame_numbers[symbol]


def partial_symbol_compare(
    item1: Constant | Predicate, item2: Constant | Predicate
) -> float:
    if strip_frame_number(item1.symbol) == strip_frame_number(item2.symbol):
        return 0.6
    return 0.0


@pytest.mark.skip(reason="Performance test")
def test_performance() -> None:
    with open("tests/logic.pickle", "rb") as f:
        data = pickle.load(f)
    knowledge: list[Clause] = data["knowledge"]
    query: Clause = data["query"]

    prover = ResolutionProver(
        knowledge=knowledge,
        similarity_func=max_similarity(
            [cosine_similarity, symbol_compare, partial_symbol_compare]
        ),
    )
    prover.prove(query)
