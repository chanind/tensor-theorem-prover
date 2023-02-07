use std::collections::{BTreeSet, VecDeque};
use std::sync::atomic::Ordering::Relaxed;

use pyo3::prelude::*;

use crate::types::CNFDisjunction;
use crate::util::PyArcItem;

use super::operations::resolve;
use super::similarity_cache::SimilarityCache;
use super::{LocalProofContext, LocalProofStats, Proof, ProofStepNode, SharedProofContext};

#[derive(Clone, Debug)]
struct ResolutionProverConfig {
    max_proof_depth: usize,
    max_resolution_attempts: Option<usize>,
    max_resolvent_width: Option<usize>,
    skip_seen_resolvents: bool,
    find_highest_similarity_proofs: bool,
    eval_batch_size: usize,
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
        eval_batch_size: usize,
    ) -> Self {
        let config = ResolutionProverConfig {
            max_proof_depth,
            max_resolvent_width,
            max_resolution_attempts,
            skip_seen_resolvents,
            find_highest_similarity_proofs,
            eval_batch_size,
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
        py: Python<'_>,
        inverted_goals: BTreeSet<CNFDisjunction>,
        extra_knowledge: Option<BTreeSet<CNFDisjunction>>,
        max_proofs: Option<usize>,
        skip_seen_resolvents: Option<bool>,
    ) -> (Vec<Proof>, LocalProofStats) {
        let parsed_extra_knowledge = extra_knowledge.unwrap_or_default();
        let mut proofs = vec![];
        let mut knowledge = self.base_knowledge.clone();
        let arc_inverted_goals = knowledge_to_arc(inverted_goals.clone());
        knowledge.extend(knowledge_to_arc(parsed_extra_knowledge));
        knowledge.extend(arc_inverted_goals.clone());
        let ctx = SharedProofContext::new(
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

        py.allow_threads(|| {
            threadpool.scope(|scope| {
                let batch = arc_inverted_goals
                    .into_iter()
                    .map(|inverted_goal| (inverted_goal, None))
                    .collect::<VecDeque<_>>();
                let worker_ctx = LocalProofContext::new(&ctx);
                search_for_proofs_batch(batch, &self.config, &knowledge, worker_ctx, scope);
            });
        });

        let frozen_stats = ctx.stats.copy_and_freeze();
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

        (proofs, frozen_stats)
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

fn search_for_proofs_batch<'a>(
    batch: VecDeque<(PyArcItem<CNFDisjunction>, Option<ProofStepNode>)>,
    config: &'a ResolutionProverConfig,
    knowledge: &'a BTreeSet<PyArcItem<CNFDisjunction>>,
    mut ctx: LocalProofContext<'a>,
    scope: &rayon::Scope<'a>,
) {
    let mut next_batch = batch;
    loop {
        let mut results_accumulator = VecDeque::new();
        for (goal, parent_state) in next_batch {
            search_proof_step(
                goal,
                config,
                knowledge,
                &mut ctx,
                parent_state,
                &mut results_accumulator,
            );
            if results_accumulator.len() >= config.eval_batch_size {
                let next_batch = results_accumulator
                    .drain(..config.eval_batch_size)
                    .collect();
                let next_ctx = LocalProofContext::new(&ctx.shared);
                scope.spawn(move |next_scope| {
                    search_for_proofs_batch(next_batch, config, knowledge, next_ctx, next_scope);
                });
            }
        }
        ctx.sync_with_shared_ctx();
        if results_accumulator.is_empty() {
            return;
        }
        next_batch = results_accumulator;
    }
}

fn search_proof_step<'a>(
    goal: PyArcItem<CNFDisjunction>,
    config: &ResolutionProverConfig,
    knowledge: &BTreeSet<PyArcItem<CNFDisjunction>>,
    ctx: &mut LocalProofContext,
    parent_state: Option<ProofStepNode>,
    results_accumulator: &mut VecDeque<(PyArcItem<CNFDisjunction>, Option<ProofStepNode>)>,
) {
    let depth = parent_state.as_ref().map(|s| s.inner.depth).unwrap_or(0);
    if parent_state.is_some() && depth >= config.max_proof_depth {
        return;
    }
    if let Some(max_resolution_attempts) = config.max_resolution_attempts {
        if ctx.shared.stats.attempted_resolutions.load(Relaxed) >= max_resolution_attempts {
            return;
        }
    }
    if let Some(max_proofs) = ctx.shared.max_proofs {
        if !config.find_highest_similarity_proofs && ctx.shared.total_leaf_proofs() >= max_proofs {
            return;
        }
    }
    if depth >= ctx.stats.max_depth_seen {
        ctx.stats.max_depth_seen = depth + 1;
    }
    let mut num_sucessful_resolutions = 0;
    for clause in knowledge {
        // resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
        // so we know what the length of the resolvent will be before we even try to resolve
        if let Some(max_resolvent_width) = config.max_resolvent_width {
            if clause.item.literals.len() + goal.item.literals.len() - 2 > max_resolvent_width {
                continue;
            }
        }
        let next_steps = resolve(&goal, &clause, ctx, parent_state.as_ref());
        if next_steps.len() > 0 {
            num_sucessful_resolutions += 1;
        }
        let min_similarity_threshold = ctx.shared.min_similarity_threshold.load(Relaxed);
        for next_step in next_steps {
            if next_step.inner.resolvent.item.literals.is_empty() {
                ctx.shared.record_leaf_proof(next_step);
            } else if depth + 1 < config.max_proof_depth {
                if next_step.inner.running_similarity <= min_similarity_threshold {
                    continue;
                }
                if !ctx.check_resolvent(&next_step.inner) {
                    continue;
                }
                let resolvent_width = next_step.inner.resolvent.item.literals.len();
                if resolvent_width > ctx.stats.max_resolvent_width_seen {
                    ctx.stats.max_resolvent_width_seen = resolvent_width;
                }
                results_accumulator.push_back((next_step.inner.resolvent.clone(), Some(next_step)));
            }
        }
    }
    // update stats at the end in bulk, doing this in the loop dramatically slows down multi-threaded performance
    // it may even be worth it to do this less often then every eval step
    ctx.stats.attempted_resolutions += knowledge.len();
    ctx.stats.successful_resolutions += num_sucessful_resolutions;
}

fn knowledge_to_arc(knowledge: BTreeSet<CNFDisjunction>) -> BTreeSet<PyArcItem<CNFDisjunction>> {
    knowledge
        .into_iter()
        .map(|x| PyArcItem::new(x.clone()))
        .collect()
}
