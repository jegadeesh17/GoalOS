#!/usr/bin/env bash
# Enforces AGENTS.md section 4 "end-of-turn clean-tree check":
# block Stop if this session introduced uncommitted changes.
input=$(cat)
sid=$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$sid" ] && sid="default"
mkdir -p .claude/.hookstate 2>/dev/null
base=".claude/.hookstate/baseline-${sid}.txt"
[ -f "$base" ] || : > "$base"
cur=$(git status --short 2>/dev/null)
new=$(comm -13 <(sort "$base") <(printf '%s\n' "$cur" | sort) 2>/dev/null | sed '/^$/d')
if [ -n "$new" ]; then
  printf '{"decision":"block","reason":"Uncommitted changes from this session were detected (run git status --short to see them). Per AGENTS.md section 4 and .agents/rules/git_discipline.md: stage your changes by filename (never git add -A or git add .) and commit them as a Conventional Commit before finishing this turn. If any are pre-existing changes you did not make this session, note that explicitly instead of committing them."}'
else
  echo '{}'
fi
