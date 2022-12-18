# Tensor Theorem Prover

[![ci](https://img.shields.io/github/actions/workflow/status/chanind/tensor-theorem-prover/ci.yaml?branch=main)](https://github.com/chanind/tensor-theorem-prover)
[![Codecov](https://img.shields.io/codecov/c/github/chanind/tensor-theorem-prover/main)](https://codecov.io/gh/chanind/tensor-theorem-prover)
[![PyPI](https://img.shields.io/pypi/v/tensor-theorem-prover?color=blue)](https://pypi.org/project/tensor-theorem-prover/)

First-order logic theorem prover supporting unification with approximate vector similarity

## Installation

```
pip install tensor-theorem-prover
```

## Usage

tensor-theorem-prover can be used either as a standard symbolic first-order theorem prover, or it can be used with vector embeddings and fuzzy unification.

The basic setup requires listing out first-order formulae, and using the `ResolutionProver` class to generate proofs.

```python
import numpy as np
from vector_theorem_prover import ResolutionProver, Constant, Predicate, Variable, Implies

X = Variable("X")
Y = Variable("Y")
Z = Variable("Z")
# predicates and constants can be given an embedding array for fuzzy unification
grandpa_of = Predicate("grandpa_of", np.array([1.0, 1.0, 0.0, 0.3, ...]))
grandfather_of = Predicate("grandfather_of", np.array([1.01, 0.95, 0.05, 0.33, ...]))
parent_of = Predicate("parent_of", np.array([ ... ]))
father_of = Predicate("father_of", np.array([ ... ]))
bart = Constant("bart", np.array([ ... ]))
homer = Constant("homer", np.array([ ... ]))
abe = Constant("abe", np.array([ ... ]))

knowledge = [
    parent_of(homer, bart),
    father_of(abe, homer),
    # father_of(X, Z) ^ parent_of(Z, Y) -> grandpa_of(X, Y)
    Implies(And(father_of(X, Z), parent_of(Z, Y)), grandpa_of(X, Y))
]

prover = ResolutionProver(knowledge=knowledge)

# query the prover to find who is bart's grandfather
proof = prover.prove(grandfather_of(X, bart))

# even though `grandpa_of` and `grandfather_of` are not identical symbols,
# their embedding is close enough that the prover can still find the answer
print(proof.substitutions[X]) # abe

# the prover will return `None` if a proof could not be found
failed_proof = prover.prove(grandfather_of(bart, homer))
print(failed_proof) # None

```

### Working with proof results

The `prover.prove()` method will return a `Proof` object if a successful proof is found. This object contains a list of all the resolutions, substitutions, and similarity calculations that went into proving the goal.

```python
proof = prover.prove(goal)

proof.substitutions # a map of all variables in the goal to their bound values
proof.similarity # the min similarity of all `unify` operations in this proof
proof.depth # the number of steps in this proof
proof.proof_steps # all the proof steps involved, including all resolutions and unifications along the way
```

The `Proof` object can be printed as a string to get a visual overview of the steps involved in the proof.

```python
X = Variable("X")
Y = Variable("Y")
father_of = Predicate("father_of")
parent_of = Predicate("parent_of")
is_male = Predicate("is_male")
bart = Constant("bart")
homer = Constant("homer")

knowledge = [
    parent_of(homer, bart),
    is_male(homer),
    Implies(And(parent_of(X, Y), is_male(X)), father_of(X, Y)),
]

prover = ResolutionProver(knowledge=knowledge)

goal = father_of(homer, X)
proof = prover.prove(goal)

print(proof)
# Goal: [¬father_of(homer,X)]
# Subsitutions: {X -> bart}
# Similarity: 1.0
# Depth: 3
# Steps:
#   Similarity: 1.0
#   Source: [¬father_of(homer,X)]
#   Target: [father_of(X,Y) ∨ ¬is_male(X) ∨ ¬parent_of(X,Y)]
#   Unify: father_of(homer,X) = father_of(X,Y)
#   Subsitutions: {}, {X -> homer, Y -> X}
#   Resolvent: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
#   ---
#   Similarity: 1.0
#   Source: [¬is_male(homer) ∨ ¬parent_of(homer,X)]
#   Target: [parent_of(homer,bart)]
#   Unify: parent_of(homer,X) = parent_of(homer,bart)
#   Subsitutions: {X -> bart}, {}
#   Resolvent: [¬is_male(homer)]
#   ---
#   Similarity: 1.0
#   Source: [¬is_male(homer)]
#   Target: [is_male(homer)]
#   Unify: is_male(homer) = is_male(homer)
#   Subsitutions: {}, {}
#   Resolvent: []
```

### Finding all possible proofs

The `prover.prove()` method will return the proof with the highest similarity score among all possible proofs, if one exists. If you want to get a list of all the possible proofs in descending order of similarity score, you can call `prover.prove_all()` to return a list of all proofs.

### Custom matching functions and similarity thresholds

By default, the prover will use cosine similarity for unification. If you'd like to use a different similarity function, you can pass in a function to the prover to perform the similarity calculation however you wish.

```python
def fancy_similarity(item1, item2):
    norm = np.linalg.norm(item1.embedding) + np.linalg.norm(item2.embedding)
    return np.linalg.norm(item1.embedding - item2.embedding) / norm

prover = ResolutionProver(knowledge=knowledge, similarity_func=fancy_similarity)
```

By default, there is a minimum similarity threshold of `0.5` for a unification to success. You can customize this as well when creating a `ResolutionProver` instance

```python
prover = ResolutionProver(knowledge=knowledge, min_similarity_threshold=0.9)
```

### Working with Tensors (Pytorch, Tensorflow, etc...)

By default, the similarity calculation assumes that the embeddings supplied for constants and predicates are numpy arrays. If you want to use tensors instead, this will work as long as you provide a `similarity_func` which can work with the tensor types you're using and return a float.

For example, if you're using Pytorch, it might look like the following:

```python
import torch

def torch_cosine_similarity(item1, item2):
    similarity = torch.nn.functional.cosine_similarity(
        item1.embedding,
        item2.embedding,
        0
    )
    return similarity.item()

prover = ResolutionProver(knowledge=knowledge, similarity_func=torch_cosine_similarity)

# for pytorch you may want to wrap the proving in torch.no_grad()
with torch.no_grad():
    proof = prover.prove(goal)
```

### Max proof depth

By default, the ResolutionProver will abort proofs after a depth of 10. You can customize this behavior by passing `max_proof_depth` when creating the prover

```python
prover = ResolutionProver(knowledge=knowledge, max_proof_depth=10)
```

### Max resolvent width

By default, the ResolutionProver has no limit on how wide resolvents can get during the proving process. If the proofs are running too slowly, you can try to set `max_resolvent_width` to limit how many literals intermediate resolvents are allowed to contain. This should narrow the search tree, but has the trade-off of not finding proofs if the proof requires unifying together a lot of very wide clauses.

```python
prover = ResolutionProver(knowledge=knowledge, max_resolvent_width=10)
```

### Skipping seen resolvents

A major performance improvement when searching through a large proof space is to stop searching any branches that encounter a resolvent that's already been seen. Doing this is still guaranteed to find the proof with the highest similarity score, but it means the prover is no longer guaranteed to find every possible proof when running `prover.prove_all()`. Although, when dealing with anything beyond very small knowledge bases, finding every possible proof is likely not going to be computationally feasible anyway.

Searching for a proof using `prover.prove()` always enables this optimization, but you can enable it when using `prover.prove_all()` as well by passing the option `skip_seen_resolvents=True` when creating the `ResolutionProver`, like below:

```python
prover = ResolutionProver(knowledge=knowledge, skip_seen_resolvents=True)
```

## Acknowledgements

This library borrows code and ideas from the earier library [fuzzy-reasoner](https://github.com/fuzzy-reasoner/fuzzy-reasoner). The main difference between these libraries is that tensor-theorem-prover supports full first-order logic using Resolution, whereas fuzzy-reasoner is restricted to Horn clauses and uses backwards chaining.

Like fuzzy-reasoner, this library also takes inspiration from the following papers for the idea of using vector similarity in theorem proving:

- [End-to-End Differentiable Proving](https://arxiv.org/abs/1705.11040) by Rocktäschel et al.
- [Braid - Weaving Symbolic and Neural Knowledge into Coherent Logical Explanations](https://arxiv.org/abs/2011.13354) by Kalyanpur et al.

## Contributing

Contributions are welcome! Please leave an issue in the Github repo if you find any bugs, and open a pull request with and fixes or improvements that you'd like to contribute.
