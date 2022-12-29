from __future__ import annotations
from dataclasses import dataclass

from .Constant import Constant
from .Variable import Variable


@dataclass(frozen=True)
class Function:
    """
    A function symbol in a logical formula.
    """

    symbol: str

    # shorthand for creating an Atom out of this predicate and terms
    def __call__(self, *terms: Constant | Variable | BoundFunction) -> BoundFunction:
        return BoundFunction(self, terms)

    def __str__(self) -> str:
        return self.symbol


@dataclass(frozen=True)
class BoundFunction:
    """
    Works like a constant or variable in atoms
    """

    function: Function
    terms: tuple[Constant | Variable | BoundFunction, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.function.symbol}({terms_str})"
