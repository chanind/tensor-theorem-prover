from __future__ import annotations
from typing import Optional
from amr_reasoner.prover.Goal import Goal
from amr_reasoner.prover.ProofState import ProofState
from amr_reasoner.prover.operations.recurse import recurse
from amr_reasoner.prover.operations.substitution import generate_variable_scope
from amr_reasoner.similarity import SimilarityFunc, cosine_similarity

from amr_reasoner.types.Atom import Atom
from amr_reasoner.prover.Proof import Proof
from amr_reasoner.types.Knowledge import Knowledge
from amr_reasoner.types.Rule import Rule


class SLDProver:
    max_proof_depth: int
    min_similarity_threshold: float
    rules: frozenset[Rule]
    # MyPy freaks out if this isn't optional, see https://github.com/python/mypy/issues/708
    similarity_func: Optional[SimilarityFunc]

    def __init__(
        self,
        knowledge: Knowledge = [],
        max_proof_depth: int = 10,
        min_similarity_threshold: float = 0.5,
        similarity_func: Optional[SimilarityFunc] = cosine_similarity,
    ) -> None:
        self.max_proof_depth = max_proof_depth
        self.min_similarity_threshold = min_similarity_threshold
        self.similarity_func = similarity_func
        self.rules = process_knowledge(knowledge)

    def prove(
        self, goal: Goal | Atom, extra_knowledge: Optional[Knowledge] = None
    ) -> Proof | None:
        result_graphs = self.prove_all(goal, extra_knowledge)
        return result_graphs[0] if len(result_graphs) > 0 else None

    def prove_all(
        self, goal: Goal | Atom, extra_knowledge: Optional[Knowledge] = None
    ) -> list[Proof]:
        adjusted_goal = (
            goal
            if isinstance(goal, Goal)
            else Goal(goal, scope=generate_variable_scope())
        )
        rules = (
            self.rules.union(process_knowledge(extra_knowledge))
            if extra_knowledge
            else self.rules
        )
        _successful_proof_states, successful_graph_nodes = recurse(
            adjusted_goal,
            self.max_proof_depth,
            ProofState(),
            rules,
            self.similarity_func,
            self.min_similarity_threshold,
        )
        if not successful_graph_nodes:
            return []
        graphs = [Proof(node) for node in successful_graph_nodes]
        return sorted(graphs, key=lambda graph: graph.similarity_score, reverse=True)


def process_knowledge(knowledge: Knowledge) -> frozenset[Rule]:
    return frozenset(
        [item if isinstance(item, Rule) else Rule(item) for item in knowledge]
    )
