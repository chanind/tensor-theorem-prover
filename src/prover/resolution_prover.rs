use std::collections::HashSet;

use pyo3::prelude::*;

use crate::types::CNFDisjunction;

use super::operations::resolve;
use super::{Proof, ProofContext, ProofStats, ProofStep};

// from tensor_theorem_prover.normalize import (
//     Skolemizer,
//     CNFDisjunction,
//     to_cnf,
// )
// from tensor_theorem_prover.prover.Proof import Proof
// from tensor_theorem_prover.prover.ProofStats import ProofStats
// from tensor_theorem_prover.prover.ProofContext import ProofContext
// from tensor_theorem_prover.prover.operations.resolve import resolve
// from tensor_theorem_prover.prover.ProofStep import ProofStep
// from tensor_theorem_prover.similarity import (
//     SimilarityCache,
//     SimilarityFunc,
//     cosine_similarity,
//     similarity_with_cache,
// )
// from tensor_theorem_prover.types import Clause, Not

// class ResolutionProver:
//     """
//     Core theorem prover class that uses input resolution to prove a goal
//     """

//     base_knowledge: set[CNFDisjunction]
//     max_proof_depth: int
//     max_resolution_attempts: Optional[int]
//     max_resolvent_width: Optional[int]
//     min_similarity_threshold: float
//     # MyPy freaks out if this isn't optional, see https://github.com/python/mypy/issues/708
//     similarity_func: Optional[SimilarityFunc]
//     skolemizer: Skolemizer
//     similarity_cache: SimilarityCache
//     cache_similarity: bool
//     skip_seen_resolvents: bool
//     find_highest_similarity_proofs: bool

