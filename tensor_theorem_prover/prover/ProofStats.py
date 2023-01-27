from __future__ import annotations
from dataclasses import dataclass

from tensor_theorem_prover._rust import RsProofStats


@dataclass
class ProofStats:
    """Stats on how complex a proof was to compute"""

    attempted_unifications: int = 0
    successful_unifications: int = 0
    similarity_comparisons: int = 0
    similarity_cache_hits: int = 0
    attempted_resolutions: int = 0
    successful_resolutions: int = 0
    max_resolvent_width_seen: int = 0
    max_depth_seen: int = 0
    discarded_proofs: int = 0
    resolvent_checks: int = 0
    resolvent_check_hits: int = 0

    @classmethod
    def from_rust(cls, rust_proof_stats: RsProofStats) -> ProofStats:
        return ProofStats(
            attempted_unifications=rust_proof_stats.attempted_unifications,
            successful_unifications=rust_proof_stats.successful_unifications,
            similarity_comparisons=rust_proof_stats.similarity_comparisons,
            similarity_cache_hits=rust_proof_stats.similarity_cache_hits,
            attempted_resolutions=rust_proof_stats.attempted_resolutions,
            successful_resolutions=rust_proof_stats.successful_resolutions,
            max_resolvent_width_seen=rust_proof_stats.max_resolvent_width_seen,
            max_depth_seen=rust_proof_stats.max_depth_seen,
            discarded_proofs=rust_proof_stats.discarded_proofs,
            resolvent_checks=rust_proof_stats.resolvent_checks,
            resolvent_check_hits=rust_proof_stats.resolvent_check_hits,
        )
