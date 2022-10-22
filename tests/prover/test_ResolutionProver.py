from __future__ import annotations

import pytest
from textwrap import dedent
import numpy as np

from amr_reasoner.prover.ResolutionProver import ResolutionProver
from amr_reasoner.types import Variable, Predicate, Constant, Implies, And, Not, Clause
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

    proofs = prover.prove_all(goal)
    # should have a separate proof for each combo of dad/father in grandpa_of
    assert len(proofs) == 4
    # proofs should be sorted by similarity
    assert proofs[0].similarity == pytest.approx(1.0)
    assert proofs[-1].similarity < 0.99
    for proof in proofs:
        assert proof.substitutions == {X: abe}
