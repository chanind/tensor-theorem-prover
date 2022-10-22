from tensor_theorem_prover.normalize.find_unbound_var_names import (
    find_unbound_var_names,
)
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Or,
    All,
    Exists,
    Function,
    Implies,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

func1 = Function("func1")
func2 = Function("func2")

X = Variable("X")
Y = Variable("Y")


def test_find_unbound_vars_returns_nothing_if_no_unbound_vars() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert find_unbound_var_names(clause) == set()


def test_find_unbound_vars_finds_unbound_vars_in_simple_clause() -> None:
    clause = pred1(X)
    assert find_unbound_var_names(clause) == {"X"}


def test_find_unbound_vars_ignores_bound_vars() -> None:
    clause1 = Exists(X, pred1(X))
    clause2 = All(X, pred1(X))
    assert find_unbound_var_names(clause1) == set()
    assert find_unbound_var_names(clause2) == set()


def test_find_unbound_vars_finds_unbound_vars_in_nested_clause() -> None:
    clause = Exists(Y, Implies(pred1(X), pred2(Y)))
    assert find_unbound_var_names(clause) == {"X"}


def test_find_unbound_vars_handles_duplicated_var_names() -> None:
    clause = Or(Exists(X, pred2(X)), pred1(X))
    assert find_unbound_var_names(clause) == {"X"}


def test_find_unbound_vars_handles_nested_functions() -> None:
    clause = And(pred1(func1(X)), All(Y, pred2(func2(X, func2(func1(Y), X)))))
    assert find_unbound_var_names(clause) == {"X"}
