from __future__ import annotations
from dataclasses import dataclass

from .Variable import Variable
from .Constant import Constant
from .Predicate import Predicate


@dataclass(frozen=True, eq=False)
class Atom:
    predicate: Predicate
    terms: tuple[Constant | Variable, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.predicate.symbol}({terms_str})"
