// from tensor_theorem_prover.normalize.to_cnf import CNFDisjunction, CNFLiteral
// from tensor_theorem_prover.prover.ProofContext import ProofContext
// from tensor_theorem_prover.prover.ProofStep import ProofStep, SubstitutionsMap
// from tensor_theorem_prover.similarity import SimilarityFunc
// from tensor_theorem_prover.types import Atom, Term, Variable

// from .unify import Unification, unify

// def resolve(
//     source: CNFDisjunction,
//     target: CNFDisjunction,
//     ctx: ProofContext,
//     similarity_func: Optional[SimilarityFunc] = None,
//     parent: Optional[ProofStep] = None,
// ) -> list[ProofStep]:
//     """Resolve a source and target CNF disjunction

//     Args:
//         source: The source CNF disjunction.
//         target: The target CNF disjunction.
//         state: The current proof state.

//     Returns:
//         A list of proof states corresponding to each possible resolution.
//     """
//     next_steps = []
//     source_literal = cast(CNFLiteral, source.head)
//     for target_literal in target.literals:
//         # we can only resolve literals with the opposite polarity
//         if source_literal.polarity == target_literal.polarity:
//             continue
//         ctx.stats.attempted_unifications += 1
//         unification = unify(
//             source_literal.atom,
//             target_literal.atom,
//             ctx,
//             similarity_func,
//         )
//         if unification:
//             ctx.stats.successful_unifications += 1

//             resolvent = _build_resolvent(
//                 source, target, source_literal, target_literal, unification
//             )
//             step = ProofStep(
//                 source=source,
//                 target=target,
//                 resolvent=resolvent,
//                 source_unification_literal=source_literal,
//                 target_unification_literal=target_literal,
//                 source_substitutions=unification.source_substitutions,
//                 target_substitutions=unification.target_substitutions,
//                 similarity=unification.similarity,
//                 # TODO: Make combining similarities customizable rather than always taking the minimum
//                 running_similarity=min(
//                     unification.similarity, parent.running_similarity
//                 )
//                 if parent
//                 else unification.similarity,
//                 parent=parent,
//                 depth=parent.depth + 1 if parent else 0,
//             )
//             next_steps.append(step)
//     return next_steps

use regex::Regex;
use std::collections::{BTreeSet, HashMap};

use crate::{
    prover::{proof_step::ProofStepNode, ProofContext, ProofStep, SubstitutionsMap},
    types::{Atom, CNFDisjunction, CNFLiteral, Term, Variable},
    util::PyArcItem,
};

use super::{unify, Unification};

/// Resolve a source and target CNF disjunction with substitutions
///    Args:
///        source: The source CNF disjunction.
///        target: The target CNF disjunction.
///        state: The current proof state.

///    Returns:
///        A list of proof states corresponding to each possible resolution.
pub fn resolve(
    source: &PyArcItem<CNFDisjunction>,
    target: &PyArcItem<CNFDisjunction>,
    ctx: &mut ProofContext,
    parent_node: Option<&ProofStepNode>,
) -> Vec<ProofStepNode> {
    let mut next_steps = Vec::new();
    let source_literal = source.item.literals.first().unwrap();
    for target_literal in target.item.literals.iter() {
        // we can only resolve literals with the opposite polarity
        if source_literal.item.polarity == target_literal.item.polarity {
            continue;
        }
        ctx.stats.attempted_unifications += 1;
        let unification = unify(&source_literal.item.atom, &target_literal.item.atom, ctx);
        if let Some(unification) = unification {
            ctx.stats.successful_unifications += 1;

            let resolvent = build_resolvent(
                source,
                target,
                &source_literal,
                &target_literal,
                &unification,
            );
            let running_similarity = match parent_node {
                Some(parent) => unification.similarity.min(parent.inner.running_similarity),
                None => unification.similarity,
            };
            let depth = match parent_node {
                Some(parent) => parent.inner.depth + 1,
                None => 0,
            };
            let new_parent: Option<ProofStepNode> = match parent_node {
                Some(parent) => Some(parent.clone()),
                None => None,
            };
            let step = ProofStepNode::new(ProofStep::new(
                source.clone(),
                target.clone(),
                source_literal.clone(),
                target_literal.clone(),
                unification.source_substitutions,
                unification.target_substitutions,
                resolvent,
                unification.similarity,
                running_similarity,
                depth,
                new_parent,
            ));
            next_steps.push(step);
        }
    }
    next_steps
}

