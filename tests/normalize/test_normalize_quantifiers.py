from tensor_theorem_prover.normalize.Skolemizer import Skolemizer
from tensor_theorem_prover.normalize.normalize_quantifiers import normalize_quantifiers
from tensor_theorem_prover.types import (
    And,
    Constant,
    Predicate,
    Variable,
    Or,
    Function,
    All,
    Exists,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

func1 = Function("func1")
func2 = Function("func2")

X = Variable("X")
Y = Variable("Y")
Z = Variable("Z")


def test_normalize_quantifiers_leaves_simple_clauses_unchanged() -> None:
    clause = And(pred1(const1), pred2(const2))
    assert (
        str(normalize_quantifiers(clause, Skolemizer()))
        == "pred1(const1) ∧ pred2(const2)"
    )


def test_normalize_quantifiers_removes_forall_quantifiers() -> None:
    clause = All(Y, And(pred1(Y), All(X, pred2(X))))
    assert str(normalize_quantifiers(clause, Skolemizer())) == "pred1(Y) ∧ pred2(X)"


def test_normalize_quantifiers_skolemizes_exists_quantifiers() -> None:
    clause = Exists(Y, And(pred1(Y), Exists(X, pred2(X, Y))))
    assert (
        str(normalize_quantifiers(clause, Skolemizer()))
        == "pred1(_SK_1()) ∧ pred2(_SK_2(),_SK_1())"
    )


def test_normalize_quantifiers_binds_universal_vars_in_skolem_funcs() -> None:
    clause = All(Y, And(pred1(Y), Exists(X, And(pred2(X, Y), pred2(X, Z)))))
    assert (
        str(normalize_quantifiers(clause, Skolemizer()))
        == "pred1(Y) ∧ pred2(_SK_1(Y,Z),Y) ∧ pred2(_SK_1(Y,Z),Z)"
    )


def test_normalize_quantifiers_binds_universal_vars_by_scope_in_skolem_funcs() -> None:
    clause = All(Y, And(pred1(Y), Exists(X, All(Z, And(pred2(X, Y), pred2(X, Z))))))
    assert (
        str(normalize_quantifiers(clause, Skolemizer()))
        == "pred1(Y) ∧ pred2(_SK_1(Y),Y) ∧ pred2(_SK_1(Y),Z)"
    )


def test_normalize_quantifiers_works_with_nested_functions() -> None:
    clause = And(
        pred1(Y),
        Exists(X, Or(pred2(func1(func1(X)), Y), pred1(const1, func2(Y, func1(X))))),
    )
    assert (
        str(normalize_quantifiers(clause, Skolemizer()))
        == "pred1(Y) ∧ (pred2(func1(func1(_SK_1(Y))),Y) ∨ pred1(const1,func2(Y,func1(_SK_1(Y)))))"
    )
