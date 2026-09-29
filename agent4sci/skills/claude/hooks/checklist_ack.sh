#!/bin/bash
# PostToolUse hook for Skill tool — clears the checklist reminder lock
# Only fires when matcher is "Skill" (configured in settings.json)

LOCK_FILE="/tmp/claude_reminder_lock"
DEBUG_LOG="/tmp/claude_reminder_debug.log"

# Read hook input
INPUT=$(cat)

# Check if this was the checklist skill specifically
SKILL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('skill',''))" 2>/dev/null)

if [ "$SKILL_NAME" = "checklist" ] && [ -f "$LOCK_FILE" ]; then
  LOCK_TIME=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  DUR=$((NOW - LOCK_TIME))
  if [ $DUR -lt 60 ]; then
    FMT="${DUR}s"
  elif [ $DUR -lt 3600 ]; then
    FMT="$((DUR / 60))m$((DUR % 60))s"
  else
    FMT="$((DUR / 3600))h$(( (DUR % 3600) / 60 ))m"
  fi
  rm -f "$LOCK_FILE"
  echo "$(date '+%Y-%m-%d %H:%M:%S') | CHECKLIST_COMPLETED | lock_duration=${FMT} | /checklist skill finished, lock cleared. Normal tool use resumed." >> "$DEBUG_LOG"
fi

exit 0
