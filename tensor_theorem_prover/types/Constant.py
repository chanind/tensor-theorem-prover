from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class Constant:
    symbol: str
    embedding: Optional[Any] = None

    def __hash__(self) -> int:
        return hash(self.symbol) + id(self.embedding)

    def __str__(self) -> str:
        return self.symbol
