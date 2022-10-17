import numpy as np
from amr_reasoner.prover.SLDProver import SLDProver
from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Rule import Rule
from amr_reasoner.types.Variable import Variable
from amr_reasoner.types.Predicate import Predicate


def test_basic_proof_without_amr_unification() -> None:
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

    grandpa_of_def = Rule(grandpa_of(X, Y), (father_of(X, Z), parent_of(Z, Y)))
    grandma_of_def = Rule(grandma_of(X, Y), (mother_of(X, Z), parent_of(Z, Y)))

    knowledge = [
        # base facts
        Rule(parent_of(homer, bart)),
        Rule(parent_of(marge, bart)),
        Rule(father_of(abe, homer)),
        Rule(mother_of(mona, homer)),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = SLDProver(knowledge=knowledge)
    goal = grandpa_of(abe, bart)

    proof = prover.prove(goal)
    assert proof is not None
    assert proof.similarity_score == 1.0
    assert proof.goal == goal

    # should first unify against grandpa_of(X,Y) :- father_of(X,Z), parent_of(Z,Y)
    assert proof.head.rule == grandpa_of_def

    # should then join the 2 subgoals
    assert proof.head.children is not None
    assert len(proof.head.children) == 2

    assert grandpa_of_def.body is not None  # for mypy

    # should then unify father_of(X,Z) with father_of(abe, homer)
    assert proof.head.children[0].goal == grandpa_of_def.body[0]
    assert proof.head.children[0].children is None

    # should then unify parent_of(Z,Y) with parent_of(homer, bart)
    assert proof.head.children[1].goal == grandpa_of_def.body[1]
    assert proof.head.children[1].children is None

    # should not be able to prove things that are false
    assert prover.prove(grandpa_of(mona, bart)) is None
    assert prover.prove(grandpa_of(bart, abe)) is None


def test_can_use_composite_knowledge() -> None:
    X = Variable("X")
    Y = Variable("Y")
    Z = Variable("Z")
    grandpa_of = Predicate("grandpa_of")
    parent_of = Predicate("parent_of")
    father_of = Predicate("father_of")
    is_male = Predicate("is_male")
    is_female = Predicate("is_female")
    bart = Constant("bart")
    marge = Constant("marge")
    homer = Constant("homer")
    abe = Constant("abe")

    grandpa_of_def = Rule(grandpa_of(X, Y), (father_of(X, Z), parent_of(Z, Y)))
    father_of_def = Rule(father_of(X, Y), (parent_of(X, Y), is_male(X)))

    knowledge = [
        # base facts
        Rule(parent_of(homer, bart)),
        Rule(parent_of(abe, homer)),
        Rule(is_male(abe)),
        Rule(is_male(homer)),
        Rule(is_male(bart)),
        Rule(is_female(marge)),
        # theorems
        grandpa_of_def,
        father_of_def,
    ]

    prover = SLDProver(knowledge=knowledge)
    goal = grandpa_of(abe, bart)

    result = prover.prove(goal)
    assert result is not None


def test_can_use_recursive_theorems() -> None:
    X = Variable("X")
    Y = Variable("Y")
    Z = Variable("Z")
    ancestor_of = Predicate("ancestor_of")
    parent_of = Predicate("parent_of")
    a = Constant("a")
    b = Constant("b")
    c = Constant("c")
    d = Constant("d")
    e = Constant("e")

    knowledge = [
        # base facts
        Rule(parent_of(a, b)),
        Rule(parent_of(b, c)),
        Rule(parent_of(c, d)),
        Rule(parent_of(d, e)),
        # theorems
        Rule(ancestor_of(X, Y), (parent_of(X, Z), ancestor_of(Z, Y))),
        Rule(ancestor_of(X, Y), (parent_of(X, Y),)),
    ]

    prover = SLDProver(knowledge=knowledge)

    assert prover.prove(ancestor_of(a, b)) is not None
    assert prover.prove(ancestor_of(a, c)) is not None
    assert prover.prove(ancestor_of(a, d)) is not None
    assert prover.prove(ancestor_of(a, e)) is not None
    assert prover.prove(ancestor_of(c, e)) is not None

    assert prover.prove(ancestor_of(e, c)) is None
    assert prover.prove(ancestor_of(b, a)) is None
    assert prover.prove(ancestor_of(e, a)) is None


def test_can_solve_for_variable_values() -> None:
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

    grandpa_of_def = Rule(grandpa_of(X, Y), (father_of(X, Z), parent_of(Z, Y)))
    grandma_of_def = Rule(grandma_of(X, Y), (mother_of(X, Z), parent_of(Z, Y)))

    knowledge = [
        # base facts
        Rule(parent_of(homer, bart)),
        Rule(parent_of(marge, bart)),
        Rule(father_of(abe, homer)),
        Rule(mother_of(mona, homer)),
        # theorems
        grandpa_of_def,
        grandma_of_def,
    ]

    prover = SLDProver(knowledge=knowledge)
    single_var_goal = grandpa_of(X, bart)

    result = prover.prove(single_var_goal)
    assert result is not None
    assert len(result.variable_bindings) == 1
    assert result.variable_bindings[X] == abe

    # should be able to solve for multiple variables together
    multi_var_goal = grandpa_of(X, Y)

    result = prover.prove(multi_var_goal)
    assert result is not None
    assert len(result.variable_bindings) == 2
    assert result.variable_bindings[X] == abe
    assert result.variable_bindings[Y] == bart

    # should not be able to find proofs of things that are false
    assert prover.prove(grandpa_of(X, homer)) is None
    assert prover.prove(grandpa_of(bart, X)) is None


def test_prove_all_can_find_multiple_solutions() -> None:
    X = Variable("X")
    Y = Variable("Y")
    Z = Variable("Z")
    grandpa_of = Predicate("grandpa_of")
    parent_of = Predicate("parent_of")
    father_of = Predicate("father_of")
    bart = Constant("bart")
    homer = Constant("homer")
    marge = Constant("marge")
    clancy = Constant("clancy")
    abe = Constant("abe")

    grandpa_of_def = Rule(grandpa_of(X, Y), (father_of(X, Z), parent_of(Z, Y)))

    knowledge = [
        # base facts
        Rule(parent_of(homer, bart)),
        Rule(parent_of(marge, bart)),
        Rule(father_of(abe, homer)),
        Rule(father_of(clancy, marge)),
        # theorems
        grandpa_of_def,
    ]

    prover = SLDProver(knowledge=knowledge)

    goal = grandpa_of(X, bart)

    results = prover.prove_all(goal)
    assert len(results) == 2
    var_bindings_for_x = {result.variable_bindings[X] for result in results}
    assert abe in var_bindings_for_x
    assert clancy in var_bindings_for_x


def test_prove_all_with_multiple_valid_proof_paths() -> None:
    X = Variable("X")
    Y = Variable("Y")
    Z = Variable("Z")
    grandpa_of = Predicate("grandpa_of")
    father_of = Predicate("father_of", np.array([0.99, 0.05, 1.07]))
    dad_of = Predicate("dad_of", np.array([1.0, 0.0, 1.0]))
    bart = Constant("bart")
    homer = Constant("homer")
    abe = Constant("abe")

    grandpa_of_def = Rule(grandpa_of(X, Y), (father_of(X, Z), father_of(Z, Y)))

    knowledge = [
        # base facts
        Rule(father_of(homer, bart)),
        Rule(dad_of(homer, bart)),
        Rule(father_of(abe, homer)),
        Rule(dad_of(abe, homer)),
        # theorems
        grandpa_of_def,
    ]

    prover = SLDProver(knowledge=knowledge)

    goal = grandpa_of(X, bart)

    results = prover.prove_all(goal)
    assert len(results) == 4
    var_bindings_for_x = [result.variable_bindings[X] for result in results]
    assert [abe, abe, abe, abe] == var_bindings_for_x
