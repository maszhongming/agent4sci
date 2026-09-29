"""Backend-agnostic description of a run.

A run is a sequence of *stages*, each a single container session in one MODE.
A stage runs an ordered list of *agent steps* (launch a CLI with a prompt, wait
for a sentinel or a deadline). Backends consume this spec:

- the local backend runs each stage as a persistent Docker container it exec's into.
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentStep:
    name: str                 # "hillclimb" | "wrapup" | "eval" | "audit"
    prompt_text: str          # written to <run>/.prompts/<name>.txt
    command: str              # fully-rendered agent CLI command (reads that prompt file)
    process_pattern: str      # for liveness / stop (pgrep -f / pkill -f)
    sentinel: str | None      # a file under <run>/ whose appearance ends the step early
    deadline_s: float         # hard wall-clock cap for the step


@dataclass
class Stage:
    name: str                 # "hillclimb" | "evaluate"
    image: str
    mode: str                 # sets MODE in the container (controls data staging)
    run_dir: Path             # bind-mounted to /workspace/runs
    env: dict
    gpus: str                 # local: docker --gpus value
    skill_mounts: dict        # {package_skill_dir: container_dotdir}; empty = no skills
    steps: list = field(default_factory=list)
