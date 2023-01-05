from __future__ import annotations

import pytest
import pickle
import re
import time

from tensor_theorem_prover import (
    Clause,
    ResolutionProver,
    Constant,
    Predicate,
    max_similarity,
    cosine_similarity,
    symbol_compare,
)
from tensor_theorem_prover.prover import ProofStats


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
        max_proof_depth=13,
        max_resolvent_width=6,
        min_similarity_threshold=0.7,
        skip_seen_resolvents=True,
    )
    start = time.time()
    proof, stats = prover.prove_all_with_stats(query, max_proofs=1)
    print(proof[0])
    print(stats)
    elapsed = time.time() - start
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(
        f"attempted resolutions per second: {int(stats.attempted_resolutions / elapsed):,}"
    )
    assert proof[0].similarity == pytest.approx(0.9049135)


@pytest.mark.skip(reason="Performance test")
def test_performance_with_amr_reasoner_batch() -> None:
    with open("tests/amr_logic_batch.pickle", "rb") as f:
        batch = pickle.load(f)
    stats = []
    start = time.time()
    for sample in batch:
        prover = ResolutionProver(
            knowledge=sample["knowledge"],
            similarity_func=max_similarity(
                [cosine_similarity, symbol_compare, partial_symbol_compare]
            ),
            max_proof_depth=13,
            max_resolvent_width=8,
            min_similarity_threshold=0.5,
            skip_seen_resolvents=True,
        )
        for goal in sample["goals"]:
            _proof, proof_stats = prover.prove_all_with_stats(goal, max_proofs=1)
            stats.append(proof_stats)
    summed_stats = ProofStats(
        attempted_unifications=sum(s.attempted_unifications for s in stats),
        successful_unifications=sum(s.successful_unifications for s in stats),
        similarity_comparisons=sum(s.similarity_comparisons for s in stats),
        similarity_cache_hits=sum(s.similarity_cache_hits for s in stats),
        attempted_resolutions=sum(s.attempted_resolutions for s in stats),
        successful_resolutions=sum(s.successful_resolutions for s in stats),
        max_resolvent_width_seen=max(s.max_resolvent_width_seen for s in stats),
        max_depth_seen=max(s.max_depth_seen for s in stats),
        discarded_proofs=sum(s.discarded_proofs for s in stats),
        resolvent_checks=sum(s.resolvent_checks for s in stats),
        resolvent_check_hits=sum(s.resolvent_check_hits for s in stats),
    )
    print(summed_stats)
    elapsed = time.time() - start
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(
        f"attempted resolutions per second: {int(summed_stats.attempted_resolutions / elapsed):,}"
    )
    assert False
