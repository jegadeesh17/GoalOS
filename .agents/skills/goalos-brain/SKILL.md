---
name: goalos-brain
description: >-
  Manage, query, and update the GoalOS Project Brain. Use this skill whenever
  learning new repository insights, updating architectural decisions, recording
  prompt reflections, or querying project memory.
---

# GoalOS Brain Management Skill

Use this skill to interact with the persistent GoalOS Brain located in `.agents/brain/`.

## Procedures

### 1. Querying Knowledge
To search the brain knowledge base for a specific concept or past issue:
```bash
python .agents/brain/update_brain.py --query "<search-term>"
```

### 2. Appending a Project Learning
When a new bug fix, library nuance, or performance insight is discovered:
```bash
python .agents/brain/update_brain.py --add-learning --domain "<domain>" --summary "<Short Summary>" --details "<Detailed Insight>"
```

### 3. Logging Prompt Reflections & Evolution
At the end of a non-trivial prompt or refactor:
```bash
python .agents/brain/update_brain.py --log-evolution --action "<Action Taken>" --rationale "<Why>" --reflection "<Self-improvement insight>"
```

## Key Files
- [Brain Index](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/README.md)
- [System Patterns](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/system_patterns.md)
- [Project Learnings](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/project_learnings.md)
- [ADRs](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/architectural_decisions.md)
- [Troubleshooting KB](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/troubleshooting_kb.md)
- [Evolution Log](file:///C:/Users/jegad/projects/GoalOS/.agents/brain/evolution_log.md)
