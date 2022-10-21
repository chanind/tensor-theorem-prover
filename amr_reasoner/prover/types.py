from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Union, Optional

from amr_reasoner.types import Constant, Variable
from amr_reasoner.normalize import CNFDisjunction


SubstitutionsMap = Dict[Variable, Union[Constant, Variable]]


@dataclass
class ProofState:
    knowledge: frozenset[CNFDisjunction]
    source: Optional[CNFDisjunction] = None
    target: Optional[CNFDisjunction] = None
    resolvent: Optional[CNFDisjunction] = None
    source_substitutions: SubstitutionsMap = field(default_factory=dict)
    target_substitutions: SubstitutionsMap = field(default_factory=dict)
    depth: int = 0
    substitutions: SubstitutionsMap = field(default_factory=dict)
    parent: Optional[ProofState] = None
