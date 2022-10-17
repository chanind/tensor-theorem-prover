from __future__ import annotations
from dataclasses import dataclass
from immutables import Map
from amr_reasoner.prover.operations.substitution import SubstitutionsMap


@dataclass
class ProofState:
    similarity: float = 1.0
    substitutions: SubstitutionsMap = Map()
