from __future__ import annotations
import itertools
from tensor_theorem_prover.normalize.normalize_quantifiers import (
    SimplifiedClause,
    assert_simplified,
)

from tensor_theorem_prover.types import (
    And,
    Or,
    Not,
    Atom,
)


def normalize_conjunctions(clause: SimplifiedClause) -> SimplifiedClause:
    """Move 'or' inwards as far as possible to get a conjunction of disjunctions."""
    if isinstance(clause, Not) or isinstance(clause, Atom):
        return clause
    if isinstance(clause, Or):
        combinations: list[list[SimplifiedClause]] = []
        for term in clause.args:
            norm_term = normalize_conjunctions(assert_simplified(term))
            if isinstance(norm_term, And):
                combinations.append(list(map(assert_simplified, norm_term.args)))
            else:
                combinations.append([norm_term])
        disjunctions_terms = list(itertools.product(*combinations))
        disjunctions = [Or(*terms) for terms in disjunctions_terms]
        return And(*disjunctions)
    if isinstance(clause, And):
        simp_terms = map(assert_simplified, clause.args)
        return And(*map(normalize_conjunctions, simp_terms))
    raise ValueError(f"Unexpected clause type: {type(clause)}")
