from dataclasses import dataclass


@dataclass(frozen=True)
class Variable:
    name: str

    def __str__(self) -> str:
        return self.name
