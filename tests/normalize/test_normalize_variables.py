from amr_reasoner.normalize.normalize_variables import normalize_variables
from amr_reasoner.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Implies,
    Or,
    All,
    Exists,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

X = Variable("X")
Y = Variable("Y")


def test_normalize_variables_leaves_simple_clauses_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert str(normalize_variables(clause)) == "pred1(const1) ∧ pred2(const2)"


def test_normalize_variables_renames_unbound_vars() -> None:
    clause = And(pred1(X), pred2(Y), pred2(X))
    assert str(normalize_variables(clause)) == "pred1(X_1) ∧ pred2(Y_2) ∧ pred2(X_1)"


def test_normalize_variables_handles_nested_vars_with_same_name() -> None:
    clause = And(pred1(X), Exists(X, Or(pred2(X), pred1(X))))
    assert (
        str(normalize_variables(clause)) == "pred1(X_1) ∧ ∃X_2(pred2(X_2) ∨ pred1(X_2))"
    )


def test_normalize_variables_handles_nested_vars_with_same_name_2() -> None:
    clause = And(pred1(X), All(X, Or(pred2(X, X), pred1(X))))
    assert (
        str(normalize_variables(clause))
        == "pred1(X_1) ∧ ∀X_2(pred2(X_2,X_2) ∨ pred1(X_2))"
    )
