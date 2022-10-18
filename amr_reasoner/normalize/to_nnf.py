from typing import Union
from amr_reasoner.types.Atom import Atom
from amr_reasoner.types.connectives import All, And, Clause, Exists, Implies, Not, Or


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
        return not_to_nnf(clause)
    if isinstance(clause, And):
        return and_to_nnf(clause)
    if isinstance(clause, Or):
        return or_to_nnf(clause)
    if isinstance(clause, Implies):
        return implies_to_nnf(clause)
    if isinstance(clause, All):
        return All(clause.variable, to_nnf(clause.body))
    if isinstance(clause, Exists):
        return Exists(clause.variable, to_nnf(clause.body))
    if isinstance(clause, Atom):
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def not_to_nnf(clause: Not) -> NNFClause:
    if isinstance(clause.body, And):
        return or_to_nnf(Or(*map(Not, clause.body.args)))
    if isinstance(clause.body, Or):
        return and_to_nnf(And(*map(Not, clause.body.args)))
    if isinstance(clause.body, Not):
        return to_nnf(clause.body.body)
    if isinstance(clause.body, Implies):
        return not_to_nnf(Not(implies_to_nnf(clause.body)))
    if isinstance(clause.body, Exists):
        return All(clause.body.variable, not_to_nnf(Not(clause.body.body)))
    if isinstance(clause.body, All):
        return Exists(clause.body.variable, not_to_nnf(Not(clause.body.body)))
    if isinstance(clause.body, Atom):
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def implies_to_nnf(clause: Implies) -> NNFClause:
    return or_to_nnf(Or(Not(clause.antecedent), clause.consequent))


def and_to_nnf(clause: And) -> NNFClause:
    return And(*[to_nnf(arg) for arg in clause.args])


def or_to_nnf(clause: Or) -> NNFClause:
    return Or(*[to_nnf(arg) for arg in clause.args])
