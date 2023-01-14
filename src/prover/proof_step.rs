use pyo3::prelude::*;

use std::collections::HashMap;

use crate::types::{CNFDisjunction, CNFLiteral, Term, Variable};

// TODO: should this use references?
pub type SubstitutionsMap = HashMap<Variable, Term>;

#[pyclass(name = "RsProofStepBox")]
#[derive(Clone, PartialEq, Debug)]
pub struct ProofStepBox {
    pub inner: Box<ProofStep>,
}
impl ProofStepBox {
    pub fn new(inner: ProofStep) -> Self {
        Self {
            inner: Box::new(inner),
        }
    }
}

/// A single step in a proof of a goal
#[pyclass(name = "RsProofStep")]
#[derive(Clone, PartialEq, Debug)]
pub struct ProofStep {
    #[pyo3(get)]
    pub source: CNFDisjunction,
    #[pyo3(get)]
    pub target: CNFDisjunction,
    #[pyo3(get)]
    pub source_unification_literal: CNFLiteral,
    #[pyo3(get)]
    pub target_unification_literal: CNFLiteral,
    #[pyo3(get)]
    pub source_substitutions: SubstitutionsMap,
    #[pyo3(get)]
    pub target_substitutions: SubstitutionsMap,
    #[pyo3(get)]
    pub resolvent: CNFDisjunction,
    #[pyo3(get)]
    pub similarity: f64,
    // this refers to the overall similarity of this step and all of its parents
    #[pyo3(get)]
    pub running_similarity: f64,
    #[pyo3(get)]
    pub depth: usize,
    pub parent: Option<ProofStepBox>,
}
#[pymethods]
impl ProofStep {
    #[new]
    pub fn new(
        source: CNFDisjunction,
        target: CNFDisjunction,
        source_unification_literal: CNFLiteral,
        target_unification_literal: CNFLiteral,
        source_substitutions: SubstitutionsMap,
        target_substitutions: SubstitutionsMap,
        resolvent: CNFDisjunction,
        similarity: f64,
        running_similarity: f64,
        depth: usize,
        parent: Option<ProofStepBox>,
    ) -> ProofStep {
        ProofStep {
            source,
            target,
            source_unification_literal,
            target_unification_literal,
            source_substitutions,
            target_substitutions,
            resolvent,
            similarity,
            running_similarity,
            depth,
            parent,
        }
    }
}
