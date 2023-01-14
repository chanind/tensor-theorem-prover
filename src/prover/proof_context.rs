use fxhash::FxHasher;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

use crate::types::SimilarityComparable;

use super::ProofStats;
use super::ProofStep;

/// Helper class which accumulates successful proof steps and keeps track of stats during the proof process
#[derive(Clone)]
pub struct ProofContext {
    pub stats: ProofStats,
    pub min_similarity_threshold: f64,
    pub max_proofs: Option<usize>,
    scored_leaf_proof_steps: Vec<(f64, usize, ProofStep, ProofStats)>,
    skip_seen_resolvents: bool,
    seen_resolvents: HashMap<u64, (usize, f64)>,
    similarity_cache: Option<HashMap<(String, Option<isize>, String, Option<isize>), f64>>,
    py_similarity_fn: Option<PyObject>,
}
impl ProofContext {
    pub fn new(
        initial_min_similarity_threshold: f64,
        max_proofs: Option<usize>,
        skip_seen_resolvents: bool,
        cache_similarity: bool,
        py_similarity_fn: Option<PyObject>,
    ) -> Self {
        Self {
            stats: ProofStats::new(),
            min_similarity_threshold: initial_min_similarity_threshold,
            max_proofs,
            scored_leaf_proof_steps: Vec::new(),
            seen_resolvents: HashMap::new(),
            skip_seen_resolvents,
            similarity_cache: if cache_similarity {
                Some(HashMap::new())
            } else {
                None
            },
            py_similarity_fn,
        }
    }

    pub fn record_leaf_proof(&mut self, proof_step: ProofStep) {
        // make sure to clone the stats before appending, since the stats will continue to get mutated after this
        self.scored_leaf_proof_steps.push((
            proof_step.running_similarity,
            proof_step.depth,
            proof_step,
            self.stats.clone(),
        ));
        self.scored_leaf_proof_steps.sort_by(|a, b| {
            if a.0 == b.0 {
                a.1.cmp(&b.1)
            } else {
                b.0.partial_cmp(&a.0).unwrap()
            }
        });
        if let Some(max_proofs) = self.max_proofs {
            if self.scored_leaf_proof_steps.len() > max_proofs {
                // Remove the proof step with the lowest similarity
                self.scored_leaf_proof_steps.pop();
            }
        }
    }

    pub fn leaf_proof_steps_with_stats(&self) -> Vec<(ProofStep, ProofStats)> {
        self.scored_leaf_proof_steps
            .iter()
            .map(|(_, _, proof_step, stats)| (proof_step.clone(), stats.clone()))
            .collect::<Vec<(ProofStep, ProofStats)>>()
    }

    pub fn total_leaf_proofs(&self) -> usize {
        self.scored_leaf_proof_steps.len()
    }

    /// Check if the resolvent has already been seen at the current depth or below and if so, return False.
    /// Otherwise, add it to the seen set and return True
    pub fn check_resolvent(&mut self, proof_step: &ProofStep) -> bool {
        if !self.skip_seen_resolvents {
            return true;
        }
        self.stats.resolvent_checks += 1;
        let mut hasher = FxHasher::default();
        proof_step.resolvent.hash(&mut hasher);
        let resolvent_hash = hasher.finish();
        if let Some((prev_depth, prev_similarity)) = self.seen_resolvents.get(&resolvent_hash) {
            if prev_depth <= &proof_step.depth && prev_similarity >= &proof_step.running_similarity
            {
                self.stats.resolvent_check_hits += 1;
                return false;
            }
        }
        self.seen_resolvents.insert(
            resolvent_hash,
            (proof_step.depth, proof_step.running_similarity),
        );
        true
    }

    pub fn calc_similarity<T>(&mut self, source: &T, target: &T) -> f64
    where
        T: SimilarityComparable + IntoPy<PyObject> + Clone,
    {
        let (src_sym, src_embed, src_embed_ptr) = source.similarity_fields();
        let (tgt_sym, tgt_embed, tgt_embed_ptr) = target.similarity_fields();
        let src_param = (src_sym, src_embed);
        let tgt_param = (tgt_sym, tgt_embed);
        match self.similarity_cache.as_mut() {
            Some(cache) => {
                let key = (
                    src_param.0.clone(),
                    src_embed_ptr.clone(),
                    tgt_param.0.clone(),
                    tgt_embed_ptr.clone(),
                );
                if let Some(similarity) = cache.get(&key) {
                    self.stats.similarity_cache_hits += 1;
                    *similarity
                } else {
                    let similarity =
                        raw_calc_similarity(&self.py_similarity_fn, source.clone(), target.clone());
                    cache.insert(key, similarity);
                    similarity
                }
            }
            None => raw_calc_similarity(&self.py_similarity_fn, source.clone(), target.clone()),
        }
    }
}

