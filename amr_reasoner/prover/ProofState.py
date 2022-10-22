from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from amr_reasoner.types import Variable, Term
from amr_reasoner.normalize import CNFDisjunction, CNFLiteral


SubstitutionsMap = Dict[Variable, Term]


def subsitutions_to_str(substitutions: SubstitutionsMap) -> str:
    inner_str = ", ".join(f"{var} -> {term}" for var, term in substitutions.items())
    return "{" + inner_str + "}"


@dataclass
class ProofState:
    source: CNFDisjunction
    target: CNFDisjunction
    source_unification_literal: CNFLiteral
    target_unification_literal: CNFLiteral
    source_substitutions: SubstitutionsMap
    target_substitutions: SubstitutionsMap
    resolvent: CNFDisjunction
    similarity: float
    parent: Optional[ProofState] = None

    def __str__(self) -> str:
        output = f"Similarity: {self.similarity}\n"
        output += f"Source: {self.source}\n"
        output += f"Target: {self.target}\n"
        output += f"Unify: {self.source_unification_literal.atom} = {self.target_unification_literal.atom}\n"
        output += f"Subsitutions: {subsitutions_to_str(self.source_substitutions)}, {subsitutions_to_str(self.target_substitutions)}\n"
        output += f"Resolvent: {self.resolvent}"
        return output
