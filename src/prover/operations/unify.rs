use rustc_hash::FxHashMap;

use crate::prover::{ProofContext, SubstitutionsMap};
use crate::types::{Atom, Term};

#[derive(Debug, Clone, PartialEq)]
pub struct Unification {
    pub source_substitutions: SubstitutionsMap,
    pub target_substitutions: SubstitutionsMap,
    pub similarity: f64,
}

/// Fuzzy-optional implementation of unify
/// If no similarity_func is provided, or if either atom lacks a embedding,
/// then it will do an exact match on the symbols themselves
pub fn unify(source: &Atom, target: &Atom, ctx: &mut ProofContext) -> Option<Unification> {
    if source.terms.len() != target.terms.len() {
        return None;
    }

    let similarity = ctx.calc_similarity(&source.predicate, &target.predicate);
    ctx.stats.similarity_comparisons += 1;

    // abort early if the predicate similarity is too low
    if similarity <= ctx.min_similarity_threshold {
        return None;
    }

    unify_terms(&source.terms, &target.terms, similarity, ctx)
}

#[derive(Debug, PartialEq, Eq, Hash, Clone)]
enum BindingLabel {
    Source,
    Target,
}

#[derive(Debug, PartialEq, Eq, Hash, Clone)]
struct LabeledTerm {
    label: BindingLabel,
    term: Term,
}
impl LabeledTerm {
    fn new(label: BindingLabel, term: Term) -> Self {
        Self { label, term }
    }
}

// I want to also create something like a LabeledVariable, which is a LabeledTerm but with Term::Variable as the term type
// but can't figure out how to do that or if it's even possible
// Ideally, this should be HashMap<LabeledVariable, LabeledTerm> but I can't figure out how to do that
type SubstitutionSet = FxHashMap<LabeledTerm, LabeledTerm>;

/// Unification with optional vector similarity, based on Robinson's 1965 algorithm, as described in:
/// "Comparing unification algorithms in first-order theorem proving", Hoder et al. 2009
/// https://www.cs.man.ac.uk/~hoderk/ubench/unification_full.pdf
fn unify_terms(
    source_terms: &[Term],
    target_terms: &[Term],
    similarity: f64,
    ctx: &mut ProofContext,
) -> Option<Unification> {
    let mut cur_similarity = similarity;
    let mut substitutions: SubstitutionSet = FxHashMap::default();
    for (source_term, target_term) in source_terms.iter().zip(target_terms.iter()) {
        let new_similarity = unify_term_pair(
            source_term,
            target_term,
            &mut substitutions,
            cur_similarity,
            ctx,
        );
        cur_similarity = new_similarity?;
    }

    let mut source_substitutions: SubstitutionsMap = FxHashMap::default();
    let mut target_substitutions: SubstitutionsMap = FxHashMap::default();
    for labeled_var in substitutions.keys() {
        let resolved_labeled_term = _resolve_labeled_term(labeled_var, &substitutions);
        match &labeled_var.term {
            Term::Variable(variable) => {
                if labeled_var.label == BindingLabel::Source {
                    source_substitutions
                        .insert(variable.clone(), resolved_labeled_term.term.clone());
                } else {
                    target_substitutions
                        .insert(variable.clone(), resolved_labeled_term.term.clone());
                }
            }
            _ => unreachable!("Substitutions keys should only contain variables"),
        }
    }
    Some(Unification {
        source_substitutions,
        target_substitutions,
        similarity: cur_similarity,
    })
}

/// Resolve a labeled term by recursively following substitutions, part of Robinson's 1965 algorithm
fn _resolve_labeled_term<'a>(
    labeled_term: &'a LabeledTerm,
    substitutions: &'a SubstitutionSet,
) -> &'a LabeledTerm {
    match labeled_term.term {
        Term::Variable(_) => {
            if let Some(sub_term) = substitutions.get(labeled_term) {
                return _resolve_labeled_term(sub_term, substitutions);
            }
        }
        _ => {}
    }
    labeled_term
}

