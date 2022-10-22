__version__ = "0.1.0"

from .prover.ResolutionProver import ResolutionProver

from .types import Atom, Constant, Predicate, Variable

from .similarity import cosine_similarity, symbol_compare

__all__ = (
    "ResolutionProver",
    "Atom",
    "Constant",
    "Predicate",
    "Variable",
    "cosine_similarity",
    "symbol_compare",
)
