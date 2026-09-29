"""Pipeline orchestration tests using a mock backend (no container runtime)."""
import types

import agent4sci.pipeline as pipeline
from tests.mock_backend import MockBackend


def _args(**kw):
    base = dict(
        project="PFDelta", image=None, model="claude-opus-4.6", hours=1.0,
        skills=True, backend="mock", out="./_test_runs", dry_run=False, gpus="all",
    )
    base.update(kw)
    return types.SimpleNamespace(**base)


def _run(monkeypatch, **kw):
    mock = MockBackend()
    monkeypatch.setattr(pipeline, "get_backend", lambda name, dry_run: mock)
    rc = pipeline.cmd_run(_args(**kw))
    assert rc == 0
    return mock


def test_two_stages_in_order(monkeypatch):
    mock = _run(monkeypatch)
    assert [s.mode for s in mock.stages] == ["hillclimb", "evaluate"]
    assert [s.name for s in mock.stages] == ["hillclimb", "evaluate"]


def test_stage_steps(monkeypatch):
    mock = _run(monkeypatch)
    hc, ev = mock.stages
    assert [s.name for s in hc.steps] == ["hillclimb", "wrapup"]
    assert [s.name for s in ev.steps] == ["eval", "audit"]


def test_skills_toggle(monkeypatch):
    on = _run(monkeypatch, skills=True)
    assert on.stages[0].skill_mounts == {"claude": ".claude"}
    off = _run(monkeypatch, skills=False)
    assert off.stages[0].skill_mounts == {}
    # eval stage never gets skills
    assert on.stages[1].skill_mounts == {}


def test_wrapup_resumes_session(monkeypatch):
    mock = _run(monkeypatch)
    wrapup = mock.stages[0].steps[1]
    assert "--continue" in wrapup.command
    assert wrapup.sentinel == "METHODOLOGY.md"


def test_eval_audit_use_claude_and_sentinels(monkeypatch):
    mock = _run(monkeypatch, model="codex-5.4")  # hill-climb with codex...
    hc, ev = mock.stages
    assert "codex" in hc.steps[0].command            # ...but eval/audit stay on claude
    assert "claude" in ev.steps[0].command
    assert ev.steps[0].sentinel == "EVAL_RESULTS.md"
    assert ev.steps[1].sentinel == "AUDIT_RESULTS.md"


def test_hillclimb_budget_applied(monkeypatch):
    mock = _run(monkeypatch, hours=7.0)
    assert mock.stages[0].steps[0].deadline_s == 7.0 * 3600