/// Recursively check if variable occurs in a term, part of Robinson's 1965 algorithm
fn check_var_occurrence(
    var: &Term,
    term: &Term,
    substitutions: &SubstitutionSet,
    is_source_var: bool,
) -> bool {
    let var_label = if is_source_var {
        BindingLabel::Source
    } else {
        BindingLabel::Target
    };
    let labeled_var = LabeledTerm::new(var_label, var.clone());
    // term is opposite label of var
    let term_label = if is_source_var {
        BindingLabel::Target
    } else {
        BindingLabel::Source
    };
    let labeled_term = LabeledTerm::new(term_label, term.clone());
    let mut term_stack: Vec<&LabeledTerm> = vec![&labeled_term];
    while let Some(cur_labeled_term) = term_stack.pop() {
        let cur_labeled_term = _resolve_labeled_term(&cur_labeled_term, substitutions);
        let mut comparison_vars: Vec<LabeledTerm> = Vec::new();
        if let Term::Variable(_) = cur_labeled_term.term {
            comparison_vars.push(cur_labeled_term.clone());
        } else if let Term::BoundFunction(cur_bound_func) = cur_labeled_term.term.clone() {
            for sub_term in cur_bound_func.terms {
                if let Term::Variable(_) = sub_term {
                    comparison_vars.push(LabeledTerm::new(
                        cur_labeled_term.label.clone(),
                        sub_term.clone(),
                    ));
                }
            }
        }
        for comparison_var in comparison_vars {
            if comparison_var == labeled_var {
                return false;
            } else if let Some(sub_term) = substitutions.get(&comparison_var) {
                term_stack.push(sub_term);
            }
        }
    }
    true
}

/// Check if a pair of terms can be unified, part of Robinson's 1965 algorithm
/// NOTE: modifies substitutions in place
fn unify_term_pair(
    source_term: &Term,
    target_term: &Term,
    substitutions: &mut SubstitutionSet,
    similarity: f64,
    ctx: &mut ProofContext,
) -> Option<f64> {
    let mut pairs_stack: Vec<(LabeledTerm, LabeledTerm)> = vec![(
        LabeledTerm::new(BindingLabel::Source, source_term.clone()),
        LabeledTerm::new(BindingLabel::Target, target_term.clone()),
    )];
    let mut cur_similarity = similarity;
    while let Some((cur_labeled_source_term, cur_labeled_target_term)) = pairs_stack.pop() {
        let cur_labeled_source_term =
            _resolve_labeled_term(&cur_labeled_source_term, substitutions);
        let LabeledTerm {
            label: cur_source_label,
            term: cur_source_term,
        } = cur_labeled_source_term;

        let cur_labeled_target_term =
            _resolve_labeled_term(&cur_labeled_target_term, substitutions);
        let LabeledTerm {
            label: cur_target_label,
            term: cur_target_term,
        } = cur_labeled_target_term;
        if let (Term::Constant(cur_source_const), Term::Constant(cur_target_const)) =
            (cur_source_term, cur_target_term)
        {
            // if these are identical objects, no need to compare them, just continue on
            if cur_source_const != cur_target_const {
                cur_similarity =
                    cur_similarity.min(ctx.calc_similarity(cur_source_const, cur_target_const));
                ctx.stats.similarity_comparisons += 1;
                if cur_similarity <= ctx.min_similarity_threshold {
                    return None;
                }
            }
        } else if let Term::Variable(_) = &cur_source_term {
            if let Term::Variable(_) = &cur_target_term {
                // if both are variables, replace the target with the source
                substitutions.insert(
                    cur_labeled_target_term.clone(),
                    cur_labeled_source_term.clone(),
                );
            } else if check_var_occurrence(
                cur_source_term,
                cur_target_term,
                substitutions,
                *cur_source_label == BindingLabel::Source,
            ) {
                substitutions.insert(
                    cur_labeled_source_term.clone(),
                    cur_labeled_target_term.clone(),
                );
            } else {
                return None;
            }
        } else if let Term::Variable(_) = cur_target_term {
            if check_var_occurrence(
                &cur_target_term,
                &cur_source_term,
                substitutions,
                *cur_target_label == BindingLabel::Source,
            ) {
                substitutions.insert(
                    cur_labeled_target_term.clone(),
                    cur_labeled_source_term.clone(),
                );
            } else {
                return None;
            }
        } else if let (Term::BoundFunction(cur_source_func), Term::BoundFunction(cur_target_func)) =
            (cur_source_term, cur_target_term)
        {
            if cur_source_func.function != cur_target_func.function {
                return None;
            }
            if cur_source_func.terms.len() != cur_target_func.terms.len() {
                return None;
            }
            for (source_sub_term, target_sub_term) in cur_source_func
                .terms
                .iter()
                .zip(cur_target_func.terms.iter())
            {
                pairs_stack.push((
                    LabeledTerm::new(cur_source_label.clone(), source_sub_term.clone()),
                    LabeledTerm::new(cur_target_label.clone(), target_sub_term.clone()),
                ));
            }
        }
    }

    Some(cur_similarity)
}

#[cfg(test)]
mod test {

    use rustc_hash::FxHashMap;

