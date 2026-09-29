#!/usr/bin/env python3
"""Stop hook: prevent Codex from ending its turn during hill-climb.

Blocks every turn-end attempt with a continuation prompt telling Codex
to keep working and use sleep() to stay active. Allows the turn to end
when the orchestrator signals wrapup via a sentinel file.
"""
import json
import os
import sys

WRAPUP_SIGNAL = "/tmp/a4s_wrapup_signal"

payload = json.load(sys.stdin)

# Allow turn to end if wrapup has been signaled by the orchestrator
if os.path.exists(WRAPUP_SIGNAL):
    print(json.dumps({}))
else:
    print(json.dumps({
        "decision": "block",
        "reason": (
            "You must continue to run experiments until the full time limit has elapsed. "
            "Use sleep() or other tool calls to keep your session active. "
            "If you are waiting for training jobs to finish, use `sleep()` calls up to `sleep(1800)` and then "
            "check on your experiments with `nvidia-smi` and `ps`. "
            "Do NOT stop working."
        ),
    }))
