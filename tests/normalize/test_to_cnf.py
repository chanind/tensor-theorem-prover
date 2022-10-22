from __future__ import annotations

from tensor_theorem_prover.normalize import Skolemizer, to_cnf
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Implies,
    Or,
    Not,
    Exists,
    Function,
)
from tests.helpers import to_disj_set

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

func1 = Function("func1")
func2 = Function("func2")

X = Variable("X")
Y = Variable("Y")


def test_to_cnf_simple_and() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert to_cnf(clause, Skolemizer()) == to_disj_set(
        [[pred1(const1)], [pred2(const2)]]
    )


def test_to_cnf_simple_or() -> None:
    clause = Or(pred1(const1), pred2(const2))
    assert to_cnf(clause, Skolemizer()) == to_disj_set([[pred1(const1), pred2(const2)]])


def test_to_cnf_plain_atom() -> None:
    clause = pred1(const1)
    assert to_cnf(clause, Skolemizer()) == to_disj_set([[pred1(const1)]])


def test_to_cnf_not_atom() -> None:
    clause = Not(pred1(const1))
    assert to_cnf(clause, Skolemizer()) == to_disj_set([[Not(pred1(const1))]])


def test_to_cnf_with_nested_functions() -> None:
    clause = And(
        pred1(Y),
        Exists(X, Or(pred2(func1(func1(X)), Y), pred1(const1, func2(Y, func1(X))))),
    )
    assert set(map(str, to_cnf(clause, Skolemizer()))) == {
        "[pred1(Y)]",
        "[pred1(const1,func2(Y,func1(_SK_1(Y)))) ∨ pred2(func1(func1(_SK_1(Y))),Y)]",
    }


def test_to_cnf_with_implies_clause() -> None:
    clause = Implies(pred1(X), pred2(X))
    assert set(map(str, to_cnf(clause, Skolemizer()))) == {"[pred2(X) ∨ ¬pred1(X)]"}
