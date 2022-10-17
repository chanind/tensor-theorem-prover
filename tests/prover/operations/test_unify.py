from immutables import Map
import numpy as np
import pytest
from amr_reasoner.prover.Goal import Goal

from amr_reasoner.prover.operations.unify import (
    unify,
)
from amr_reasoner.similarity import cosine_similarity
from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Predicate import Predicate
from amr_reasoner.types.Rule import Rule
from amr_reasoner.types.Variable import Variable


scope = 7  # scope is just a number to identify variable bindings


def test_unify_returns_new_substitution_map_and_similarity_on_success() -> None:
    is_dog = Predicate("is_dog")
    X = Variable("X")
    fluffy = Constant("fluffy")

    rule1 = Rule(is_dog(X))
    rule2 = Rule(is_dog(fluffy))

    goal = Goal(rule1.head, scope)

    result = unify(
        rule2,
        goal,
        scope,
        Map(),
        similarity_func=cosine_similarity,
        min_similarity_threshold=0.5,
    )
    assert result is not None
    assert result[0] == Map({scope: Map({X: fluffy})})
    assert result[1] == 1.0


def test_unify_fails_if_similarity_is_below_threshold() -> None:
    is_person = Predicate("is_person", np.array([1, 0, 1]))
    is_dog = Predicate("is_dog", np.array([0, 1, 1]))
    X = Variable("X")
    fluffy = Constant("fluffy")

    rule1 = Rule(is_person(X))
    rule2 = Rule(is_dog(fluffy))

    goal = Goal(rule1.head, scope)

    assert (
        unify(
            rule2,
            goal,
            scope,
            Map(),
            similarity_func=cosine_similarity,
            min_similarity_threshold=0.9,
        )
        is None
    )


def test_unify_fails_if_the_terms_are_different_lengths() -> None:
    is_doggo = Predicate("is_doggo", np.array([1, 0, 1]))
    is_dog = Predicate("is_dog", np.array([0, 1, 1]))
    X = Variable("X")
    fluffy = Constant("fluffy")
    face = Constant("face")

    rule1 = Rule(is_doggo(X))
    rule2 = Rule(is_dog(fluffy, face))

    goal = Goal(rule1.head, scope)

    assert (
        unify(
            rule2,
            goal,
            scope,
            Map(),
            similarity_func=cosine_similarity,
            min_similarity_threshold=0.1,
        )
        is None
    )


def test_unify_uses_the_min_similarity_of_all_unified_items() -> None:
    is_doggo = Predicate("is_doggo", np.array([1, 0, 1, 1]))
    is_dog = Predicate("is_dog", np.array([0, 1, 1, 1]))
    fluffy = Constant("fluffy", np.array([1, 0, 1]))
    furball = Constant("furball", np.array([0, 1, 1]))

    rule1 = Rule(is_doggo(furball))
    rule2 = Rule(is_dog(fluffy))

    goal = Goal(rule1.head, scope)

    result = unify(
        rule2,
        goal,
        scope,
        Map(),
        similarity_func=cosine_similarity,
        min_similarity_threshold=0.1,
    )
    assert result is not None
    assert result[0] == Map()
    assert result[1] == pytest.approx(0.5)
