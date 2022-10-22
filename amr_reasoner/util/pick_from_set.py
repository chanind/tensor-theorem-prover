from __future__ import annotations
from typing import Iterable, TypeVar


T = TypeVar("T")


def pick_from_set(s: Iterable[T]) -> T:
    return next(iter(s))
