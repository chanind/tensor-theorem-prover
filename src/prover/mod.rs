use pyo3::prelude::*;

mod operations;
mod proof;
mod proof_context;
mod proof_stats;
mod proof_step;
mod resolution_prover;
mod similarity_cache;

pub use proof::Proof;
pub use proof_context::{LocalProofContext, SharedProofContext};
pub use proof_stats::{LocalProofStats, SharedProofStats};
pub use proof_step::{ProofStep, ProofStepNode, SubstitutionsMap};
pub use resolution_prover::ResolutionProverBackend;

pub fn register_python_symbols(_py: Python<'_>, module: &PyModule) -> PyResult<()> {
    module.add_class::<ProofStep>()?;
    module.add_class::<LocalProofStats>()?;
    module.add_class::<Proof>()?;
    module.add_class::<ResolutionProverBackend>()?;
    Ok(())
}
