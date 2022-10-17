from textwrap import dedent
from amr_reasoner import (
    SLDProver,
    Atom,
    Constant,
    Predicate,
    Rule,
    Variable,
    Knowledge,
    cosine_similarity,
    symbol_compare,
)


def test_imports() -> None:
    assert SLDProver is not None
    assert Atom is not None
    assert Constant is not None
    assert Predicate is not None
    assert Rule is not None
    assert Variable is not None
    assert cosine_similarity is not None
    assert symbol_compare is not None


def test_basic_proof() -> None:
    X = Variable("X")
    Y = Variable("Y")
    father_of = Predicate("father_of")
    parent_of = Predicate("parent_of")
    is_male = Predicate("is_male")
    bart = Constant("bart")
    homer = Constant("homer")

    knowledge: Knowledge = [
        parent_of(homer, bart),
        is_male(homer),
        Rule(father_of(X, Y), (parent_of(X, Y), is_male(X))),
    ]

    prover = SLDProver(knowledge=knowledge)
    goal = father_of(homer, X)

    proof = prover.prove(goal)
    assert proof is not None
    assert proof.variable_bindings[X] == bart

    pretty_proof = dedent(
        """
        | goal: father_of(CONST:homer,VAR:X)
        | rule: father_of(VAR:X,VAR:Y):-[parent_of(VAR:X,VAR:Y), is_male(VAR:X)]
        | unification similarity: 1.0
        | overall similarity: 1.0
        | goal subs: X->bart
        | rule subs: X->homer, Y->bart
        | subgoals: parent_of(VAR:X,VAR:Y), is_male(VAR:X)
          ║
          ╠═ | goal: parent_of(VAR:X,VAR:Y)
          ║  | rule: parent_of(CONST:homer,CONST:bart):-[]
          ║  | unification similarity: 1.0
          ║  | overall similarity: 1.0
          ║  | goal subs: X->homer, Y->bart
          ║
          ╠═ | goal: is_male(VAR:X)
          ║  | rule: is_male(CONST:homer):-[]
          ║  | unification similarity: 1.0
          ║  | overall similarity: 1.0
          ║  | goal subs: X->homer
        """
    ).strip()
    print(proof.pretty_print())
    assert proof.pretty_print() == pretty_proof