#[pyclass(name = "RsResolutionProverBackend")]
pub struct ResolutionProverBackend {
    max_proof_depth: usize,
    max_resolution_attempts: Option<usize>,
    max_resolvent_width: Option<usize>,
    min_similarity_threshold: f64,
    py_similarity_fn: Option<PyObject>,
    cache_similarity: bool,
    skip_seen_resolvents: bool,
    find_highest_similarity_proofs: bool,
    base_knowledge: HashSet<CNFDisjunction>,
}
#[pymethods]
impl ResolutionProverBackend {
    //     def __init__(
    //         self,
    //         knowledge: Optional[Iterable[Clause]] = None,
    //         max_proof_depth: int = 10,
    //         max_resolvent_width: Optional[int] = None,
    //         max_resolution_attempts: Optional[int] = None,
    //         similarity_func: Optional[SimilarityFunc] = cosine_similarity,
    //         min_similarity_threshold: float = 0.5,
    //         cache_similarity: bool = True,
    //         skip_seen_resolvents: bool = False,
    //         find_highest_similarity_proofs: bool = True,
    //     ) -> None:
    //         self.max_proof_depth = max_proof_depth
    //         self.max_resolvent_width = max_resolvent_width
    //         self.max_resolution_attempts = max_resolution_attempts
    //         self.min_similarity_threshold = min_similarity_threshold
    //         self.skolemizer = Skolemizer()
    //         self.similarity_cache = {}
    //         self.cache_similarity = cache_similarity
    //         self.skip_seen_resolvents = skip_seen_resolvents
    //         self.similarity_func = similarity_func
    //         self.find_highest_similarity_proofs = find_highest_similarity_proofs
    //         self.base_knowledge = set()
    //         if knowledge is not None:
    //             self.extend_knowledge(knowledge)
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
        base_knowledge: HashSet<CNFDisjunction>,
    ) -> Self {
        Self {
            max_proof_depth,
            max_resolvent_width,
            max_resolution_attempts,
            py_similarity_fn,
            min_similarity_threshold,
            cache_similarity,
            skip_seen_resolvents,
            find_highest_similarity_proofs,
            base_knowledge,
        }
    }

    //     def extend_knowledge(self, knowledge: Iterable[Clause]) -> None:
    //         """Add more knowledge to the prover"""
    //         self.base_knowledge.update(self._parse_knowledge(knowledge))

    pub fn extend_knowledge(&mut self, knowledge: HashSet<CNFDisjunction>) {
        self.base_knowledge.extend(knowledge);
    }

    //     def prove_all_with_stats(
    //         self,
    //         goal: Clause,
    //         extra_knowledge: Optional[Iterable[Clause]] = None,
    //         max_proofs: Optional[int] = None,
    //         skip_seen_resolvents: Optional[bool] = None,
    //     ) -> tuple[list[Proof], ProofStats]:
    //         """
    //         Find all possible proofs for the given goal, sorted by similarity score.
    //         Return the proofs and the stats for the proof search.
    //         """
    //         inverted_goals = set(to_cnf(Not(goal), self.skolemizer))
    //         parsed_extra_knowledge = self._parse_knowledge(extra_knowledge or [])
    //         proofs = []
    //         knowledge = self.base_knowledge | parsed_extra_knowledge | inverted_goals
    //         # knowledge.sort(key=lambda clause: len(clause.literals), reverse=True)
    //         ctx = ProofContext(
    //             initial_min_similarity_threshold=self.min_similarity_threshold,
    //             max_proofs=max_proofs,
    //             skip_seen_resolvents=self.skip_seen_resolvents
    //             if skip_seen_resolvents is None
    //             else skip_seen_resolvents,
    //         )
    //         similarity_func = self.similarity_func
    //         if self.cache_similarity and self.similarity_func:
    //             similarity_func = similarity_with_cache(
    //                 self.similarity_func, self.similarity_cache, ctx.stats
    //             )

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
        knowledge.extend(parsed_extra_knowledge);
        knowledge.extend(inverted_goals.clone());
        let mut ctx = ProofContext::new(
            self.min_similarity_threshold,
            max_proofs,
            skip_seen_resolvents.unwrap_or(self.skip_seen_resolvents),
            self.cache_similarity,
            self.py_similarity_fn.clone(),
        );

        //    for inverted_goal in inverted_goals:
        //         self._prove_all_recursive(
        //             inverted_goal,
        //             knowledge,
        //             similarity_func,
        //             ctx,
        //         )
        //         for (
        //             leaf_proof_step,
        //             leaf_proof_stats,
        //         ) in ctx.leaf_proof_steps_with_stats():
        //             proofs.append(
        //                 Proof(
        //                     inverted_goal,
        //                     leaf_proof_step.running_similarity,
        //                     leaf_proof_step,
        //                     leaf_proof_stats,
        //                 )
        //             )
        //     proofs = sorted(proofs, key=lambda proof: proof.similarity, reverse=True)
        //     if max_proofs:
        //         proofs = proofs[:max_proofs]

        //     return (
        //         proofs,
        //         ctx.stats,
        //     )

        for inverted_goal in inverted_goals {
            self.prove_all_recursive(inverted_goal.clone(), &knowledge, &mut ctx, 0, None);
            for (leaf_proof_step, leaf_proof_stats) in ctx.leaf_proof_steps_with_stats() {
                proofs.push(Proof::new(
                    inverted_goal.clone(),
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

    //     def reset(self) -> None:
    //         """Clear all knowledge from the prover and wipe the similarity cache"""
    //         self.base_knowledge = set()
    //         self.purge_similarity_cache()

    pub fn reset(&mut self) {
        self.base_knowledge = HashSet::new();
    }
}

impl ResolutionProverBackend {
    //     def _prove_all_recursive(
    //         self,
    //         goal: CNFDisjunction,
    //         knowledge: Iterable[CNFDisjunction],
    //         similarity_func: Optional[SimilarityFunc],
    //         ctx: ProofContext,
    //         depth: int = 0,
    //         parent_state: Optional[ProofStep] = None,
    //     ) -> None:
    //         if parent_state and depth >= self.max_proof_depth:
    //             return
    //         if (
    //             self.max_resolution_attempts
    //             and ctx.stats.attempted_resolutions >= self.max_resolution_attempts
    //         ):
    //             return
    //         # if we don't need to find the best proofs, and we've already found enough, stop
    //         if (
    //             ctx.max_proofs
    //             and not self.find_highest_similarity_proofs
    //             and ctx.total_leaf_proofs() >= ctx.max_proofs
    //         ):
    //             return
    //         if depth >= ctx.stats.max_depth_seen:
    //             # add 1 to match the depth stat seen in proofs. It's strange if the proof has depth 12, but max_depth_seen is 11
    //             ctx.stats.max_depth_seen = depth + 1

    fn prove_all_recursive(
        &self,
        goal: CNFDisjunction,
        knowledge: &HashSet<CNFDisjunction>,
        ctx: &mut ProofContext,
        depth: usize,
        parent_state: Option<ProofStep>,
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

        //         for clause in knowledge:
        //             # resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
        //             # so we know what the length of the resolvent will be before we even try to resolve
        //             if (
        //                 self.max_resolvent_width
        //                 and len(clause.literals) + len(goal.literals) - 2
        //                 > self.max_resolvent_width
        //             ):
        //                 continue
        //             ctx.stats.attempted_resolutions += 1
        //             next_steps = resolve(
        //                 goal,
        //                 clause,
        //                 similarity_func=similarity_func,
        //                 parent=parent_state,
        //                 ctx=ctx,
        //             )
        //             if len(next_steps) > 0:
        //                 ctx.stats.successful_resolutions += 1
        //             for next_step in next_steps:
        //                 if next_step.resolvent is None:
        //                     raise ValueError("Resolvent was unexpectedly not present")
        //                 if next_step.resolvent.is_empty():
        //                     ctx.record_leaf_proof(next_step)
        //                 else:
        //                     # the similarity moving forward can never exceed the running similarity of the parent node,
        //                     # so if we've already seen a proof that's better than this step, we can just stop here
        //                     # NOTE: we might not find the shortest proof, may want to revisit this in the future
        //                     if next_step.running_similarity <= ctx.min_similarity_threshold:
        //                         continue
        //                     if not ctx.check_resolvent(next_step):
        //                         continue
        //                     resolvent_width = len(next_step.resolvent.literals)
        //                     if resolvent_width >= ctx.stats.max_resolvent_width_seen:
        //                         ctx.stats.max_resolvent_width_seen = resolvent_width
        //                     self._prove_all_recursive(
        //                         next_step.resolvent,
        //                         knowledge,
        //                         similarity_func,
        //                         ctx,
        //                         depth + 1,
        //                         next_step,
        //                     )

        for clause in knowledge {
            // resolution always ends up removing a literal from the clause and the goal, and combining the remaining literals
            // so we know what the length of the resolvent will be before we even try to resolve
            if let Some(max_resolvent_width) = self.max_resolvent_width {
                if clause.literals.len() + goal.literals.len() - 2 > max_resolvent_width {
                    continue;
                }
            }
            ctx.stats.attempted_resolutions += 1;
            let next_steps = resolve(&goal, &clause, ctx, parent_state.as_ref());
            if next_steps.len() > 0 {
                ctx.stats.successful_resolutions += 1;
            }
            for next_step in next_steps {
                if next_step.resolvent.literals.is_empty() {
                    ctx.record_leaf_proof(next_step);
                } else {
                    if next_step.running_similarity <= ctx.min_similarity_threshold {
                        continue;
                    }
                    if !ctx.check_resolvent(&next_step) {
                        continue;
                    }
                    let resolvent_width = next_step.resolvent.literals.len();
                    if resolvent_width >= ctx.stats.max_resolvent_width_seen {
                        ctx.stats.max_resolvent_width_seen = resolvent_width;
                    }
                    self.prove_all_recursive(
                        next_step.resolvent.clone(),
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
