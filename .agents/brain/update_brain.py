#!/usr/bin/env python3
"""GoalOS Autonomous Brain CLI Utility.

Allows agents and developers to programmatically query, update, and append
learnings, evolution logs, and architectural decision records to the GoalOS Brain.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BRAIN_DIR.parent.parent

LEARNINGS_FILE = BRAIN_DIR / "project_learnings.md"
EVOLUTION_FILE = BRAIN_DIR / "evolution_log.md"
ADR_FILE = BRAIN_DIR / "architectural_decisions.md"
PATTERNS_FILE = BRAIN_DIR / "system_patterns.md"
TROUBLESHOOTING_FILE = BRAIN_DIR / "troubleshooting_kb.md"


def append_learning(domain: str, summary: str, details: str) -> None:
  """Append a structured learning entry to project_learnings.md."""
  if not LEARNINGS_FILE.exists():
    print(f"Error: {LEARNINGS_FILE} not found.", file=sys.stderr)
    return

  entry = f"\n### {summary}\n- **Domain:** `{domain}`\n- **Date:** {datetime.date.today().isoformat()}\n- **Insight:** {details}\n"
  with open(LEARNINGS_FILE, "a", encoding="utf-8") as f:
    f.write(entry)
  print(f"✅ Successfully appended learning: '{summary}' to {LEARNINGS_FILE.name}")


def log_evolution(action: str, rationale: str = "", reflection: str = "") -> None:
  """Append a structured evolution/prompt reflection to evolution_log.md."""
  if not EVOLUTION_FILE.exists():
    print(f"Error: {EVOLUTION_FILE} not found.", file=sys.stderr)
    return

  today = datetime.date.today().isoformat()
  entry = f"\n---\n\n## {today} — {action}\n\n- **Action:** {action}\n"
  if rationale:
    entry += f"- **Rationale:** {rationale}\n"
  if reflection:
    entry += f"- **Agent Reflection & Learning:** {reflection}\n"

  # Read existing content and insert near the top (after header)
  content = EVOLUTION_FILE.read_text(encoding="utf-8")
  marker = "---\n\n"
  first_marker = content.find(marker)

  if first_marker != -1:
    idx = first_marker + len(marker)
    updated = content[:idx] + entry.lstrip("\n---\n\n") + "\n" + content[idx:]
  else:
    updated = content + entry

  EVOLUTION_FILE.write_text(updated, encoding="utf-8")
  print(f"✅ Successfully recorded evolution log for: '{action}'")


def search_brain(query: str) -> None:
  """Search all markdown files in the brain for a given query."""
  query_lower = query.lower()
  matches_found = 0
  print(f"🔍 Searching GoalOS Brain for '{query}'...\n")

  for md_file in BRAIN_DIR.glob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
      if query_lower in line.lower():
        print(f"  [{md_file.name}:{idx}] {line.strip()}")
        matches_found += 1

  if matches_found == 0:
    print("  No matches found in GoalOS Brain.")
  else:
    print(f"\nFound {matches_found} matching line(s).")


def main() -> None:
  parser = argparse.ArgumentParser(description="GoalOS Autonomous Brain Manager")
  parser.add_argument("--add-learning", action="store_true", help="Add a new project learning")
  parser.add_argument("--domain", type=str, default="general", help="Domain for the learning")
  parser.add_argument("--summary", type=str, help="Short title/summary of the learning")
  parser.add_argument("--details", type=str, help="Detailed explanation of the insight/learning")

  parser.add_argument("--log-evolution", action="store_true", help="Log a prompt reflection or evolution step")
  parser.add_argument("--action", type=str, help="Action taken during the session")
  parser.add_argument("--rationale", type=str, default="", help="Rationale for changes")
  parser.add_argument("--reflection", type=str, default="", help="Agent reflection & self-improvement takeaway")

  parser.add_argument("--query", type=str, help="Search the GoalOS brain knowledge base")

  args = parser.parse_args()

  if args.add_learning:
    if not args.summary or not args.details:
      print("Error: --summary and --details are required for --add-learning.", file=sys.stderr)
      sys.exit(1)
    append_learning(args.domain, args.summary, args.details)

  elif args.log_evolution:
    if not args.action:
      print("Error: --action is required for --log-evolution.", file=sys.stderr)
      sys.exit(1)
    log_evolution(args.action, args.rationale, args.reflection)

  elif args.query:
    search_brain(args.query)

  else:
    parser.print_help()


if __name__ == "__main__":
  main()
