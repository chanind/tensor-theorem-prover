from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent

from tensor_theorem_prover.normalize.to_cnf import CNFDisjunction
from tensor_theorem_prover.prover.ProofStats import ProofStats
from tensor_theorem_prover.types import Variable
from tensor_theorem_prover.types.Term import term_from_rust

from tensor_theorem_prover._rust import RsProof

from .ProofStep import ProofStep, SubstitutionsMap


@dataclass(frozen=True, eq=True)
class Proof:
    """
    Respresentation of a successful proof of a goal
    """

    goal: CNFDisjunction
    similarity: float
    stats: ProofStats
    proof_steps: list[ProofStep]
    depth: int
    substitutions: SubstitutionsMap

    def __str__(self) -> str:
        substitutions_str_inner = ", ".join(
            f"{var} -> {term}" for var, term in self.substitutions.items()
        )
        substitutions_str = "{" + substitutions_str_inner + "}"
        output = f"Goal: {self.goal}\n"
        output += f"Subsitutions: {substitutions_str}\n"
        output += f"Similarity: {self.similarity}\n"
        output += f"Depth: {self.depth}\n"
        output += "Steps:\n"
        output += "\n  ---\n".join(
            indent(str(proof_state), "  ") for proof_state in self.proof_steps
        )
        return output

    @classmethod
    def from_rust(cls, rust_proof: RsProof) -> Proof:
        substitutions = {
            Variable.from_rust(var): term_from_rust(term)
            for var, term in rust_proof.substitutions.items()
        }
        return Proof(
            goal=CNFDisjunction.from_rust(rust_proof.goal),
            similarity=rust_proof.similarity,
            stats=ProofStats.from_rust(rust_proof.stats),
            proof_steps=[
                ProofStep.from_rust(proof_step) for proof_step in rust_proof.proof_steps
            ],
            depth=rust_proof.depth,
            substitutions=substitutions,
        )
