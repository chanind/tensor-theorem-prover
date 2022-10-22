from __future__ import annotations
from typing import Iterable
from amr_reasoner.normalize.to_cnf import (
    CNFDisjunction,
    _element_to_cnf_literal,
)
from amr_reasoner.types import (
    Not,
    Atom,
)


def to_disj(clause: Iterable[Atom | Not]) -> CNFDisjunction:
    return CNFDisjunction(frozenset(_element_to_cnf_literal(elm) for elm in clause))


def to_disj_set(clauses: list[list[Atom | Not]]) -> set[CNFDisjunction]:
    return set(to_disj(clause) for clause in clauses)
