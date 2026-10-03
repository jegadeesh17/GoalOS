#!/usr/bin/env bash
# Captures the git status baseline at session start so the Stop hook
# can tell "changes made this session" apart from pre-existing ones.
mkdir -p .claude/.hookstate 2>/dev/null
input=$(cat)
sid=$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$sid" ] && sid="default"
git status --short > ".claude/.hookstate/baseline-${sid}.txt" 2>/dev/null
echo '{}'
