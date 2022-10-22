from typing import Union
from tensor_theorem_prover.types.Atom import Atom
from tensor_theorem_prover.types.connectives import (
    All,
    And,
    Clause,
    Exists,
    Implies,
    Not,
    Or,
)


NNFClause = Union[Atom, Not, And, Or, All, Exists]


def assert_nnf(clause: Clause) -> NNFClause:
    assert isinstance(clause, (Atom, Not, And, Or, All, Exists))
    return clause


def to_nnf(clause: Clause) -> NNFClause:
    """
    Convert clause to negation normal form.
    From https://en.wikipedia.org/wiki/Conjunctive_normal_form#Converting_from_first-order_logic
    """
    if isinstance(clause, Not):
        return _not_to_nnf(clause)
    if isinstance(clause, And):
        return _and_to_nnf(clause)
    if isinstance(clause, Or):
        return _or_to_nnf(clause)
    if isinstance(clause, Implies):
        return _implies_to_nnf(clause)
    if isinstance(clause, All):
        return All(clause.variable, to_nnf(clause.body))
    if isinstance(clause, Exists):
        return Exists(clause.variable, to_nnf(clause.body))
    if isinstance(clause, Atom):
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def _not_to_nnf(clause: Not) -> NNFClause:
    if isinstance(clause.body, And):
        return _or_to_nnf(Or(*map(Not, clause.body.args)))
    if isinstance(clause.body, Or):
        return _and_to_nnf(And(*map(Not, clause.body.args)))
    if isinstance(clause.body, Not):
        return to_nnf(clause.body.body)
    if isinstance(clause.body, Implies):
        return _not_to_nnf(Not(_implies_to_nnf(clause.body)))
    if isinstance(clause.body, Exists):
        return All(clause.body.variable, _not_to_nnf(Not(clause.body.body)))
    if isinstance(clause.body, All):
        return Exists(clause.body.variable, _not_to_nnf(Not(clause.body.body)))
    if isinstance(clause.body, Atom):
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def _implies_to_nnf(clause: Implies) -> NNFClause:
    return _or_to_nnf(Or(Not(clause.antecedent), clause.consequent))


def _and_to_nnf(clause: And) -> NNFClause:
    return And(*[to_nnf(arg) for arg in clause.args])


def _or_to_nnf(clause: Or) -> NNFClause:
    return Or(*[to_nnf(arg) for arg in clause.args])
