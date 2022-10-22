from __future__ import annotations

from tensor_theorem_prover.util.find_variables_in_terms import find_variables_in_terms
from tensor_theorem_prover.types import Constant, Variable, Function, Term

const1 = Constant("const1")
const2 = Constant("const2")

func1 = Function("func1")
func2 = Function("func2")

X = Variable("X")
Y = Variable("Y")
Z = Variable("Z")


def test_find_variables_in_terms_with_no_variables() -> None:
    terms = [const1, const2]
    variables = find_variables_in_terms(terms)
    assert variables == set()


def test_find_variables_with_one_variable() -> None:
    terms: list[Term] = [const1, X]
    variables = find_variables_in_terms(terms)
    assert variables == {X}


def test_find_variables_with_repeated_variables() -> None:
    terms: list[Term] = [const1, X, X, Y]
    variables = find_variables_in_terms(terms)
    assert variables == {X, Y}


def test_find_variables_in_functions() -> None:
    terms: list[Term] = [func1(X, Y), func2(X, Z)]
    variables = find_variables_in_terms(terms)
    assert variables == {X, Y, Z}


def test_find_variables_in_nested_functions() -> None:
    terms: list[Term] = [func1(func2(X, Y), Z)]
    variables = find_variables_in_terms(terms)
    assert variables == {X, Y, Z}
