from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from tensor_theorem_prover.types import Variable, Term
from tensor_theorem_prover.types.Term import term_from_rust
from tensor_theorem_prover.normalize import CNFDisjunction, CNFLiteral

from tensor_theorem_prover._rust import RsProofStep


SubstitutionsMap = Dict[Variable, Term]


def subsitutions_to_str(substitutions: SubstitutionsMap) -> str:
    inner_str = ", ".join(f"{var} -> {term}" for var, term in substitutions.items())
    return "{" + inner_str + "}"


@dataclass
class ProofStep:
    """A single step in a proof of a goal"""

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

    def __str__(self) -> str:
        output = f"Similarity: {self.similarity}\n"
        output += f"Source: {self.source}\n"
        output += f"Target: {self.target}\n"
        output += f"Unify: {self.source_unification_literal.atom} = {self.target_unification_literal.atom}\n"
        output += f"Subsitutions: {subsitutions_to_str(self.source_substitutions)}, {subsitutions_to_str(self.target_substitutions)}\n"
        output += f"Resolvent: {self.resolvent}"
        return output

    @classmethod
    def from_rust(cls, rust_proof_step: RsProofStep) -> ProofStep:
        source_substitutions = {
            Variable.from_rust(var): term_from_rust(term)
            for var, term in rust_proof_step.source_substitutions.items()
        }
        target_substitutions = {
            Variable.from_rust(var): term_from_rust(term)
            for var, term in rust_proof_step.target_substitutions.items()
        }
        return ProofStep(
            source=CNFDisjunction.from_rust(rust_proof_step.source),
            target=CNFDisjunction.from_rust(rust_proof_step.target),
            source_unification_literal=CNFLiteral.from_rust(
                rust_proof_step.source_unification_literal
            ),
            target_unification_literal=CNFLiteral.from_rust(
                rust_proof_step.target_unification_literal
            ),
            source_substitutions=source_substitutions,
            target_substitutions=target_substitutions,
            resolvent=CNFDisjunction.from_rust(rust_proof_step.resolvent),
            similarity=rust_proof_step.similarity,
            running_similarity=rust_proof_step.running_similarity,
            depth=rust_proof_step.depth,
        )
