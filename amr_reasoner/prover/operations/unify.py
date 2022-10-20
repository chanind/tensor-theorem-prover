from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, cast
from immutables import Map

from amr_reasoner.prover.types import (
    SOURCE_BINDING_LABEL,
    TARGET_BINDING_LABEL,
    BindingLabel,
    SubstitutionsMap,
)
from amr_reasoner.similarity import SimilarityFunc, symbol_compare
from amr_reasoner.types import Atom, Constant, Variable, BoundFunction, Term


@dataclass
class Unification:
    similarity: float
    source_substitutions: SubstitutionsMap = Map()
    target_substitutions: SubstitutionsMap = Map()


def unify(
    source: Atom,
    target: Atom,
    min_similarity_threshold: float = 0.5,
    similarity_func: Optional[SimilarityFunc] = None,
) -> Unification | None:
    """
    Fuzzy-optional implementation of unify
    If no similarity_func is provided, or if either atom lacks a embedding,
    then it will do an exact match on the symbols themselves

    Based on unification module from "End-to-End Differentiable Proving" by Rocktäschel et al.
    https://arxiv.org/abs/1705.11040

    Returns a tuple with new substitutions and new similariy if successful or None if the unification fails
    """
    if len(source.terms) != len(target.terms):
        return None

    # if there is no comparison function provided, just use symbol compare (non-fuzzy comparisons)
    adjusted_similarity_func = similarity_func or symbol_compare
    similarity = adjusted_similarity_func(source.predicate, target.predicate)

    # abort early if the predicate similarity is too low
    if similarity < min_similarity_threshold:
        return None

    return unify_terms(
        source.terms,
        target.terms,
        similarity,
        adjusted_similarity_func,
        min_similarity_threshold,
    )


def unify_terms(
    source_terms: Iterable[Term],
    target_terms: Iterable[Term],
    similarity: float,
    similarity_func: SimilarityFunc,
    min_similarity_threshold: float,
) -> Unification | None:
    cur_similarity = similarity

    source_bindings: dict[Variable, list[Variable | Constant]] = defaultdict(list)
    target_bindings: dict[Variable, list[Variable | Constant]] = defaultdict(list)

    for source_term, target_term in zip(source_terms, target_terms):
        # TODO: implement bound function unification
        if isinstance(source_term, BoundFunction) or isinstance(
            target_term, BoundFunction
        ):
            raise NotImplementedError("BoundFunction unification not implemented")
        if isinstance(source_term, Variable):
            source_bindings[source_term].append(target_term)
        if isinstance(target_term, Variable):
            target_bindings[target_term].append(source_term)

        if isinstance(source_term, Constant) and isinstance(target_term, Constant):
            cur_similarity = min(
                cur_similarity,
                similarity_func(source_term, target_term),
            )
            # abort early if the predicate similarity is too low
            if cur_similarity < min_similarity_threshold:
                return None

    return resolve_bindings(
        source_bindings=source_bindings,
        target_bindings=target_bindings,
        similarity=cur_similarity,
        similarity_func=similarity_func,
        min_similarity_threshold=min_similarity_threshold,
    )


