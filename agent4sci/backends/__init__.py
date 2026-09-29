"""Execution backends: where the container runs.

Currently only the local Docker backend is supported. The backend interface
(agent4sci.backends.base.Backend, driven by agent4sci.run_spec.Stage) is kept
deliberately small so other backends can be added without touching the pipeline.
"""


def get_backend(name: str, dry_run: bool = False):
    if name == "local":
        from agent4sci.backends.local import LocalDockerBackend
        return LocalDockerBackend(dry_run=dry_run)
    raise SystemExit(f"unknown backend '{name}'. supported: local")
