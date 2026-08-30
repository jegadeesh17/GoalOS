"""Unit tests for the GoalOS AI Evaluation Framework & Vision Metrics."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from ai.eval.evaluator import GoalOSEvaluator
from ai.eval.metrics import (
  ActionabilityDirectnessMetric,
  GroundingAntiHallucinationMetric,
  HorizonAlignmentMetric,
  OperationalEfficiencyMetric,
  SchemaIntegrityMetric,
  ToolCallingPrecisionMetric,
)
from ai.eval.rate_limiter import RateLimiter


def test_schema_integrity_metric():
  metric = SchemaIntegrityMetric()
  valid_response = {
    "mentor_rule": "Block 9-11 AM for deep work",
    "why_this_rule": "Context switching destroys momentum",
    "past_mistake_called_out": "Checking Slack early",
    "goal_connection": "Ship V2.2",
    "if_you_ignore_this": "Sprint delayed",
    "confidence": 0.9,
  }
  expected = ["mentor_rule", "why_this_rule", "past_mistake_called_out", "goal_connection", "if_you_ignore_this", "confidence"]
  score = metric.evaluate(valid_response, expected)
  assert score.passed is True
  assert score.score == 1.0

  # Missing key
  score_missing = metric.evaluate({"mentor_rule": "Only rule"}, expected)
  assert score_missing.passed is False
  assert score_missing.score < 0.5


def test_grounding_metric():
  metric = GroundingAntiHallucinationMetric()
  response_text = "Focus on the SQLite Distributed Cache engine and protect your 6.5h sleep routine from Slack distractions."
  context_entities = ["Distributed Cache", "Slack", "6.5h sleep"]

  score = metric.evaluate(response_text, context_entities, prompt_context="User context")
  assert score.passed is True
  assert score.score >= 0.80

  # Hallucinated / unrelated response
  score_bad = metric.evaluate("As an AI language model, I don't have access to your personal Zoom calendar event.", context_entities, prompt_context="")
  assert score_bad.passed is False
  assert score_bad.score == 0.0


def test_actionability_metric():
  metric = ActionabilityDirectnessMetric()
  actionable = "Execute 2 uninterrupted hours on cache architecture before 11:00 AM."
  score = metric.evaluate(actionable)
  assert score.passed is True
  assert score.score >= 0.80

  vague = "Try your best to stay positive and be happy today."
  score_vague = metric.evaluate(vague)
  assert score_vague.passed is False
  assert score_vague.score < 0.50


def test_horizon_alignment_metric():
  metric = HorizonAlignmentMetric()
  response = {
    "mentor_rule": "Refactor migrations",
    "goal_connection": "Directly impacts 1-Year Goal: Master Distributed Systems Architecture",
  }
  score = metric.evaluate(response, ["Master Distributed Systems Architecture", "Ship V2.2"])
  assert score.passed is True
  assert score.score >= 0.70


def test_tool_calling_metric():
  metric = ToolCallingPrecisionMetric()
  tools_used = [{"name": "search_memories", "arguments": {"query": "cache"}}, {"name": "get_active_goals", "arguments": {}}]
  score = metric.evaluate(tools_used, ["search_memories", "get_active_goals"])
  assert score.passed is True
  assert score.score == 1.0


def test_operational_efficiency_metric():
  metric = OperationalEfficiencyMetric()
  score_fast = metric.evaluate(latency_seconds=1.2, response_length_chars=450)
  assert score_fast.passed is True
  assert score_fast.score >= 0.90

  score_slow = metric.evaluate(latency_seconds=9.5, response_length_chars=5000)
  assert score_slow.passed is False
  assert score_slow.score < 0.60


def test_rate_limiter_throttling():
  limiter = RateLimiter(requests_per_minute=60.0)  # 1.0s interval
  counter = 0

  def dummy_op():
    nonlocal counter
    counter += 1
    return {"status": "ok"}

  res, lat = limiter.execute_with_retry(dummy_op, operation_name="DummyTest")
  assert res["status"] == "ok"
  assert counter == 1


def test_evaluator_composite_and_aggregation():
  evaluator = GoalOSEvaluator()
  scenario = {
    "id": "TEST-01",
    "pipeline": "morning_coach",
    "expected_keys": ["mentor_rule", "why_this_rule"],
    "context_entities": ["ChromaDB", "deep work"],
    "active_goals": ["ChromaDB Local Vector Search"],
    "expected_tools": [],
  }
  mock_response = {
    "mentor_rule": "Execute 3 hours on ChromaDB deep work before noon.",
    "why_this_rule": "Critical for vector search milestone.",
    "goal_connection": "ChromaDB Local Vector Search",
  }
  result = evaluator.evaluate_response(scenario, mock_response, latency_seconds=1.5, model_name="test-model")
  assert result.success is True
  assert result.composite_score >= 80.0

  report = evaluator.aggregate_report("test-model", [result])
  assert report.total_scenarios == 1
  assert report.successful_scenarios == 1
  assert report.average_composite_score >= 80.0


def test_load_benchmark_scenarios():
  from scripts.run_model_eval import load_benchmark_scenarios
  scenarios = load_benchmark_scenarios()
  assert len(scenarios) == 15
  assert any(s["pipeline"] == "morning_coach" for s in scenarios)
  assert any(s["pipeline"] == "agent_morning_coach" for s in scenarios)
