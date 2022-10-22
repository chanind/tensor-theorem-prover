from __future__ import annotations
from typing import Iterable
from tensor_theorem_prover.types import Term, Variable, BoundFunction


def find_variables_in_terms(terms: Iterable[Term]) -> set[Variable]:
    """Recursively find all variables in a list of terms."""
    variables = set()
    for term in terms:
        if isinstance(term, Variable):
            if term not in variables:
                variables.add(term)
        elif isinstance(term, BoundFunction):
            variables.update(find_variables_in_terms(term.terms))
    return variables
