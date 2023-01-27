use pyo3::prelude::*;
use rustc_hash::FxHashMap;

use super::{ProofStats, ProofStep, SubstitutionsMap};
use crate::types::{BoundFunction, CNFDisjunction, Term};
use crate::util::find_variables_in_terms;

/// Respresentation of a successful proof of a goal
#[pyclass(name = "RsProof")]
#[derive(Clone)]
pub struct Proof {
    #[pyo3(get)]
    pub goal: CNFDisjunction,
    #[pyo3(get)]
    pub similarity: f64,
    #[pyo3(get)]
    pub stats: ProofStats,
    leaf_proof_step: ProofStep,
}
#[pymethods]
impl Proof {
    #[new]
    pub fn new(
        goal: CNFDisjunction,
        similarity: f64,
        stats: ProofStats,
        leaf_proof_step: ProofStep,
    ) -> Proof {
        Proof {
            goal,
            similarity,
            stats,
            leaf_proof_step,
        }
    }

    #[getter]
    pub fn depth(&self) -> usize {
        self.proof_steps().len()
    }

    #[getter]
    pub fn proof_steps(&self) -> Vec<ProofStep> {
        let mut proof_steps: Vec<ProofStep> = Vec::new();
        let mut cur_step = self.leaf_proof_step.clone();
        while let Some(parent) = &cur_step.parent {
            proof_steps.push(cur_step.clone());
            cur_step = (*parent.inner).clone();
        }
        proof_steps.push(cur_step);
        proof_steps.reverse();
        proof_steps
    }

    /// The substitutions made in the proof
    #[getter]
    pub fn substitutions(&self) -> SubstitutionsMap {
        let goal_terms = self
            .goal
            .literals
            .iter()
            .flat_map(|literal| literal.item.atom.terms.iter())
            .collect::<Vec<&Term>>();
        let goal_variables = find_variables_in_terms(&goal_terms);
        let step_substitutions = self
            .proof_steps()
            .iter()
            .map(|step| step.source_substitutions.clone())
            .collect::<Vec<SubstitutionsMap>>();
        let mut substitutions: SubstitutionsMap = FxHashMap::default();
        for variable in goal_variables {
            substitutions.insert(
                variable.clone(),
                resolve_var_value(&Term::Variable(variable.clone()), &step_substitutions, 0),
            );
        }
        substitutions
    }
}

fn resolve_var_value(var: &Term, substitutions: &Vec<SubstitutionsMap>, index: usize) -> Term {
    if index >= substitutions.len() {
        return var.clone();
    }
    if let Term::Variable(var_term) = var {
        // if this variable doesn't occur in the substitutions, assume it remains unchanged
        let new_var_value = substitutions[index].get(var_term).unwrap_or(var);
        match new_var_value {
            Term::Variable(_) => resolve_var_value(new_var_value, substitutions, index + 1),
            Term::Constant(_) => new_var_value.clone(),
            Term::BoundFunction(bound_function) => Term::BoundFunction(BoundFunction::new(
                bound_function.function.clone(),
                bound_function
                    .terms
                    .iter()
                    .map(|term| resolve_var_value(term, substitutions, index + 1))
                    .collect(),
            )),
        }
    } else {
        var.clone()
    }
}
