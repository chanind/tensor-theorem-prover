use pyo3::prelude::*;

/// Stats on how complex a proof was to compute
#[pyclass(name = "RsProofStats")]
#[derive(Clone)]
pub struct ProofStats {
    #[pyo3(get)]
    pub attempted_unifications: usize,
    #[pyo3(get)]
    pub successful_unifications: usize,
    #[pyo3(get)]
    pub similarity_comparisons: usize,
    #[pyo3(get)]
    pub similarity_cache_hits: usize,
    #[pyo3(get)]
    pub attempted_resolutions: usize,
    #[pyo3(get)]
    pub successful_resolutions: usize,
    #[pyo3(get)]
    pub max_resolvent_width_seen: usize,
    #[pyo3(get)]
    pub max_depth_seen: usize,
    #[pyo3(get)]
    pub discarded_proofs: usize,
    #[pyo3(get)]
    pub resolvent_checks: usize,
    #[pyo3(get)]
    pub resolvent_check_hits: usize,
}
#[pymethods]
impl ProofStats {
    #[new]
    pub fn new() -> Self {
        Self {
            attempted_unifications: 0,
            successful_unifications: 0,
            similarity_comparisons: 0,
            similarity_cache_hits: 0,
            attempted_resolutions: 0,
            successful_resolutions: 0,
            max_resolvent_width_seen: 0,
            max_depth_seen: 0,
            discarded_proofs: 0,
            resolvent_checks: 0,
            resolvent_check_hits: 0,
        }
    }
}