# TODO: rewrite this method to properly handle binding labels and recursive var substitutions
def resolve_bindings(
    source_bindings: dict[Variable, list[Variable | Constant]],
    target_bindings: dict[Variable, list[Variable | Constant]],
    similarity: float,
    similarity_func: SimilarityFunc,
    min_similarity_threshold: float,
) -> Unification | None:
    source_substitutions: dict[Variable, Variable | Constant] = {}
    target_substitutions: dict[Variable, Variable | Constant] = {}
    cur_similarity = similarity

    # first, bind all constants to source variables and all linked targets
    for source_var, bindings in source_bindings.items():
        constants = [binding for binding in bindings if isinstance(binding, Constant)]
        linked_target_variables = [
            binding for binding in bindings if isinstance(binding, Variable)
        ]
        existing_binding = source_substitutions.get(source_var)
        if isinstance(existing_binding, Constant):
            constants.append(existing_binding)
        if len(constants) > 0:
            constant = constants[-1]
            cur_similarity = resolve_constant_similarity(constants, similarity_func)
            if cur_similarity < min_similarity_threshold:
                return None
            source_substitutions[source_var] = constant
            for target_var in linked_target_variables:
                existing_target_var_binding = target_substitutions.get(target_var)
                if isinstance(existing_target_var_binding, Constant):
                    cur_similarity = resolve_constant_similarity(
                        [existing_target_var_binding, constant], similarity_func
                    )
                    if cur_similarity < min_similarity_threshold:
                        return None
                target_substitutions[target_var] = constant
    # now, do the reverse for target to source
    for target_var, bindings in target_bindings.items():
        constants = [binding for binding in bindings if isinstance(binding, Constant)]
        linked_source_variables = [
            binding for binding in bindings if isinstance(binding, Variable)
        ]
        existing_binding = target_substitutions.get(target_var)
        if isinstance(existing_binding, Constant):
            constants.append(existing_binding)
        if len(constants) > 0:
            constant = constants[-1]
            cur_similarity = resolve_constant_similarity(constants, similarity_func)
            if cur_similarity < min_similarity_threshold:
                return None
            target_substitutions[target_var] = constant
            for source_var in linked_source_variables:
                existing_source_var_binding = source_substitutions.get(source_var)
                if isinstance(existing_source_var_binding, Constant):
                    cur_similarity = resolve_constant_similarity(
                        [existing_source_var_binding, constant], similarity_func
                    )
                    if cur_similarity < min_similarity_threshold:
                        return None
                else:
                    source_substitutions[source_var] = constant
    # now bind any remaining variables to each other
    unmapped_source_vars = set(source_bindings.keys()) - set(
        source_substitutions.keys()
    )
    unmapped_target_vars = set(target_bindings.keys()) - set(
        target_substitutions.keys()
    )
    for source_var in unmapped_source_vars:
        # these have to all be variables, else it would have been bound already
        target_vars = cast(List[Variable], source_bindings[source_var])
        existing_binding = target_substitutions.get(source_var)
        for target_var in target_vars:
            if existing_binding == target_var:
                continue
            if target_var in target_substitutions:
                source_substitutions[source_var] = target_substitutions[target_var]
            else:
                target_substitutions[target_var] = source_var
    for target_var in unmapped_target_vars:
        source_vars = cast(List[Variable], target_bindings[target_var])
        existing_binding = target_substitutions.get(target_var)
        for source_var in source_vars:
            if existing_binding == source_var:
                continue
            if source_var in source_substitutions:
                target_substitutions[target_var] = source_substitutions[source_var]
            else:
                source_substitutions[source_var] = target_var

    # TODO: handle binding labels properly and delete this hack
    def hacky_add_binding_labels(
        substitutions: dict[Variable, Variable | Constant], label: BindingLabel
    ) -> SubstitutionsMap:
        labeled_bindings: dict[Variable, tuple[BindingLabel, Variable] | Constant] = {}
        for var, binding in substitutions.items():
            if isinstance(binding, Constant):
                labeled_bindings[var] = binding
            else:
                labeled_bindings[var] = (label, binding)
        return Map(labeled_bindings)

    return Unification(
        source_substitutions=hacky_add_binding_labels(
            source_substitutions, TARGET_BINDING_LABEL
        ),
        target_substitutions=hacky_add_binding_labels(
            target_substitutions, SOURCE_BINDING_LABEL
        ),
        similarity=cur_similarity,
    )


def resolve_constant_similarity(
    constants: Sequence[Constant],
    similarity_func: SimilarityFunc,
) -> float:
    if len(constants) <= 1:
        return 1.0
    # TODO: this is inneficient for lots of constants, think of a better solution
    # Need to check both direction similarity since there's no inherent directionality here between constants here
    return min(
        similarity_func(constants[i], constants[j])
        for i in range(len(constants))
        for j in range(len(constants))
        if j != i
    )
