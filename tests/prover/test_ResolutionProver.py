from __future__ import annotations
from textwrap import dedent

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


def test_solve_basic_proof() -> None:
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

    EXPECTED_PROOF_STR = """\
    Goal: [¬grandpa_of(X,bart)]
    Subsitutions: {X -> abe}
    Similarity: 1.0
    Depth: 3
    Steps:
      Similarity: 1.0
      Source: [¬grandpa_of(X,bart)]
      Target: [grandpa_of(X,Y) ∨ ¬father_of(X,Z) ∨ ¬parent_of(Z,Y)]
      Unify: grandpa_of(X,bart) = grandpa_of(X,Y)
      Subsitutions: {}, {X -> X, Y -> bart}
      Resolvent: [¬father_of(X,Z) ∨ ¬parent_of(Z,bart)]
      ---
      Similarity: 1.0
      Source: [¬father_of(X,Z) ∨ ¬parent_of(Z,bart)]
      Target: [parent_of(homer,bart)]
      Unify: parent_of(Z,bart) = parent_of(homer,bart)
      Subsitutions: {Z -> homer}, {}
      Resolvent: [¬father_of(X,homer)]
      ---
      Similarity: 1.0
      Source: [¬father_of(X,homer)]
      Target: [father_of(abe,homer)]
      Unify: father_of(X,homer) = father_of(abe,homer)
      Subsitutions: {X -> abe}, {}
      Resolvent: []  
    """

    assert str(proof) == dedent(EXPECTED_PROOF_STR).strip()


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
