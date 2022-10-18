from __future__ import annotations
from typing import Iterable, Union, cast
from amr_reasoner.normalize.find_unbound_var_names import find_unbound_var_names
from amr_reasoner.normalize.to_nnf import NNFClause, assert_nnf

from amr_reasoner.types import (
    Function,
    Variable,
    And,
    Or,
    Not,
    All,
    Exists,
    Constant,
    Atom,
    BoundFunction,
)


SimplifiedClause = Union[And, Or, Not, Atom]


class SkolemNameGenerator:
    def __init__(self) -> None:
        self.index = 0

    def __call__(self) -> str:
        self.index += 1
        return f"_SK_{self.index}"


def normalize_quantifiers(clause: NNFClause) -> SimplifiedClause:
    """Skolemize 'exists' quantifiers and remove 'for all' quantifiers"""
    name_generator = SkolemNameGenerator()
    universal_var_names = find_unbound_var_names(clause)
    skolem_map: dict[str, BoundFunction] = {}
    return normalize_quantifiers_recursive(
        clause, name_generator, universal_var_names, skolem_map
    )


def normalize_quantifiers_recursive(
    clause: NNFClause,
    name_generator: SkolemNameGenerator,
    universal_var_names: set[str],
    skolem_map: dict[str, BoundFunction],
) -> SimplifiedClause:
    normalize_term = lambda term: normalize_quantifiers_recursive(
        assert_nnf(term), name_generator, universal_var_names, skolem_map
    )
    if isinstance(clause, And):
        return And(*map(normalize_term, clause.args))
    if isinstance(clause, Or):
        return Or(*map(normalize_term, clause.args))
    if isinstance(clause, Not):
        return Not(normalize_term(clause.body))
    if isinstance(clause, All):
        next_universal_var_names = universal_var_names | {clause.variable.name}
        return normalize_quantifiers_recursive(
            assert_nnf(clause.body),
            name_generator,
            next_universal_var_names,
            skolem_map,
        )
    if isinstance(clause, Exists):
        skolem_func = Function(name_generator())
        next_skolem_map = {
            **skolem_map,
            clause.variable.name: skolem_func(
                *map(Variable, sorted(universal_var_names))
            ),
        }
        return normalize_quantifiers_recursive(
            assert_nnf(clause.body),
            name_generator,
            universal_var_names,
            next_skolem_map,
        )

    if isinstance(clause, Atom):
        terms = normalize_terms_recursive(clause.terms, skolem_map)
        return Atom(clause.predicate, terms)
    else:
        raise ValueError(f"Unknown clause type: {type(clause)}")


def normalize_terms_recursive(
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
                    normalize_terms_recursive(term.terms, skolem_map),
                )
            )
        else:
            normalized_terms.append(term)
    return tuple(normalized_terms)
