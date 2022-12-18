from __future__ import annotations
import re
from typing import Optional, cast

from tensor_theorem_prover.normalize.to_cnf import CNFDisjunction, CNFLiteral
from tensor_theorem_prover.prover.ProofContext import ProofContext
from tensor_theorem_prover.prover.ProofStep import ProofStep, SubstitutionsMap
from tensor_theorem_prover.similarity import SimilarityFunc
from tensor_theorem_prover.types import Atom, Term, Variable

from .unify import Unification, unify


def resolve(
    source: CNFDisjunction,
    target: CNFDisjunction,
    ctx: ProofContext,
    similarity_func: Optional[SimilarityFunc] = None,
    parent: Optional[ProofStep] = None,
) -> list[ProofStep]:
    """Resolve a source and target CNF disjunction

    Args:
        source: The source CNF disjunction.
        target: The target CNF disjunction.
        state: The current proof state.

    Returns:
        A list of proof states corresponding to each possible resolution.
    """
    next_steps = []
    source_literal = cast(CNFLiteral, source.head)
    for target_literal in target.literals:
        # we can only resolve literals with the opposite polarity
        if source_literal.polarity == target_literal.polarity:
            continue
        ctx.stats.attempted_unifications += 1
        unification = unify(
            source_literal.atom,
            target_literal.atom,
            ctx,
            similarity_func,
        )
        if unification:
            ctx.stats.successful_unifications += 1

            resolvent = _build_resolvent(
                source, target, source_literal, target_literal, unification
            )
            step = ProofStep(
                source=source,
                target=target,
                resolvent=resolvent,
                source_unification_literal=source_literal,
                target_unification_literal=target_literal,
                source_substitutions=unification.source_substitutions,
                target_substitutions=unification.target_substitutions,
                similarity=unification.similarity,
                # TODO: Make combining similarities customizable rather than always taking the minimum
                running_similarity=min(
                    unification.similarity, parent.running_similarity
                )
                if parent
                else unification.similarity,
                parent=parent,
                depth=parent.depth + 1 if parent else 0,
            )
            next_steps.append(step)
    return next_steps


def _build_resolvent(
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
    source_literals = [lit for lit in source.literals if lit is not source_literal]
    target_literals = [lit for lit in target.literals if lit is not target_literal]
    # find all variables in source and target that aren't being substituted to avoid overlapping names
    unused_source_vars = _find_unused_variables(
        source_literals, unification.source_substitutions
    )
    unused_target_vars = _find_unused_variables(
        target_literals, unification.target_substitutions
    )
    all_vars = (
        unused_source_vars
        | unused_target_vars
        | set(unification.source_substitutions.keys())
        | set(unification.target_substitutions.keys())
    )
    rename_vars_map = _find_non_overlapping_var_names(
        unused_source_vars, unused_target_vars, all_vars
    )
    target_literals = _rename_variables_in_literals(target_literals, rename_vars_map)
    updated_source_literals = _perform_substitution(
        source_literals, unification.source_substitutions
    )
    updated_target_literals = _perform_substitution(
        target_literals, unification.target_substitutions
    )
    resolvent_literals = updated_source_literals + updated_target_literals
    if len(resolvent_literals) == 0:
        resolvent = CNFDisjunction.empty()
    else:
        resolvent = CNFDisjunction.from_literals_list(resolvent_literals)
    return resolvent


def _find_unused_variables(
    literals: list[CNFLiteral], substitutions: SubstitutionsMap
) -> set[Variable]:
    """return a list of all variables in the literals that aren't being substituted"""
    unused_variables = set()
    for literal in literals:
        for term in literal.atom.terms:
            if isinstance(term, Variable) and term not in substitutions:
                unused_variables.add(term)
    return unused_variables


def _find_non_overlapping_var_names(
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


def _rename_variables_in_literals(
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


def _perform_substitution(
    literals: list[CNFLiteral], substitutions: SubstitutionsMap
) -> list[CNFLiteral]:
    new_literals = []
    for literal in literals:
        terms: list[Term] = []
        for term in literal.atom.terms:
            if isinstance(term, Variable) and term in substitutions:
                terms.append(substitutions[term])
            else:
                terms.append(term)
        new_atom = Atom(literal.atom.predicate, tuple(terms))
        new_literals.append(CNFLiteral(new_atom, literal.polarity))
    return new_literals
