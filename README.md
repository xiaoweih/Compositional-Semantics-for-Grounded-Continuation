# What Still Stands? — reproducibility artefact

This repository contains the executable reference semantics and finite checks for
*What Still Stands? A Compositional Semantics for Grounded Continuation in
LLM Conversations*.
It mirrors the paper's state $D=(\Sigma,\mathit{Args},E,S,B)$, typed event
families, grounding operator, certificates, and fixed-point invalidation.

## Run

Python 3.9 or later is sufficient; there are no third-party dependencies.

```sh
python3 run_experiments.py
```

The command reproduces the paper's running examples and checks 800 generated
acyclic states. For every generated state, it compares the declarative and
worklist computations of grounding and invalidation, and checks
$X^*=\mathit{Args}\setminus\mathit{Gr}$.

To also write a small timing dataset to `results/scaling.csv`, run:

```sh
python3 run_experiments.py --scale
```

The random seed and number of generated states can be changed with `--seed` and
`--trials`.

## Contents

- `gc_semantics.py`: state, warrants, event application, grounding,
  certificates, invalidation, and affected records.
- `run_experiments.py`: running examples, randomized consistency checks, and
  an optional scaling run.
- `CITATION.cff`: citation metadata for the artefact.

The code is deliberately compact and standard-library only. It is a reference
implementation of the formal model, not a natural-language parser or a
production conversation system.

Before publishing the repository, add the open-source licence agreed by all
authors. No licence is imposed by this package.
