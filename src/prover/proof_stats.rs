use std::sync::atomic::AtomicUsize;
use std::sync::atomic::Ordering::Relaxed;

use pyo3::prelude::*;

/// Stats on how complex a proof was to compute
pub struct SharedProofStats {
    pub attempted_resolutions: AtomicUsize,
    pub successful_resolutions: AtomicUsize,
    pub max_resolvent_width_seen: AtomicUsize,
    pub max_depth_seen: AtomicUsize,
    pub discarded_proofs: AtomicUsize,
}
impl SharedProofStats {
    pub fn new() -> Self {
        Self {
            attempted_resolutions: AtomicUsize::new(0),
            successful_resolutions: AtomicUsize::new(0),
            max_resolvent_width_seen: AtomicUsize::new(0),
            max_depth_seen: AtomicUsize::new(0),
            discarded_proofs: AtomicUsize::new(0),
        }
    }
}
impl SharedProofStats {
    pub fn copy_and_freeze(&self) -> LocalProofStats {
        LocalProofStats {
            attempted_resolutions: self.attempted_resolutions.load(Relaxed),
            successful_resolutions: self.successful_resolutions.load(Relaxed),
            max_resolvent_width_seen: self.max_resolvent_width_seen.load(Relaxed),
            max_depth_seen: self.max_depth_seen.load(Relaxed),
            discarded_proofs: self.discarded_proofs.load(Relaxed),
        }
    }
}

#[pyclass(name = "RsProofStats")]
#[derive(Clone)]
pub struct LocalProofStats {
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
}
impl LocalProofStats {
    pub fn new() -> Self {
        Self {
            attempted_resolutions: 0,
            successful_resolutions: 0,
            max_resolvent_width_seen: 0,
            max_depth_seen: 0,
            discarded_proofs: 0,
        }
    }
}
