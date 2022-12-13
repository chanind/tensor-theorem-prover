from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Tuple
from typing_extensions import Literal
from tensor_theorem_prover.prover.ProofContext import ProofContext

from tensor_theorem_prover.prover.ProofStep import SubstitutionsMap
from tensor_theorem_prover.similarity import SimilarityFunc, symbol_compare
from tensor_theorem_prover.types import Atom, Constant, Variable, BoundFunction, Term


@dataclass
class Unification:
    source_substitutions: SubstitutionsMap = field(default_factory=dict)
    target_substitutions: SubstitutionsMap = field(default_factory=dict)
    similarity: float = 1.0


def unify(
    source: Atom,
    target: Atom,
    ctx: ProofContext,
    similarity_func: Optional[SimilarityFunc] = None,
) -> Unification | None:
    """
    Fuzzy-optional implementation of unify
    If no similarity_func is provided, or if either atom lacks a embedding,
    then it will do an exact match on the symbols themselves

    Returns a tuple with new substitutions and new similariy if successful or None if the unification fails
    """
    if len(source.terms) != len(target.terms):
        return None

    # if there is no comparison function provided, just use symbol compare (non-fuzzy comparisons)
    adjusted_similarity_func = similarity_func or symbol_compare
    similarity = adjusted_similarity_func(source.predicate, target.predicate)
    ctx.stats.similarity_comparisons += 1

    # abort early if the predicate similarity is too low
    if similarity <= ctx.min_similarity_threshold:
        return None

    return _unify_terms(
        source.terms, target.terms, similarity, adjusted_similarity_func, ctx
    )


BindingLabel = Literal["source", "target"]
LabeledTerm = Tuple[BindingLabel, Term]

SubstitutionSet = Dict[Tuple[BindingLabel, Variable], LabeledTerm]


def _unify_terms(
    source_terms: Iterable[Term],
    target_terms: Iterable[Term],
    similarity: float,
    similarity_func: SimilarityFunc,
    ctx: ProofContext,
) -> Unification | None:
    """
    Unification with optional vector similarity, based on Robinson's 1965 algorithm, as described in:
    "Comparing unification algorithms in first-order theorem proving", Hoder et al. 2009
    https://www.cs.man.ac.uk/~hoderk/ubench/unification_full.pdf
    """
    cur_similarity = similarity
    substitutions: SubstitutionSet = {}
    for source_term, target_term in zip(source_terms, target_terms):
        result = _unify_term_pair(
            source_term,
            target_term,
            substitutions,
            cur_similarity,
            similarity_func,
            ctx,
        )
        if result is None:
            return None
        substitutions, cur_similarity = result

    source_substitutions: SubstitutionsMap = {}
    target_substitutions: SubstitutionsMap = {}
    for labeled_var in substitutions.keys():
        # need to recreate this and explicitly tell MyPy that it's a LabeledTerm because it can't infer it somehow
        label, var = labeled_var
        if label == "source":
            source_substitutions[var] = _resolve_labeled_term(
                labeled_var, substitutions
            )[1]
        else:
            target_substitutions[var] = _resolve_labeled_term(
                labeled_var, substitutions
            )[1]
    return Unification(source_substitutions, target_substitutions, cur_similarity)


def _resolve_labeled_term(
    labeled_term: LabeledTerm, substitutions: SubstitutionSet
) -> LabeledTerm:
    """
    Resolve a labeled term by recursively following substitutions, part of Robinson's 1965 algorithm
    """
    label, term = labeled_term
    if isinstance(term, Variable) and labeled_term in substitutions:
        return _resolve_labeled_term(substitutions[(label, term)], substitutions)
    return labeled_term


