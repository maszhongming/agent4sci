Each experiment consists of a training run and task evaluation on a single seed and/or fold of the training and validation sets. Experiments are organized by subdirectories with individual aliases (`runs/experiments/{alias}`).

**If you are a subagent, follow your instructions carefully: you MUST run the smoke test and write `CHANGES.md` before concluding your session.**

# Implementing Experiment Code

Step 1: Find the training code and identify the entry point, model class, dataset class, training loop, and loss function. Trace the full forward pass to understand what happens on CPU vs GPU.

Step 2: Identify the entrypoints for the experiment code you need to implement. Work within the repo, writing additional modules as necessary. **Never modify shared package code in `/usr/local/`**: this will contaminate other experiments relying on the same packages.

## Preparing Wrapper Scripts

All experiments require individual `train.py` and `eval.py` wrapper scripts.
`train.py`: Training code, may include automatic validation (e.g. for early stopping). **Training must use only training data, not val data**.
`eval.py`: This should be run to evaluate hill-climb performance on the validation set.

### Arguments

Wrapper scripts should take `--data-dir`, `--checkpoint-dir`, and `--output-dir` arguments. They may optionally take `--seed` and `--fold` arguments if multiple seeds/folds are referenced in the baseline.

Each script should save:
- Checkpoints in `/workspace/runs/checkpoints/{alias}/*`
- Outputs in `/workspace/runs/outputs/{alias}/*`
- Logs in `/workspace/runs/logs/{alias}/*`

Carefully check for hard-coded paths and redirect them to these target directories.

### Logging

Both training and validation wrappers should write logs that track runtime and training progress. You should implement this from scratch if the reference code is insufficient.

All logging statements must be timestamped.

Always use `flush=True` for print statements.

```python
# CORRECT
print(f"Epoch {epoch} loss: {loss:.4f}", flush=True)

# WRONG: Output buffered
print(f"Epoch {epoch} loss: {loss:.4f}")
```

Use the logging module for structured output.

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("/workspace/runs/logs/{alias}/train.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

# Documenting Experiment Code

If your experiment code required significant changes, write a summary of your work at `/workspace/runs/experiments/{alias}/CHANGES.md`.

Example of `CHANGES.md`:
```
# Experiment: [Brief Description]

## Changes Made
- [Change 1]
- [Change 2]

## Why These Changes
[Explanation of why modifications were necessary]

## Files Changed
[Explanation of key files created or modified]

## How to Run
[Provide instructions on how to run a short 1-2 epoch smoke test to verify correctness.]
python train.py [args]
python eval.py [args]
```
