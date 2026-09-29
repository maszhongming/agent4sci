"""Backend interface.

A backend consumes a `Stage` (see agent4sci.run_spec) and executes it: bring a
container up in the stage's MODE (which controls whether the held-out test set
is staged), install skills, run each agent step, and tear down. The MODE-driven
data staging and the /workspace layout are the *image contract* (see
docs/image-contract.md); backends only provision and drive.
"""
import shlex
import subprocess


class Backend:
    name = "base"

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.runid = "run"
        self._secrets: set[str] = set()

    def set_runid(self, runid: str):
        self.runid = runid

    # -- secret redaction ----------------------------------------------------
    def register_secrets(self, values):
        """Register secret strings so they are never printed, even in dry-run."""
        for v in values:
            if v and len(str(v)) >= 8:
                self._secrets.add(str(v))

    def _redact(self, text: str) -> str:
        for s in self._secrets:
            text = text.replace(s, "***REDACTED***")
        return text

    # -- shared shell helper -------------------------------------------------
    def _sh(self, cmd, capture=False, check=True, timeout=None, env=None):
        """Run a command (list of args). In dry-run, print and return ('', 0)."""
        printable = self._redact(" ".join(shlex.quote(str(c)) for c in cmd))
        if self.dry_run:
            print(f"  [dry-run] {printable}")
            return "", 0
        proc = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, env=env)
        if check and proc.returncode != 0:
            err = (proc.stderr or "").strip() if capture else ""
            raise RuntimeError(f"command failed ({proc.returncode}): {printable}\n{err}")
        return (proc.stdout if capture else ""), proc.returncode

    def _note(self, msg: str):
        prefix = "[dry-run] " if self.dry_run else ""
        print(f"  {prefix}{self._redact(msg)}")

    # -- interface -----------------------------------------------------------
    def run_stage(self, stage):
        """Execute one Stage (a single container session and its agent steps)."""
        raise NotImplementedError
