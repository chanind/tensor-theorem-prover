from __future__ import annotations
from dataclasses import dataclass
from amr_reasoner.types import Clause, Atom, Not, And, Or

from .to_nnf import to_nnf
from .normalize_variables import normalize_variables
from .normalize_quantifiers import SimplifiedClause, normalize_quantifiers
from .normalize_conjunctions import normalize_conjunctions


@dataclass(frozen=True)
class CNFLiteral:
    atom: Atom
    polarity: bool

    def __str__(self) -> str:
        if self.polarity:
            return str(self.atom)
        else:
            return f"¬{self.atom}"


@dataclass(frozen=True)
class CNFDisjunction:
    literals: frozenset[CNFLiteral]

    def __str__(self) -> str:
        inner_disjunction = " ∨ ".join(
            sorted(str(literal) for literal in self.literals)
        )
        return f"[{inner_disjunction}]"


# TODO: dedupe literals/disjunctions based on embedding vectors, if present
def to_cnf(clause: Clause) -> set[CNFDisjunction]:
    """Convert a clause to conjunctive normal form (CNF).
    Args:
        clauses: The clause to convert.
    Returns:
        The clause in CNF.
    """

    nnf_clause = to_nnf(clause)
    nnf_clause = normalize_variables(nnf_clause)
    simplified_clause = normalize_quantifiers(nnf_clause)
    normalized_clause = normalize_conjunctions(simplified_clause)
    return _norm_clause_to_cnf(normalized_clause)


def _norm_clause_to_cnf(clause: SimplifiedClause) -> set[CNFDisjunction]:
    if isinstance(clause, Atom) or isinstance(clause, Not):
        literal = _element_to_cnf_literal(clause)
        return set([CNFDisjunction(frozenset([literal]))])
    if isinstance(clause, Not):
        # this should already be basically in CNF, so there can only be atoms inside of a Not
        assert isinstance(clause.body, Atom)
        return set([CNFDisjunction(frozenset([CNFLiteral(clause.body, False)]))])
    if isinstance(clause, And):
        disjunctions = set()
        for term in clause.args:
            literals = set()
            if isinstance(term, Atom) or isinstance(term, Not):
                literals.add(_element_to_cnf_literal(term))
            elif isinstance(term, Or):
                for element in term.args:
                    assert isinstance(element, Atom) or isinstance(element, Not)
                    literals.add(_element_to_cnf_literal(element))
            disjunctions.add(CNFDisjunction(frozenset(literals)))
        return set(disjunctions)
    raise ValueError(f"Unnormalized clause type in CNF conversion: {type(clause)}")


def _element_to_cnf_literal(element: Atom | Not) -> CNFLiteral:
    if isinstance(element, Atom):
        return CNFLiteral(element, True)
    if isinstance(element, Not):
        assert isinstance(element.body, Atom)
        return CNFLiteral(element.body, False)
    raise ValueError(f"Unexpected element type: {type(element)}")
