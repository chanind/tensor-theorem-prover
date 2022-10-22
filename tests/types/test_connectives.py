from __future__ import annotations

from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Implies,
    Or,
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


def test_or_to_string() -> None:
    clause = Or(
        And(pred1(const1), pred2(X)), pred1(const2), Implies(pred1(X), pred2(X))
    )
    assert (
        str(clause)
        == "(pred1(const1) ∧ pred2(X)) ∨ pred1(const2) ∨ (pred1(X) → pred2(X))"
    )


def test_nested_implies_to_string() -> None:
    clause = Implies(Implies(pred1(X), pred2(X)), Or(pred2(X), pred1(X)))
    assert str(clause) == "(pred1(X) → pred2(X)) → (pred2(X) ∨ pred1(X))"
