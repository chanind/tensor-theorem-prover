from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .Constant import Constant
from .Variable import Variable

# hacky solution to solving circular import for type-checking only
# from https://stackoverflow.com/a/39757388/245362
if TYPE_CHECKING:
    from .Atom import Atom


@dataclass(frozen=True, eq=False)
class Function:
    symbol: str

    # shorthand for creating an Atom out of this predicate and terms
    def __call__(self, *terms: Constant | Variable | BoundFunction) -> BoundFunction:
        return BoundFunction(self, terms)

    def __str__(self) -> str:
        return self.symbol


@dataclass(frozen=True, eq=False)
class BoundFunction:
    function: Function
    terms: tuple[Constant | Variable | BoundFunction, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.function.symbol}({terms_str})"
