from __future__ import annotations

from amr_reasoner.normalize.to_cnf import CNFDisjunction, CNFLiteral
from amr_reasoner.prover.operations.resolve import (
    _find_unused_variables,
    _find_non_overlapping_var_names,
    _rename_variables_in_literals,
    _perform_substitution,
    _build_resolvent,
)
from amr_reasoner.prover.operations.unify import Unification
from amr_reasoner.prover.ProofStep import SubstitutionsMap
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
A = Variable("A")
B = Variable("B")
C = Variable("C")


def test_find_unused_variables() -> None:
    literals = [
        CNFLiteral(pred1(X, const1), True),
        CNFLiteral(pred2(Y), False),
    ]
    assert _find_unused_variables(literals, {}) == {X, Y}
    assert _find_unused_variables(literals, {Y: const1}) == {X}
    assert _find_unused_variables(literals, {Y: const1, X: const2}) == set()


def test_find_non_overlapping_var_names_leaves_vars_unchanged_if_no_overlaps() -> None:
    source_vars = {X, Y, Z}
    target_vars = {A, B, C}
    all_vars = source_vars | target_vars
    assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {}


def test_find_non_overlapping_var_names_renames_vars_if_overlaps() -> None:
    source_vars = {X, Y, Z}
    target_vars = {A, B, X}
    all_vars = source_vars | target_vars
    assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {
        X: Variable("X_1")
    }


def test_find_non_overlapping_keeps_iterating_var_names_until_a_non_bound_one_is_found() -> None:
    source_vars = {X, Y, Z}
    target_vars = {A, B, X}
    all_vars = source_vars | target_vars | {Variable("X_1"), Variable("X_2")}
    assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {
        X: Variable("X_3")
    }


def test_rename_variables_in_literals() -> None:
    literals = [
        CNFLiteral(pred1(X, const1), True),
        CNFLiteral(pred2(Y), False),
    ]
    rename_vars_map = {X: Variable("X_1"), Y: Variable("Y_1")}
    renamed_literals = _rename_variables_in_literals(literals, rename_vars_map)
    assert renamed_literals == [
        CNFLiteral(pred1(Variable("X_1"), const1), True),
        CNFLiteral(pred2(Variable("Y_1")), False),
    ]


def test_perform_substitution_basic() -> None:
    literals = [
        CNFLiteral(pred1(X, const1), True),
        CNFLiteral(pred2(Y), False),
    ]
    substitutions: SubstitutionsMap = {X: const2, Y: const1}
    substituted_literals = _perform_substitution(literals, substitutions)
    assert substituted_literals == [
        CNFLiteral(pred1(const2, const1), True),
        CNFLiteral(pred2(const1), False),
    ]


def test_perform_substitution_with_repeated_vars() -> None:
    literals = [CNFLiteral(pred1(X, Y), True)]
    substitutions: SubstitutionsMap = {
        X: Y,
        Y: const2,
    }
    substituted_literals = _perform_substitution(literals, substitutions)
    assert substituted_literals == [
        CNFLiteral(pred1(Y, const2), True),
    ]


def test_build_resolvent() -> None:
    source_literal = CNFLiteral(pred2(Y, const2), False)
    target_literal = CNFLiteral(pred2(const1, X), True)

    source_literals = [
        source_literal,
        CNFLiteral(pred1(Y, const1), True),
    ]
    source_disjunction = CNFDisjunction(source_literals)
    target_literals = [
        target_literal,
        CNFLiteral(pred2(const2, X), False),
    ]
    target_disjunction = CNFDisjunction(target_literals)
    unification = Unification(
        similarity=1.0,
        source_substitutions={Y: const1},
        target_substitutions={X: const2},
    )
    resolvent = _build_resolvent(
        source=source_disjunction,
        target=target_disjunction,
        source_literal=source_literal,
        target_literal=target_literal,
        unification=unification,
    )

    expected_literals = [
        CNFLiteral(pred1(const1, const1), True),
        CNFLiteral(pred2(const2, const2), False),
    ]
    assert resolvent == CNFDisjunction(expected_literals)