// def _build_resolvent(
//     source: CNFDisjunction,
//     target: CNFDisjunction,
//     source_literal: CNFLiteral,
//     target_literal: CNFLiteral,
//     unification: Unification,
// ) -> CNFDisjunction:
//     """Resolve a source and target CNF disjunction with substitutions

//     Args:
//         source: The source CNF disjunction.
//         target: The target CNF disjunction.
//         source_literal: The source CNF literal.
//         target_literal: The target CNF literal.
//         unification: The unification between the source and target literals.

//     Returns:
//         A proof state corresponding to the resolution.
//     """
//     # these are the literals that will be combined into the resolved disjunction
//     source_literals = [lit for lit in source.literals if lit is not source_literal]
//     target_literals = [lit for lit in target.literals if lit is not target_literal]
//     # find all variables in source and target that aren't being substituted to avoid overlapping names
//     unused_source_vars = _find_unused_variables(
//         source_literals, unification.source_substitutions
//     )
//     unused_target_vars = _find_unused_variables(
//         target_literals, unification.target_substitutions
//     )
//     all_vars = (
//         unused_source_vars
//         | unused_target_vars
//         | set(unification.source_substitutions.keys())
//         | set(unification.target_substitutions.keys())
//     )
//     rename_vars_map = _find_non_overlapping_var_names(
//         unused_source_vars, unused_target_vars, all_vars
//     )
//     target_literals = _rename_variables_in_literals(target_literals, rename_vars_map)
//     updated_source_literals = _perform_substitution(
//         source_literals, unification.source_substitutions
//     )
//     updated_target_literals = _perform_substitution(
//         target_literals, unification.target_substitutions
//     )
//     resolvent_literals = updated_source_literals + updated_target_literals
//     if len(resolvent_literals) == 0:
//         resolvent = CNFDisjunction.empty()
//     else:
//         resolvent = CNFDisjunction.from_literals_list(resolvent_literals)
//     return resolvent

/// Resolve a source and target CNF disjunction with substitutions
///    Args:
///        source: The source CNF disjunction.
///        target: The target CNF disjunction.
///        source_literal: The source CNF literal.
///        target_literal: The target CNF literal.
///        unification: The unification between the source and target literals.

///    Returns:
///        A proof state corresponding to the resolution
fn build_resolvent(
    source: &PyArcItem<CNFDisjunction>,
    target: &PyArcItem<CNFDisjunction>,
    source_literal: &PyArcItem<CNFLiteral>,
    target_literal: &PyArcItem<CNFLiteral>,
    unification: &Unification,
) -> PyArcItem<CNFDisjunction> {
    // these are the literals that will be combined into the resolved disjunction
    let mut source_literals = source.item.literals.clone();
    assert!(
        source_literals.remove(source_literal),
        "source literal not found in source disjunction"
    );
    let mut target_literals = target.item.literals.clone();
    assert!(
        target_literals.remove(target_literal),
        "target literal not found in target disjunction"
    );
    // find all variables in source and target that aren't being substituted to avoid overlapping names
    let unused_source_vars =
        find_unused_variables(&source_literals, &unification.source_substitutions);
    let unused_target_vars =
        find_unused_variables(&target_literals, &unification.target_substitutions);
    let all_vars = unused_source_vars
        .union(&unused_target_vars)
        .chain(unification.source_substitutions.keys())
        .chain(unification.target_substitutions.keys())
        .cloned()
        .collect::<BTreeSet<_>>();
    let rename_vars_map =
        find_non_overlapping_var_names(&unused_source_vars, &unused_target_vars, &all_vars);
    let target_literals = rename_variables_in_literals(&target_literals, &rename_vars_map);
    let updated_source_literals =
        perform_substitution(&source_literals, &unification.source_substitutions);
    let updated_target_literals =
        perform_substitution(&target_literals, &unification.target_substitutions);
    let resolvent_literals = updated_source_literals
        .union(&updated_target_literals)
        .cloned()
        .collect::<BTreeSet<_>>();
    if resolvent_literals.is_empty() {
        PyArcItem::new(CNFDisjunction::new(BTreeSet::new()))
    } else {
        PyArcItem::new(CNFDisjunction::new(resolvent_literals))
    }
}

