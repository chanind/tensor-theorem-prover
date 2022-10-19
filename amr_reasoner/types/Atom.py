from __future__ import annotations
from dataclasses import dataclass

from .Variable import Variable
from .Constant import Constant
from .Predicate import Predicate
from .Function import BoundFunction


@dataclass(frozen=True)
class Atom:
    predicate: Predicate
    terms: tuple[Constant | Variable | BoundFunction, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.predicate.symbol}({terms_str})"
