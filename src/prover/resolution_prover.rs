use std::collections::HashSet;

use pyo3::prelude::*;

use crate::types::CNFDisjunction;
use crate::util::PyArcItem;

use super::operations::resolve;
use super::similarity_cache::SimilarityCache;
use super::{Proof, ProofContext, ProofStats, ProofStepNode};

#[pyclass(name = "RsResolutionProverBackend")]
pub struct ResolutionProverBackend {
    max_proof_depth: usize,
    max_resolution_attempts: Option<usize>,
    max_resolvent_width: Option<usize>,
    min_similarity_threshold: f64,
    py_similarity_fn: Option<PyObject>,
    similarity_cache: Option<SimilarityCache>,
    skip_seen_resolvents: bool,
    find_highest_similarity_proofs: bool,
    base_knowledge: HashSet<PyArcItem<CNFDisjunction>>,
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
        base_knowledge: HashSet<PyArcItem<CNFDisjunction>>,
    ) -> Self {
        Self {
            max_proof_depth,
            max_resolvent_width,
            max_resolution_attempts,
            py_similarity_fn,
            min_similarity_threshold,
            similarity_cache: if cache_similarity {
                Some(SimilarityCache::default())
            } else {
                None
            },
            skip_seen_resolvents,
            find_highest_similarity_proofs,
            base_knowledge,
        }
    }

    pub fn extend_knowledge(&mut self, knowledge: HashSet<CNFDisjunction>) {
        self.base_knowledge.extend(knowledge_to_arc(knowledge));
    }

    /// Find all possible proofs for the given goal, sorted by similarity score.
    /// Return the proofs and the stats for the proof search.
    pub fn prove_all_with_stats(
        &self,
        inverted_goals: HashSet<CNFDisjunction>,
        extra_knowledge: Option<HashSet<CNFDisjunction>>,
        max_proofs: Option<usize>,
        skip_seen_resolvents: Option<bool>,
    ) -> (Vec<Proof>, ProofStats) {
        let parsed_extra_knowledge = extra_knowledge.unwrap_or_default();
        let mut proofs = vec![];
        let mut knowledge = self.base_knowledge.clone();
        let arc_inverted_goals = knowledge_to_arc(inverted_goals.clone());
        knowledge.extend(knowledge_to_arc(parsed_extra_knowledge));
        knowledge.extend(arc_inverted_goals.clone());
        let mut ctx = ProofContext::new(
            self.min_similarity_threshold,
            max_proofs,
            skip_seen_resolvents.unwrap_or(self.skip_seen_resolvents),
            self.similarity_cache.clone(),
            self.py_similarity_fn.clone(),
        );

        for inverted_goal in arc_inverted_goals {
            self.prove_all_recursive(inverted_goal.clone(), &knowledge, &mut ctx, 0, None);
            for (leaf_proof_step, leaf_proof_stats) in ctx.leaf_proof_steps_with_stats() {
                proofs.push(Proof::new(
                    (*inverted_goal.item).clone(),
                    leaf_proof_step.running_similarity,
                    leaf_proof_stats,
                    leaf_proof_step,
                ));
            }
        }

        proofs.sort_by(|a, b| b.similarity.partial_cmp(&a.similarity).unwrap());
        if let Some(max_proofs) = max_proofs {
            proofs.truncate(max_proofs);
        }

        (proofs, ctx.stats)
    }

    pub fn purge_similarity_cache(&mut self) {
        if let Some(_) = self.similarity_cache.as_mut() {
            self.similarity_cache = Some(SimilarityCache::default());
        }
    }

    pub fn reset(&mut self) {
        self.base_knowledge = HashSet::new();
        self.purge_similarity_cache();
    }
}

impl ResolutionProverBackend {
    fn prove_all_recursive(
        &self,
        goal: PyArcItem<CNFDisjunction>,
        knowledge: &HashSet<PyArcItem<CNFDisjunction>>,
        ctx: &mut ProofContext,
        depth: usize,
        parent_state: Option<ProofStepNode>,
    ) {
        if parent_state.is_some() && depth >= self.max_proof_depth {
            return;
        }
        if let Some(max_resolution_attempts) = self.max_resolution_attempts {
            if ctx.stats.attempted_resolutions >= max_resolution_attempts {
                return;
            }
        }
        if let Some(max_proofs) = ctx.max_proofs {
            if !self.find_highest_similarity_proofs && ctx.total_leaf_proofs() >= max_proofs {
                return;
            }
        }
        if depth >= ctx.stats.max_depth_seen {
            ctx.stats.max_depth_seen = depth + 1;
        }

        for clause in knowledge {
            // resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
            // so we know what the length of the resolvent will be before we even try to resolve
            if let Some(max_resolvent_width) = self.max_resolvent_width {
                if clause.item.literals.len() + goal.item.literals.len() - 2 > max_resolvent_width {
                    continue;
                }
            }
            ctx.stats.attempted_resolutions += 1;
            let next_steps = resolve(&goal, &clause, ctx, parent_state.as_ref());
            if next_steps.len() > 0 {
                ctx.stats.successful_resolutions += 1;
            }
            for next_step in next_steps {
                if next_step.inner.resolvent.item.literals.is_empty() {
                    ctx.record_leaf_proof(next_step);
                } else {
                    if next_step.inner.running_similarity <= ctx.min_similarity_threshold {
                        continue;
                    }
                    if !ctx.check_resolvent(&next_step.inner) {
                        continue;
                    }
                    let resolvent_width = next_step.inner.resolvent.item.literals.len();
                    if resolvent_width >= ctx.stats.max_resolvent_width_seen {
                        ctx.stats.max_resolvent_width_seen = resolvent_width;
                    }
                    self.prove_all_recursive(
                        next_step.inner.resolvent.clone(),
                        knowledge,
                        ctx,
                        depth + 1,
                        Some(next_step),
                    );
                }
            }
        }
    }
}

fn knowledge_to_arc(knowledge: HashSet<CNFDisjunction>) -> HashSet<PyArcItem<CNFDisjunction>> {
    knowledge
        .into_iter()
        .map(|x| PyArcItem::new(x.clone()))
        .collect()
}
