from __future__ import annotations

from typing import Iterable, Union

from tensor_theorem_prover.normalize.Skolemizer import Skolemizer
from tensor_theorem_prover.normalize.find_unbound_var_names import (
    find_unbound_var_names,
)
from tensor_theorem_prover.normalize.to_nnf import NNFClause, assert_nnf
from tensor_theorem_prover.types import (
    Variable,
    And,
    Or,
    Not,
    All,
    Exists,
    Constant,
    Atom,
    BoundFunction,
    Clause,
)


SimplifiedClause = Union[And, Or, Not, Atom]


def assert_simplified(clause: Clause) -> SimplifiedClause:
    assert isinstance(clause, (Atom, Not, And, Or))
    return clause


def normalize_quantifiers(
    clause: NNFClause, skolemizer: Skolemizer
) -> SimplifiedClause:
    """Skolemize 'exists' quantifiers and remove 'for all' quantifiers"""
    universal_var_names = find_unbound_var_names(clause)
    skolem_map: dict[str, BoundFunction] = {}
    return _normalize_quantifiers_recursive(
        clause, skolemizer, universal_var_names, skolem_map
    )


def _normalize_quantifiers_recursive(
    clause: NNFClause,
    skolemizer: Skolemizer,
    universal_var_names: set[str],
    skolem_map: dict[str, BoundFunction],
) -> SimplifiedClause:
    normalize_term = lambda term: _normalize_quantifiers_recursive(
        assert_nnf(term), skolemizer, universal_var_names, skolem_map
    )
    if isinstance(clause, And):
        return And(*map(normalize_term, clause.args))
    if isinstance(clause, Or):
        return Or(*map(normalize_term, clause.args))
    if isinstance(clause, Not):
        return Not(normalize_term(clause.body))
    if isinstance(clause, All):
        next_universal_var_names = universal_var_names | {clause.variable.name}
        return _normalize_quantifiers_recursive(
            assert_nnf(clause.body),
            skolemizer,
            next_universal_var_names,
            skolem_map,
        )
    if isinstance(clause, Exists):
        next_skolem_map = {
            **skolem_map,
            clause.variable.name: skolemizer(
                *map(Variable, sorted(universal_var_names))
            ),
        }
        return _normalize_quantifiers_recursive(
            assert_nnf(clause.body),
            skolemizer,
            universal_var_names,
            next_skolem_map,
        )

    if isinstance(clause, Atom):
        terms = _normalize_terms_recursive(clause.terms, skolem_map)
        return Atom(clause.predicate, terms)
    else:
        raise ValueError(f"Unknown clause type: {type(clause)}")


def _normalize_terms_recursive(
    terms: Iterable[Variable | Constant | BoundFunction],
    skolem_map: dict[str, BoundFunction],
) -> tuple[Variable | Constant | BoundFunction, ...]:
    normalized_terms: list[Variable | Constant | BoundFunction] = []
    for term in terms:
        if isinstance(term, Variable):
            if term.name in skolem_map:
                normalized_terms.append(skolem_map[term.name])
            else:
                normalized_terms.append(term)
        elif isinstance(term, BoundFunction):
            normalized_terms.append(
                BoundFunction(
                    term.function,
                    _normalize_terms_recursive(term.terms, skolem_map),
                )
            )
        else:
            normalized_terms.append(term)
    return tuple(normalized_terms)
