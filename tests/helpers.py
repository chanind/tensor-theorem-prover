from __future__ import annotations
from tensor_theorem_prover.normalize.to_cnf import (
    CNFDisjunction,
    _element_to_cnf_literal,
)
from tensor_theorem_prover.types import (
    Not,
    Atom,
)


def to_disj(clause: list[Atom | Not]) -> CNFDisjunction:
    literals = [_element_to_cnf_literal(elm) for elm in clause]
    return CNFDisjunction.from_literals_list(literals)


def to_disj_set(clauses: list[list[Atom | Not]]) -> list[CNFDisjunction]:
    return [to_disj(clause) for clause in clauses]
