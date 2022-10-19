from __future__ import annotations
from dataclasses import dataclass
from typing import Union

from .Variable import Variable
from .Constant import Constant
from .Predicate import Predicate
from .Function import BoundFunction

Term = Union[Constant, Variable, BoundFunction]


@dataclass(frozen=True)
class Atom:
    predicate: Predicate
    terms: tuple[Term, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.predicate.symbol}({terms_str})"
