from __future__ import annotations
from dataclasses import dataclass

from tensor_theorem_prover._rust import RsAtom

from .Predicate import Predicate
from .Term import Term, term_from_rust


@dataclass(frozen=True)
class Atom:
    """
    Logical Atom (predicate with terms)
    """

    predicate: Predicate
    terms: tuple[Term, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.predicate.symbol}({terms_str})"

    def to_rust(self) -> RsAtom:
        return RsAtom(
            self.predicate.to_rust(), list(term.to_rust() for term in self.terms)
        )

    @classmethod
    def from_rust(cls, rust_atom: RsAtom) -> "Atom":
        return cls(
            Predicate.from_rust(rust_atom.predicate),
            tuple(term_from_rust(term) for term in rust_atom.terms),
        )
