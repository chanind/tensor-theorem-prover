from __future__ import annotations
from typing import TypeVar


T = TypeVar("T")


def pick_from_set(s: set[T]) -> T:
    return next(iter(s))
