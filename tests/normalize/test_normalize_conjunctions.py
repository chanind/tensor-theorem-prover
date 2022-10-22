from tensor_theorem_prover.normalize.normalize_conjunctions import (
    normalize_conjunctions,
)
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Or,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")
const3 = Constant("const3")
const4 = Constant("const4")


def test_normalize_conjunctions_leaves_simple_clauses_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert str(normalize_conjunctions(clause)) == "pred1(const1) ∧ pred2(const2)"


def test_normalize_conjunctions_leaves_already_normalized_clauses_unchanged() -> None:
    clause = And(Or(pred1(const1), pred1(const2)), Or(pred1(const3), pred2(const2)))
    assert (
        str(normalize_conjunctions(clause))
        == "(pred1(const1) ∨ pred1(const2)) ∧ (pred1(const3) ∨ pred2(const2))"
    )


def test_normalize_conjunctions_distributes_or_inwards() -> None:
    clause = Or(
        And(pred1(const1), pred1(const2)),
        And(pred1(const3), pred2(const2)),
        pred1(const4),
    )
    assert (
        str(normalize_conjunctions(clause))
        == "(pred1(const1) ∨ pred1(const3) ∨ pred1(const4)) ∧ (pred1(const1) ∨ pred2(const2) ∨ pred1(const4)) ∧ (pred1(const2) ∨ pred1(const3) ∨ pred1(const4)) ∧ (pred1(const2) ∨ pred2(const2) ∨ pred1(const4))"
    )


def test_normalize_conjunctions_handles_nested_or() -> None:
    clause = Or(
        And(pred1(const1), pred1(const2)),
        Or(pred1(const3), And(pred2(const2), pred1(const4))),
    )
    assert (
        str(normalize_conjunctions(clause))
        == "(pred1(const1) ∨ pred1(const3) ∨ pred2(const2)) ∧ (pred1(const1) ∨ pred1(const3) ∨ pred1(const4)) ∧ (pred1(const2) ∨ pred1(const3) ∨ pred2(const2)) ∧ (pred1(const2) ∨ pred1(const3) ∨ pred1(const4))"
    )
