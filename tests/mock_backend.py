"""A Backend that records the stages it is asked to run, for testing the
pipeline's orchestration without a container runtime."""
from agent4sci.backends.base import Backend


class MockBackend(Backend):
    name = "mock"

    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run=dry_run)
        self.stages = []

    def run_stage(self, stage):
        self.stages.append(stage)
