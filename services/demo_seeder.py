"""Automated sanitized demo environment seeder for GoalOS (zero PII).

Seeds realistic, production-grade engineering demo data on startup when the database
is unpopulated. Ensures all UI panels (Life Calendar, Journal, Goals, Analytics,
APM Telemetry, and Memories) display rich, compelling data without any personal
identifiers (PII).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.memory_repository import MemoryRepository
from database.repositories.score_repository import ScoreRepository
from models.goal import GoalCreate
from models.memory import MemoryCreate
from services.observability_service import ObservabilityService

logger = logging.getLogger(__name__)


def seed_demo_goals() -> int:
  """Seed sanitized, professional engineering goals across 1-month, 1-year, and 5-year horizons."""
  goal_repo = GoalRepository()
  if goal_repo.get_all():
    return 0

  today = date.today()
  demo_goals = [
    GoalCreate(
      title="Master Multi-Agent Systems & Tool-Calling Architectures",
      description="Design, benchmark, and deploy production-grade multi-agent coordinator pipelines.",
      category="career",
      horizon="1-year",
      priority=1,
      progress=0.65,
      status="active",
      deadline=today + timedelta(days=240),
      reason="Build resilient agent architectures with verifiable reliability and minimal hallucination.",
      success_criteria="Achieve <1% tool call schema failure rate across comprehensive evaluation harness.",
    ),
    GoalCreate(
      title="Sustained Peak Energy & Aerobic Conditioning",
      description="Maintain high cardiovascular stamina and consistent morning circadian discipline.",
      category="health",
      horizon="1-month",
      priority=2,
      progress=0.80,
      status="active",
      deadline=today + timedelta(days=30),
      reason="High physical stamina directly drives sustained afternoon deep work capacity.",
      success_criteria="Log 20km+ weekly running volume and maintain 7.5+ hours sleep consistency.",
    ),
    GoalCreate(
      title="GoalOS — Open-Source Life Operating System",
      description="Develop a local-first, privacy-respecting executive life operating system for engineers.",
      category="projects",
      horizon="1-year",
      priority=1,
      progress=0.85,
      status="active",
      deadline=today + timedelta(days=120),
      reason="Create an integrated system for Memento Mori pacing, daily journaling, and cognitive retrieval.",
      success_criteria="Deploy React 18 + FastAPI container to Cloud Run with full test suite passing.",
    ),
    GoalCreate(
      title="Lead Scalable AI Infrastructure & Platform Design",
      description="Direct system architecture for high-throughput distributed machine learning workflows.",
      category="vision",
      horizon="5-year",
      priority=3,
      progress=0.30,
      status="active",
      deadline=today + timedelta(days=1825),
      reason="Architect resilient infrastructure that scales gracefully under exponential compute demand.",
      success_criteria="Design distributed serving pipelines with 99.99% availability and sub-100ms p95 latency.",
    ),
  ]

  for g in demo_goals:
    goal_repo.create(g)

  logger.info("Seeded %d demo goals", len(demo_goals))
  return len(demo_goals)


def seed_demo_memories() -> int:
  """Seed sanitized engineering lessons and cognitive principles."""
  memory_repo = MemoryRepository()
  if memory_repo.get_all():
    return 0

  today = date.today()
  demo_memories = [
    MemoryCreate(
      text="Tackle the highest-leverage architectural bottleneck in the first morning focus block before communication tools.",
      type="insight",
      importance=0.95,
      source_date=today - timedelta(days=12),
      source_type="journal",
    ),
    MemoryCreate(
      text="Combining dense embeddings with BM25 keyword matching (Reciprocal Rank Fusion) delivers 70%+ hit rate on domain queries.",
      type="technical",
      importance=0.90,
      source_date=today - timedelta(days=8),
      source_type="journal",
    ),
    MemoryCreate(
      text="Strict JSON schema validation via Pydantic v2 eliminates hallucinated tool arguments in autonomous agent coordinator loops.",
      type="technical",
      importance=0.85,
      source_date=today - timedelta(days=6),
      source_type="journal",
    ),
    MemoryCreate(
      text="Consistent aerobic tempo running (5km) directly increases afternoon cognitive stamina and reduces context-switching fatigue.",
      type="habit",
      importance=0.80,
      source_date=today - timedelta(days=4),
      source_type="journal",
    ),
    MemoryCreate(
      text="Minimal multi-stage Docker builds reduce container image footprints by over 80% and accelerate cold starts on GCP Cloud Run.",
      type="technical",
      importance=0.85,
      source_date=today - timedelta(days=2),
      source_type="journal",
    ),
    MemoryCreate(
      text="Automate test fixtures early so regressions, migration bugs, and schema mismatches are caught prior to staging deployment.",
      type="insight",
      importance=0.80,
      source_date=today - timedelta(days=1),
      source_type="journal",
    ),
  ]

  for m in demo_memories:
    memory_repo.create(m)

  logger.info("Seeded %d demo memories", len(demo_memories))
  return len(demo_memories)


def seed_demo_telemetry() -> int:
  """Seed sanitized AI execution spans to populate the AI Observability & APM dashboard."""
  obs = ObservabilityService()
  summary = obs.get_summary(days=30)
  if summary.total_calls > 0:
    return 0

  now = datetime.now(timezone.utc)
  spans = [
    ("coach_morning_brief", "google/gemini-2.5-flash", 820, 240, 720.0, timedelta(hours=2)),
    ("agent_coordinator_chat", "deepseek/deepseek-chat", 1240, 380, 610.0, timedelta(hours=5)),
    ("tool_call_extract_tasks", "meta-llama/llama-3.3-70b-instruct", 650, 110, 430.0, timedelta(hours=8)),
    ("hybrid_memory_rerank", "google/gemini-2.5-flash", 940, 180, 520.0, timedelta(hours=14)),
    ("coach_evening_review", "anthropic/claude-3.5-sonnet", 1450, 420, 1120.0, timedelta(days=1, hours=3)),
    ("eval_retrieval_benchmark", "deepseek/deepseek-chat", 1850, 510, 890.0, timedelta(days=1, hours=10)),
    ("coach_future_self", "google/gemini-2.5-flash", 1120, 310, 760.0, timedelta(days=2, hours=4)),
    ("coach_weekly_digest", "anthropic/claude-3.5-sonnet", 2150, 640, 1380.0, timedelta(days=3, hours=1)),
    ("agent_coordinator_chat", "deepseek/deepseek-chat", 1310, 390, 640.0, timedelta(days=4, hours=2)),
    ("coach_morning_brief", "google/gemini-2.5-flash", 810, 230, 690.0, timedelta(days=5, hours=6)),
  ]

  count = 0
  with get_db() as conn:
    for span_name, model, p_tokens, c_tokens, lat, offset in spans:
      span_time = (now - offset).strftime("%Y-%m-%d %H:%M:%S")
      cost = obs.calculate_cost(model, p_tokens, c_tokens)
      total = p_tokens + c_tokens
      conn.execute(
        """
        INSERT INTO ai_telemetry (
          trace_id, span_name, model,
          prompt_tokens, completion_tokens, total_tokens,
          estimated_cost_usd, latency_ms, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'success', ?)
        """,
        (f"tr_{count+1:04d}", span_name, model, p_tokens, c_tokens, total, cost, lat, span_time),
      )
      count += 1

  logger.info("Seeded %d demo telemetry spans", count)
  return count


def seed_demo_user_profile() -> None:
  """Ensure the demo user profile has generic, non-PII executive visions and demo persona."""
  with get_db() as conn:
    conn.execute("""
      UPDATE user SET
        name = 'Alex Chen',
        birth_date = '2000-01-15',
        target_age = 75,
        one_year_vision = 'Lead AI systems engineering and ship high-impact agentic architectures.',
        five_year_vision = 'Architect robust AI infrastructure and build impactful open-source developer tools.',
        life_vision = 'Master technical craft, build enduring systems, and empower engineering leverage.'
      WHERE id = 1
    """)


def seed_demo_environment() -> dict[str, int]:
  """Orchestrate end-to-end sanitized demo seeding."""
  results = {
    "journal_imported": 0,
    "goals_seeded": 0,
    "memories_seeded": 0,
    "telemetry_seeded": 0,
    "analytics_backfilled": 0,
  }

  # 1. Import sanitized journal entries if empty (explicitly demo_seed.csv with ZERO PII)
  from config.settings import settings
  log_repo = LogRepository()
  demo_csv = Path(__file__).resolve().parent.parent / "data" / "demo_seed.csv"
  if log_repo.count() == 0:
    from scripts.import_journal_csv import run_import
    results["journal_imported"] = run_import(csv_path=str(demo_csv), db_path=settings.DB_PATH)

  # 2. Seed generic executive goals
  results["goals_seeded"] = seed_demo_goals()

  # 3. Backfill metrics (deep work, sleep, mood, and daily growth scores)
  score_repo = ScoreRepository()
  all_logs = log_repo.get_all()
  needs_backfill = (score_repo.count() == 0) or (bool(all_logs) and (all_logs[0].deep_work_hours is None or all_logs[0].deep_work_hours == 0))
  if needs_backfill and len(all_logs) > 0:
    from scripts.backfill_analytics import run_backfill
    backfill_res = run_backfill(db_path=settings.DB_PATH)
    results["analytics_backfilled"] = backfill_res.get("scores_generated", 0)

  # 4. Seed sanitized memories
  results["memories_seeded"] = seed_demo_memories()

  # 5. Seed sanitized APM telemetry spans
  results["telemetry_seeded"] = seed_demo_telemetry()

  # 6. Profile visions
  seed_demo_user_profile()

  logger.info("Demo environment seeding complete: %s", results)
  return results


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  print(seed_demo_environment())
