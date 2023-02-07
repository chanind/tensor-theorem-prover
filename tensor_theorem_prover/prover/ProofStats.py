from __future__ import annotations
from dataclasses import dataclass

from tensor_theorem_prover._rust import RsProofStats


@dataclass
class ProofStats:
    """Stats on how complex a proof was to compute"""

    attempted_resolutions: int = 0
    successful_resolutions: int = 0
    max_resolvent_width_seen: int = 0
    max_depth_seen: int = 0
    discarded_proofs: int = 0

    @classmethod
    def from_rust(cls, rust_proof_stats: RsProofStats) -> ProofStats:
        return ProofStats(
            attempted_resolutions=rust_proof_stats.attempted_resolutions,
            successful_resolutions=rust_proof_stats.successful_resolutions,
            max_resolvent_width_seen=rust_proof_stats.max_resolvent_width_seen,
            max_depth_seen=rust_proof_stats.max_depth_seen,
            discarded_proofs=rust_proof_stats.discarded_proofs,
        )
