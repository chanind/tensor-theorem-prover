from __future__ import annotations
from dataclasses import dataclass

from .Variable import Variable
from .Constant import Constant
from .Predicate import Predicate
from .Function import Function


@dataclass(frozen=True, eq=False)
class Atom:
    operator: Predicate | Function
    terms: tuple[Constant | Variable, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.operator.symbol}({terms_str})"
