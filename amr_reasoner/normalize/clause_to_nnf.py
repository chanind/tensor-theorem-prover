from typing import Union
from amr_reasoner.types.Atom import Atom
from amr_reasoner.types.connectives import All, And, Clause, Exists, Implies, Not, Or


NNFClause = Union[Atom, Not, And, Or, All, Exists]


def clause_to_nnf(clause: Clause) -> NNFClause:
    """
    Convert clause to negation normal form.
    From https://en.wikipedia.org/wiki/Conjunctive_normal_form#Converting_from_first-order_logic
    """
    if type(clause) is Not:
        return not_clause_to_nnf(clause)
    if type(clause) is And:
        return and_clause_to_nnf(clause)
    if type(clause) is Or:
        return or_clause_to_nnf(clause)
    if type(clause) is Implies:
        return implies_clause_to_nnf(clause)
    if type(clause) is All:
        return All(clause.variable, clause_to_nnf(clause.body))
    if type(clause) is Exists:
        return Exists(clause.variable, clause_to_nnf(clause.body))
    if type(clause) is Atom:
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def not_clause_to_nnf(clause: Not) -> NNFClause:
    if type(clause.body) is And:
        return or_clause_to_nnf(Or(*map(Not, clause.body.args)))
    if type(clause.body) is Or:
        return and_clause_to_nnf(And(*map(Not, clause.body.args)))
    if type(clause.body) is Not:
        return clause_to_nnf(clause.body.body)
    if type(clause.body) is Implies:
        return not_clause_to_nnf(Not(implies_clause_to_nnf(clause.body)))
    if type(clause.body) is Exists:
        return All(clause.body.variable, not_clause_to_nnf(Not(clause.body.body)))
    if type(clause.body) is All:
        return Exists(clause.body.variable, not_clause_to_nnf(Not(clause.body.body)))
    if type(clause.body) is Atom:
        return clause
    raise ValueError(f"Unknown clause type: {type(clause)}")


def implies_clause_to_nnf(clause: Implies) -> NNFClause:
    return or_clause_to_nnf(Or(Not(clause.antecedent), clause.consequent))


def and_clause_to_nnf(clause: And) -> NNFClause:
    return And(*[clause_to_nnf(arg) for arg in clause.args])


def or_clause_to_nnf(clause: Or) -> NNFClause:
    return Or(*[clause_to_nnf(arg) for arg in clause.args])
