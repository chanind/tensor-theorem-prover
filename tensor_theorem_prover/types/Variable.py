from dataclasses import dataclass


@dataclass(frozen=True)
class Variable:
    """
    A variable symbol in a logical formula.
    """

    name: str

    def __str__(self) -> str:
        return self.name
