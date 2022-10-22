from __future__ import annotations
from typing import Iterable

from tensor_theorem_prover.types import (
    Atom,
    Clause,
    Term,
    Variable,
    And,
    Or,
    Implies,
    Not,
    All,
    Exists,
    BoundFunction,
)


def find_unbound_var_names(clause: Clause, bound_vars: set[str] = set()) -> set[str]:
    """Find all unbound variable names in a clause.

    Args:
        clauses: The clause to search.

    Returns:
        The set of unbound variables.
    """
    unbound_vars: set[str] = set()
    if isinstance(clause, And) or isinstance(clause, Or):
        for arg in clause.args:
            unbound_vars.update(find_unbound_var_names(arg, bound_vars))
    elif isinstance(clause, Implies):
        unbound_vars.update(find_unbound_var_names(clause.antecedent, bound_vars))
        unbound_vars.update(find_unbound_var_names(clause.consequent, bound_vars))
    elif isinstance(clause, Not):
        unbound_vars.update(find_unbound_var_names(clause.body, bound_vars))
    elif isinstance(clause, Exists) or isinstance(clause, All):
        unbound_vars.update(
            find_unbound_var_names(clause.body, bound_vars | {clause.variable.name})
        )
    elif isinstance(clause, Atom):
        unbound_vars.update(_find_unbound_var_names_in_terms(clause.terms, bound_vars))
    return unbound_vars


def _find_unbound_var_names_in_terms(
    terms: Iterable[Term], bound_vars: set[str]
) -> set[str]:
    unbound_vars: set[str] = set()
    for term in terms:
        if isinstance(term, Variable):
            if term.name not in bound_vars:
                unbound_vars.add(term.name)
        elif isinstance(term, BoundFunction):
            unbound_vars.update(
                _find_unbound_var_names_in_terms(term.terms, bound_vars)
            )
    return unbound_vars