// def _find_unused_variables(
//     literals: list[CNFLiteral], substitutions: SubstitutionsMap
// ) -> set[Variable]:
//     """return a list of all variables in the literals that aren't being substituted"""
//     unused_variables = set()
//     for literal in literals:
//         for term in literal.atom.terms:
//             if isinstance(term, Variable) and term not in substitutions:
//                 unused_variables.add(term)
//     return unused_variables

/// return a list of all variables in the literals that aren't being substituted
fn find_unused_variables(
    literals: &BTreeSet<PyArcItem<CNFLiteral>>,
    substitutions: &SubstitutionsMap,
) -> BTreeSet<Variable> {
    let mut unused_variables = BTreeSet::new();
    for literal in literals {
        for term in &literal.item.atom.terms {
            if let Term::Variable(var) = term {
                if !substitutions.contains_key(var) {
                    unused_variables.insert(var.clone());
                }
            }
        }
    }
    unused_variables
}

// def _find_non_overlapping_var_names(
//     source_vars: set[Variable], target_vars: set[Variable], all_variables: set[Variable]
// ) -> dict[Variable, Variable]:
//     """Find new unused vars names for all overlapping variables between source and target"""
//     # make a copy to avoid modifying the original
//     used_vars = set(all_variables)
//     overlapping_variables = source_vars.intersection(target_vars)
//     renamed_vars = {}
//     for var in overlapping_variables:
//         base_name = re.sub(r"_\d+$", "", var.name)
//         counter = 0
//         while True:
//             counter += 1
//             new_var = Variable(f"{base_name}_{counter}")
//             if new_var not in used_vars:
//                 used_vars.add(new_var)
//                 renamed_vars[var] = new_var
//                 break
//     return renamed_vars

/// Find new unused vars names for all overlapping variables between source and target
fn find_non_overlapping_var_names(
    source_vars: &BTreeSet<Variable>,
    target_vars: &BTreeSet<Variable>,
    all_variables: &BTreeSet<Variable>,
) -> HashMap<Variable, Variable> {
    let mut used_vars = all_variables.clone();
    let overlapping_variables = source_vars.intersection(target_vars);
    let mut renamed_vars = HashMap::new();
    for var in overlapping_variables {
        let re = Regex::new(r"_\d+$").unwrap();
        let base_name = re.replace(&var.name, "");
        let mut counter = 0;
        loop {
            counter += 1;
            let new_var = Variable::new(&format!("{}_{}", base_name, counter));
            if !used_vars.contains(&new_var) {
                used_vars.insert(new_var.clone());
                renamed_vars.insert(var.clone(), new_var);
                break;
            }
        }
    }
    renamed_vars
}

// def _rename_variables_in_literals(
//     literals: list[CNFLiteral], rename_map: dict[Variable, Variable]
// ) -> list[CNFLiteral]:
//     new_literals = []
//     for literal in literals:
//         terms: list[Term] = []
//         for term in literal.atom.terms:
//             if isinstance(term, Variable) and term in rename_map:
//                 terms.append(rename_map[term])
//             else:
//                 terms.append(term)
//         new_atom = Atom(literal.atom.predicate, tuple(terms))
//         new_literals.append(CNFLiteral(new_atom, literal.polarity))
//     return new_literals

