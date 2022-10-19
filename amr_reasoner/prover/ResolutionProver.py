from __future__ import annotations
from typing import Iterable

from amr_reasoner.normalize.to_cnf import CNFDisjunction, to_cnf
from amr_reasoner.types import Clause, Not


class ResolutionProver:

    knowledge: frozenset[CNFDisjunction]

    def __init__(self, knowledge: Iterable[Clause]) -> None:
        parsed_knowledge = set()
        for clause in knowledge:
            parsed_knowledge.update(to_cnf(clause))
        self.knowledge = frozenset(parsed_knowledge)

    def prove(self, goal: Clause) -> bool:
        goals = to_cnf(Not(goal))
        return self._prove(goals)
