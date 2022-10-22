from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class Constant:
    symbol: str
    embedding: Optional[Any] = None

    def __str__(self) -> str:
        return self.symbol
