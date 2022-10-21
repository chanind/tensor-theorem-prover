from __future__ import annotations

from amr_reasoner.prover.operations.unify import unify, Unification
from amr_reasoner.types import (
    Constant,
    Predicate,
    Variable,
)

pred1 = Predicate("pred1")
pred2 = Predicate("pred2")

const1 = Constant("const1")
const2 = Constant("const2")

X = Variable("X")
Y = Variable("Y")
Z = Variable("Z")


def test_unify_with_all_constants() -> None:
    source = pred1(const1, const2)
    target = pred1(const1, const2)
    assert unify(source, target) == Unification({}, {})


def test_unify_fails_if_preds_dont_match() -> None:
    source = pred1(const1, const2)
    target = pred2(const1, const2)
    assert unify(source, target) is None


def test_unify_fails_if_terms_dont_match() -> None:
    source = pred1(const2, const2)
    target = pred1(const1, const2)
    assert unify(source, target) is None


def test_unify_fails_if_terms_have_differing_lengths() -> None:
    source = pred1(const1)
    target = pred1(const1, const2)
    assert unify(source, target) is None


def test_unify_with_source_var_to_target_const() -> None:
    source = pred1(X, const1)
    target = pred1(const2, const1)
    assert unify(source, target) == Unification({X: const2}, {})


def test_unify_with_source_const_to_target_var() -> None:
    source = pred1(const2, const1)
    target = pred1(X, const1)
    assert unify(source, target) == Unification({}, {X: const2})


def test_unify_with_source_var_to_target_var() -> None:
    source = pred1(X, const1)
    target = pred1(Y, const1)
    assert unify(source, target) == Unification({}, {Y: X})


def test_unify_with_repeated_vars_in_source() -> None:
    source = pred1(X, X)
    target = pred1(Y, const1)
    assert unify(source, target) == Unification({X: const1}, {Y: const1})


def test_unify_with_repeated_vars_in_target() -> None:
    source = pred1(X, const1)
    target = pred1(Y, Y)
    assert unify(source, target) == Unification({X: const1}, {Y: const1})


def test_unify_fails_with_unfulfilable_constraints() -> None:
    source = pred1(X, X)
    target = pred1(const1, const2)
    assert unify(source, target) is None


def test_unify_with_source_var_to_target_var_with_repeat_constants() -> None:
    source = pred1(X, X, X, X)
    target = pred1(const1, Y, Z, const1)
    assert unify(source, target) == Unification({X: const1}, {Y: const1, Z: const1})


def test_unify_with_chained_vars() -> None:
    source = pred1(X, X, Y, Y, Z, Z)
    target = pred1(Y, X, X, Z, Z, const2)
    assert unify(source, target) == Unification(
        {X: const2, Y: const2, Z: const2}, {X: const2, Y: const2, Z: const2}
    )
