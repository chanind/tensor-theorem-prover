use atomic_float::AtomicF64;
use dashmap::DashMap;
use pyo3::prelude::*;
use rustc_hash::FxHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};
use std::sync::atomic::Ordering::Relaxed;
use std::sync::RwLock;

use crate::types::SimilarityComparable;

use super::proof_step::ProofStepNode;
use super::similarity_cache::{FallthroughSimilarityCache, SimilarityCache};
use super::ProofStep;
use super::{LocalProofStats, SharedProofStats};

type SeenResolventsMap = DashMap<u64, (usize, f64), BuildHasherDefault<FxHasher>>;

/// Helper class which accumulates successful proof steps and keeps track of stats during the proof process
pub struct SharedProofContext {
    pub stats: SharedProofStats,
    // pub min_similarity_threshold: f64,
    pub min_similarity_threshold: AtomicF64,
    pub max_proofs: Option<usize>,
    scored_leaf_proof_steps: RwLock<Vec<(f64, usize, ProofStepNode, LocalProofStats)>>,
    skip_seen_resolvents: bool,
    seen_resolvents: SeenResolventsMap,
    similarity_cache: Option<SimilarityCache>,
    py_similarity_fn: Option<PyObject>,
}
impl SharedProofContext {
    pub fn new(
        initial_min_similarity_threshold: f64,
        max_proofs: Option<usize>,
        skip_seen_resolvents: bool,
        similarity_cache: Option<SimilarityCache>,
        py_similarity_fn: Option<PyObject>,
    ) -> Self {
        Self {
            stats: SharedProofStats::new(),
            min_similarity_threshold: AtomicF64::new(initial_min_similarity_threshold),
            max_proofs,
            scored_leaf_proof_steps: RwLock::new(Vec::new()),
            seen_resolvents: SeenResolventsMap::default(),
            skip_seen_resolvents,
            similarity_cache,
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

    pub fn leaf_proof_steps_with_stats(&self) -> Vec<(ProofStep, LocalProofStats)> {
        let scored_leaf_proof_steps_guard = self.scored_leaf_proof_steps.read();
        scored_leaf_proof_steps_guard
            .unwrap()
            .iter()
            .map(|(_, _, proof_step, stats)| ((*proof_step.inner).clone(), stats.clone()))
            .collect::<Vec<(ProofStep, LocalProofStats)>>()
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
        let mut hasher = FxHasher::default();
        proof_step.resolvent.hash(&mut hasher);
        let resolvent_hash = hasher.finish();
        let (is_new, _) = self.check_seen_resolvent_info(resolvent_hash, proof_step);
        is_new
    }

    fn check_seen_resolvent_info(
        &self,
        resolvent_hash: u64,
        proof_step: &ProofStep,
    ) -> (bool, (usize, f64)) {
        if let Some(seen_resolvent_data) = self.seen_resolvents.get(&resolvent_hash) {
            let (prev_depth, prev_similarity) = *seen_resolvent_data;
            if prev_depth <= proof_step.depth && prev_similarity >= proof_step.running_similarity {
                return (false, (prev_depth, prev_similarity));
            }
        }
        let seen_resolvent_data = (proof_step.depth, proof_step.running_similarity);
        self.seen_resolvents
            .insert(resolvent_hash, seen_resolvent_data);
        return (true, seen_resolvent_data);
    }

    pub fn calc_similarity<T>(&self, source: &T, target: &T) -> f64
    where
        T: SimilarityComparable + IntoPy<PyObject> + Clone,
    {
        match &self.similarity_cache {
            Some(_) => {
                let src_key = source.similarity_key();
                let tgt_key = target.similarity_key();
                let key = src_key ^ tgt_key;
                self.calc_similarity_cached(source, target, key)
            }
            None => raw_calc_similarity(&self.py_similarity_fn, source, target),
        }
    }

    fn calc_similarity_cached<T>(&self, source: &T, target: &T, key: u64) -> f64
    where
        T: SimilarityComparable + IntoPy<PyObject> + Clone,
    {
        let cache = self.similarity_cache.as_ref().unwrap();
        if let Some(similarity) = cache.get(&key) {
            return *similarity;
        }
        // avoiding if/else here to avoid deadlocks around the read and write locks held at the same time
        let similarity = raw_calc_similarity(&self.py_similarity_fn, source, target);
        cache.insert(key.clone(), similarity);
        similarity
    }
}

/// A wrapper context for each thread to avoid needing to always load from the shared context
/// to reduce contention
pub struct LocalProofContext<'a> {
    pub shared: &'a SharedProofContext,
    pub stats: LocalProofStats,
    fallthrough_similarity_cache: Option<FallthroughSimilarityCache>,
}

impl<'a> LocalProofContext<'a> {
    pub fn new(shared: &'a SharedProofContext) -> Self {
        let fallthrough_similarity_cache = match &shared.similarity_cache {
            Some(_) => Some(FallthroughSimilarityCache::default()),
            None => None,
        };
        Self {
            shared,
            fallthrough_similarity_cache,
            stats: LocalProofStats::new(),
        }
    }