def _check_var_occurrence(
    var: Variable, term: Term, substitutions: SubstitutionSet, is_source_var: bool
) -> bool:
    """
    Recursively check if variable occurs in a term, part of Robinson's 1965 algorithm
    """
    var_label: BindingLabel = "source" if is_source_var else "target"
    labeled_var = (var_label, var)
    # term is opposite label of var
    term_label: BindingLabel = "target" if is_source_var else "source"
    term_stack: list[LabeledTerm] = [(term_label, term)]
    while term_stack:
        cur_labeled_term = term_stack.pop()
        cur_labeled_term = _resolve_labeled_term(cur_labeled_term, substitutions)
        cur_label, cur_term = cur_labeled_term
        comparison_vars: list[tuple[BindingLabel, Variable]] = []
        if isinstance(cur_term, Variable):
            comparison_vars.append((cur_label, cur_term))
        elif isinstance(cur_term, BoundFunction):
            for sub_term in cur_term.terms:
                if isinstance(sub_term, Variable):
                    comparison_vars.append((cur_label, sub_term))
        for comparison_var in comparison_vars:
            if comparison_var == labeled_var:
                return False
            elif comparison_var in substitutions:
                term_stack.append(substitutions[comparison_var])
    return True


def _unify_term_pair(
    source_term: Term,
    target_term: Term,
    substitutions: SubstitutionSet,
    similarity: float,
    similarity_func: SimilarityFunc,
    ctx: ProofContext,
) -> tuple[SubstitutionSet, float] | None:
    """
    Check if a pair of terms can be unified, part of Robinson's 1965 algorithm
    """
    pairs_stack: list[tuple[LabeledTerm, LabeledTerm]] = [
        (("source", source_term), ("target", target_term))
    ]
    cur_similarity = similarity
    while pairs_stack:
        cur_labeled_source_term, cur_labeled_target_term = pairs_stack.pop()
        cur_labeled_source_term = _resolve_labeled_term(
            cur_labeled_source_term, substitutions
        )
        cur_source_label, cur_source_term = cur_labeled_source_term
        cur_labeled_target_term = _resolve_labeled_term(
            cur_labeled_target_term, substitutions
        )
        cur_target_label, cur_target_term = cur_labeled_target_term
        if isinstance(cur_source_term, Constant) and isinstance(
            cur_target_term, Constant
        ):
            # if these are identical objects, no need to compare them, just continue on
            if cur_source_term is not cur_target_term:
                cur_similarity = min(
                    cur_similarity,
                    # TODO: should we add a separate similarity func for constants which is bidirectional?
                    similarity_func(cur_source_term, cur_target_term),
                )
                ctx.stats.similarity_comparisons += 1
                if cur_similarity <= ctx.min_similarity_threshold:
                    return None
        elif isinstance(cur_source_term, Variable):
            if isinstance(cur_target_term, Variable):
                # if both are variables, replace the target with the source
                substitutions[
                    (cur_target_label, cur_target_term)
                ] = cur_labeled_source_term
            elif _check_var_occurrence(
                cur_source_term,
                cur_target_term,
                substitutions,
                cur_source_label == "source",
            ):
                substitutions[
                    (cur_source_label, cur_source_term)
                ] = cur_labeled_target_term
            else:
                return None
        elif isinstance(cur_target_term, Variable):
            if _check_var_occurrence(
                cur_target_term,
                cur_source_term,
                substitutions,
                cur_target_label == "source",
            ):
                substitutions[
                    (cur_target_label, cur_target_term)
                ] = cur_labeled_source_term
            else:
                return None
        elif isinstance(cur_source_term, BoundFunction) and isinstance(
            cur_target_term, BoundFunction
        ):
            if cur_source_term.function != cur_target_term.function:
                return None
            if len(cur_source_term.terms) != len(cur_target_term.terms):
                return None
            for source_sub_term, target_sub_term in zip(
                cur_source_term.terms, cur_target_term.terms
            ):
                pairs_stack.append(
                    (
                        (cur_source_label, source_sub_term),
                        (cur_target_label, target_sub_term),
                    )
                )
    return substitutions, cur_similarity
