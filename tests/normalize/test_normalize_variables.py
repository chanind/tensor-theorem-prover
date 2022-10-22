from tensor_theorem_prover.normalize.normalize_variables import normalize_variables
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Or,
    All,
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


def test_normalize_variables_leaves_simple_clauses_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert str(normalize_variables(clause)) == "pred1(const1) ∧ pred2(const2)"


def test_normalize_variables_leaves_variables_alone_if_no_nesting() -> None:
    clause = And(pred1(X), pred2(Y), pred2(X))
    assert str(normalize_variables(clause)) == "pred1(X) ∧ pred2(Y) ∧ pred2(X)"


def test_normalize_variables_handles_nested_vars_with_same_name() -> None:
    clause = And(pred1(X), Exists(X, Or(pred2(X), pred1(X))))
    assert (
        str(normalize_variables(clause)) == "pred1(X) ∧ ∃X_1(pred2(X_1) ∨ pred1(X_1))"
    )


def test_normalize_variables_handles_nested_vars_with_same_name_2() -> None:
    clause = And(pred1(X), All(X, Or(pred2(X, X), pred1(X))))
    assert (
        str(normalize_variables(clause))
        == "pred1(X) ∧ ∀X_1(pred2(X_1,X_1) ∨ pred1(X_1))"
    )


def test_normalize_variables_handles_nested_functions() -> None:
    clause = And(pred1(func1(X)), All(Y, pred2(func2(X, func2(func1(Y), X)))))
    assert (
        str(normalize_variables(clause))
        == "pred1(func1(X)) ∧ ∀Y(pred2(func2(X,func2(func1(Y),X))))"
    )


def test_normalize_variables_handles_nested_functions_with_overlapping_var_names() -> None:
    clause = And(pred1(func1(X, Y)), All(Y, pred2(func2(X, func2(func1(Y), X)))))
    assert (
        str(normalize_variables(clause))
        == "pred1(func1(X,Y)) ∧ ∀Y_1(pred2(func2(X,func2(func1(Y_1),X))))"
    )
