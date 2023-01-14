from dataclasses import dataclass
from typing import Optional, Any

from tensor_theorem_prover._rust import RsConstant


@dataclass(frozen=True)
class Constant:
    """
    A constant symbol in a logical formula.
    Can contain an embedding for use in vector similarity calculations.
    """

    symbol: str
    embedding: Optional[Any] = None

    def __hash__(self) -> int:
        return hash(self.symbol) + id(self.embedding)

    def __str__(self) -> str:
        return self.symbol

    def to_rust(self) -> RsConstant:
        return RsConstant(self.symbol, self.embedding)

    @classmethod
    def from_rust(cls, rust_constant: RsConstant) -> "Constant":
        return Constant(rust_constant.symbol, rust_constant.embedding)
