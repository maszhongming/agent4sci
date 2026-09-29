#!/bin/bash
# Hourly checklist reminder hook (PreToolUse)
#
# Design:
#   - When timer elapses: exit 0 + additionalContext (model sees reminder), set lock
#   - When lock active + tool is NOT Skill: exit 2 (hard-block)
#   - When lock active + tool IS Skill: exit 0 (allow checklist to run)
#   - Lock is cleared by a separate PostToolUse hook on Skill completion
#
# Debug metrics logged to /tmp/claude_reminder_debug.log

INTERVAL=3600
TIMESTAMP_FILE="/tmp/claude_reminder_ts"
DEBUG_LOG="/tmp/claude_reminder_debug.log"
LOCK_FILE="/tmp/claude_reminder_lock"
MODE="${MODE:-}"

log_debug() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" >> "$DEBUG_LOG"
}

fmt_duration() {
  local secs=$1
  if [ $secs -lt 60 ]; then
    echo "${secs}s"
  elif [ $secs -lt 3600 ]; then
    echo "$((secs / 60))m$((secs % 60))s"
  else
    echo "$((secs / 3600))h$(( (secs % 3600) / 60 ))m"
  fi
}

# Skip in evaluation mode
if [ "$MODE" = "evaluate" ]; then
  exit 0
fi

# Read hook input from stdin
INPUT=$(cat)

# Skip subagents
if echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('agent_id') else 1)" 2>/dev/null; then
  exit 0
fi

# Extract tool_name and tool_input summary
TOOL_INFO=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
name = d.get('tool_name', 'unknown')
inp = d.get('tool_input', {})
# Summarize input based on tool type
if name == 'Bash':
    detail = inp.get('description', inp.get('command', ''))[:80]
elif name == 'Skill':
    detail = inp.get('skill', '')
elif name in ('Read', 'Edit', 'Write'):
    detail = inp.get('file_path', '')
elif name == 'Agent':
    detail = inp.get('description', '')[:80]
elif name in ('Glob', 'Grep'):
    detail = inp.get('pattern', '')
else:
    detail = str(inp)[:80]
print(f'{name}({detail})')
" 2>/dev/null || echo "unknown")

TOOL_NAME=$(echo "$TOOL_INFO" | cut -d'(' -f1)

NOW=$(date +%s)

# If timestamp file doesn't exist, initialize it to now and exit.
# This prevents the first tool call in a new session from triggering
# the reminder (since LAST would default to 0, making SINCE_LAST huge).
if [ ! -f "$TIMESTAMP_FILE" ]; then
  echo "$NOW" > "$TIMESTAMP_FILE"
  log_debug "TIMER_INITIALIZED | tool=${TOOL_INFO} | First run: timestamp file created, timer starts now"
  exit 0
fi

LAST=$(cat "$TIMESTAMP_FILE" 2>/dev/null || echo 0)
SINCE_LAST=$((NOW - LAST))

# If lock is active...
if [ -f "$LOCK_FILE" ]; then
  LOCK_TIME=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
  LOCK_AGE=$((NOW - LOCK_TIME))

  # Auto-clear stale locks after 10 min
  if [ $LOCK_AGE -gt 600 ]; then
    rm -f "$LOCK_FILE"
    log_debug "STALE_LOCK_CLEARED | lock_age=$(fmt_duration $LOCK_AGE) | tool=${TOOL_INFO} | Lock exceeded 10min timeout, auto-clearing to prevent deadlock"
    exit 0
  fi

  # Allow Skill tool through (so /checklist can run)
  if [ "$TOOL_NAME" = "Skill" ]; then
    log_debug "SKILL_ALLOWED | lock_age=$(fmt_duration $LOCK_AGE) | tool=${TOOL_INFO} | Skill tool exempted from block so /checklist can execute"
    exit 0
  fi

  # Hard-block everything else
  log_debug "TOOL_BLOCKED | lock_age=$(fmt_duration $LOCK_AGE) | tool=${TOOL_INFO} | Agent attempted tool use while checklist lock is active"
  echo "BLOCKED: Hourly checklist reminder is active. You MUST run /checklist before using any other tools." >&2
  exit 2
fi

# No lock — check if timer has elapsed
if [ $SINCE_LAST -lt $INTERVAL ]; then
  exit 0
fi

# Timer elapsed — fire Phase 1: set lock, inject context, allow this one tool call through
echo "$NOW" > "$LOCK_FILE"
echo "$NOW" > "$TIMESTAMP_FILE"

log_debug "REMINDER_FIRED | elapsed_since_last=$(fmt_duration $SINCE_LAST) | tool=${TOOL_INFO} | Phase 1: context injected into model, lock set. Next non-Skill tool call will be hard-blocked."

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "**MANDATORY HOURLY CHECK** — STOP what you are doing.\n\n1. Run /checklist RIGHT NOW and work through it fully.\n2. Answer every question out loud, ONE BY ONE\n3. All further tool calls will be BLOCKED until you complete the checklist."
  }
}
EOF
exit 0
