from __future__ import annotations
from typing import Optional
from amr_reasoner.prover.Goal import Goal

from amr_reasoner.prover.operations.substitution import (
    is_var_bound,
    resolve_term,
    set_var_binding,
    SubstitutionsMap,
)
from amr_reasoner.similarity import SimilarityFunc, symbol_compare
from amr_reasoner.types.Constant import Constant
from amr_reasoner.types.Rule import Rule
from amr_reasoner.types.Variable import Variable


def unify(
    rule: Rule,
    goal: Goal,
    scope: int,
    substitutions: SubstitutionsMap,
    similarity_func: Optional[SimilarityFunc] = None,
    min_similarity_threshold: float = 0.5,
) -> tuple[SubstitutionsMap, float] | None:
    """
    amr-optional implementation of prolog's unify
    If no similarity_func is provided, of if either atom lacks a embedding,
    then it will do an exact match on the symbols themselves

    Based on unification module from "End-to-End Differentiable Proving" by Rocktäschel et al.
    https://arxiv.org/abs/1705.11040

    Returns a tuple with new substitutions and new similariy if successful or None if the unification fails
    """
    head = rule.head
    next_substitutions = substitutions
    if len(head.terms) != len(goal.statement.terms):
        return None

    # if there is no comparison function provided, just use symbol compare (non-amr comparisons)
    adjusted_similarity_func = similarity_func or symbol_compare
    similarity = adjusted_similarity_func(head.predicate, goal.statement.predicate)

    # abort early if the predicate similarity is too low
    if similarity < min_similarity_threshold:
        return None

    for head_term, goal_term in zip(head.terms, goal.statement.terms):
        head_term_resolution = resolve_term(head_term, scope, next_substitutions)
        goal_term_resolution = resolve_term(goal_term, goal.scope, next_substitutions)
        if isinstance(head_term_resolution, Variable):
            # fail unification if it requires rebinding an already bound variable
            if is_var_bound(head_term_resolution, scope, next_substitutions):
                return None
            target_value: Constant | tuple[int, Variable] = (
                goal_term_resolution
                if isinstance(goal_term_resolution, Constant)
                else (goal.scope, goal_term_resolution)
            )
            next_substitutions = set_var_binding(
                head_term_resolution, scope, target_value, next_substitutions
            )
        elif isinstance(goal_term_resolution, Variable):
            # fail unification if it requires rebinding an already bound variable
            if is_var_bound(goal_term_resolution, goal.scope, next_substitutions):
                return None
            next_substitutions = set_var_binding(
                goal_term_resolution,
                goal.scope,
                head_term_resolution,
                next_substitutions,
            )
        else:
            similarity = min(
                similarity,
                adjusted_similarity_func(head_term_resolution, goal_term_resolution),
            )
            # abort early if the predicate similarity is too low
            if similarity < min_similarity_threshold:
                return None

    return (next_substitutions, similarity)
