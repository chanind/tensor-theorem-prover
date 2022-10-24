__version__ = "0.3.0"

from .prover.ResolutionProver import ResolutionProver

from .types import (
    Atom,
    Constant,
    Predicate,
    Variable,
    And,
    Or,
    Not,
    Implies,
    Exists,
    All,
    Function,
    Clause,
)

from .similarity import cosine_similarity, symbol_compare, max_similarity

__all__ = (
    "ResolutionProver",
    "Atom",
    "Constant",
    "Predicate",
    "Variable",
    "And",
    "Or",
    "Not",
    "Implies",
    "Exists",
    "All",
    "Clause",
    "Function",
    "cosine_similarity",
    "symbol_compare",
    "max_similarity",
)
