"""Unit tests for the registry, presets, and prompts."""
import pytest

from agent4sci import prompts as P
from agent4sci.models import get_preset, load_presets
from agent4sci.registry import load_registry, resolve_image


def test_registry_has_suite_plus_pfdelta2000():
    reg = load_registry()
    suite = [k for k in reg if k != "PFDelta_2000"]
    assert len(suite) == 20            # the published suite
    assert "PFDelta_2000" in reg       # plus the case-study variant
    assert "ZAPBench" not in reg       # dropped from the final suite


def test_resolve_image_case_insensitive():
    assert resolve_image("PFDelta") == resolve_image("pfdelta")
    assert resolve_image("PFDelta").startswith("ghcr.io/")


def test_resolve_image_override_wins():
    assert resolve_image("PFDelta", "my/custom:img") == "my/custom:img"


def test_unknown_project_errors():
    with pytest.raises(SystemExit):
        resolve_image("NotARealProject")


def test_presets_families():
    presets = load_presets()
    assert presets["claude-opus-4.6"].family == "claude"
    assert presets["codex-5.4"].family == "codex"


def test_launch_and_resume_commands():
    claude = get_preset("claude-opus-4.6")
    launch = claude.launch_command("/p.txt")
    assert "claude" in launch and "opus[1m]" in launch and "/p.txt" in launch
    assert "--continue" in claude.resume_command("/w.txt")
    codex = get_preset("codex-5.4")
    assert "codex" in codex.launch_command("/p.txt")


def test_prompts_render_project_substitution():
    assert "PFDelta" in P.render("audit_start", "PFDelta")
    # hillclimb prompt has no placeholder but should still render
    assert P.render("hillclimb_start", "PFDelta")


def test_hillclimb_prompt_substitutes_hours():
    out = P.render("hillclimb_start", "PFDelta", hours="2")
    assert "2 hours" in out
    assert "{HOURS}" not in out


def test_wrapup_prompt_names_audit_log_and_checkpoints():
    out = P.render("hillclimb_end", "PFDelta", session_log_glob="/x/*.jsonl")
    assert "hillclimb_logs.jsonl" in out
    assert "/x/*.jsonl" in out
    assert "best_checkpoints" in out


def test_unknown_preset_errors():
    with pytest.raises(SystemExit):
        get_preset("no-such-model")


def test_hours_below_minimum_rejected():
    from agent4sci.cli import build_parser
    with pytest.raises(SystemExit):
        build_parser().parse_args(["run", "--project", "X", "--hours", "0.5"])
    # 1.0 and above are accepted
    args = build_parser().parse_args(["run", "--project", "X", "--hours", "1"])
    assert args.hours == 1.0


def test_opus_48_is_default_model():
    from agent4sci.cli import build_parser
    import agent4sci.pipeline as pipeline
    presets = load_presets()
    assert "claude-opus-4.8" in presets
    assert presets["claude-opus-4.8"].model_flag == "claude-opus-4-8[1m]"
    assert pipeline._EVAL_MODEL == "claude-opus-4.8"
    args = build_parser().parse_args(["run", "--project", "X"])
    assert args.model == "claude-opus-4.8"


def test_gpu_args_formats_device_selection():
    from agent4sci.backends.local import LocalDockerBackend as B
    assert B._gpu_args("all") == ["--gpus", "all"]
    assert B._gpu_args("") == ["--gpus", "all"]
    assert B._gpu_args("none") == []
    # a bare "device=1,6" is misparsed by docker; it must be quoted.
    assert B._gpu_args("device=1,6") == ["--gpus", '"device=1,6"']
    assert B._gpu_args("1,6") == ["--gpus", '"device=1,6"']
