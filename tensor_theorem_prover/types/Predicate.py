from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any

from .Function import BoundFunction
from .Constant import Constant
from .Variable import Variable

# hacky solution to solving circular import for type-checking only
# from https://stackoverflow.com/a/39757388/245362
if TYPE_CHECKING:
    from .Atom import Atom


@dataclass(frozen=True)
class Predicate:
    symbol: str
    embedding: Optional[Any] = None

    def __hash__(self) -> int:
        return hash(self.symbol) + id(self.embedding)

    # shorthand for creating an Atom out of this predicate and terms
    def __call__(self, *terms: Constant | Variable | BoundFunction) -> Atom:
        # need to import inside of here to avoid circular references
        from .Atom import Atom

        return Atom(self, terms)

    def __str__(self) -> str:
        return self.symbol
