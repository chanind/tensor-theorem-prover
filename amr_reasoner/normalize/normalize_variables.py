from __future__ import annotations
from typing import TypeVar, cast
from amr_reasoner.normalize.find_unbound_var_names import find_unbound_var_names

from amr_reasoner.types import (
    Clause,
    Variable,
    And,
    Or,
    Implies,
    Not,
    All,
    Exists,
    Constant,
)
from amr_reasoner.types.Atom import Atom
from .to_nnf import NNFClause

T = TypeVar("T", Clause, NNFClause)


class VarNameGenerator:
    def __init__(self) -> None:
        self.index = 0

    def __call__(self, name: str) -> str:
        self.index += 1
        return f"{name}_{self.index}"


def normalize_variables(clause: T) -> T:
    """Ensure that every variable has a unique name."""
    name_generator = VarNameGenerator()
    unbound_var_names = sorted(find_unbound_var_names(clause))
    remap_var_names = {name: name_generator(name) for name in unbound_var_names}
    return normalize_variables_recursive(clause, name_generator, remap_var_names)


def normalize_variables_recursive(
    clause: T, name_generator: VarNameGenerator, remap_var_names: dict[str, str]
) -> T:
    if isinstance(clause, And):
        return And(
            *[
                normalize_variables_recursive(arg, name_generator, remap_var_names)
                for arg in clause.args
            ]
        )
    if isinstance(clause, Or):
        return Or(
            *[
                normalize_variables_recursive(arg, name_generator, remap_var_names)
                for arg in clause.args
            ]
        )
    if isinstance(clause, Implies):
        # If the clause is NNF, this will never be called so the cast is safe.
        return cast(
            T,
            Implies(
                normalize_variables_recursive(
                    clause.antecedent, name_generator, remap_var_names
                ),
                normalize_variables_recursive(
                    clause.consequent, name_generator, remap_var_names
                ),
            ),
        )
    if isinstance(clause, Not):
        return Not(
            normalize_variables_recursive(clause.body, name_generator, remap_var_names)
        )
    if isinstance(clause, All):
        new_var_name = name_generator(clause.variable.name)
        next_remap = {**remap_var_names, clause.variable.name: new_var_name}
        return All(
            Variable(new_var_name),
            normalize_variables_recursive(clause.body, name_generator, next_remap),
        )
    if isinstance(clause, Exists):
        new_var_name = name_generator(clause.variable.name)
        next_remap = {**remap_var_names, clause.variable.name: new_var_name}
        return Exists(
            Variable(new_var_name),
            normalize_variables_recursive(clause.body, name_generator, next_remap),
        )
    if isinstance(clause, Atom):
        terms: list[Variable | Constant] = []
        for term in clause.terms:
            if isinstance(term, Variable):
                # should never happen, since we should find all unbound variables before entering this function
                if term.name not in remap_var_names:
                    raise ValueError(
                        f"Variable {term.name} is not bound in clause {clause}."
                    )
                terms.append(Variable(remap_var_names[term.name]))
            else:
                terms.append(term)
        return Atom(clause.operator, tuple(terms))
    else:
        raise ValueError(f"Unknown clause type: {type(clause)}")
