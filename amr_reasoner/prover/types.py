from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Union, Optional
from immutables import Map

from amr_reasoner.types import Constant, Variable
from amr_reasoner.normalize import CNFDisjunction

SubstitutionsMap = Map[Variable, Union[Constant, Variable]]


@dataclass
class ProofState:
    knowledge: frozenset[CNFDisjunction]
    source: CNFDisjunction
    target: CNFDisjunction
    resolvent: CNFDisjunction
    source_substitutions: SubstitutionsMap = Map()
    target_substitutions: SubstitutionsMap = Map()
    depth: int = 0
    substitutions: SubstitutionsMap = Map()
    parent: Optional[ProofState] = None
