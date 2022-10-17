from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class Variable:
    name: str

    def __str__(self) -> str:
        return f"VAR:{self.name}"
