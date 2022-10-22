from __future__ import annotations

import numpy as np

from amr_reasoner.prover.operations.unify import unify, Unification
from amr_reasoner.similarity import cosine_similarity
from amr_reasoner.types import (
    Constant,
    Function,
    Predicate,
    Variable,
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


def test_unify_fails_if_functions_dont_match() -> None:
    source = pred1(func1(X))
    target = pred1(func2(Y))
    assert unify(source, target) is None


def test_unify_fails_if_functions_take_different_number_of_params() -> None:
    source = pred1(func1(X, Y))
    target = pred1(func1(X))
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


def test_unify_with_function_map_var_to_const() -> None:
    source = pred1(func1(X))
    target = pred1(func1(const1))
    assert unify(source, target) == Unification({X: const1}, {})


def test_unify_with_function_map_var_to_var() -> None:
    source = pred1(func1(X))
    target = pred1(func1(Y))
    assert unify(source, target) == Unification({}, {Y: X})


def test_unify_with_function_map_var_to_var_with_repeat_constants() -> None:
    source = pred1(func1(X, X))
    target = pred1(func1(const1, Y))
    assert unify(source, target) == Unification({X: const1}, {Y: const1})


def test_unify_with_function_map_var_to_var_with_repeat_constants2() -> None:
    source = pred1(func1(const1, Y))
    target = pred1(func1(X, X))
    assert unify(source, target) == Unification({Y: const1}, {X: const1})


def test_unify_bind_nested_function_var() -> None:
    source = pred1(func1(X))
    target = pred1(func1(func2(const1)))
    assert unify(source, target) == Unification({X: func2(const1)}, {})


def test_unify_fails_to_bind_reciprocal_functions() -> None:
    source = pred1(func1(X), X)
    target = pred1(Y, func1(Y))
    assert unify(source, target) is None


def test_unify_with_predicate_vector_embeddings() -> None:
    vec_pred1 = Predicate("pred1", np.array([1, 0, 1, 1]))
    vec_pred2 = Predicate("pred2", np.array([1, 0, 0.9, 1]))
    source = vec_pred1(X)
    target = vec_pred2(const1)
    unification = unify(source, target, similarity_func=cosine_similarity)
    assert unification is not None
    assert unification.source_substitutions == {X: const1}
    assert unification.target_substitutions == {}
    assert unification.similarity > 0.9 and unification.similarity < 1.0


def test_unify_fails_with_dissimilar_predicate_vector_embeddings() -> None:
    vec_pred1 = Predicate("pred1", np.array([0, 1, 1, 0]))
    vec_pred2 = Predicate("pred2", np.array([1, 0, 0.3, 1]))
    source = vec_pred1(X)
    target = vec_pred2(const1)
    assert unify(source, target, similarity_func=cosine_similarity) is None


def test_unify_with_constant_vector_embeddings() -> None:
    vec_const1 = Constant("const1", np.array([1, 0, 1, 1]))
    vec_const2 = Constant("const2", np.array([1, 0, 0.9, 1]))
    source = pred1(vec_const1)
    target = pred1(vec_const2)
    unification = unify(source, target, similarity_func=cosine_similarity)
    assert unification is not None
    assert unification.source_substitutions == {}
    assert unification.target_substitutions == {}
    assert unification.similarity > 0.9 and unification.similarity < 1.0


def test_unify_fails_with_dissimilar_constant_vector_embeddings() -> None:
    vec_const1 = Constant("const1", np.array([0, 1, 1, 0]))
    vec_const2 = Constant("const2", np.array([1, 0, 0.3, 1]))
    source = pred1(vec_const1)
    target = pred1(vec_const2)
    assert unify(source, target, similarity_func=cosine_similarity) is None
