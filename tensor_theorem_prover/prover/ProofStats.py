from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ProofStats:
    """Stats on how complex a proof was to complete"""

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
