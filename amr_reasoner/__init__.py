__version__ = "0.1.0"

from .prover.SLDProver import SLDProver

from .types import Atom, Constant, Predicate, Rule, Variable, Knowledge

from .similarity import cosine_similarity, symbol_compare

__all__ = (
    "SLDProver",
    "Atom",
    "Constant",
    "Predicate",
    "Knowledge",
    "Rule",
    "Variable",
    "cosine_similarity",
    "symbol_compare",
)
