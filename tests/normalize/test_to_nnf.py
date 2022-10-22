from tensor_theorem_prover.normalize.to_nnf import to_nnf
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Implies,
    Or,
    Not,
    All,
    Exists,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

X = Variable("X")
Y = Variable("Y")


def test_to_nnf_leaves_simple_clauses_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert to_nnf(clause) == clause


def test_to_nnf_simplifies_implies_clause() -> None:
    clause = Implies(pred1(X), pred2(X))
    assert str(to_nnf(clause)) == "¬pred1(X) ∨ pred2(X)"


def test_to_nnf_simplifies_not_implies_clause() -> None:
    clause = Not(Implies(pred1(X), pred2(X)))
    assert str(to_nnf(clause)) == "pred1(X) ∧ ¬pred2(X)"


def test_to_nnf_simplifies_not_all_clause() -> None:
    clause = Not(All(X, pred1(X)))
    assert str(to_nnf(clause)) == "∃X(¬pred1(X))"


def test_to_nnf_simplifies_not_exists_clause() -> None:
    clause = Not(Exists(X, pred1(X)))
    assert str(to_nnf(clause)) == "∀X(¬pred1(X))"


def test_to_nnf_leave_for_all_clause_alone() -> None:
    clause = All(X, pred1(X))
    assert str(to_nnf(clause)) == "∀X(pred1(X))"


def test_to_nnf_simplifies_not_or_clause() -> None:
    clause = Not(Or(pred1(X), pred2(X)))
    assert str(to_nnf(clause)) == "¬pred1(X) ∧ ¬pred2(X)"


def test_to_nnf_simplifies_not_and_clause() -> None:
    clause = Not(And(pred1(X), pred2(X)))
    assert str(to_nnf(clause)) == "¬pred1(X) ∨ ¬pred2(X)"


def test_to_nnf_simplifies_not_not_clause() -> None:
    clause = Not(Not(pred1(X)))
    assert str(to_nnf(clause)) == "pred1(X)"


def test_to_nnf_simplifies_nested_clause() -> None:
    # ¬∀X(∃Y(¬((pred1(X) ∨ pred2(Y)) ∧ pred1(const1))))
    clause = Not(All(X, Exists(Y, Not(And(Or(pred1(X), pred2(Y)), pred1(const1))))))
    assert str(to_nnf(clause)) == "∃X(∀Y((pred1(X) ∨ pred2(Y)) ∧ pred1(const1)))"
