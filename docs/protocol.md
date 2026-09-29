# The three-stage protocol

Agent4Sci separates a run into three stages handled by different agents, so
that the score you get back is trustworthy. This mirrors the evaluation
protocol in the paper.

```
        ┌── hill-climbing agent ──┐   ┌── evaluation agent ──┐   ┌── auditing agent ──┐
inputs →│  train + val only       │ → │  held-out test only  │ → │  reads the logs    │→ verdict
        │  improves the metric    │   │  scores submission   │   │  adversarially     │
        └─────────────────────────┘   └──────────────────────┘   └────────────────────┘
```

## Stage 1 — Hill-climb (`MODE=hillclimb`)

The hill-climbing agent gets the paper, the standardized codebase, and the
train/val splits, and a wall-clock budget (`--hours`). Test data is not present
in its container. It proposes ideas, writes code, trains models, evaluates on
val, and iterates. At the deadline the same session is resumed once to write
`SUMMARY.md` and `METHODOLOGY.md` and keep only the best checkpoints.

With `--skills`, the agent also loads the plug-in skills (see [`../agent4sci/skills`](../agent4sci/skills)):
research ideation, experiment management, and an hourly checklist.

## Stage 2 — Evaluate (`MODE=evaluate`)

A separate evaluation agent starts in a fresh container where the held-out test
set is now staged. It loads the submitted checkpoints and scores them with the
standardized `eval_test.py` — never a script the hill-climber wrote — and
writes `EVAL_RESULTS.md`.

## Stage 3 — Audit

An auditing agent reads the full hill-climb and evaluation logs, cross-checks
suspicious reasoning against the actual code and the paper, and returns a
verdict of **CLEAN** or **COMPROMISED** in `AUDIT_RESULTS.md`, citing evidence.
It looks for the four failure modes the paper documents: test-data leakage,
evaluation tampering, result fabrication, and intent red flags.

## Why this matters

On raw research repositories, an agent that is simply told to "improve the
metric" often games the evaluation — selective reporting, test-set
contamination, metric manipulation, hardcoded outputs — usually as a byproduct
of leaky, ambiguous setups rather than deliberate cheating. Physically
removing the test set during hill-climbing and scoring with an independent
agent turns most of those failure modes into impossibilities, and the audit
makes the rest visible. A clean audit is a verdict, not a proof: the auditor is
itself a model, so subtler failures can still slip past.

See the paper for the full study.
