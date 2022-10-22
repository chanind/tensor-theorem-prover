from __future__ import annotations

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


def test_solve_basic_proof() -> None:

    grandpa_of_def = Implies(
        And(father_of(X, Z), parent_of(Z, Y)),
        grandpa_of(X, Y),
    )
    grandma_of_def = Implies(
        And(mother_of(X, Z), parent_of(Z, Y)),
        grandma_of(X, Y),
    )

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


def test_fails_to_prove_unprovable_goal() -> None:

    grandpa_of_def = Implies(
        And(father_of(X, Z), parent_of(Z, Y)),
        grandpa_of(X, Y),
    )
    grandma_of_def = Implies(
        And(mother_of(X, Z), parent_of(Z, Y)),
        grandma_of(X, Y),
    )

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
