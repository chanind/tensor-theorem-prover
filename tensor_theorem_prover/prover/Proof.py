from __future__ import annotations
from collections import deque

from dataclasses import dataclass
from textwrap import indent

from tensor_theorem_prover.normalize.to_cnf import CNFDisjunction
from tensor_theorem_prover.prover.ProofStats import ProofStats
from tensor_theorem_prover.types import Constant, Variable, Term
from tensor_theorem_prover.types.Function import BoundFunction
from tensor_theorem_prover.util.find_variables_in_terms import find_variables_in_terms
from .ProofStep import ProofStep, SubstitutionsMap


@dataclass(frozen=True, eq=True)
class Proof:
    goal: CNFDisjunction
    similarity: float
    leaf_proof_step: ProofStep
    stats: ProofStats

    @property
    def depth(self) -> int:
        return len(self.proof_steps)

    @property
    def proof_steps(self) -> list[ProofStep]:
        proof_steps: deque[ProofStep] = deque()
        cur_step = self.leaf_proof_step
        while True:
            proof_steps.appendleft(cur_step)
            if not cur_step.parent:
                break
            cur_step = cur_step.parent
        return list(proof_steps)

    @property
    def substitutions(self) -> SubstitutionsMap:
        goal_terms = [
            term for literal in self.goal.literals for term in literal.atom.terms
        ]
        goal_variables = find_variables_in_terms(goal_terms)
        step_substitutions = [step.source_substitutions for step in self.proof_steps]
        substitutions: SubstitutionsMap = {}
        for variable in goal_variables:
            substitutions[variable] = _resolve_var_value(variable, step_substitutions)
        return substitutions

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


def _resolve_var_value(
    var: Term, substitutions: list[SubstitutionsMap], index: int = 0
) -> Term:
    if index >= len(substitutions):
        return var
    if not isinstance(var, Variable):
        return var
    # if this variable doesn't occur in the substitutions, assume it remains unchanged
    new_var_value = substitutions[index].get(var, var)
    if isinstance(new_var_value, Variable):
        return _resolve_var_value(new_var_value, substitutions, index + 1)
    elif isinstance(new_var_value, Constant):
        return new_var_value
    elif isinstance(new_var_value, BoundFunction):
        return BoundFunction(
            new_var_value.function,
            tuple(
                _resolve_var_value(term, substitutions, index + 1)
                for term in new_var_value.terms
            ),
        )
    else:
        raise ValueError(f"Unexpected term type: {new_var_value}")
