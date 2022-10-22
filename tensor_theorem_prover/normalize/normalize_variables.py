from __future__ import annotations
from typing import Iterable
from tensor_theorem_prover.normalize.find_unbound_var_names import (
    find_unbound_var_names,
)

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
)
from .to_nnf import NNFClause, assert_nnf


class VarNameGenerator:
    used_names: set[str]

    def __init__(self) -> None:
        self.used_names = set()

    def __call__(self, name: str) -> str:
        index = 0
        cur_name = name
        while True:
            if cur_name not in self.used_names:
                self.used_names.add(cur_name)
                return cur_name
            index += 1
            cur_name = f"{name}_{index}"


def normalize_variables(clause: NNFClause) -> NNFClause:
    """Ensure that every variable has a unique name."""
    unbound_var_names = sorted(find_unbound_var_names(clause))
    name_generator = VarNameGenerator()
    remap_var_names = {name: name_generator(name) for name in unbound_var_names}
    return _normalize_variables_recursive(clause, name_generator, remap_var_names)


def _normalize_variables_recursive(
    clause: NNFClause, name_generator: VarNameGenerator, remap_var_names: dict[str, str]
) -> NNFClause:
    normalize_term = lambda term: _normalize_variables_recursive(
        assert_nnf(term), name_generator, remap_var_names
    )
    if isinstance(clause, And):
        return And(*map(normalize_term, clause.args))
    if isinstance(clause, Or):
        return Or(*map(normalize_term, clause.args))
    if isinstance(clause, Not):
        return Not(normalize_term(clause.body))
    if isinstance(clause, Atom):
        terms = _normalize_terms_recursive(clause.terms, remap_var_names)
        return Atom(clause.predicate, terms)
    new_var_name = name_generator(clause.variable.name)
    next_remap = {**remap_var_names, clause.variable.name: new_var_name}
    if isinstance(clause, All):
        return All(
            Variable(new_var_name),
            _normalize_variables_recursive(
                assert_nnf(clause.body), name_generator, next_remap
            ),
        )
    if isinstance(clause, Exists):
        return Exists(
            Variable(new_var_name),
            _normalize_variables_recursive(
                assert_nnf(clause.body), name_generator, next_remap
            ),
        )
    else:
        raise ValueError(f"Unknown clause type: {type(clause)}")


def _normalize_terms_recursive(
    terms: Iterable[Variable | Constant | BoundFunction],
    remap_var_names: dict[str, str],
) -> tuple[Variable | Constant | BoundFunction, ...]:
    normalized_terms: list[Variable | Constant | BoundFunction] = []
    for term in terms:
        if isinstance(term, Variable):
            if isinstance(term, Variable):
                # should never happen, since we should find all unbound variables before entering this function
                if term.name not in remap_var_names:
                    raise ValueError(f"Variable {term.name} is not bound.")
                normalized_terms.append(Variable(remap_var_names[term.name]))
        elif isinstance(term, BoundFunction):
            normalized_terms.append(
                BoundFunction(
                    term.function,
                    _normalize_terms_recursive(term.terms, remap_var_names),
                )
            )
        else:
            normalized_terms.append(term)
    return tuple(normalized_terms)
