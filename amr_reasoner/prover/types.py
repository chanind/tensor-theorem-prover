from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Union, Optional
from typing_extensions import Literal
from immutables import Map

from amr_reasoner.types import Constant, Variable
from amr_reasoner.normalize import CNFDisjunction

# S means 'source', T means 'target'
BindingLabel = Union[Literal["S"], Literal["T"]]
SOURCE_BINDING_LABEL: BindingLabel = "S"
TARGET_BINDING_LABEL: BindingLabel = "T"

SubstitutionsMap = Map[Variable, Union[Constant, Tuple[BindingLabel, Variable]]]


@dataclass
class ProofState:
    knowledge: frozenset[CNFDisjunction]
    source: Optional[CNFDisjunction] = None
    target: Optional[CNFDisjunction] = None
    resolvent: Optional[CNFDisjunction] = None
    source_substitutions: SubstitutionsMap = Map()
    target_substitutions: SubstitutionsMap = Map()
    depth: int = 0
    substitutions: SubstitutionsMap = Map()
    parent: Optional[ProofState] = None
