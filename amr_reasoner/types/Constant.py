from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True, eq=False)
class Constant:
    symbol: str
    embedding: Optional[Any] = None

    def __str__(self) -> str:
        return f"CONST:{self.symbol}"
