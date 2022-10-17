from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .Atom import Atom


@dataclass(frozen=True, eq=False)
class Rule:
    head: Atom
    body: Optional[tuple[Atom, ...]] = None

    def __str__(self) -> str:
        body_str = ", ".join([atom.__str__() for atom in self.body or []])
        return f"{self.head}:-[{body_str}]"
