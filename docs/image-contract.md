# Benchmark image contract

Agent4Sci runs each benchmark as a self-contained container image. The runner
(`agent4sci`) only provisions the image, installs skills, launches the agent,
and collects artifacts. Everything task-specific lives in the image. This
document specifies the contract an image must satisfy, so you can use the
published images or build your own.

## Startup: keyed on `MODE`

The entrypoint reads the `MODE` environment variable and stages `/workspace`
accordingly:

| `MODE` | Data staged under `/workspace/data/<task>/` | Extra files staged |
|--------|---------------------------------------------|--------------------|
| `hillclimb` | `train/`, `val/` (**never** `test/`) | agent instructions (`CLAUDE.md` / `AGENTS.md`) |
| `evaluate`  | `test/` (plus `train/`, `val/`)             | `evaluation.md`, the standardized `eval_test.py` |

Test data must be **absent** in `hillclimb` mode. This is what enforces the
held-out split: the hill-climbing agent physically cannot read the test set.

Data is downloaded at startup (e.g. from a HuggingFace dataset repo) using the
`HF_TOKEN` passed by the runner. After download, any bootstrap/download helper
should be removed so the agent cannot re-fetch other splits.

Staging must run from the image's **`ENTRYPOINT`** (not `CMD`): the local
backend launches the container as `docker run -d <image> sleep infinity`, so the
entrypoint receives `sleep infinity` as its arguments. The entrypoint should
stage `/workspace`, then either `exec "$@"` (letting the appended `sleep
infinity` keep the container alive) or start its own long-running process (e.g.
sshd). Either way the container must stay alive after staging so the runner can
`docker exec` into it.

## `/workspace` layout

```
/workspace/
├── task.md                 # task description + target metric (readiness signal)
├── paper/paper.pdf         # the source paper
├── repo/                   # standardized reference code (read-only)
├── data/<task>/            # train/ val/ [test/ only in evaluate mode]
├── CLAUDE.md | AGENTS.md   # top-level agent instructions (the active one)
├── evaluation.md           # evaluate mode only
└── runs/                   # the agent writes ALL artifacts here (bind-mounted to the host)
```

The agent runs as user `agent`, works in `/workspace`, and writes to
`/workspace/runs/`. The runner bind-mounts `runs/` to the host, so best
checkpoints and logs persist across the hill-climb → evaluate container switch.

## Readiness signal

The runner considers the container ready when `/workspace/task.md` exists and
data download has finished. Make sure `task.md` is staged **last**, or expose a
separate completion sentinel.

## Artifacts the agent produces (under `/workspace/runs/`)

- `best_checkpoints/` — the model(s) the evaluator will score.
- `SUMMARY.md`, `METHODOLOGY.md` — what was tried and why (written at wrap-up).
- `hillclimb_logs.jsonl` — the hill-climb session log (the auditor's primary evidence).
- `EVAL_RESULTS.md` (evaluate), `eval_logs.jsonl`, `AUDIT_RESULTS.md` (audit).

## Installed tooling

The image must have the agent CLIs on `PATH` (`claude` and/or `codex`) and a
GPU-enabled runtime. The published images build `FROM` a shared base image that
provides CUDA, Python, Node, and the agent CLIs.

## Environment variables the runner sets

`MODE` (`hillclimb` | `evaluate`), `HF_TOKEN`, and the agent API key(s)
(`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`).
