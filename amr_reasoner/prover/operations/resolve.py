from __future__ import annotations
import re
from typing import Optional
from amr_reasoner.normalize.to_cnf import CNFDisjunction, CNFLiteral

from amr_reasoner.prover.types import ProofState, SubstitutionsMap
from amr_reasoner.similarity import SimilarityFunc
from amr_reasoner.types import Atom, Constant, Term, Variable

from .unify import Unification, unify


def resolve(
    source: CNFDisjunction,
    target: CNFDisjunction,
    state: ProofState,
    min_similarity_threshold: float = 0.5,
    similarity_func: Optional[SimilarityFunc] = None,
) -> list[ProofState]:
    """Resolve a source and target CNF disjunction

    Args:
        source: The source CNF disjunction.
        target: The target CNF disjunction.
        state: The current proof state.

    Returns:
        A list of proof states corresponding to each possible resolution.
    """
    states = []
    for source_literal in source.literals:
        for target_literal in target.literals:
            # we can only resolve literals with the opposite polarity
            if source_literal.polarity == target_literal.polarity:
                continue
            unification = unify(
                source_literal.atom,
                target_literal.atom,
                min_similarity_threshold,
                similarity_func,
            )
            if unification:
                resolvent = resolve_with_substitutions(
                    source, target, source_literal, target_literal, unification
                )
                new_state = ProofState(
                    state.knowledge,
                    source,
                    target,
                    resolvent,
                    unification.source_substitutions,
                    unification.target_substitutions,
                    state.depth + 1,
                    state.substitutions,
                    state,
                )
                states.append(new_state)
    return states


def resolve_with_substitutions(
    source: CNFDisjunction,
    target: CNFDisjunction,
    source_literal: CNFLiteral,
    target_literal: CNFLiteral,
    unification: Unification,
) -> CNFDisjunction:
    """Resolve a source and target CNF disjunction with substitutions

    Args:
        source: The source CNF disjunction.
        target: The target CNF disjunction.
        source_literal: The source CNF literal.
        target_literal: The target CNF literal.
        unification: The unification between the source and target literals.

    Returns:
        A proof state corresponding to the resolution.
    """
    # these are the literals that will be combined into the resolved disjunction
    source_literals = [lit for lit in source.literals if lit != source_literal]
    target_literals = [lit for lit in target.literals if lit != target_literal]
    # find all variables in source and target that aren't being substituted to avoid overlapping names
    unused_source_vars = find_unused_variables(
        source_literals, unification.source_substitutions
    )
    unused_target_vars = find_unused_variables(
        target_literals, unification.target_substitutions
    )
    all_vars = (
        unused_source_vars
        | unused_target_vars
        | set(unification.source_substitutions.keys())
        | set(unification.target_substitutions.keys())
    )
    rename_vars_map = find_non_overlapping_var_names(
        unused_source_vars, unused_target_vars, all_vars
    )
    target_literals = rename_variables_in_literals(target_literals, rename_vars_map)
    updated_source_literals = perform_substitution(
        source_literals, unification.source_substitutions
    )
    updated_target_literals = perform_substitution(
        target_literals, unification.target_substitutions
    )
    resolvent_literals = updated_source_literals + updated_target_literals
    resolvent = CNFDisjunction(frozenset(resolvent_literals))
    return resolvent


def find_unused_variables(
    literals: list[CNFLiteral], substitutions: SubstitutionsMap
) -> set[Variable]:
    """return a list of all variables in the literals that aren't being substituted"""
    unused_variables = set()
    for literal in literals:
        for term in literal.atom.terms:
            if isinstance(term, Variable) and term not in substitutions:
                unused_variables.add(term)
    return unused_variables


def find_non_overlapping_var_names(
    source_vars: set[Variable], target_vars: set[Variable], all_variables: set[Variable]
) -> dict[Variable, Variable]:
    """Find new unused vars names for all overlapping variables between source and target"""
    # make a copy to avoid modifying the original
    used_vars = set(all_variables)
    overlapping_variables = source_vars.intersection(target_vars)
    renamed_vars = {}
    for var in overlapping_variables:
        base_name = re.sub(r"_\d+$", "", var.name)
        counter = 0
        while True:
            counter += 1
            new_var = Variable(f"{base_name}_{counter}")
            if new_var not in used_vars:
                used_vars.add(new_var)
                renamed_vars[var] = new_var
                break
    return renamed_vars


def rename_variables_in_literals(
    literals: list[CNFLiteral], rename_map: dict[Variable, Variable]
) -> list[CNFLiteral]:
    new_literals = []
    for literal in literals:
        terms: list[Term] = []
        for term in literal.atom.terms:
            if isinstance(term, Variable) and term in rename_map:
                terms.append(rename_map[term])
            else:
                terms.append(term)
        new_atom = Atom(literal.atom.predicate, tuple(terms))
        new_literals.append(CNFLiteral(new_atom, literal.polarity))
    return new_literals


def perform_substitution(
    literals: list[CNFLiteral], substitutions: SubstitutionsMap
) -> list[CNFLiteral]:
    new_literals = []
    for literal in literals:
        terms: list[Term] = []
        for term in literal.atom.terms:
            if isinstance(term, Variable) and term in substitutions:
                substitution = substitutions[term]
                new_term: Term = (
                    substitution
                    if isinstance(substitution, Constant)
                    else substitution[1]
                )
                terms.append(new_term)
            else:
                terms.append(term)
        new_atom = Atom(literal.atom.predicate, tuple(terms))
        new_literals.append(CNFLiteral(new_atom, literal.polarity))
    return new_literals