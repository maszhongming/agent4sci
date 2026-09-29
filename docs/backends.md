# How a run executes

`agent4sci run` runs each stage of the pipeline as a Docker container on the
local machine and drives the agent inside it with `docker exec`.

## Local Docker

For each stage the runner:

1. `docker run -d` the benchmark image with the stage's `MODE`
   (`hillclimb` stages train+val only; `evaluate` stages the held-out test set),
   bind-mounting the run directory at `/workspace/runs`;
2. waits for the image entrypoint to stage `/workspace` and finish downloading data;
3. (if `--skills`) copies the plug-in skills into the container;
4. runs each agent step headless, capturing logs to `/workspace/runs/*.log`;
5. tears the container down.

Because `/workspace/runs` is a host bind mount, the agent's best checkpoints and
logs persist across the hill-climb → evaluate container switch and are what the
evaluation and auditing agents read.

**Requirements:** Docker, the NVIDIA Container Toolkit, and at least one GPU.

```bash
agent4sci run --project PFDelta --model claude-opus-4.8 --hours 12 --skills
```

## Preview without running

`--dry-run` prints every command it would execute, with API keys and tokens
redacted, without starting anything:

```bash
agent4sci run --project PFDelta --dry-run
```
