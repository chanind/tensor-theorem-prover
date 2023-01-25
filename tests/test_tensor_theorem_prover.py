from __future__ import annotations
from textwrap import dedent

from tensor_theorem_prover import (
    Variable,
    Predicate,
    Constant,
    Implies,
    And,
    ResolutionProver,
    Clause,
)


def test_basic_proof() -> None:
    X = Variable("X")
    Y = Variable("Y")
    father_of = Predicate("father_of")
    parent_of = Predicate("parent_of")
    is_male = Predicate("is_male")
    bart = Constant("bart")
    homer = Constant("homer")

    knowledge: list[Clause] = [
        parent_of(homer, bart),
        is_male(homer),
        Implies(And(parent_of(X, Y), is_male(X)), father_of(X, Y)),
    ]

    prover = ResolutionProver(knowledge=knowledge)

    goal = father_of(homer, X)
    proof = prover.prove(goal)

    EXPECTED_PROOF_STRS = [
        """\
    Goal: [¬father_of(homer,X)]
    Subsitutions: {X -> bart}
    Similarity: 1.0
    Depth: 3
    Steps:
      Similarity: 1.0
      Source: [¬father_of(homer,X)]
      Target: [father_of(X,Y) ∨ ¬is_male(X) ∨ ¬parent_of(X,Y)]
      Unify: father_of(homer,X) = father_of(X,Y)
      Subsitutions: {}, {X -> homer, Y -> X}
      Resolvent: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      ---
      Similarity: 1.0
      Source: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      Target: [parent_of(homer,bart)]
      Unify: parent_of(homer,X) = parent_of(homer,bart)
      Subsitutions: {X -> bart}, {}
      Resolvent: [¬is_male(homer)]
      ---
      Similarity: 1.0
      Source: [¬is_male(homer)]
      Target: [is_male(homer)]
      Unify: is_male(homer) = is_male(homer)
      Subsitutions: {}, {}
      Resolvent: []
    """,
        """\
    Goal: [¬father_of(homer,X)]
    Subsitutions: {X -> bart}
    Similarity: 1.0
    Depth: 3
    Steps:
      Similarity: 1.0
      Source: [¬father_of(homer,X)]
      Target: [father_of(X,Y) ∨ ¬is_male(X) ∨ ¬parent_of(X,Y)]
      Unify: father_of(homer,X) = father_of(X,Y)
      Subsitutions: {}, {X -> homer, Y -> X}
      Resolvent: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      ---
      Similarity: 1.0
      Source: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      Target: [is_male(homer)]
      Unify: is_male(homer) = is_male(homer)
      Subsitutions: {}, {}
      Resolvent: [¬parent_of(homer,X)]
      ---
      Similarity: 1.0
      Source: [¬parent_of(homer,X)]
      Target: [parent_of(homer,bart)]
      Unify: parent_of(homer,X) = parent_of(homer,bart)
      Subsitutions: {X -> bart}, {}
      Resolvent: []
    """,
        """\
    Goal: [¬father_of(homer,X)]
    Subsitutions: {X -> bart}
    Similarity: 1.0
    Depth: 3
    Steps:
      Similarity: 1.0
      Source: [¬father_of(homer,X)]
      Target: [father_of(X,Y) ∨ ¬is_male(X) ∨ ¬parent_of(X,Y)]
      Unify: father_of(homer,X) = father_of(X,Y)
      Subsitutions: {}, {Y -> X, X -> homer}
      Resolvent: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      ---
      Similarity: 1.0
      Source: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
      Target: [is_male(homer)]
      Unify: is_male(homer) = is_male(homer)
      Subsitutions: {}, {}
      Resolvent: [¬parent_of(homer,X)]
      ---
      Similarity: 1.0
      Source: [¬parent_of(homer,X)]
      Target: [parent_of(homer,bart)]
      Unify: parent_of(homer,X) = parent_of(homer,bart)
      Subsitutions: {X -> bart}, {}
      Resolvent: []
        """,
    ]
    print(proof)
    assert str(proof) in [
        dedent(proof_str).strip() for proof_str in EXPECTED_PROOF_STRS
    ]
