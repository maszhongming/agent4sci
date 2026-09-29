"""Load and render the three-stage instruction prompts (prompts/prompts.yaml).

Keys: hillclimb_start, hillclimb_end, eval_start, audit_start. Placeholders
({PROJECT}, {HOURS}, {SESSION_LOG_GLOB}, ...) are filled by literal string
replacement, so prompt bodies may otherwise contain braces.
"""
from pathlib import Path

import yaml

_PROMPTS_PATH = Path(__file__).resolve().parent / "prompts" / "prompts.yaml"


def load_prompts() -> dict:
    with open(_PROMPTS_PATH) as f:
        return yaml.safe_load(f) or {}


def render(key: str, project: str = "", **subs) -> str:
    prompts = load_prompts()
    if key not in prompts:
        raise KeyError(f"prompt '{key}' not found in {_PROMPTS_PATH}")
    text = prompts[key].replace("{PROJECT}", project)
    for name, value in subs.items():
        text = text.replace("{" + name.upper() + "}", str(value))
    return text