fn rename_variables_in_literals(
    literals: &BTreeSet<PyArcItem<CNFLiteral>>,
    rename_map: &HashMap<Variable, Variable>,
) -> BTreeSet<PyArcItem<CNFLiteral>> {
    let mut new_literals = BTreeSet::new();
    for literal in literals {
        // don't rebuild a literal from scratch if it doesn't need to be changed
        if literal_requires_var_rename(&literal, &rename_map) {
            let mut terms = Vec::new();
            for term in &literal.item.atom.terms {
                if let Term::Variable(var) = term {
                    if let Some(new_var) = rename_map.get(var) {
                        terms.push(Term::Variable(new_var.clone()));
                    } else {
                        terms.push(term.clone());
                    }
                } else {
                    terms.push(term.clone());
                }
            }
            let new_atom = Atom::new(literal.item.atom.predicate.clone(), terms);
            new_literals.insert(PyArcItem::new(CNFLiteral::new(
                new_atom,
                literal.item.polarity,
            )));
        } else {
            new_literals.insert(literal.clone());
        }
    }
    new_literals
}

fn literal_requires_var_rename(
    literal: &PyArcItem<CNFLiteral>,
    rename_map: &HashMap<Variable, Variable>,
) -> bool {
    for term in &literal.item.atom.terms {
        if let Term::Variable(var) = term {
            if rename_map.contains_key(var) {
                return true;
            }
        }
    }
    false
}

// def _perform_substitution(
//     literals: list[CNFLiteral], substitutions: SubstitutionsMap
// ) -> list[CNFLiteral]:
//     new_literals = []
//     for literal in literals:
//         terms: list[Term] = []
//         for term in literal.atom.terms:
//             if isinstance(term, Variable) and term in substitutions:
//                 terms.append(substitutions[term])
//             else:
//                 terms.append(term)
//         new_atom = Atom(literal.atom.predicate, tuple(terms))
//         new_literals.append(CNFLiteral(new_atom, literal.polarity))
//     return new_literals

fn perform_substitution(
    literals: &BTreeSet<PyArcItem<CNFLiteral>>,
    substitutions: &SubstitutionsMap,
) -> BTreeSet<PyArcItem<CNFLiteral>> {
    let mut new_literals = BTreeSet::new();
    for literal in literals {
        // don't rebuild a literal from scratch if it doesn't need to be changed
        if literal_requires_substitution(literal, substitutions) {
            let mut terms = Vec::new();
            for term in &literal.item.atom.terms {
                if let Term::Variable(var) = term {
                    if let Some(new_term) = substitutions.get(var) {
                        terms.push(new_term.clone());
                    } else {
                        terms.push(term.clone());
                    }
                } else {
                    terms.push(term.clone());
                }
            }
            let new_atom = Atom::new(literal.item.atom.predicate.clone(), terms);
            new_literals.insert(PyArcItem::new(CNFLiteral::new(
                new_atom,
                literal.item.polarity,
            )));
        } else {
            new_literals.insert(literal.clone());
        }
    }
    new_literals
}

fn literal_requires_substitution(
    literal: &PyArcItem<CNFLiteral>,
    substitutions: &SubstitutionsMap,
) -> bool {
    for term in &literal.item.atom.terms {
        if let Term::Variable(var) = term {
            if substitutions.contains_key(var) {
                return true;
            }
        }
    }
    false
}

#[cfg(test)]
mod test {

    use super::*;
    use crate::test_utils::test::{a, b, c, const1, const2, pred1, pred2, to_numpy_array, x, y, z};
    use crate::types::Predicate;
    use sugars::{btset, hmap};

