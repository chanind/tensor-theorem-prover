use atomic_float::AtomicF64;
use pyo3::prelude::*;
use rustc_hash::{FxHashMap, FxHasher};
use std::hash::{Hash, Hasher};
use std::sync::atomic::Ordering::Relaxed;
use std::sync::RwLock;

use crate::types::SimilarityComparable;

use super::proof_step::ProofStepNode;
use super::similarity_cache::SimilarityCache;
use super::ProofStep;
use super::{FrozenProofStats, ProofStats};

/// Helper class which accumulates successful proof steps and keeps track of stats during the proof process
pub struct ProofContext {
    pub stats: ProofStats,
    pub min_similarity_threshold: AtomicF64,
    pub max_proofs: Option<usize>,
    scored_leaf_proof_steps: RwLock<Vec<(f64, usize, ProofStepNode, FrozenProofStats)>>,
    skip_seen_resolvents: bool,
    seen_resolvents: RwLock<FxHashMap<u64, (usize, f64)>>,
    similarity_cache: Option<RwLock<SimilarityCache>>,
    py_similarity_fn: Option<PyObject>,
}
impl ProofContext {
    pub fn new(
        initial_min_similarity_threshold: f64,
        max_proofs: Option<usize>,
        skip_seen_resolvents: bool,
        similarity_cache: Option<SimilarityCache>,
        py_similarity_fn: Option<PyObject>,
    ) -> Self {
        Self {
            stats: ProofStats::new(),
            min_similarity_threshold: AtomicF64::new(initial_min_similarity_threshold),
            max_proofs,
            scored_leaf_proof_steps: RwLock::new(Vec::new()),
            seen_resolvents: RwLock::new(FxHashMap::default()),
            skip_seen_resolvents,
            similarity_cache: similarity_cache.map(RwLock::new),
            py_similarity_fn,
        }
    }

    pub fn record_leaf_proof(&self, proof_step: ProofStepNode) {
        // make sure to clone the stats before appending, since the stats will continue to get mutated after this
        let scored_leaf_proof_steps_guard = self.scored_leaf_proof_steps.write();
        let mut scored_leaf_proof_steps = scored_leaf_proof_steps_guard.unwrap();
        scored_leaf_proof_steps.push((
            proof_step.inner.running_similarity,
            proof_step.inner.depth,
            proof_step,
            self.stats.copy_and_freeze(),
        ));
        scored_leaf_proof_steps.sort_by(|a, b| {
            if a.0 == b.0 {
                a.1.cmp(&b.1)
            } else {
                b.0.partial_cmp(&a.0).unwrap()
            }
        });
        if let Some(max_proofs) = self.max_proofs {
            if scored_leaf_proof_steps.len() > max_proofs {
                // Remove the proof step with the lowest similarity
                scored_leaf_proof_steps.pop();
                self.stats.discarded_proofs.fetch_add(1, Relaxed);
                self.min_similarity_threshold
                    .swap(scored_leaf_proof_steps.last().unwrap().0, Relaxed);
            }
        }
    }

    pub fn leaf_proof_steps_with_stats(&self) -> Vec<(ProofStep, FrozenProofStats)> {
        let scored_leaf_proof_steps_guard = self.scored_leaf_proof_steps.read();
        scored_leaf_proof_steps_guard
            .unwrap()
            .iter()
            .map(|(_, _, proof_step, stats)| ((*proof_step.inner).clone(), stats.clone()))
            .collect::<Vec<(ProofStep, FrozenProofStats)>>()
    }

    pub fn total_leaf_proofs(&self) -> usize {
        self.scored_leaf_proof_steps.read().unwrap().len()
    }

    /// Check if the resolvent has already been seen at the current depth or below and if so, return False.
    /// Otherwise, add it to the seen set and return True
    pub fn check_resolvent(&self, proof_step: &ProofStep) -> bool {
        if !self.skip_seen_resolvents {
            return true;
        }
        self.stats.resolvent_checks.fetch_add(1, Relaxed);
        let mut hasher = FxHasher::default();
        proof_step.resolvent.hash(&mut hasher);
        let resolvent_hash = hasher.finish();
        let cached_seen_resolvent = self.seen_resolvents.read().unwrap().get(&resolvent_hash);
        if let Some((prev_depth, prev_similarity)) = cached_seen_resolvent {
            if prev_depth <= &proof_step.depth && prev_similarity >= &proof_step.running_similarity
            {
                self.stats.resolvent_check_hits.fetch_add(1, Relaxed);
                return false;
            }
        }
        // explicit drop to make sure we don't hold the read lock while we're writing
        drop(cached_seen_resolvent);
        self.seen_resolvents.write().unwrap().insert(
            resolvent_hash,
            (proof_step.depth, proof_step.running_similarity),
        );
        true
    }

