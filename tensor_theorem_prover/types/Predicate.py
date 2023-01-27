from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any

from tensor_theorem_prover._rust import RsPredicate

from .Function import BoundFunction
from .Constant import Constant
from .Variable import Variable

# hacky solution to solving circular import for type-checking only
# from https://stackoverflow.com/a/39757388/245362
if TYPE_CHECKING:
    from .Atom import Atom


@dataclass(frozen=True)
class Predicate:
    """
    A predicate symbol in a logical formula.
    Can contain an embedding for use in vector similarity calculations.
    """

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

    def to_rust(self) -> RsPredicate:
        return RsPredicate(self.symbol, self.embedding)

    @classmethod
    def from_rust(cls, rust_predicate: RsPredicate) -> "Predicate":
        return Predicate(rust_predicate.symbol, rust_predicate.embedding)
