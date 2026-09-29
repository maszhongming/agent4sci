"""`agent4sci watch <run-dir>`: snapshot of a run's progress.

Shows which stage artifacts exist and tails the newest log. For a live feed,
`tail -f <run-dir>/hillclimb.log` works too.
"""
from pathlib import Path

from rich.console import Console

_ARTIFACTS = ["SUMMARY.md", "METHODOLOGY.md", "EVAL_RESULTS.md", "AUDIT_RESULTS.md"]


def cmd_watch(run_dir: str, tail: int = 40) -> int:
    d = Path(run_dir)
    if not d.exists():
        raise SystemExit(f"run directory not found: {d}")

    c = Console()
    c.print(f"[bold]{d}[/bold]")
    for name in _ARTIFACTS:
        present = (d / name).exists()
        mark = "[green]✓[/green]" if present else "[dim]·[/dim]"
        c.print(f"  {mark} {name}")

    logs = [p for p in d.glob("*.log") if p.is_file()]
    if logs:
        newest = max(logs, key=lambda p: p.stat().st_mtime)
        c.rule(f"tail {newest.name} (last {tail} lines)")
        lines = newest.read_text(errors="replace").splitlines()[-tail:]
        c.print("\n".join(lines) if lines else "[dim](empty)[/dim]")
    else:
        c.print("[dim]no logs yet[/dim]")
    return 0
