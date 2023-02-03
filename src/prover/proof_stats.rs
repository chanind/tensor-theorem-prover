use std::sync::atomic::AtomicUsize;
use std::sync::atomic::Ordering::Relaxed;

use pyo3::prelude::*;

/// Stats on how complex a proof was to compute
pub struct ProofStats {
    pub attempted_unifications: AtomicUsize,
    pub successful_unifications: AtomicUsize,
    pub similarity_comparisons: AtomicUsize,
    pub similarity_cache_hits: AtomicUsize,
    pub attempted_resolutions: AtomicUsize,
    pub successful_resolutions: AtomicUsize,
    pub max_resolvent_width_seen: AtomicUsize,
    pub max_depth_seen: AtomicUsize,
    pub discarded_proofs: AtomicUsize,
    pub resolvent_checks: AtomicUsize,
    pub resolvent_check_hits: AtomicUsize,
}
impl ProofStats {
    pub fn new() -> Self {
        Self {
            attempted_unifications: AtomicUsize::new(0),
            successful_unifications: AtomicUsize::new(0),
            similarity_comparisons: AtomicUsize::new(0),
            similarity_cache_hits: AtomicUsize::new(0),
            attempted_resolutions: AtomicUsize::new(0),
            successful_resolutions: AtomicUsize::new(0),
            max_resolvent_width_seen: AtomicUsize::new(0),
            max_depth_seen: AtomicUsize::new(0),
            discarded_proofs: AtomicUsize::new(0),
            resolvent_checks: AtomicUsize::new(0),
            resolvent_check_hits: AtomicUsize::new(0),
        }
    }
}
impl ProofStats {
    pub fn copy_and_freeze(&self) -> FrozenProofStats {
        FrozenProofStats {
            attempted_unifications: self.attempted_unifications.load(Relaxed),
            successful_unifications: self.successful_unifications.load(Relaxed),
            similarity_comparisons: self.similarity_comparisons.load(Relaxed),
            similarity_cache_hits: self.similarity_cache_hits.load(Relaxed),
            attempted_resolutions: self.attempted_resolutions.load(Relaxed),
            successful_resolutions: self.successful_resolutions.load(Relaxed),
            max_resolvent_width_seen: self.max_resolvent_width_seen.load(Relaxed),
            max_depth_seen: self.max_depth_seen.load(Relaxed),
            discarded_proofs: self.discarded_proofs.load(Relaxed),
            resolvent_checks: self.resolvent_checks.load(Relaxed),
            resolvent_check_hits: self.resolvent_check_hits.load(Relaxed),
        }
    }
}

#[pyclass(name = "RsProofStats")]
#[derive(Clone)]
pub struct FrozenProofStats {
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
