"""Benchmark registry: resolve a project name to its container image."""
from dataclasses import dataclass
from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"


@dataclass(frozen=True)
class Benchmark:
    name: str
    image: str
    domain: str
    task: str


def load_registry() -> dict[str, Benchmark]:
    with open(_REGISTRY_PATH) as f:
        raw = yaml.safe_load(f) or {}
    out = {}
    for name, spec in raw.items():
        out[name] = Benchmark(
            name=name,
            image=spec["image"],
            domain=spec.get("domain", ""),
            task=spec.get("task", ""),
        )
    return out


def resolve_image(project: str | None, image_override: str | None = None) -> str:
    """Resolve the image to run: an explicit --image wins, else map --project."""
    if image_override:
        return image_override
    if not project:
        raise SystemExit("specify --project (see `agent4sci list`) or --image.")
    reg = load_registry()
    # case-insensitive match on project name for convenience
    for name, bench in reg.items():
        if name.lower() == project.lower():
            return bench.image
    raise SystemExit(
        f"unknown project '{project}'. run `agent4sci list` to see available benchmarks."
    )


def cmd_list() -> int:
    from rich.console import Console
    from rich.table import Table

    reg = load_registry()
    table = Table(title=f"Agent4Sci benchmarks ({len(reg)})")
    table.add_column("project", style="bold cyan")
    table.add_column("domain")
    table.add_column("task")
    for name in sorted(reg):
        b = reg[name]
        table.add_row(b.name, b.domain, b.task)
    Console().print(table)
    return 0
