__version__ = "0.14.0"

from .prover import ResolutionProver, Proof, ProofStep, ProofStats

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

from .similarity import (
    cosine_similarity,
    symbol_compare,
    max_similarity,
    SimilarityFunc,
)

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
    "SimilarityFunc",
    "Proof",
    "ProofStep",
    "ProofStats",
)
