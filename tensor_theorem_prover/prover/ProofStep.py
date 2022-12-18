from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from tensor_theorem_prover.types import Variable, Term
from tensor_theorem_prover.normalize import CNFDisjunction, CNFLiteral


SubstitutionsMap = Dict[Variable, Term]


def subsitutions_to_str(substitutions: SubstitutionsMap) -> str:
    inner_str = ", ".join(f"{var} -> {term}" for var, term in substitutions.items())
    return "{" + inner_str + "}"


@dataclass
class ProofStep:
    source: CNFDisjunction
    target: CNFDisjunction
    source_unification_literal: CNFLiteral
    target_unification_literal: CNFLiteral
    source_substitutions: SubstitutionsMap
    target_substitutions: SubstitutionsMap
    resolvent: CNFDisjunction
    similarity: float
    # this refers to the overall similarity of this step and all of its parents
    running_similarity: float
    depth: int
    parent: Optional[ProofStep] = None

    def __str__(self) -> str:
        output = f"Similarity: {self.similarity}\n"
        output += f"Source: {self.source}\n"
        output += f"Target: {self.target}\n"
        output += f"Unify: {self.source_unification_literal.atom} = {self.target_unification_literal.atom}\n"
        output += f"Subsitutions: {subsitutions_to_str(self.source_substitutions)}, {subsitutions_to_str(self.target_substitutions)}\n"
        output += f"Resolvent: {self.resolvent}"
        return output
