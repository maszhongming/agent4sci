"""Command-line interface for Agent4Sci.

Usage:
    agent4sci list
    agent4sci run --project PFDelta --model claude-opus-4.8 --hours 12 --skills
    agent4sci watch <run-dir>
"""
import argparse
import sys

from agent4sci import __version__


def _min_hours(v):
    """Reject sub-1h budgets: research + experiment setup (with --skills, a
    literature review runs first) can consume a tiny budget before any real
    hill-climbing happens. Use --dry-run to preview a run cost-free."""
    try:
        f = float(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid float value: {v!r}")
    if f < 1.0:
        raise argparse.ArgumentTypeError(f"must be at least 1.0 hour (got {f})")
    return f


def _add_run_parser(sub):
    p = sub.add_parser(
        "run",
        help="Run the hill-climb → evaluate → audit pipeline on a benchmark.",
    )
    p.add_argument("--project", help="Benchmark name (resolved to an image via registry.yaml).")
    p.add_argument("--image", help="Explicit container image (advanced; overrides --project).")
    p.add_argument("--model", default="claude-opus-4.8", help="Model preset (see `agent4sci models`).")
    p.add_argument("--hours", type=_min_hours, default=12.0, help="Hill-climbing wall-clock budget in hours (minimum 1.0; with --skills, 2h+ is practical).")
    skills = p.add_mutually_exclusive_group()
    skills.add_argument("--skills", dest="skills", action="store_true", help="Enable the plug-in research skills.")
    skills.add_argument("--no-skills", dest="skills", action="store_false", help="Disable the plug-in skills (default).")
    p.set_defaults(skills=False)
    p.add_argument("--gpus", default="all", help="GPUs to expose to each container (Docker --gpus value, e.g. 'all' or 'device=0,1').")
    p.add_argument("--out", default="./runs", help="Directory to write run artifacts into.")
    p.add_argument("--dry-run", action="store_true", help="Print the commands that would run, without executing.")


def _add_list_parser(sub):
    sub.add_parser("list", help="List the benchmarks available in the registry.")


def _add_models_parser(sub):
    sub.add_parser("models", help="List the available model presets.")


def _add_watch_parser(sub):
    p = sub.add_parser("watch", help="Tail progress of a run directory.")
    p.add_argument("run_dir", help="Path to a run directory produced by `agent4sci run`.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent4sci",
        description="Run frontier coding agents on scientific ML benchmarks: hill-climb, evaluate, and audit.",
    )
    parser.add_argument("--version", action="version", version=f"agent4sci {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    _add_run_parser(sub)
    _add_list_parser(sub)
    _add_models_parser(sub)
    _add_watch_parser(sub)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "list":
        from agent4sci.registry import cmd_list
        return cmd_list()
    if args.command == "models":
        from agent4sci.models import cmd_models
        return cmd_models()
    if args.command == "run":
        from agent4sci.pipeline import cmd_run
        return cmd_run(args)
    if args.command == "watch":
        from agent4sci.watch import cmd_watch
        return cmd_watch(args.run_dir)

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
