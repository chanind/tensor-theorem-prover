from __future__ import annotations
from typing import Iterable
from tensor_theorem_prover.normalize.to_cnf import (
    CNFDisjunction,
    _element_to_cnf_literal,
)
from tensor_theorem_prover.types import (
    Not,
    Atom,
)


def to_disj(clause: Iterable[Atom | Not]) -> CNFDisjunction:
    return CNFDisjunction([_element_to_cnf_literal(elm) for elm in clause])


def to_disj_set(clauses: list[list[Atom | Not]]) -> list[CNFDisjunction]:
    return [to_disj(clause) for clause in clauses]
