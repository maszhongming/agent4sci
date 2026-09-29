"""The Agent4Sci run pipeline: hill-climb -> evaluate -> audit.

Two stages, each one container session. Stage 1 (MODE=hillclimb, train+val only)
runs the hill-climbing agent then a wrap-up that resumes the same session to
write SUMMARY.md/METHODOLOGY.md. Stage 2 (MODE=evaluate, test staged) runs the
evaluation agent then the auditing agent. The run directory is shared across
both, so the best checkpoints and logs persist. The backend decides *how* a
stage runs; the pipeline only describes what each stage does.
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from agent4sci import prompts as P
from agent4sci.backends import get_backend
from agent4sci.models import get_preset
from agent4sci.registry import resolve_image
from agent4sci.run_spec import AgentStep, Stage

_console = Console()

_WRAPUP_MINUTES = 30
_EVAL_HOURS = 3
_AUDIT_HOURS = 3
_EVAL_MODEL = "claude-opus-4.8"   # evaluation + audit always run with a fixed strong model


def _runid(project: str, model: str) -> str:
    return f"{(project or 'custom').lower()}-{model.replace('.', '')}-{int(time.time())}"


def _prompt_path(name: str) -> str:
    return f"/workspace/runs/.prompts/{name}.txt"


def cmd_run(args) -> int:
    load_dotenv(override=False)

    image = resolve_image(args.project, args.image)
    label = args.project or "this benchmark"
    preset = get_preset(args.model)
    eval_preset = get_preset(_EVAL_MODEL)
    run_dir = Path(args.out) / _runid(args.project or "custom", args.model)
    env = {
        "HF_TOKEN": os.environ.get("HF_TOKEN", ""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    }
    gpus = args.gpus

    hillclimb = Stage(
        name="hillclimb", image=image, mode="hillclimb", run_dir=run_dir, env=env, gpus=gpus,
        skill_mounts=(preset.spec.skill_mounts if args.skills else {}),
        steps=[
            AgentStep(
                name="hillclimb", prompt_text=P.render("hillclimb_start", label, hours=f"{args.hours:g}"),
                command=preset.launch_command(_prompt_path("hillclimb")),
                process_pattern=preset.process_pattern, sentinel=None,
                deadline_s=args.hours * 3600,
            ),
            AgentStep(
                name="wrapup", prompt_text=P.render("hillclimb_end", label, session_log_glob=preset.spec.session_log_glob),
                command=preset.resume_command(_prompt_path("wrapup")),
                process_pattern=preset.process_pattern, sentinel="METHODOLOGY.md",
                deadline_s=_WRAPUP_MINUTES * 60,
            ),
        ],
    )
    evaluate = Stage(
        name="evaluate", image=image, mode="evaluate", run_dir=run_dir, env=env, gpus=gpus,
        skill_mounts={},
        steps=[
            AgentStep(
                name="eval", prompt_text=P.render("eval_start", label),
                command=eval_preset.launch_command(_prompt_path("eval")),
                process_pattern=eval_preset.process_pattern, sentinel="EVAL_RESULTS.md",
                deadline_s=_EVAL_HOURS * 3600,
            ),
            AgentStep(
                name="audit", prompt_text=P.render("audit_start", label),
                command=eval_preset.launch_command(_prompt_path("audit")),
                process_pattern=eval_preset.process_pattern, sentinel="AUDIT_RESULTS.md",
                deadline_s=_AUDIT_HOURS * 3600,
            ),
        ],
    )

    backend_name = "local"
    backend = get_backend(backend_name, dry_run=args.dry_run)
    backend.register_secrets(env.values())
    backend.set_runid(run_dir.name)

    mode_note = " [dim](dry-run: no containers/jobs are started)[/dim]" if args.dry_run else ""
    _console.print(
        f"[bold]Agent4Sci run[/bold]{mode_note}\n"
        f"  project : {args.project or '(custom image)'}\n"
        f"  image   : {image}\n"
        f"  model   : {preset.name} ({preset.family})\n"
        f"  budget  : {args.hours}h hill-climb\n"
        f"  skills  : {'on' if args.skills else 'off'}\n"
        f"  backend : {backend_name}\n"
        f"  out     : {run_dir}\n"
    )

    _console.rule("[bold]Stage 1 — Hill-climb")
    backend.run_stage(hillclimb)
    _console.rule("[bold]Stage 2 — Evaluate & audit")
    backend.run_stage(evaluate)

    audit_file = run_dir / "AUDIT_RESULTS.md"
    verdict_text = audit_file.read_text() if audit_file.exists() else ""
    verdict = "COMPROMISED" if "COMPROMISED" in verdict_text.upper() else (
        "CLEAN" if "CLEAN" in verdict_text.upper() else "unknown"
    )

    _console.rule("[bold]Done")
    _console.print(
        f"  artifacts    : {run_dir}\n"
        f"  summary      : {run_dir}/SUMMARY.md\n"
        f"  eval result  : {run_dir}/EVAL_RESULTS.md\n"
        f"  audit verdict: {verdict}\n"
    )
    if args.dry_run:
        _console.print("[dim]dry-run complete.[/dim]")
    return 0
