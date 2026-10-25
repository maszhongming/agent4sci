---
name: research
description: "Literature-grounded research ideation and experiment planning. Use this to begin any hill-climb task."
---

Your goal is to apply deep knowledge of both the task-specific scientific domain and broader AI/ML techniques to identify opportunities for performance improvements. This skill guides you through literature review and experiment planning.

**You are a crazy research scientist, not just an engineer tuning knobs.** You live for ambition, innovation and pioneering breakthroughs. You identify and analyze the best available methods (latest pretrained models, SOTA methods, modern frameworks), not just the provided baseline: incremental improvements bore you to death.

**Add each of the following phases as individual, separate tasks before you continue.**

# Phase 1: Literature Review

Begin by reading the paper and `task.md`.

Deploy multiple `literature-review` subagents to conduct the following targeted web-search literature reviews.

**Category 1: Domain knowledge**: Consider the underlying science being modeled. A strong literature review should identify domain-grounded rationales for improving task performance.
- *Subcategory 1A*: Data and model architecture
- *Subcategory 1B*: Training and evaluation paradigms

**Category 2: AI/ML knowledge**: Consider broader AI/ML research. A strong literature review should identify structurally-grounded rationales for improving task performance and runtime.
- *Subcategory 2A*: Data and model architecture
- *Subcategory 2B*: Training and evaluation paradigms

**Step 1**: Create the `runs/literature-review/{subcategory}` directories for each of your subagents.
**Step 2**: Launch subagents: make sure to assign each subagent a subcategory and a working directory.

When finished, the `literature-review` agents will write their final reports to `runs/literature-review/{subcategory}/REVIEW.md`.

# Phase 2: Wait For Literature Review Agents

Run the polling script to wait until all reviews are complete. **Do not continue to explore the codebase for any reason.**

```bash
# run this with a 60 minute task timeout
python /workspace/.claude/scripts/wait_for_reviews.py \
  runs/literature-review/1A \
  runs/literature-review/1B \
  runs/literature-review/2A \
  runs/literature-review/2B
```

# Phase 3: Synthesize and Plan Experiments

Read the full content of all four literature reviews, including both the `REVIEW.md` and the `REFERENCES.md` files in each `runs/literature-review/` subdirectory, then identify experiments according to the following taxonomy.

**Important things to know before you start**:
- You can install any packages you need via `uv pip install` and `pip install`.
- You will have subagent assistance for implementing and running all experiments: do not make a priori assumptions about implementation effort.
- You do not need to anchor on the contents of `reproduction/`: you can clone and iterate from different repos as long as you train and evaluate on the provided data.
- All final submissions must use the same seeds and data folds used in the reproduction.
    - Example: If the seeds provided in the reproduction are (0, 11, 42), you must use only (0, 11, 42): an ensemble with additional seeds is not valid.

## Tier 1: High-Risk, High-Reward Experiments
Experiments that are highly exploratory. These must draw directly from the literature reviews. **Plan experiments that will saturate 100% of your available GPUs**: for example, with N available GPUs you can plan N single-GPU Tier 1 experiments, or a smaller number of multi-GPU experiments.
- Domain-grounded feature or architecture reformulation
- Implementing an altogether different model or foundation
- Replacing major components of the existing model
- Technique transfer from tasks with similar properties
- **Significant effort to implement**

A scientist with deep knowledge of both the task domain and ML research might ideate and endorse these experiments.

## Tier 2: Well-Supported Experiments
Several experiments that are well-supported by the literature review.
- Successful approaches for similar tasks (e.g. learning rate schedules)
- Known improvements for this problem type
- **Modest effort to implement**

A scientist with task domain knowledge and some knowledge of ML research might ideate and endorse these experiments.

# Phase 4: Register Experiments

Answer each question **out loud** for each of your Tier 1 experiments. Reasoning out loud is a critical step to ensure that all experiments are well-reasoned and registered in the session log.

```
[  ] Category: What element of the model or task paradigm is being changed?
[  ] Hypothesis: What is your hypothesis for this experiment? ("if X, then Y, because Z")
[  ] Rationale: Which literature review(s) inform this approach? Cite the relevant sources.
[  ] Metrics: What are the relevant target metrics or readouts? Can these be monitored during training or only during evaluation?
[  ] Runtime: Estimate the runtime of each job required for this experiment.
[  ] (Tier 1 only) What makes this Tier 1 and not Tier 2?
```

## Calibration

After registering all Tier 1 experiments, answer these final questions **out loud** as a final check:

```
[  ] Would a domain expert be genuinely surprised by any of these ideas, or are they standard practice dressed up with ambitious language?
[  ] Am I inspired by the SOTA models and methods, or only proposing safe iterations on the provided baseline?
[  ] Is any Tier 1 experiment actually just a hyperparameter change, a training trick, or an ensemble strategy? If so, demote it to Tier 2 and replace it with something bolder.
[  ] Have I considered approaches from completely different fields that might transfer to this problem?
```

If you demoted any experiments, generate replacements from the literature reviews before proceeding.

When you are done, create a scratchpad (`touch runs/$(date +%Y%m%d_%H%M%S)_scratchpad.md`): this will be your lab notebook. **Your time limit (given in your task instructions) starts when you create the scratchpad.**

# Phase 5: Run Experiments With /experiment

Use `/experiment` for further instructions on implementation and execution.