    pub fn calc_similarity<T>(&self, source: &T, target: &T) -> f64
    where
        T: SimilarityComparable + IntoPy<PyObject> + Clone,
    {
        let src_key = source.similarity_key();
        let tgt_key = target.similarity_key();
        let key = src_key ^ tgt_key;
        match self.similarity_cache {
            Some(cache) => {
                if let Some(similarity) = cache.read().unwrap().get(&key) {
                    self.stats.similarity_cache_hits.fetch_add(1, Relaxed);
                    *similarity
                } else {
                    let similarity =
                        raw_calc_similarity(&self.py_similarity_fn, source.clone(), target.clone());
                    cache.write().unwrap().insert(key.clone(), similarity);
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
    use rustc_hash::FxHashMap;
    use std::sync::atomic::Ordering::Relaxed;

    use crate::prover::{ProofStep, ProofStepNode};
    use crate::types::{Atom, CNFDisjunction, CNFLiteral, Predicate};
    use crate::util::PyArcItem;
    use std::collections::BTreeSet;

    fn create_proof_step_node(depth: usize, running_similarity: f64) -> ProofStepNode {
        let pred = Predicate::new("Rust", None);
        let disj = PyArcItem::new(CNFDisjunction::new(BTreeSet::new()));
        let lit = PyArcItem::new(CNFLiteral::new(Atom::new(pred.clone(), vec![]), true));
        let subs = FxHashMap::default();
        ProofStepNode::new(ProofStep::new(
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
        ))
    }

    #[test]
    fn test_new() {
        let ctx = super::ProofContext::new(0.0, Some(2), false, None, None);
        assert_eq!(ctx.max_proofs, Some(2));
    }

    #[test]
    fn test_record_leaf_proof_keeps_step_with_highest_similarity() {
        let mut ctx = super::ProofContext::new(0.0, Some(1), false, None, None);
        let proof_step1 = create_proof_step_node(2, 0.5);
        ctx.record_leaf_proof(proof_step1.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.read().unwrap().len(), 1);
        assert_eq!(
            ctx.scored_leaf_proof_steps.read().unwrap()[0].2,
            proof_step1
        );
        // higher similarity, so it should kick out step 1
        let proof_step2 = create_proof_step_node(4, 0.6);
        ctx.record_leaf_proof(proof_step2.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.read().unwrap().len(), 1);
        assert_eq!(
            ctx.scored_leaf_proof_steps.read().unwrap()[0].2,
            proof_step2
        );
    }

    #[test]
    fn test_record_leaf_proof_keeps_step_with_lowest_depth_if_similarity_is_equal() {
        let mut ctx = super::ProofContext::new(0.0, Some(1), false, None, None);
        let proof_step1 = create_proof_step_node(4, 0.5);
        ctx.record_leaf_proof(proof_step1.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.read().unwrap().len(), 1);
        assert_eq!(
            ctx.scored_leaf_proof_steps.read().unwrap()[0].2,
            proof_step1
        );
        // higher similarity, so it should kick out step 1
        let proof_step2 = create_proof_step_node(3, 0.5);
        ctx.record_leaf_proof(proof_step2.clone());
        assert_eq!(ctx.scored_leaf_proof_steps.read().unwrap().len(), 1);
        assert_eq!(
            ctx.scored_leaf_proof_steps.read().unwrap()[0].2,
            proof_step2
        );
    }

    #[test]
    fn test_check_resolvent() {
        let mut ctx: super::ProofContext = super::ProofContext::new(0.0, Some(1), true, None, None);
        let proof_step = create_proof_step_node(4, 0.5);
        assert!(ctx.check_resolvent(&proof_step.inner));

        let worse_sim_step = create_proof_step_node(4, 0.4);
        assert!(!ctx.check_resolvent(&worse_sim_step.inner));

        let worse_depth_step = create_proof_step_node(5, 0.5);
        assert!(!ctx.check_resolvent(&worse_depth_step.inner));

        let better_sim_step = create_proof_step_node(4, 0.6);
        assert!(ctx.check_resolvent(&better_sim_step.inner));

        let better_depth_step = create_proof_step_node(3, 0.5);
        assert!(ctx.check_resolvent(&better_depth_step.inner));

        assert_eq!(ctx.stats.resolvent_checks.load(Relaxed), 5);
        assert_eq!(ctx.stats.resolvent_check_hits.load(Relaxed), 2);
    }
}
