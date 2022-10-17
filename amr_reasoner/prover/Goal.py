from __future__ import annotations
from dataclasses import dataclass

from amr_reasoner.types.Atom import Atom


@dataclass(frozen=True, eq=False)
class Goal:
    statement: Atom
    scope: int

    def __str__(self) -> str:
        return f"GOAL:{self.statement}"
