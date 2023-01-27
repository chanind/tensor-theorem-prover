# Changelog

<!--next-version-placeholder-->

## v0.13.7 (2023-01-27)
### Fix
* Trying a different method to skip buiding the release commit ([`44c2523`](https://github.com/chanind/tensor-theorem-prover/commit/44c2523f6be1ead4c28c05120caa73a3c57f7616))

## v0.13.6 (2023-01-27)
### Fix
* Fixing deploy and stopping infinite run loop ([`1e63a10`](https://github.com/chanind/tensor-theorem-prover/commit/1e63a1074ce565284503d93af511e174cb172a26))

## v0.13.5 (2023-01-27)
### Fix
* Trying using the PAT for checkout too to see if the workflow will run... ([`b84b6c7`](https://github.com/chanind/tensor-theorem-prover/commit/b84b6c7fda242e2cc87a53b4c87eae18da8959be))

## v0.13.4 (2023-01-27)
### Fix
* Bump for deploy ([`22c2582`](https://github.com/chanind/tensor-theorem-prover/commit/22c2582819b1b455e8cefc3e0db283477c38d466))

## v0.13.3 (2023-01-27)
### Fix
* Bump for deploy ([`65839da`](https://github.com/chanind/tensor-theorem-prover/commit/65839da18e7fedf3c562218aef325d6498ce2755))

## v0.13.2 (2023-01-27)
### Fix
* Try creating an empty dist/ during semantic release ([`8e79326`](https://github.com/chanind/tensor-theorem-prover/commit/8e793264b69bc33b8f0f842016983866adb0b6bd))

## v0.13.1 (2023-01-27)
### Fix
* Tweak job syntax to run on all tags ([`36089b1`](https://github.com/chanind/tensor-theorem-prover/commit/36089b19361a4e24890e3b074ec10890fccb47fb))

## v0.13.0 (2023-01-27)
### Feature
* Ignore build step in semantic-release ([`0ed0c35`](https://github.com/chanind/tensor-theorem-prover/commit/0ed0c358c742853dc31ecf450bd7816e9a2d7a39))

## v0.13.0 (2023-01-27)


## v0.12.0 (2023-01-09)
### Feature
* Adding options to skip finding best proof, and abort early ([`ed23460`](https://github.com/chanind/tensor-theorem-prover/commit/ed23460995043317ccdce13c3bac66eb0b796a43))

## v0.11.3 (2023-01-05)
### Fix
* Revert knowledge sort as it seems to hurt performance, and adding more perf tests ([`db51214`](https://github.com/chanind/tensor-theorem-prover/commit/db512140e6e1ab49e3031cb9758f788fdf5db89a))

## v0.11.2 (2023-01-03)
### Fix
* Slighly more consistent proving by sorting knowledge in advance ([`5bead37`](https://github.com/chanind/tensor-theorem-prover/commit/5bead37f25f68ad18e1f438f554db4e1eaabd018))

## v0.11.1 (2022-12-22)
### Fix
* Dedupe knowledge in ResolutionProver ([`b16c899`](https://github.com/chanind/tensor-theorem-prover/commit/b16c89974669b92b24468ad76110d99e3c5e1403))

## v0.11.0 (2022-12-18)
### Feature
* Dedupe disjunctions and add option to prune search tree ([#2](https://github.com/chanind/tensor-theorem-prover/issues/2)) ([`b0576b5`](https://github.com/chanind/tensor-theorem-prover/commit/b0576b5a229181ec4ef6eddec002b243418b7731))

## v0.10.2 (2022-12-13)
### Fix
* More perf improvements around early stopping ([`948d896`](https://github.com/chanind/tensor-theorem-prover/commit/948d896e02d49d66c2330a6097f6f21f006245ed))

## v0.10.1 (2022-12-13)
### Fix
* Refactor min similarity tracking for better performance ([`256ca65`](https://github.com/chanind/tensor-theorem-prover/commit/256ca65a8abdfb0e98f5546e350442a5ba98dfa2))

## v0.10.0 (2022-12-13)
### Feature
* Track proof stats to make performance tweaks easier ([#1](https://github.com/chanind/tensor-theorem-prover/issues/1)) ([`b52192f`](https://github.com/chanind/tensor-theorem-prover/commit/b52192fd6499520c36892918aef1a8f18f2f2072))

## v0.9.0 (2022-12-13)
### Feature
* Allow capping number of returned proofs to boost performance ([`dd92a22`](https://github.com/chanind/tensor-theorem-prover/commit/dd92a220c0034f84c696c630c5f3adff96751ada))

## v0.8.0 (2022-12-12)
### Feature
* Adding a max_resolvent_width option to speed up solving ([`6adc64e`](https://github.com/chanind/tensor-theorem-prover/commit/6adc64eea9c89e8bbf0b435f1e285af70ed8e41b))

## v0.7.0 (2022-12-08)
### Feature
* Adding option to reset the ResolutionProver ([`8649c91`](https://github.com/chanind/tensor-theorem-prover/commit/8649c91e6769828bb14f5ab7fe7d828a9b0637ff))

## v0.6.2 (2022-12-07)
### Fix
* Exporting types for SimilarityFunc ([`6432960`](https://github.com/chanind/tensor-theorem-prover/commit/64329605e85c694079304da914bf12be35618250))

## v0.6.1 (2022-12-07)
### Fix
* Exporting types for Proof and ProofStep ([`c909c6f`](https://github.com/chanind/tensor-theorem-prover/commit/c909c6f281433c94f76707be34be91909807e243))

## v0.6.0 (2022-12-05)
### Feature
* Allow providing extra knowledge when proving ([`f1e53c8`](https://github.com/chanind/tensor-theorem-prover/commit/f1e53c8a4d782f256e640646f3f78c6423bb9857))

## v0.5.0 (2022-12-05)
### Feature
* Adding ResolutionProver.extend_knowledge method to add knowledge to the prover later ([`d21dd91`](https://github.com/chanind/tensor-theorem-prover/commit/d21dd911f994abb69fe7d19a2c8e143dcc3192fe))

## v0.4.0 (2022-10-27)
### Feature
* Adding similarity cache to speed up similarity calculations ([`5bd8c13`](https://github.com/chanind/tensor-theorem-prover/commit/5bd8c1386410d2b4bf04b59c999c4a83e3abd69b))

## v0.3.0 (2022-10-24)
### Feature
* Adding a 'max_similarity' helper to combine different similarity funcs ([`b92c35a`](https://github.com/chanind/tensor-theorem-prover/commit/b92c35ae06d707d462010f38e1d59b22f051d145))

## v0.2.3 (2022-10-23)
### Fix
* Fixing bug when predicates with the same symbol occur in resolve with embeddings ([`17c138c`](https://github.com/chanind/tensor-theorem-prover/commit/17c138c64c8beb449b9e42847db343cb4b7d12e1))

## v0.2.2 (2022-10-23)
### Fix
* Adding py.typed file ([`c01f016`](https://github.com/chanind/tensor-theorem-prover/commit/c01f01604cc48c1f2f1fede77e1f6d8ad08bb189))

## v0.2.1 (2022-10-23)
### Fix
* Adding typing_extensions dep explicitly ([`58e8340`](https://github.com/chanind/tensor-theorem-prover/commit/58e83401e64887635727c7db1ff508c47e4f826d))

## v0.2.0 (2022-10-22)
### Feature
* Enabling auto-publish ([`6fd5b89`](https://github.com/chanind/tensor-theorem-prover/commit/6fd5b897b343a1f5b3b90038c8d8abb0ba011bca))
