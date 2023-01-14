from dataclasses import dataclass

from tensor_theorem_prover._rust import RsVariable


@dataclass(frozen=True)
class Variable:
    """
    A variable symbol in a logical formula.
    """

    name: str

    def __str__(self) -> str:
        return self.name

    def to_rust(self) -> RsVariable:
        return RsVariable(self.name)

    @classmethod
    def from_rust(cls, rust_variable: RsVariable) -> "Variable":
        return cls(rust_variable.name)
