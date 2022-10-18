from amr_reasoner.normalize.clause_to_nnf import clause_to_nnf
from amr_reasoner.types import (
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


def test_simplifies_and_clause_to_nnf_stays_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert clause_to_nnf(clause) == clause


def test_simplifies_implies_clause() -> None:
    clause = Implies(pred1(X), pred2(X))
    assert str(clause_to_nnf(clause)) == "¬pred1(X) ∨ pred2(X)"


def test_simplifies_not_all_clause() -> None:
    clause = Not(All(X, pred1(X)))
    assert str(clause_to_nnf(clause)) == "∃X(¬pred1(X))"


def test_simplifies_not_exists_clause() -> None:
    clause = Not(Exists(X, pred1(X)))
    assert str(clause_to_nnf(clause)) == "∀X(¬pred1(X))"


def test_simplifies_not_or_clause() -> None:
    clause = Not(Or(pred1(X), pred2(X)))
    assert str(clause_to_nnf(clause)) == "¬pred1(X) ∧ ¬pred2(X)"


def test_simplifies_not_and_clause() -> None:
    clause = Not(And(pred1(X), pred2(X)))
    assert str(clause_to_nnf(clause)) == "¬pred1(X) ∨ ¬pred2(X)"


def test_simplifies_not_not_clause() -> None:
    clause = Not(Not(pred1(X)))
    assert str(clause_to_nnf(clause)) == "pred1(X)"
