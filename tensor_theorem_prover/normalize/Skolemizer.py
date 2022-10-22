from __future__ import annotations

from tensor_theorem_prover.types import Term, BoundFunction, Function


class Skolemizer:
    """Helper class to generate unique skolem function names during conversion to CNF"""

    counter: int = 0

    def __call__(self, *terms: Term) -> BoundFunction:
        self.counter += 1
        func = Function(f"_SK_{self.counter}")
        return func(*terms)