// perform the actual similarity calculation, ignoring caching
fn raw_calc_similarity<T>(py_similarity_fn: &Option<PyObject>, src: T, tgt: T) -> f64
where
    T: SimilarityComparable + IntoPy<PyObject>,
{
    match py_similarity_fn {
        Some(py_similarity_fn) => {
            Python::with_gil(|py| {
                // TODO: make sure similarity_func is callable, and handle errors better
                let py_res = py_similarity_fn.call1(py, (src, tgt)).unwrap();
                py_res.extract::<f64>(py).unwrap()
            })
        }
        None => {
            // if no similarity function is provided, just do plain string equality on symbols
            if src.symbol() == tgt.symbol() {
                1.0
            } else {
                0.0
            }
        }
    }
}

#[cfg(test)]
mod test {
    use crate::types::{Atom, CNFDisjunction, CNFLiteral, Predicate};
    use std::collections::BTreeSet;
    use std::collections::HashMap;

    fn create_proof_step(depth: usize, running_similarity: f64) -> super::ProofStep {
        let pred = Predicate::new("Rust", None);
        let disj = CNFDisjunction::new(BTreeSet::new());
        let lit = CNFLiteral::new(Atom::new(pred.clone(), vec![]), true);
        let subs = HashMap::new();
        super::ProofStep::new(
            disj.clone(),
            disj.clone(),
            lit.clone(),
            lit.clone(),
            subs.clone(),
            subs.clone(),
            disj.clone(),
            0.5,
            running_similarity,
            depth,
            None,
        )
    }

    #[test]
    fn test_new() {
        let ctx = super::ProofContext::new(0.0, Some(2), false, false, None);
        assert_eq!(ctx.max_proofs, Some(2));
    }

    #[test]
    fn test_record_leaf_proof_keeps_step_with_highest_similarity() {
        let mut ctx = super::ProofContext::new(0.0, Some(1), false, false, None);
        let proof_step1 = create_proof_step(2, 0.5);
        ctx.record_leaf_proof(proof_step1.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.len(), 1);
        assert_eq!(ctx.scored_leaf_proof_steps[0].2, proof_step1);
        // higher similarity, so it should kick out step 1
        let proof_step2 = create_proof_step(4, 0.6);
        ctx.record_leaf_proof(proof_step2.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.len(), 1);
        assert_eq!(ctx.scored_leaf_proof_steps[0].2, proof_step2);
    }

    #[test]
    fn test_record_leaf_proof_keeps_step_with_lowest_depth_if_similarity_is_equal() {
        let mut ctx = super::ProofContext::new(0.0, Some(1), false, false, None);
        let proof_step1 = create_proof_step(4, 0.5);
        ctx.record_leaf_proof(proof_step1.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.len(), 1);
        assert_eq!(ctx.scored_leaf_proof_steps[0].2, proof_step1);
        // higher similarity, so it should kick out step 1
        let proof_step2 = create_proof_step(3, 0.5);
        ctx.record_leaf_proof(proof_step2.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.len(), 1);
        assert_eq!(ctx.scored_leaf_proof_steps[0].2, proof_step2);
    }

    #[test]
    fn test_check_resolvent() {
        let mut ctx: super::ProofContext =
            super::ProofContext::new(0.0, Some(1), true, false, None);
        let proof_step = create_proof_step(4, 0.5);
        assert!(ctx.check_resolvent(&proof_step));

        let worse_sim_step = create_proof_step(4, 0.4);
        assert!(!ctx.check_resolvent(&worse_sim_step));

        let worse_depth_step = create_proof_step(5, 0.5);
        assert!(!ctx.check_resolvent(&worse_depth_step));

        let better_sim_step = create_proof_step(4, 0.6);
        assert!(ctx.check_resolvent(&better_sim_step));

        let better_depth_step = create_proof_step(3, 0.5);
        assert!(ctx.check_resolvent(&better_depth_step));

        assert_eq!(ctx.stats.resolvent_checks, 5);
        assert_eq!(ctx.stats.resolvent_check_hits, 2);
    }
}
