from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tensor_theorem_prover._rust import (
    RsFunction,
    RsBoundFunction,
)

from .Constant import Constant
from .Variable import Variable

if TYPE_CHECKING:
    from .Term import Term


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

    def to_rust(self) -> RsFunction:
        return RsFunction(self.symbol)

    @classmethod
    def from_rust(cls, rust_function: RsFunction) -> Function:
        return cls(rust_function.symbol)


@dataclass(frozen=True)
class BoundFunction:
    """
    Works like a constant or variable in atoms
    """

    function: Function
    terms: tuple[Term, ...]

    def __str__(self) -> str:
        terms_str = ",".join([str(term) for term in self.terms])
        return f"{self.function.symbol}({terms_str})"

    def to_rust(self) -> RsBoundFunction:
        return RsBoundFunction(
            self.function.to_rust(), list(term.to_rust() for term in self.terms)
        )

    @classmethod
    def from_rust(cls, rust_bound_function: RsBoundFunction) -> "BoundFunction":
        # putting this import here to avoid circular imports
        from .Term import term_from_rust

        return cls(
            Function.from_rust(rust_bound_function.function),
            tuple(term_from_rust(term) for term in rust_bound_function.terms),
        )
