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
    if "MERGED" in item1.symbol or "MERGED" in item2.symbol:
        return 0.0
    if strip_frame_number(item1.symbol) == strip_frame_number(item2.symbol):
        return 0.6
    if (
        item1.embedding is None or item2.embedding is None
    ) and item1.symbol == item2.symbol:
        return 1.0
    return 0.0


@pytest.mark.skip(reason="Performance test")
def test_performance() -> None:
    with open("tests/logic.pickle", "rb") as f:
        data = pickle.load(f)
    knowledge: list[Clause] = data["knowledge"]
    query: Clause = data["query"]

    prover = ResolutionProver(
        knowledge=knowledge,
        similarity_func=max_similarity([cosine_similarity, partial_symbol_compare]),
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
    assert False


@pytest.mark.skip(reason="Performance test")
def test_performance_with_amr_reasoner_batch() -> None:
    with open("tests/amr_logic_batch.pickle", "rb") as f:
        batch = pickle.load(f)
    stats = []
    start = time.time()
    total_proofs = 0
    for sample in batch:
        prover = ResolutionProver(
            knowledge=sample["knowledge"],
            similarity_func=max_similarity([cosine_similarity, partial_symbol_compare]),
            max_proof_depth=15,
            max_resolvent_width=10,
            min_similarity_threshold=0.5,
            skip_seen_resolvents=True,
        )
        for goal in sample["goals"]:
            proofs, proof_stats = prover.prove_all_with_stats(goal, max_proofs=None)
            stats.append(proof_stats)
            total_proofs += len(proofs)
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
    print(f"Total proofs: {total_proofs}")
    assert False


@pytest.mark.skip(reason="Performance test")
def test_performance_with_mixed_amr_reasoner_batch() -> None:
    with open("tests/amr_logic_batch.pickle", "rb") as f:
        batch = pickle.load(f)
    stats = []
    start = time.time()
    total_proofs = 0
    all_knowledge = []
    for sample in batch[0:8]:
        all_knowledge.extend(sample["knowledge"])
    prover = ResolutionProver(
        knowledge=all_knowledge,
        similarity_func=max_similarity([cosine_similarity, partial_symbol_compare]),
        max_proof_depth=10,
        max_resolvent_width=6,
        min_similarity_threshold=0.5,
        skip_seen_resolvents=True,
    )
    for goal in sample["goals"]:
        proofs, proof_stats = prover.prove_all_with_stats(goal, max_proofs=1)
        stats.append(proof_stats)
        total_proofs += len(proofs)
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
    print(f"Total proofs: {total_proofs}")
    assert False