    /// Calculate the similarity between two objects
    /// Caches the results locally as well to reduce contention with the shared context
    pub fn calc_similarity<T>(&mut self, source: &T, target: &T) -> f64
    where
        T: SimilarityComparable + IntoPy<PyObject> + Clone,
    {
        match self.fallthrough_similarity_cache.as_mut() {
            Some(cache) => {
                let src_key = source.similarity_key();
                let tgt_key = target.similarity_key();
                let key = src_key ^ tgt_key;
                if let Some(similarity) = cache.get(&key) {
                    return *similarity;
                }
                let similarity = self.shared.calc_similarity_cached(source, target, key);
                cache.insert(key.clone(), similarity);
                similarity
            }
            None => self.shared.calc_similarity(source, target),
        }
    }

    /// Check if the resolvent has already been seen at the current depth or below and if so, return False.
    /// Otherwise, add it to the seen set and return True
    pub fn check_resolvent(&mut self, proof_step: &ProofStep) -> bool {
        self.shared.check_resolvent(proof_step)
    }

    pub fn min_similarity_threshold(&self) -> f64 {
        self.shared.min_similarity_threshold.load(Relaxed)
    }

    /// Write out any local state to the shared context
    pub fn sync_with_shared_ctx(&mut self) {
        let main_stats = &self.shared.stats;
        main_stats
            .attempted_resolutions
            .fetch_add(self.stats.attempted_resolutions, Relaxed);
        main_stats
            .successful_resolutions
            .fetch_add(self.stats.successful_resolutions, Relaxed);
        main_stats
            .max_resolvent_width_seen
            .fetch_max(self.stats.max_resolvent_width_seen, Relaxed);
        main_stats
            .max_depth_seen
            .fetch_max(self.stats.max_depth_seen, Relaxed);
        main_stats
            .discarded_proofs
            .fetch_add(self.stats.discarded_proofs, Relaxed);
        self.stats = LocalProofStats::new();
    }
}

// perform the actual similarity calculation, ignoring caching
fn raw_calc_similarity<T>(py_similarity_fn: &Option<PyObject>, src: &T, tgt: &T) -> f64
where
    T: SimilarityComparable + IntoPy<PyObject> + Clone,
{
    match py_similarity_fn {
        Some(py_similarity_fn) => {
            Python::with_gil(|py| {
                // TODO: make sure similarity_func is callable, and handle errors better
                let py_res = py_similarity_fn
                    .call1(py, (src.clone(), tgt.clone()))
                    .unwrap();
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
        let ctx = super::SharedProofContext::new(0.0, Some(2), false, None, None);
        assert_eq!(ctx.max_proofs, Some(2));
    }

    #[test]
    fn test_record_leaf_proof_keeps_step_with_highest_similarity() {
        let ctx = super::SharedProofContext::new(0.0, Some(1), false, None, None);
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
        let ctx = super::SharedProofContext::new(0.0, Some(1), false, None, None);
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
        let ctx: super::SharedProofContext =
            super::SharedProofContext::new(0.0, Some(1), true, None, None);
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
    }
}
