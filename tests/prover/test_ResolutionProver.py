from __future__ import annotations

import pytest
from textwrap import dedent
import numpy as np

from tensor_theorem_prover.prover.ResolutionProver import ResolutionProver
from tensor_theorem_prover.types import (
    Variable,
    Predicate,
    Constant,
    Implies,
    And,
    Not,
    Clause,
)
from tests.helpers import to_disj


X = Variable("X")
Y = Variable("Y")
Z = Variable("Z")
grandpa_of = Predicate("grandpa_of")
grandma_of = Predicate("grandma_of")
parent_of = Predicate("parent_of")
father_of = Predicate("father_of")
mother_of = Predicate("mother_of")
bart = Constant("bart")
homer = Constant("homer")
marge = Constant("marge")
mona = Constant("mona")
abe = Constant("abe")

# amr-inspired logic
arg0 = Predicate("arg0")
arg1 = Predicate("arg1")
you = Predicate("you")
commit = Predicate("commit")
follow_through = Predicate("follow_through")
good = Predicate("good")
bad = Predicate("bad")
y = Constant("y")
x = Constant("x")
z = Constant("z")

# amr-inspired knowledge
amr_knowledge: list[Clause] = [
    # ¬(follow-through-07(X) ∧ :ARG0(X,Y) ∧ you(Y) ∧ :ARG1(X,Z) ∧ commit-01(Z) ∧ :ARG1(Z,Y)) → (¬good(X) ∧ bad(X))
    # not following through on your commitments is bad and not good
    Implies(
        Not(
            And(
                follow_through(X),
                arg0(X, Y),
                you(Y),
                arg1(X, Z),
                commit(Z),
                arg1(Z, Y),
            )
        ),
        And(Not(good(X)), bad(X)),
    ),
    # you don't follow through on your commitments
    # ¬(follow-through-07(x) ∧ :ARG0(x,y) ∧ you(y) ∧ :ARG1(x,z) ∧ commit-01(z) ∧ :ARG1(z,y))
    Not(
        And(
            follow_through(x),
            arg0(x, y),
            you(y),
            arg1(x, z),
            commit(z),
            arg1(z, y),
        )
    ),
]

grandpa_of_def = Implies(
    And(father_of(X, Z), parent_of(Z, Y)),
    grandpa_of(X, Y),
)
grandma_of_def = Implies(
    And(mother_of(X, Z), parent_of(Z, Y)),
    grandma_of(X, Y),
)


def test_single_step_proof() -> None:
    knowledge: list[Clause] = [
        parent_of(homer, bart),
        parent_of(marge, bart),
        father_of(abe, homer),
        mother_of(mona, homer),
    ]

    prover = ResolutionProver(knowledge=knowledge)
    goal = father_of(X, homer)

    proof = prover.prove(goal)

    assert proof is not None
    assert proof.similarity == 1.0
    assert proof.goal == to_disj([Not(goal)])
    assert proof.substitutions == {X: abe}
    assert proof.depth == 1

    EXPECTED_PROOF_STR = """\
    Goal: [¬father_of(X,homer)]
    Subsitutions: {X -> abe}
    Similarity: 1.0
    Depth: 1
    Steps:
      Similarity: 1.0
      Source: [¬father_of(X,homer)]
      Target: [father_of(abe,homer)]
      Unify: father_of(X,homer) = father_of(abe,homer)
      Subsitutions: {X -> abe}, {}
      Resolvent: []
    """
    assert str(proof) == dedent(EXPECTED_PROOF_STR).strip()