    // def test_find_unused_variables() -> None:
    //     literals = [
    //         CNFLiteral(pred1(X, const1), True),
    //         CNFLiteral(pred2(Y), False),
    //     ]
    //     assert _find_unused_variables(literals, {}) == {X, Y}
    //     assert _find_unused_variables(literals, {Y: const1}) == {X}
    //     assert _find_unused_variables(literals, {Y: const1, X: const2}) == set()

    #[test]
    fn test_find_unused_variables() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(Atom::new(pred1(), vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(Atom::new(pred2(), vec![y().into()]), false)),
        };
        assert_eq!(
            find_unused_variables(&literals, &HashMap::new()),
            btset! { x(), y() }
        );
        assert_eq!(
            find_unused_variables(&literals, &hmap! { y() => const1().into() }),
            btset! { x() }
        );
        assert_eq!(
            find_unused_variables(
                &literals,
                &hmap! { y() => const1().into(), x() => const2().into() }
            ),
            btset! {}
        );
    }

    // def test_find_non_overlapping_var_names_leaves_vars_unchanged_if_no_overlaps() -> None:
    //     source_vars = {X, Y, Z}
    //     target_vars = {A, B, C}
    //     all_vars = source_vars | target_vars
    //     assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {}

    #[test]
    fn test_find_non_overlapping_var_names_leaves_vars_unchanged_if_no_overlaps() {
        let source_vars = btset! { x(), y(), z() };
        let target_vars = btset! { a(), b(), c() };
        let all_vars = source_vars.union(&target_vars).cloned().collect();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &all_vars),
            HashMap::new()
        );
    }

    // def test_find_non_overlapping_var_names_renames_vars_if_overlaps() -> None:
    //     source_vars = {X, Y, Z}
    //     target_vars = {A, B, X}
    //     all_vars = source_vars | target_vars
    //     assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {
    //         X: Variable("X_1")
    //     }

    #[test]
    fn test_find_non_overlapping_var_names_renames_vars_if_overlaps() {
        let source_vars = btset! { x(), y(), z() };
        let target_vars = btset! { a(), b(), x() };
        let all_vars = source_vars.union(&target_vars).cloned().collect();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &all_vars),
            hmap! { x() => Variable::new("X_1") }
        );
    }

    // def test_find_non_overlapping_keeps_iterating_var_names_until_a_non_bound_one_is_found() -> None:
    //     source_vars = {X, Y, Z}
    //     target_vars = {A, B, X}
    //     all_vars = source_vars | target_vars | {Variable("X_1"), Variable("X_2")}
    //     assert _find_non_overlapping_var_names(source_vars, target_vars, all_vars) == {
    //         X: Variable("X_3")
    //     }

    #[test]
    fn test_find_non_overlapping_keeps_iterating_var_names_until_a_non_bound_one_is_found() {
        let source_vars = btset! { x(), y(), z() };
        let target_vars = btset! { a(), b(), x() };
        let all_vars = source_vars
            .union(&target_vars)
            .cloned()
            .chain(btset! { Variable::new("X_1"), Variable::new("X_2") })
            .collect();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &all_vars),
            hmap! { x() => Variable::new("X_3") }
        );
    }

    // def test_rename_variables_in_literals() -> None:
    //     literals = [
    //         CNFLiteral(pred1(X, const1), True),
    //         CNFLiteral(pred2(Y), False),
    //     ]
    //     rename_vars_map = {X: Variable("X_1"), Y: Variable("Y_1")}
    //     renamed_literals = _rename_variables_in_literals(literals, rename_vars_map)
    //     assert renamed_literals == [
    //         CNFLiteral(pred1(Variable("X_1"), const1), True),
    //         CNFLiteral(pred2(Variable("Y_1")), False),
    //     ]

    #[test]
    fn test_rename_variables_in_literals() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![y().into()]), false)),
        };
        let rename_vars_map = hmap! { x() => Variable::new("X_1"), y() => Variable::new("Y_1") };
        let renamed_literals = rename_variables_in_literals(&literals, &rename_vars_map);
        assert_eq!(
            renamed_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![Variable::new("X_1").into(), const1().into()]), true)),
                PyArcItem::new(CNFLiteral::new(pred2().atom(vec![Variable::new("Y_1").into()]), false)),
            }
        );
    }

    // def test_perform_substitution_basic() -> None:
    //     literals = [
    //         CNFLiteral(pred1(X, const1), True),
    //         CNFLiteral(pred2(Y), False),
    //     ]
    //     substitutions: SubstitutionsMap = {X: const2, Y: const1}
    //     substituted_literals = _perform_substitution(literals, substitutions)
    //     assert substituted_literals == [
    //         CNFLiteral(pred1(const2, const1), True),
    //         CNFLiteral(pred2(const1), False),
    //     ]

    #[test]
    fn test_perform_substitution_basic() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![y().into()]), false)),
        };
        let substitutions: SubstitutionsMap =
            hmap! { x() => const2().into(), y() => const1().into() };
        let substituted_literals = perform_substitution(&literals, &substitutions);
        assert_eq!(
            substituted_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![const2().into(), const1().into()]), true)),
                PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const1().into()]), false)),
            }
        );
    }

    // def test_perform_substitution_with_repeated_vars() -> None:
    //     literals = [CNFLiteral(pred1(X, Y), True)]
    //     substitutions: SubstitutionsMap = {
    //         X: Y,
    //         Y: const2,
    //     }
    //     substituted_literals = _perform_substitution(literals, substitutions)
    //     assert substituted_literals == [
    //         CNFLiteral(pred1(Y, const2), True),
    //     ]

    #[test]
    fn test_perform_substitution_with_repeated_vars() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), y().into()]), true)),
        };
        let substitutions: SubstitutionsMap = hmap! { x() => y().into(), y() => const2().into() };
        let substituted_literals = perform_substitution(&literals, &substitutions);
        assert_eq!(
            substituted_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![y().into(), const2().into()]), true)),
            }
        );
    }

    // def test_build_resolvent() -> None:
    //     source_literal = CNFLiteral(pred2(Y, const2), False)
    //     target_literal = CNFLiteral(pred2(const1, X), True)

    //     source_literals = [
    //         source_literal,
    //         CNFLiteral(pred1(Y, const1), True),
    //     ]
    //     source_disjunction = CNFDisjunction.from_literals_list(source_literals)
    //     target_literals = [
    //         target_literal,
    //         CNFLiteral(pred2(const2, X), False),
    //     ]
    //     target_disjunction = CNFDisjunction.from_literals_list(target_literals)
    //     unification = Unification(
    //         similarity=1.0,
    //         source_substitutions={Y: const1},
    //         target_substitutions={X: const2},
    //     )
    //     resolvent = _build_resolvent(
    //         source=source_disjunction,
    //         target=target_disjunction,
    //         source_literal=source_literal,
    //         target_literal=target_literal,
    //         unification=unification,
    //     )
    //     expected_literals = [
    //         CNFLiteral(pred1(const1, const1), True),
    //         CNFLiteral(pred2(const2, const2), False),
    //     ]
    //     assert resolvent == CNFDisjunction.from_literals_list(expected_literals)

    #[test]
    fn test_build_resolvent() {
        let source_literal = PyArcItem::new(CNFLiteral::new(
            pred2().atom(vec![y().into(), const2().into()]),
            false,
        ));
        let target_literal = PyArcItem::new(CNFLiteral::new(
            pred2().atom(vec![const1().into(), x().into()]),
            true,
        ));

        let source_literals = btset! {
            source_literal.clone(),
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![y().into(), const1().into()]), true)),
        };
        let source_disjunction = PyArcItem::new(CNFDisjunction::new(source_literals));
        let target_literals = btset! {
            target_literal.clone(),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const2().into(), x().into()]), false)),
        };
        let target_disjunction = PyArcItem::new(CNFDisjunction::new(target_literals));
        let unification = Unification {
            similarity: 1.0,
            source_substitutions: hmap! { y() => const1().into() },
            target_substitutions: hmap! { x() => const2().into() },
        };
        let resolvent = build_resolvent(
            &source_disjunction,
            &target_disjunction,
            &source_literal,
            &target_literal,
            &unification,
        );

        let expected_literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![const1().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const2().into(), const2().into()]), false)),
        };
        assert_eq!(
            resolvent,
            PyArcItem::new(CNFDisjunction::new(expected_literals))
        );
    }

    // def test_build_resolvent_with_similar_predicates_with_embeddings() -> None:
    //     p1 = Predicate("p1", embedding=np.array([1, 2, 3]))
    //     p1_same_name = Predicate("p1", embedding=np.array([1, 4, 3]))

    //     source_literal = CNFLiteral(p1(Y, const2), False)
    //     target_literal = CNFLiteral(p1(const1, X), True)

    //     source_literals = [
    //         source_literal,
    //         CNFLiteral(p1_same_name(Y, const1), True),
    //     ]
    //     source_disjunction = CNFDisjunction.from_literals_list(source_literals)
    //     target_literals = [
    //         target_literal,
    //         CNFLiteral(pred2(const2, X), False),
    //     ]
    //     target_disjunction = CNFDisjunction.from_literals_list(target_literals)
    //     unification = Unification(
    //         similarity=1.0,
    //         source_substitutions={Y: const1},
    //         target_substitutions={X: const2},
    //     )
    //     resolvent = _build_resolvent(
    //         source=source_disjunction,
    //         target=target_disjunction,
    //         source_literal=source_literal,
    //         target_literal=target_literal,
    //         unification=unification,
    //     )

    //     expected_literals = [
    //         CNFLiteral(p1_same_name(const1, const1), True),
    //         CNFLiteral(pred2(const2, const2), False),
    //     ]
    //     assert resolvent == CNFDisjunction.from_literals_list(expected_literals)

    #[test]
    fn test_build_resolvent_with_similar_predicates_with_embeddings() {
        let embed_p1 = to_numpy_array(vec![1.0, 2.0, 3.0]);
        let embed_p1_same_name = to_numpy_array(vec![1.0, 4.0, 3.0]);

        let p1 = Predicate::new("p1", Some(embed_p1));
        let p1_same_name = Predicate::new("p1", Some(embed_p1_same_name));

        let source_literal = PyArcItem::new(CNFLiteral::new(
            p1.atom(vec![y().into(), const2().into()]),
            false,
        ));
        let target_literal = PyArcItem::new(CNFLiteral::new(
            p1.atom(vec![const1().into(), x().into()]),
            true,
        ));

        let source_literals = btset! {
            source_literal.clone(),
            PyArcItem::new(CNFLiteral::new(p1_same_name.atom(vec![y().into(), const1().into()]), true)),
        };
        let source_disjunction = PyArcItem::new(CNFDisjunction::new(source_literals));
        let target_literals = btset! {
            target_literal.clone(),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const2().into(), x().into()]), false)),
        };
        let target_disjunction = PyArcItem::new(CNFDisjunction::new(target_literals));
        let unification = Unification {
            similarity: 1.0,
            source_substitutions: hmap! { y() => const1().into() },
            target_substitutions: hmap! { x() => const2().into() },
        };
        let resolvent = build_resolvent(
            &source_disjunction,
            &target_disjunction,
            &source_literal,
            &target_literal,
            &unification,
        );

        let expected_literals = btset! {
            PyArcItem::new(CNFLiteral::new(p1_same_name.atom(vec![const1().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const2().into(), const2().into()]), false)),
        };
        assert_eq!(
            resolvent,
            PyArcItem::new(CNFDisjunction::new(expected_literals))
        );
    }
}
