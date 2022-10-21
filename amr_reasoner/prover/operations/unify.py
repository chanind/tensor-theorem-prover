from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

from amr_reasoner.prover.types import SubstitutionsMap
from amr_reasoner.similarity import SimilarityFunc, symbol_compare
from amr_reasoner.types import Atom, Constant, Variable, BoundFunction, Term


@dataclass
class Unification:
    source_substitutions: SubstitutionsMap = field(default_factory=dict)
    target_substitutions: SubstitutionsMap = field(default_factory=dict)
    similarity: float = 1.0


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

    return _unify_terms(
        source.terms,
        target.terms,
        similarity,
        adjusted_similarity_func,
        min_similarity_threshold,
    )


def _unify_terms(
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

    binding_groups = find_binding_groups(source_bindings, target_bindings)
    return _resolve_bindings(
        binding_groups=binding_groups,
        similarity=cur_similarity,
        similarity_func=similarity_func,
        min_similarity_threshold=min_similarity_threshold,
    )


@dataclass
class BindingGroup:
    """
    Helper Class to handle the grouping of variables and constants that are bound to each other during unification
    """

    source_variables: set[Variable] = field(default_factory=set)
    target_variables: set[Variable] = field(default_factory=set)
    constants: set[Constant] = field(default_factory=set)
    # hack to make this deterministic, since otherwise we'll pick elements at random from the sets
    first_constant: Optional[Constant] = None
    first_source_variable: Variable | None = None
    first_target_variable: Variable | None = None

    def add_variable(self, variable: Variable, is_source_var: bool) -> None:
        if is_source_var:
            self.source_variables.add(variable)
            if self.first_source_variable is None:
                self.first_source_variable = variable
        else:
            self.target_variables.add(variable)
            if self.first_target_variable is None:
                self.first_target_variable = variable

    def has_variable(self, variable: Variable, is_source_var: bool) -> bool:
        if is_source_var:
            return variable in self.source_variables
        else:
            return variable in self.target_variables

    def add_constant(self, constant: Constant) -> None:
        self.constants.add(constant)
        if self.first_constant is None:
            self.first_constant = constant


def find_binding_groups(
    source_bindings: dict[Variable, list[Variable | Constant]],
    target_bindings: dict[Variable, list[Variable | Constant]],
) -> list[BindingGroup]:
    """
    Find all groups of variables/constants that are bound together
    """
    binding_groups = []
    # keep a set of tuples of <is_source_var, variable> to keep track of which variables we still need to group
    remaining_variables = set(map(lambda v: (True, v), source_bindings.keys())) | set(
        map(lambda v: (False, v), target_bindings.keys())
    )

    while len(remaining_variables) > 0:
        is_source_var, cur_var = remaining_variables.pop()
        binding_group = BindingGroup()
        _populate_binding_group(
            binding_group,
            cur_var,
            is_source_var,
            source_bindings,
            target_bindings,
        )
        binding_groups.append(binding_group)
        remaining_variables -= set(
            map(lambda v: (True, v), binding_group.source_variables)
        ) | set(map(lambda v: (False, v), binding_group.target_variables))

    return binding_groups


def _populate_binding_group(
    binding_group: BindingGroup,
    cur_var: Variable,
    is_source_var: bool,
    source_bindings: dict[Variable, list[Variable | Constant]],
    target_bindings: dict[Variable, list[Variable | Constant]],
) -> None:
    """Recursively populate a binding group in-place with all variables/constants that are bound together"""
    binding_group.add_variable(cur_var, is_source_var)
    cur_bindings = (
        source_bindings[cur_var] if is_source_var else target_bindings[cur_var]
    )
    for binding in cur_bindings:
        if isinstance(binding, Variable):
            if not binding_group.has_variable(binding, not is_source_var):
                _populate_binding_group(
                    binding_group,
                    binding,
                    not is_source_var,
                    source_bindings,
                    target_bindings,
                )
        else:
            binding_group.add_constant(binding)


# TODO: rewrite this method to properly handle binding labels and recursive var substitutions
def _resolve_bindings(
    binding_groups: Iterable[BindingGroup],
    similarity: float,
    similarity_func: SimilarityFunc,
    min_similarity_threshold: float,
) -> Unification | None:
    source_substitutions: SubstitutionsMap = {}
    target_substitutions: SubstitutionsMap = {}
    cur_similarity = similarity
    for binding_group in binding_groups:
        # note which var we choose to assign this group to, so we don't accidentally try to sub a var with itself
        skip_source_var: Variable | None = None
        skip_target_var: Variable | None = None
        binding: Constant | Variable
        if binding_group.first_constant:
            binding = binding_group.first_constant
            cur_similarity = _resolve_constant_similarity(
                binding_group.constants, similarity_func
            )
            if cur_similarity < min_similarity_threshold:
                return None
        elif binding_group.first_source_variable:
            binding = binding_group.first_source_variable
            skip_source_var = binding_group.first_source_variable
        elif binding_group.first_target_variable:
            binding = binding_group.first_target_variable
            skip_target_var = binding_group.first_target_variable
        else:
            raise ValueError("Binding group has no variables/constants")
        for source_var in binding_group.source_variables:
            if source_var is not skip_source_var:
                source_substitutions[source_var] = binding
        for target_var in binding_group.target_variables:
            if target_var is not skip_target_var:
                target_substitutions[target_var] = binding

    return Unification(
        source_substitutions=source_substitutions,
        target_substitutions=target_substitutions,
        similarity=cur_similarity,
    )


def _resolve_constant_similarity(
    constants: set[Constant],
    similarity_func: SimilarityFunc,
) -> float:
    if len(constants) <= 1:
        return 1.0
    # TODO: this is inneficient for lots of constants, think of a better solution
    # Need to check both direction similarity since there's no inherent directionality here between constants here
    # maybe we can add a separate similarity function for constants that's bidirectional?
    return min(
        similarity_func(constant1, constant2)
        for constant1 in constants
        for constant2 in constants
        if constant1 != constant2
    )