    use super::*;
    use crate::fxmap;
    use crate::test_utils::test::{
        const1, const2, func1, func2, get_py_similarity_fn, pred1, pred2, to_numpy_array, x, y, z,
    };
    use crate::{
        prover::ProofContext,
        types::{Constant, Predicate},
    };

    fn ctx() -> ProofContext {
        ProofContext::new(0.5, None, true, None, Some(get_py_similarity_fn()))
    }

    #[test]
    fn test_unify_with_all_constants() {
        let source = pred1().atom(vec![const1().into(), const2().into()]);
        let target = pred1().atom(vec![const1().into(), const2().into()]);
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            Unification {
                source_substitutions: FxHashMap::default(),
                target_substitutions: FxHashMap::default(),
                similarity: 1.0
            }
        );
    }

    #[test]
    fn test_unify_fails_if_preds_dont_match() {
        let source = pred1().atom(vec![const1().into(), const2().into()]);
        let target = pred2().atom(vec![const1().into(), const2().into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_fails_if_terms_dont_match() {
        let source = pred1().atom(vec![const2().into(), const2().into()]);
        let target = pred1().atom(vec![const1().into(), const2().into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_fails_if_functions_dont_match() {
        let source = pred1().atom(vec![func1().bind(vec![x().into()]).into()]);
        let target = pred1().atom(vec![func2().bind(vec![y().into()]).into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_fails_if_functions_take_different_number_of_params() {
        let source = pred1().atom(vec![func1().bind(vec![x().into(), y().into()]).into()]);
        let target = pred1().atom(vec![func1().bind(vec![x().into()]).into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_fails_if_terms_have_differing_lengths() {
        let source = pred1().atom(vec![const1().into()]);
        let target = pred1().atom(vec![const1().into(), const2().into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_with_source_var_to_target_const() {
        let source = pred1().atom(vec![x().into(), const1().into()]);
        let target = pred1().atom(vec![const2().into(), const1().into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const2().into() },
            target_substitutions: FxHashMap::default(),
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_source_const_to_target_var() {
        let source = pred1().atom(vec![const2().into(), const1().into()]);
        let target = pred1().atom(vec![x().into(), const1().into()]);
        let expected_unification = Unification {
            source_substitutions: FxHashMap::default(),
            target_substitutions: fxmap! { x() => const2().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_source_var_to_target_var() {
        let source = pred1().atom(vec![x().into(), const1().into()]);
        let target = pred1().atom(vec![y().into(), const1().into()]);
        let expected_unification = Unification {
            source_substitutions: FxHashMap::default(),
            target_substitutions: fxmap! { y() => x().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_repeated_vars_in_source() {
        let source = pred1().atom(vec![x().into(), x().into()]);
        let target = pred1().atom(vec![y().into(), const1().into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const1().into() },
            target_substitutions: fxmap! { y() => const1().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_repeated_vars_in_target() {
        let source = pred1().atom(vec![x().into(), const1().into()]);
        let target = pred1().atom(vec![y().into(), y().into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const1().into() },
            target_substitutions: fxmap! { y() => const1().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_fails_with_unfulfilable_constraints() {
        let source = pred1().atom(vec![x().into(), x().into()]);
        let target = pred1().atom(vec![const1().into(), const2().into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_with_source_var_to_target_var_with_repeat_constants() {
        let source = pred1().atom(vec![x().into(), x().into(), x().into(), x().into()]);
        let target = pred1().atom(vec![
            const1().into(),
            y().into(),
            z().into(),
            const1().into(),
        ]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const1().into() },
            target_substitutions: fxmap! { y() => const1().into(), z() => const1().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_chained_vars() {
        let source = pred1().atom(vec![
            x().into(),
            x().into(),
            y().into(),
            y().into(),
            z().into(),
            z().into(),
        ]);
        let target = pred1().atom(vec![
            y().into(),
            x().into(),
            x().into(),
            z().into(),
            z().into(),
            const2().into(),
        ]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const2().into(), y() => const2().into(), z() => const2().into() },
            target_substitutions: fxmap! { x() => const2().into(), y() => const2().into(), z() => const2().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_function_map_var_to_const() {
        let source = pred1().atom(vec![func1().bind(vec![x().into()]).into()]);
        let target = pred1().atom(vec![func1().bind(vec![const1().into()]).into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const1().into() },
            target_substitutions: FxHashMap::default(),
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_function_map_var_to_var() {
        let source = pred1().atom(vec![func1().bind(vec![x().into()]).into()]);
        let target = pred1().atom(vec![func1().bind(vec![y().into()]).into()]);
        let expected_unification = Unification {
            source_substitutions: FxHashMap::default(),
            target_substitutions: fxmap! { y() => x().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_function_map_var_to_var_with_repeat_constants() {
        let source = pred1().atom(vec![func1().bind(vec![x().into(), x().into()]).into()]);
        let target = pred1().atom(vec![func1().bind(vec![const1().into(), y().into()]).into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => const1().into() },
            target_substitutions: fxmap! { y() => const1().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_with_function_map_var_to_var_with_repeat_constants2() {
        let source = pred1().atom(vec![func1().bind(vec![const1().into(), y().into()]).into()]);
        let target = pred1().atom(vec![func1().bind(vec![x().into(), x().into()]).into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { y() => const1().into() },
            target_substitutions: fxmap! { x() => const1().into() },
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_bind_nested_function_var() {
        let source = pred1().atom(vec![func1().bind(vec![x().into()]).into()]);
        let target = pred1().atom(vec![func1()
            .bind(vec![func2().bind(vec![const1().into()]).into()])
            .into()]);
        let expected_unification = Unification {
            source_substitutions: fxmap! { x() => func2().bind(vec![const1().into()]).into() },
            target_substitutions: FxHashMap::default(),
            similarity: 1.0,
        };
        assert_eq!(
            unify(&source, &target, &mut ctx()).unwrap(),
            expected_unification
        );
    }

    #[test]
    fn test_unify_fails_to_bind_reciprocal_functions() {
        let source = pred1().atom(vec![func1().bind(vec![x().into()]).into(), x().into()]);
        let target = pred1().atom(vec![y().into(), func1().bind(vec![y().into()]).into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_with_predicate_vector_embeddings() {
        let embedding1 = to_numpy_array(vec![1.0, 0.0, 1.0, 1.0]);
        let embedding2 = to_numpy_array(vec![1.0, 0.0, 0.9, 1.0]);
        let vec_pred1 = Predicate::new("pred1", Some(embedding1));
        let vec_pred2 = Predicate::new("pred2", Some(embedding2));
        let source = vec_pred1.atom(vec![x().into()]);
        let target = vec_pred2.atom(vec![const1().into()]);
        let unification = unify(&source, &target, &mut ctx()).unwrap();
        assert_eq!(
            unification.source_substitutions,
            fxmap! { x() => const1().into() }
        );
        assert_eq!(unification.target_substitutions, FxHashMap::default());
        assert!(unification.similarity > 0.9 && unification.similarity < 1.0);
    }

    #[test]
    fn test_unify_fails_with_dissimilar_predicate_vector_embeddings() {
        let embedding1 = to_numpy_array(vec![0.0, 1.0, 1.0, 0.0]);
        let embedding2 = to_numpy_array(vec![1.0, 0.0, 0.3, 1.0]);
        let vec_pred1 = Predicate::new("pred1", Some(embedding1));
        let vec_pred2 = Predicate::new("pred2", Some(embedding2));
        let source = vec_pred1.atom(vec![x().into()]);
        let target = vec_pred2.atom(vec![const1().into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }

    #[test]
    fn test_unify_with_constant_vector_embeddings() {
        let embedding1 = to_numpy_array(vec![1.0, 0.0, 1.0, 1.0]);
        let embedding2 = to_numpy_array(vec![1.0, 0.0, 0.9, 1.0]);
        let vec_const1 = Constant::new("const1", Some(embedding1));
        let vec_const2 = Constant::new("const2", Some(embedding2));
        let source = pred1().atom(vec![vec_const1.into()]);
        let target = pred1().atom(vec![vec_const2.into()]);
        let unification = unify(&source, &target, &mut ctx()).unwrap();
        assert_eq!(unification.source_substitutions, FxHashMap::default());
        assert_eq!(unification.target_substitutions, FxHashMap::default());
        assert!(unification.similarity > 0.9 && unification.similarity < 1.0);
    }

    #[test]
    fn test_unify_fails_with_dissimilar_constant_vector_embeddings() {
        let embedding1 = to_numpy_array(vec![0.0, 1.0, 1.0, 0.0]);
        let embedding2 = to_numpy_array(vec![1.0, 0.0, 0.3, 1.0]);
        let vec_const1 = Constant::new("const1", Some(embedding1));
        let vec_const2 = Constant::new("const2", Some(embedding2));
        let source = pred1().atom(vec![vec_const1.into()]);
        let target = pred1().atom(vec![vec_const2.into()]);
        assert_eq!(unify(&source, &target, &mut ctx()), None);
    }
}
