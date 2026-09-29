"""Local Docker backend.

Runs each stage as a persistent Docker container (`docker run -d`) that the
backend drives with `docker exec`. Artifacts persist on the host via a bind
mount of the run directory at /workspace/runs, which is how the agent's
checkpoints survive the hill-climb -> evaluate container switch.
"""
import time
from pathlib import Path

from agent4sci.backends.base import Backend

_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


class LocalDockerBackend(Backend):
    name = "local"

    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run=dry_run)
        self.cname: str | None = None
        self.run_dir: Path | None = None

    # -- Stage entry point ---------------------------------------------------
    def run_stage(self, stage):
        self.run_dir = Path(stage.run_dir).resolve()
        if not self.dry_run:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            # The run dir is bind-mounted and written by the container's `agent`
            # user, whose uid need not match the host owner. An in-container chown
            # fixes this on a local FS but is denied on shared/NFS mounts, so also
            # open the dir from the host side (where we own it) — otherwise the
            # agent silently can't persist any artifacts.
            self.run_dir.chmod(0o777)
        self.cname = f"agent4sci-{self.runid}-{stage.mode}"
        try:
            self._up(stage.image, stage.mode, stage.env, stage.gpus)
            if stage.skill_mounts:
                self._put_skills(stage.skill_mounts)
            for step in stage.steps:
                self._put_prompt(step.name, step.prompt_text)
                self._launch_agent(step.command, f"{step.name}.log")
                reason = self._monitor(step.process_pattern, step.deadline_s, step.sentinel)
                self._note(f"step '{step.name}' ended ({reason})")
                self._stop_agent(step.process_pattern)
        finally:
            self._down()

    # -- container operations ------------------------------------------------
    @staticmethod
    def _gpu_args(gpus):
        """Build the `docker run` GPU flag portably.

        `all` (the default) or empty exposes every GPU; `none` exposes none. A
        device selection is emitted in Docker's quoted `"device=<ids>"` form:
        a bare `--gpus device=1,6` is misparsed (the `6` is read as a GPU
        *count*), which errors on hosts whose default Docker runtime is nvidia.
        """
        g = (gpus or "all").strip()
        if g.lower() in ("", "none"):
            return []
        if g.lower() == "all":
            return ["--gpus", "all"]
        ids = g[len("device="):] if g.lower().startswith("device=") else g
        return ["--gpus", f'"device={ids}"']

    def _up(self, image, mode, env, gpus):
        self._note(f"provisioning {self.cname} (image={image}, MODE={mode}, gpus={gpus})")
        cmd = ["docker", "run", "-d", "--name", self.cname, *self._gpu_args(gpus)]
        for k, v in {"MODE": mode, **env}.items():
            if v:
                cmd += ["-e", f"{k}={v}"]
        cmd += ["-v", f"{self.run_dir}:/workspace/runs", image, "sleep", "infinity"]
        self._sh(cmd)
        self._wait_ready()
        # Best-effort: on a local FS this makes new artifacts agent-owned. On a
        # shared/NFS bind mount it is denied, but the host-side chmod in
        # run_stage already guarantees writability, so swallow any error.
        self._sh(
            ["docker", "exec", self.cname, "chown", "-R", "agent:agent", "/workspace/runs"],
            check=False, capture=True,
        )

    def _wait_ready(self, timeout_s: float = 4 * 3600):
        self._note("waiting for the image to stage /workspace and download data "
                   "(large datasets can take a while)")
        if self.dry_run:
            return
        deadline = time.time() + timeout_s
        polls = 0
        while time.time() < deadline:
            _, rc = self._sh(
                ["docker", "exec", self.cname, "test", "-f", "/workspace/task.md"], check=False,
            )
            if rc == 0:
                return
            # verify the container is still alive so we fail fast on a dead entrypoint
            _, alive = self._sh(["docker", "exec", self.cname, "true"], check=False)
            if alive != 0:
                raise RuntimeError(f"{self.cname}: container exited before staging /workspace")
            polls += 1
            if polls % 20 == 0:
                self._note(f"still waiting for /workspace/task.md (~{polls * 15 // 60} min)")
            time.sleep(15)
        raise RuntimeError(f"{self.cname}: /workspace/task.md not present within {timeout_s/3600:.0f}h")

    def _put_skills(self, mounts):
        for src, dotdir in mounts.items():
            self._note(f"installing skills: {src} -> /workspace/{dotdir}")
            self._sh(["docker", "exec", self.cname, "mkdir", "-p", f"/workspace/{dotdir}"])
            self._sh(["docker", "cp", f"{_SKILLS_DIR / src}/.", f"{self.cname}:/workspace/{dotdir}"])
            self._sh(
                ["docker", "exec", self.cname, "chown", "-R", "agent:agent", f"/workspace/{dotdir}"],
                check=False,
            )

    def _put_prompt(self, name, text) -> str:
        if not self.dry_run:
            prompts_dir = self.run_dir / ".prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            (prompts_dir / f"{name}.txt").write_text(text)
        return f"/workspace/runs/.prompts/{name}.txt"

    def _launch_agent(self, command, log_name):
        self._note(f"launching agent (background), log -> /workspace/runs/{log_name}")
        full = f"{command} > /workspace/runs/{log_name} 2>&1"
        self._sh([
            "docker", "exec", "-u", "agent", "-d", "-w", "/workspace",
            self.cname, "bash", "-lc", full,
        ])

    def _monitor(self, process_pattern, deadline_s, sentinel=None):
        self._note(f"monitoring '{process_pattern}' (cap={deadline_s/3600:.1f}h, sentinel={sentinel})")
        if self.dry_run:
            return "dry-run"
        deadline = time.time() + deadline_s
        while time.time() < deadline:
            if sentinel and (self.run_dir / sentinel).exists():
                return "sentinel"
            _, rc = self._sh(["docker", "exec", self.cname, "pgrep", "-f", process_pattern], check=False)
            if rc != 0:
                return "process-exited"
            time.sleep(60)
        return "deadline"

    def _stop_agent(self, process_pattern):
        if self.cname:
            self._sh(["docker", "exec", self.cname, "pkill", "-f", process_pattern], check=False)

    def _down(self):
        if self.cname:
            self._note(f"tearing down {self.cname}")
            # Artifacts under /workspace/runs are created by the container's
            # agent user (uid need not match the host). Relax their perms as
            # their owner — chmod is allowed on shared/NFS mounts where chown is
            # not — so the host can read and delete them after the run.
            self._sh(
                ["docker", "exec", "-u", "agent", self.cname, "chmod", "-R", "o+rwX", "/workspace/runs"],
                check=False, capture=True,
            )
            self._sh(["docker", "rm", "-f", self.cname], check=False)
            self.cname = None
