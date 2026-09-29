"""Model families and presets.

A *family* (claude | codex) fixes the CLI invocation, the agent instruction
filename, which bundled skill directories mount where, and where the session
log lands inside the container. A *preset* (from presets.yaml) picks a family
and sets the model flag and reasoning effort.
"""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_PRESETS_PATH = Path(__file__).resolve().parent / "presets.yaml"


@dataclass(frozen=True)
class ModelFamily:
    # Launch command template; formatted with {model_flag}, {effort}, {prompt_file}.
    launch_cmd: str
    # Resume the most recent session with a new prompt (used for the wrap-up stage);
    # formatted with {prompt_file}.
    resume_cmd: str
    # Which top-level agent instruction file this family reads (the others are removed at setup).
    agent_md: str
    # Bundled skill dir (under agent4sci/skills/) -> dot-directory mounted at /workspace in the container.
    skill_mounts: dict
    # Process name to match for liveness / stop (pgrep -f / pkill -f).
    process_pattern: str
    # Glob (inside the container) matching the agent's own session log; the
    # wrap-up prompt tells the agent to copy it to runs/hillclimb_logs.jsonl.
    session_log_glob: str


FAMILIES: dict[str, ModelFamily] = {
    "claude": ModelFamily(
        launch_cmd=(
            'claude --dangerously-skip-permissions'
            ' --model "{model_flag}" --effort {effort}'
            ' "$(cat {prompt_file})"'
        ),
        resume_cmd='claude --dangerously-skip-permissions --continue "$(cat {prompt_file})"',
        agent_md="CLAUDE.md",
        skill_mounts={"claude": ".claude"},
        process_pattern="claude",
        session_log_glob="/home/agent/.claude/projects/-workspace/*.jsonl",
    ),
    "codex": ModelFamily(
        launch_cmd=(
            'codex --yolo --model {model_flag}'
            ' -c model_reasoning_effort={effort}'
            ' "$(cat {prompt_file})"'
        ),
        resume_cmd='codex --yolo resume --last "$(cat {prompt_file})"',
        agent_md="AGENTS.md",
        skill_mounts={"codex": ".codex", "agents": ".agents"},
        process_pattern="codex",
        session_log_glob="/home/agent/.codex/sessions/*/*/*/**.jsonl",
    ),
}


@dataclass(frozen=True)
class ModelPreset:
    name: str
    family: str
    model_flag: str
    effort: str

    @property
    def spec(self) -> ModelFamily:
        return FAMILIES[self.family]

    @property
    def process_pattern(self) -> str:
        return self.spec.process_pattern

    def launch_command(self, prompt_file: str) -> str:
        return self.spec.launch_cmd.format(
            model_flag=self.model_flag, effort=self.effort, prompt_file=prompt_file
        )

    def resume_command(self, prompt_file: str) -> str:
        return self.spec.resume_cmd.format(prompt_file=prompt_file)


def load_presets() -> dict[str, ModelPreset]:
    with open(_PRESETS_PATH) as f:
        raw = yaml.safe_load(f) or {}
    presets = {}
    for name, spec in raw.items():
        family = spec.get("family", "")
        if family not in FAMILIES:
            raise ValueError(
                f"preset '{name}' has unknown family '{family}'; "
                f"known families: {sorted(FAMILIES)}"
            )
        presets[name] = ModelPreset(
            name=name,
            family=family,
            model_flag=spec.get("model_flag", ""),
            effort=spec.get("effort", ""),
        )
    return presets


def get_preset(name: str) -> ModelPreset:
    presets = load_presets()
    if name not in presets:
        raise SystemExit(
            f"unknown model preset '{name}'. available: {', '.join(sorted(presets))}"
        )
    return presets[name]


def cmd_models() -> int:
    from rich.console import Console
    from rich.table import Table

    presets = load_presets()
    table = Table(title="Agent4Sci model presets")
    table.add_column("preset", style="bold cyan")
    table.add_column("family")
    table.add_column("model flag")
    table.add_column("effort")
    for name in sorted(presets):
        p = presets[name]
        table.add_row(name, p.family, p.model_flag, p.effort)
    Console().print(table)
    return 0
