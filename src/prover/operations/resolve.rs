use regex::Regex;
use rustc_hash::{FxHashMap, FxHashSet};
use std::collections::BTreeSet;

use crate::{
    prover::{proof_step::ProofStepNode, ProofContext, ProofStep, SubstitutionsMap},
    types::{Atom, CNFDisjunction, CNFLiteral, Term, Variable},
    util::PyArcItem,
};

use super::{unify, Unification};

lazy_static! {
    static ref VAR_NAME_REGEX: Regex = Regex::new(r"_\d+$").unwrap();
}

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
    let mut all_vars = unused_source_vars
        .union(&unused_target_vars)
        .chain(unification.source_substitutions.keys())
        .chain(unification.target_substitutions.keys())
        .cloned()
        .collect::<FxHashSet<_>>();
    let rename_vars_map =
        find_non_overlapping_var_names(&unused_source_vars, &unused_target_vars, &mut all_vars);
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

/// return a list of all variables in the literals that aren't being substituted
fn find_unused_variables(
    literals: &BTreeSet<PyArcItem<CNFLiteral>>,
    substitutions: &SubstitutionsMap,
) -> FxHashSet<Variable> {
    let mut unused_variables = FxHashSet::default();
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

/// Find new unused vars names for all overlapping variables between source and target
fn find_non_overlapping_var_names(
    source_vars: &FxHashSet<Variable>,
    target_vars: &FxHashSet<Variable>,
    all_variables: &mut FxHashSet<Variable>,
) -> FxHashMap<Variable, Variable> {
    let overlapping_variables = source_vars.intersection(target_vars);
    let mut renamed_vars = FxHashMap::default();
    for var in overlapping_variables {
        let base_name = VAR_NAME_REGEX.replace(&var.name, "");
        let mut counter = 0;
        loop {
            counter += 1;
            let new_var = Variable::new(&format!("{}_{}", base_name, counter));
            if !all_variables.contains(&new_var) {
                all_variables.insert(new_var.clone());
                renamed_vars.insert(var.clone(), new_var);
                break;
            }
        }
    }
    renamed_vars
}

fn rename_variables_in_literals(
    literals: &BTreeSet<PyArcItem<CNFLiteral>>,
    rename_map: &FxHashMap<Variable, Variable>,
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
    rename_map: &FxHashMap<Variable, Variable>,
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

    use sugars::btset;

    use super::*;
    use crate::test_utils::test::{a, b, c, const1, const2, pred1, pred2, to_numpy_array, x, y, z};
    use crate::types::Predicate;
    use crate::{fxmap, fxset};

    #[test]
    fn test_find_unused_variables() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(Atom::new(pred1(), vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(Atom::new(pred2(), vec![y().into()]), false)),
        };
        assert_eq!(
            find_unused_variables(&literals, &FxHashMap::default()),
            fxset! { x(), y() }
        );
        assert_eq!(
            find_unused_variables(&literals, &fxmap! { y() => const1().into() }),
            fxset! { x() }
        );
        assert_eq!(
            find_unused_variables(
                &literals,
                &fxmap! { y() => const1().into(), x() => const2().into() }
            ),
            fxset! {}
        );
    }

    #[test]
    fn test_find_non_overlapping_var_names_leaves_vars_unchanged_if_no_overlaps() {
        let source_vars = fxset! { x(), y(), z() };
        let target_vars = fxset! { a(), b(), c() };
        let mut all_vars = source_vars
            .union(&target_vars)
            .cloned()
            .collect::<FxHashSet<_>>();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &mut all_vars),
            FxHashMap::default()
        );
    }

    #[test]
    fn test_find_non_overlapping_var_names_renames_vars_if_overlaps() {
        let source_vars = fxset! { x(), y(), z() };
        let target_vars = fxset! { a(), b(), x() };
        let mut all_vars = source_vars
            .union(&target_vars)
            .cloned()
            .collect::<FxHashSet<_>>();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &mut all_vars),
            fxmap! { x() => Variable::new("X_1") }
        );
    }

    #[test]
    fn test_find_non_overlapping_keeps_iterating_var_names_until_a_non_bound_one_is_found() {
        let source_vars = fxset! { x(), y(), z() };
        let target_vars = fxset! { a(), b(), x() };
        let mut all_vars = source_vars
            .union(&target_vars)
            .cloned()
            .chain(btset! { Variable::new("X_1"), Variable::new("X_2") })
            .collect::<FxHashSet<_>>();
        assert_eq!(
            find_non_overlapping_var_names(&source_vars, &target_vars, &mut all_vars),
            fxmap! { x() => Variable::new("X_3") }
        );
    }

    #[test]
    fn test_rename_variables_in_literals() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![y().into()]), false)),
        };
        let rename_vars_map = fxmap! { x() => Variable::new("X_1"), y() => Variable::new("Y_1") };
        let renamed_literals = rename_variables_in_literals(&literals, &rename_vars_map);
        assert_eq!(
            renamed_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![Variable::new("X_1").into(), const1().into()]), true)),
                PyArcItem::new(CNFLiteral::new(pred2().atom(vec![Variable::new("Y_1").into()]), false)),
            }
        );
    }

    #[test]
    fn test_perform_substitution_basic() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), const1().into()]), true)),
            PyArcItem::new(CNFLiteral::new(pred2().atom(vec![y().into()]), false)),
        };
        let substitutions: SubstitutionsMap =
            fxmap! { x() => const2().into(), y() => const1().into() };
        let substituted_literals = perform_substitution(&literals, &substitutions);
        assert_eq!(
            substituted_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![const2().into(), const1().into()]), true)),
                PyArcItem::new(CNFLiteral::new(pred2().atom(vec![const1().into()]), false)),
            }
        );
    }

    #[test]
    fn test_perform_substitution_with_repeated_vars() {
        let literals = btset! {
            PyArcItem::new(CNFLiteral::new(pred1().atom(vec![x().into(), y().into()]), true)),
        };
        let substitutions: SubstitutionsMap = fxmap! { x() => y().into(), y() => const2().into() };
        let substituted_literals = perform_substitution(&literals, &substitutions);
        assert_eq!(
            substituted_literals,
            btset! {
                PyArcItem::new(CNFLiteral::new(pred1().atom(vec![y().into(), const2().into()]), true)),
            }
        );
    }

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
            source_substitutions: fxmap! { y() => const1().into() },
            target_substitutions: fxmap! { x() => const2().into() },
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
            source_substitutions: fxmap! { y() => const1().into() },
            target_substitutions: fxmap! { x() => const2().into() },
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
