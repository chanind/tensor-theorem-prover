use std::collections::BTreeSet;
use std::sync::atomic::Ordering::Relaxed;
use std::sync::Arc;

use pyo3::prelude::*;

use crate::types::CNFDisjunction;
use crate::util::PyArcItem;

use super::operations::resolve;
use super::similarity_cache::SimilarityCache;
use super::{FrozenProofStats, Proof, ProofContext, ProofStepNode};

#[derive(Clone, Debug)]
struct ResolutionProverConfig {
    max_proof_depth: usize,
    max_resolution_attempts: Option<usize>,
    max_resolvent_width: Option<usize>,
    skip_seen_resolvents: bool,
    find_highest_similarity_proofs: bool,
}

#[pyclass(name = "RsResolutionProverBackend")]
pub struct ResolutionProverBackend {
    min_similarity_threshold: f64,
    py_similarity_fn: Option<PyObject>,
    similarity_cache: Option<SimilarityCache>,
    base_knowledge: BTreeSet<PyArcItem<CNFDisjunction>>,
    num_workers: usize,
    config: ResolutionProverConfig,
}
#[pymethods]
impl ResolutionProverBackend {
    #[new]
    pub fn new(
        max_proof_depth: usize,
        max_resolvent_width: Option<usize>,
        max_resolution_attempts: Option<usize>,
        py_similarity_fn: Option<PyObject>,
        min_similarity_threshold: f64,
        cache_similarity: bool,
        skip_seen_resolvents: bool,
        find_highest_similarity_proofs: bool,
        base_knowledge: BTreeSet<PyArcItem<CNFDisjunction>>,
        num_workers: usize,
    ) -> Self {
        let config = ResolutionProverConfig {
            max_proof_depth,
            max_resolvent_width,
            max_resolution_attempts,
            skip_seen_resolvents,
            find_highest_similarity_proofs,
        };
        Self {
            py_similarity_fn,
            min_similarity_threshold,
            similarity_cache: if cache_similarity {
                Some(SimilarityCache::default())
            } else {
                None
            },
            base_knowledge,
            num_workers,
            config,
        }
    }

    pub fn extend_knowledge(&mut self, knowledge: BTreeSet<CNFDisjunction>) {
        self.base_knowledge.extend(knowledge_to_arc(knowledge));
    }

    /// Find all possible proofs for the given goal, sorted by similarity score.
    /// Return the proofs and the stats for the proof search.
    pub fn prove_all_with_stats(
        &self,
        inverted_goals: BTreeSet<CNFDisjunction>,
        extra_knowledge: Option<BTreeSet<CNFDisjunction>>,
        max_proofs: Option<usize>,
        skip_seen_resolvents: Option<bool>,
    ) -> (Vec<Proof>, FrozenProofStats) {
        let parsed_extra_knowledge = extra_knowledge.unwrap_or_default();
        let mut proofs = vec![];
        let mut knowledge = self.base_knowledge.clone();
        let arc_inverted_goals = knowledge_to_arc(inverted_goals.clone());
        knowledge.extend(knowledge_to_arc(parsed_extra_knowledge));
        knowledge.extend(arc_inverted_goals.clone());
        let ctx = ProofContext::new(
            self.min_similarity_threshold,
            max_proofs,
            skip_seen_resolvents.unwrap_or(self.config.skip_seen_resolvents),
            self.similarity_cache.clone(),
            self.py_similarity_fn.clone(),
        );

        let threadpool = rayon::ThreadPoolBuilder::new()
            .num_threads(self.num_workers)
            .build()
            .unwrap();

        let arc_config = Arc::new(self.config.clone());
        threadpool.scope(|scope| {
            for inverted_goal in arc_inverted_goals {
                let cloned_config = Arc::clone(&arc_config);
                scope.spawn(move |next_scope| {
                    evaluate_proof_step(
                        cloned_config,
                        inverted_goal.clone(),
                        &knowledge,
                        &ctx,
                        0,
                        None,
                        next_scope,
                    );
                });
            }
        });

        for (leaf_proof_step, leaf_proof_stats) in ctx.leaf_proof_steps_with_stats() {
            proofs.push(Proof::new(
                leaf_proof_step.running_similarity,
                leaf_proof_stats,
                leaf_proof_step,
            ));
        }

        proofs.sort_by(|a, b| b.similarity.partial_cmp(&a.similarity).unwrap());
        if let Some(max_proofs) = max_proofs {
            proofs.truncate(max_proofs);
        }

        (proofs, ctx.stats.copy_and_freeze())
    }

    pub fn purge_similarity_cache(&mut self) {
        if let Some(_) = self.similarity_cache.as_mut() {
            self.similarity_cache = Some(SimilarityCache::default());
        }
    }

    pub fn reset(&mut self) {
        self.base_knowledge = BTreeSet::new();
        self.purge_similarity_cache();
    }
}

fn evaluate_proof_step<'a>(
    config: Arc<ResolutionProverConfig>,
    goal: PyArcItem<CNFDisjunction>,
    knowledge: &'a BTreeSet<PyArcItem<CNFDisjunction>>,
    ctx: &'a ProofContext,
    depth: usize,
    parent_state: Option<ProofStepNode>,
    scope: &rayon::Scope<'a>,
) {
    if parent_state.is_some() && depth >= config.max_proof_depth {
        return;
    }
    if let Some(max_resolution_attempts) = config.max_resolution_attempts {
        if ctx.stats.attempted_resolutions.load(Relaxed) >= max_resolution_attempts {
            return;
        }
    }
    if let Some(max_proofs) = ctx.max_proofs {
        if !config.find_highest_similarity_proofs && ctx.total_leaf_proofs() >= max_proofs {
            return;
        }
    }
    ctx.stats.max_depth_seen.fetch_max(depth + 1, Relaxed);

    for clause in knowledge {
        // resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
        // so we know what the length of the resolvent will be before we even try to resolve
        if let Some(max_resolvent_width) = config.max_resolvent_width {
            if clause.item.literals.len() + goal.item.literals.len() - 2 > max_resolvent_width {
                continue;
            }
        }
        ctx.stats.attempted_resolutions.fetch_add(1, Relaxed);
        let next_steps = resolve(&goal, &clause, ctx, parent_state.as_ref());
        if next_steps.len() > 0 {
            ctx.stats.successful_resolutions.fetch_add(1, Relaxed);
        }
        for next_step in next_steps {
            if next_step.inner.resolvent.item.literals.is_empty() {
                ctx.record_leaf_proof(next_step);
            } else {
                if next_step.inner.running_similarity <= ctx.min_similarity_threshold.load(Relaxed)
                {
                    continue;
                }
                if !ctx.check_resolvent(&next_step.inner) {
                    continue;
                }
                let resolvent_width = next_step.inner.resolvent.item.literals.len();
                ctx.stats
                    .max_resolvent_width_seen
                    .fetch_max(resolvent_width, Relaxed);
                let cloned_config = Arc::clone(&config);
                scope.spawn(move |next_scope| {
                    evaluate_proof_step(
                        cloned_config,
                        next_step.inner.resolvent.clone(),
                        knowledge,
                        ctx,
                        depth + 1,
                        Some(next_step),
                        next_scope,
                    );
                });
            }
        }
    }
}

fn knowledge_to_arc(knowledge: BTreeSet<CNFDisjunction>) -> BTreeSet<PyArcItem<CNFDisjunction>> {
    knowledge
        .into_iter()
        .map(|x| PyArcItem::new(x.clone()))
        .collect()
}
