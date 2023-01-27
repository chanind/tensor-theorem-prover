from __future__ import annotations

from typing import Union

from tensor_theorem_prover._rust import (
    RsVariable,
    RsConstant,
    RsBoundFunction,
)

from .Constant import Constant
from .Variable import Variable
from .Function import BoundFunction

Term = Union[Constant, Variable, BoundFunction]


def term_from_rust(rust_term: RsVariable | RsConstant | RsBoundFunction) -> Term:
    if isinstance(rust_term, RsVariable):
        return Variable.from_rust(rust_term)
    elif isinstance(rust_term, RsConstant):
        return Constant.from_rust(rust_term)
    elif isinstance(rust_term, RsBoundFunction):
        return BoundFunction.from_rust(rust_term)
    else:
        raise TypeError(f"Unknown type: {type(rust_term)}")
