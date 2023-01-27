use pyo3::prelude::*;
use rustc_hash::FxHashMap;

use std::sync::Arc;

use crate::{
    types::{CNFDisjunction, CNFLiteral, Term, Variable},
    util::PyArcItem,
};

// TODO: should this use references?
pub type SubstitutionsMap = FxHashMap<Variable, Term>;

#[derive(Clone, PartialEq, Debug)]
pub struct ProofStepNode {
    pub inner: Arc<ProofStep>,
}
impl ProofStepNode {
    pub fn new(inner: ProofStep) -> Self {
        Self {
            inner: Arc::new(inner),
        }
    }
}

/// A single step in a proof of a goal
#[pyclass(name = "RsProofStep")]
#[derive(Clone, PartialEq, Debug)]
pub struct ProofStep {
    #[pyo3(get)]
    pub source: PyArcItem<CNFDisjunction>,
    #[pyo3(get)]
    pub target: PyArcItem<CNFDisjunction>,
    #[pyo3(get)]
    pub source_unification_literal: PyArcItem<CNFLiteral>,
    #[pyo3(get)]
    pub target_unification_literal: PyArcItem<CNFLiteral>,
    #[pyo3(get)]
    pub source_substitutions: SubstitutionsMap,
    #[pyo3(get)]
    pub target_substitutions: SubstitutionsMap,
    #[pyo3(get)]
    pub resolvent: PyArcItem<CNFDisjunction>,
    #[pyo3(get)]
    pub similarity: f64,
    // this refers to the overall similarity of this step and all of its parents
    #[pyo3(get)]
    pub running_similarity: f64,
    #[pyo3(get)]
    pub depth: usize,
    pub parent: Option<ProofStepNode>,
}
impl ProofStep {
    pub fn new(
        source: PyArcItem<CNFDisjunction>,
        target: PyArcItem<CNFDisjunction>,
        source_unification_literal: PyArcItem<CNFLiteral>,
        target_unification_literal: PyArcItem<CNFLiteral>,
        source_substitutions: SubstitutionsMap,
        target_substitutions: SubstitutionsMap,
        resolvent: PyArcItem<CNFDisjunction>,
        similarity: f64,
        running_similarity: f64,
        depth: usize,
        parent: Option<ProofStepNode>,
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