def test_solve_basic_multistep_proof() -> None:
    knowledge: list[Clause] = [
        # base facts
        parent_of(homer, bart),
        parent_of(marge, bart),
        father_of(abe, homer),
        mother_of(mona, homer),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = ResolutionProver(knowledge=knowledge)
    goal = grandpa_of(abe, bart)

    proof = prover.prove(goal)

    assert proof is not None
    assert proof.similarity == 1.0
    assert proof.goal == to_disj([Not(goal)])
    assert proof.substitutions == {}


def test_solve_proof_with_variables() -> None:
    knowledge: list[Clause] = [
        # base facts
        parent_of(homer, bart),
        parent_of(marge, bart),
        father_of(abe, homer),
        mother_of(mona, homer),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = ResolutionProver(knowledge=knowledge)
    goal = grandpa_of(X, bart)

    proof = prover.prove(goal)

    assert proof is not None
    assert proof.similarity == 1.0
    assert proof.goal == to_disj([Not(goal)])
    assert proof.substitutions == {X: abe}
    assert proof.depth == 3


def test_solve_proof_beyond_horn_clauses() -> None:
    prover = ResolutionProver(knowledge=amr_knowledge, max_proof_depth=20)

    goal = bad(X)
    proof = prover.prove(goal)

    assert proof is not None
    assert proof.similarity == 1.0
    assert proof.depth >= 10


def test_max_resolvent_width() -> None:
    goal = bad(X)

    low_width_prover = ResolutionProver(
        knowledge=amr_knowledge, max_resolvent_width=3, max_proof_depth=20
    )
    proof = low_width_prover.prove(goal)
    assert proof is None

    high_width_prover = ResolutionProver(
        knowledge=amr_knowledge, max_resolvent_width=10, max_proof_depth=20
    )
    proof = high_width_prover.prove(goal)
    assert proof is not None


def test_prove_all_doesnt_duplicate_proofs() -> None:
    knowledge: list[Clause] = [
        # base facts
        parent_of(homer, bart),
        parent_of(marge, bart),
        father_of(abe, homer),
        mother_of(mona, homer),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = ResolutionProver(knowledge=knowledge)
    goal = grandpa_of(abe, Y)

    proofs = prover.prove_all(goal)
    assert len(proofs) == 1
    assert proofs[0].substitutions == {Y: bart}


def test_fails_to_prove_unprovable_goal() -> None:

    knowledge: list[Clause] = [
        # base facts
        parent_of(homer, bart),
        parent_of(marge, bart),
        father_of(abe, homer),
        mother_of(mona, homer),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = ResolutionProver(knowledge=knowledge)
    goal = grandpa_of(marge, bart)

    assert prover.prove(goal) is None


def test_prove_all_with_multiple_valid_proof_paths_and_embedding_similarities() -> None:
    father_of_embed = Predicate("father_of", np.array([0.99, 0.25, 1.17]))
    dad_of_embed = Predicate("dad_of", np.array([1.0, 0.0, 1.0]))

    grandpa_of_def_embed = Implies(
        And(father_of_embed(X, Z), father_of_embed(Z, Y)),
        grandpa_of(X, Y),
    )
    knowledge: list[Clause] = [
        # base facts
        father_of_embed(homer, bart),
        dad_of_embed(homer, bart),
        father_of_embed(abe, homer),
        dad_of_embed(abe, homer),
        # theorems
        grandpa_of_def_embed,
    ]

    prover = ResolutionProver(knowledge=knowledge)

    goal = grandpa_of(X, bart)

    proofs, stats = prover.prove_all_with_stats(goal)
    # should have a separate proof for each combo of dad/father in grandpa_of
    assert len(proofs) == 4
    # proofs should be sorted by similarity
    assert proofs[0].similarity == pytest.approx(1.0)
    assert proofs[-1].similarity < 0.99
    for proof in proofs:
        assert proof.substitutions == {X: abe}

    # make sure that stats look sane
    assert proofs[0].stats.successful_unifications <= stats.successful_unifications
    assert proofs[0].stats.attempted_unifications <= stats.attempted_unifications
    assert proofs[0].stats.attempted_resolutions <= stats.attempted_resolutions
    assert proofs[0].stats.successful_resolutions <= stats.successful_resolutions
    assert proofs[0].stats.similarity_comparisons <= stats.similarity_comparisons
    assert proofs[0].stats.similarity_cache_hits <= stats.similarity_cache_hits

    assert stats.attempted_resolutions > 0
    assert stats.attempted_unifications > 0
    assert stats.successful_resolutions > 0
    assert stats.successful_unifications > 0
    assert stats.similarity_comparisons > 0
    assert stats.similarity_cache_hits > 0
    assert stats.max_resolvent_width_seen > 0
    assert stats.max_depth_seen > 0


def test_prove_all_can_limit_the_number_of_returned_proofs() -> None:
    father_of_embed = Predicate("father_of", np.array([0.99, 0.25, 1.17]))
    dad_of_embed = Predicate("dad_of", np.array([1.0, 0.0, 1.0]))

    grandpa_of_def_embed = Implies(
        And(father_of_embed(X, Z), father_of_embed(Z, Y)),
        grandpa_of(X, Y),
    )
    knowledge: list[Clause] = [
        # base facts
        father_of_embed(homer, bart),
        dad_of_embed(homer, bart),
        father_of_embed(abe, homer),
        dad_of_embed(abe, homer),
        # theorems
        grandpa_of_def_embed,
    ]

    prover = ResolutionProver(knowledge=knowledge)

    goal = grandpa_of(X, bart)

    proofs = prover.prove_all(goal, max_proofs=2)
    assert len(proofs) == 2
    # proofs should be sorted by similarity
    assert proofs[0].similarity == pytest.approx(1.0)
    assert proofs[-1].similarity < 0.99
    for proof in proofs:
        assert proof.substitutions == {X: abe}


def test_prove_all_can_abort_early_if_best_proof_is_not_needed() -> None:
    father_of_embed = Predicate("father_of", np.array([0.99, 0.25, 1.17]))
    dad_of_embed = Predicate("dad_of", np.array([1.0, 0.0, 1.0]))

    grandpa_of_def_embed = Implies(
        And(father_of_embed(X, Z), father_of_embed(Z, Y)),
        grandpa_of(X, Y),
    )
    knowledge: list[Clause] = [
        # base facts
        father_of_embed(homer, bart),
        dad_of_embed(homer, bart),
        father_of_embed(abe, homer),
        dad_of_embed(abe, homer),
        # theorems
        grandpa_of_def_embed,
    ]

    prover = ResolutionProver(knowledge=knowledge, find_highest_similarity_proofs=False)

    goal = grandpa_of(X, bart)

    proofs = prover.prove_all(goal, max_proofs=1)
    assert len(proofs) == 1
    for proof in proofs:
        assert proof.similarity <= 1.0
        assert proof.substitutions == {X: abe}


def test_prove_all_can_abort_early_by_setting_max_resolution_attempts() -> None:
    father_of_embed = Predicate("father_of", np.array([0.99, 0.25, 1.17]))
    dad_of_embed = Predicate("dad_of", np.array([1.0, 0.0, 1.0]))

    grandpa_of_def_embed = Implies(
        And(father_of_embed(X, Z), father_of_embed(Z, Y)),
        grandpa_of(X, Y),
    )
    knowledge: list[Clause] = [
        # base facts
        father_of_embed(homer, bart),
        dad_of_embed(homer, bart),
        father_of_embed(abe, homer),
        dad_of_embed(abe, homer),
        # theorems
        grandpa_of_def_embed,
    ]

    prover = ResolutionProver(knowledge=knowledge, max_resolution_attempts=2)

    goal = grandpa_of(X, bart)

    proofs, stats = prover.prove_all_with_stats(goal, max_proofs=1)
    assert len(proofs) == 0
    # needs a slight buffer, since it doesn't check the abort condition after every resolution
    assert stats.attempted_resolutions < 25


# TODO: move these 2 tests to rust
# def test_purge_similarity_cache() -> None:
#     prover = ResolutionProver(knowledge=[])
#     prover.similarity_cache = {(1, 2): 0.5}
#     prover.purge_similarity_cache()
#     assert prover.similarity_cache == {}


# def test_reset() -> None:
#     prover = ResolutionProver(knowledge=[parent_of(homer, bart)])
#     prover.similarity_cache = {(1, 2): 0.5}
#     prover.reset()
#     assert prover.similarity_cache == {}
#     assert prover.base_knowledge == set()
