from __future__ import annotations
from amr_reasoner.normalize.to_cnf import (
    CNFDisjunction,
    to_cnf,
    element_to_cnf_literal,
)
from amr_reasoner.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Implies,
    Or,
    Not,
    Atom,
    Exists,
    Function,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

func1 = Function("func1")
func2 = Function("func2")

X = Variable("X")
Y = Variable("Y")


def to_cnf_helper(clauses: list[list[Atom | Not]]) -> set[CNFDisjunction]:
    return set(
        CNFDisjunction(frozenset(element_to_cnf_literal(elm) for elm in clause))
        for clause in clauses
    )


def test_to_cnf_simple_and() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert to_cnf(clause) == to_cnf_helper([[pred1(const1)], [pred2(const2)]])


def test_to_cnf_simple_or() -> None:
    clause = Or(pred1(const1), pred2(const2))
    assert to_cnf(clause) == to_cnf_helper([[pred1(const1), pred2(const2)]])


def test_to_cnf_plain_atom() -> None:
    clause = pred1(const1)
    assert to_cnf(clause) == to_cnf_helper([[pred1(const1)]])


def test_to_cnf_not_atom() -> None:
    clause = Not(pred1(const1))
    assert to_cnf(clause) == to_cnf_helper([[Not(pred1(const1))]])


def test_to_cnf_does_basic_deduplication_of_disjunctions() -> None:
    clause = And(pred1(const1), pred1(const1))
    assert to_cnf(clause) == to_cnf_helper([[pred1(const1)]])


def test_to_cnf_does_basic_deduplication_of_literals() -> None:
    clause = And(Or(pred1(const1), pred1(const1)), pred2(const1))
    assert to_cnf(clause) == to_cnf_helper([[pred1(const1)], [pred2(const1)]])


def test_to_cnf_with_nested_functions() -> None:
    clause = And(
        pred1(Y),
        Exists(X, Or(pred2(func1(func1(X)), Y), pred1(const1, func2(Y, func1(X))))),
    )
    assert set(map(str, to_cnf(clause))) == {
        "[pred1(Y_1)]",
        "[pred1(const1,func2(Y_1,func1(_SK_1(Y_1)))) ∨ pred2(func1(func1(_SK_1(Y_1))),Y_1)]",
    }


def test_to_cnf_with_implies_clause() -> None:
    clause = Implies(pred1(X), pred2(X))
    assert set(map(str, to_cnf(clause))) == {"[pred2(X_1) ∨ ¬pred1(X_1)]"}
