"""Multi-factor evaluation engine for GoalOS AI models."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from ai.eval.metrics import (
  ActionabilityDirectnessMetric,
  GroundingAntiHallucinationMetric,
  HorizonAlignmentMetric,
  MetricScore,
  OperationalEfficiencyMetric,
  SchemaIntegrityMetric,
  ToolCallingPrecisionMetric,
)

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
  scenario_id: str
  pipeline: str
  model: str
  composite_score: float  # 0 to 100
  latency_seconds: float
  success: bool
  metric_scores: dict[str, MetricScore]
  raw_response: Any
  error: Optional[str] = None


@dataclass
class ModelEvaluationReport:
  model: str
  total_scenarios: int
  successful_scenarios: int
  average_composite_score: float
  p50_latency: float
  p95_latency: float
  metric_breakdowns: dict[str, float]  # Metric Name -> average score
  scenario_results: list[ScenarioResult]


class GoalOSEvaluator:
  """Production evaluator executing benchmark scenarios and scoring with GoalOS Vision Metrics."""

  def __init__(self):
    self.schema_metric = SchemaIntegrityMetric()
    self.grounding_metric = GroundingAntiHallucinationMetric()
    self.actionability_metric = ActionabilityDirectnessMetric()
    self.horizon_metric = HorizonAlignmentMetric()
    self.tool_metric = ToolCallingPrecisionMetric()
    self.efficiency_metric = OperationalEfficiencyMetric()

  def evaluate_response(
    self,
    scenario: dict[str, Any],
    response: Any,
    latency_seconds: float,
    model_name: str,
  ) -> ScenarioResult:
    """Evaluate a single scenario execution against all 6 Vision Metrics."""
    expected_keys = scenario.get("expected_keys", ["mentor_rule", "why_this_rule"])
    context_entities = scenario.get("context_entities", [])
    prompt_context = scenario.get("prompt_context", "")
    active_goals = scenario.get("active_goals", [])
    expected_tools = scenario.get("expected_tools", [])

    # Extract response text & tools used
    response_text = ""
    rule_text = ""
    tools_used = []

    if isinstance(response, dict):
      response_text = " ".join(str(v) for v in response.values())
      rule_text = (
        response.get("mentor_rule")
        or response.get("takeaway")
        or response.get("strategic_directive")
        or response.get("future_projection")
        or response.get("coaching")
        or ""
      )
      tools_used = response.get("tools_used") or response.get("tool_calls_made") or []
    elif isinstance(response, str):
      response_text = response
      rule_text = response

    # 1. Schema & JSON Integrity (20%)
    sji_score = self.schema_metric.evaluate(response, expected_keys)

    # 2. Grounding & Anti-Hallucination (25%)
    gah_score = self.grounding_metric.evaluate(response_text, context_entities, prompt_context)

    # 3. Actionability & Directness (20%)
    act_score = self.actionability_metric.evaluate(rule_text)

    # 4. Horizon & Strategic Alignment (15%)
    hal_score = self.horizon_metric.evaluate(response if isinstance(response, dict) else {}, active_goals)

    # 5. Tool-Calling Precision (10%)
    tcp_score = self.tool_metric.evaluate(tools_used, expected_tools)

    # 6. Operational Efficiency (10%)
    oe_score = self.efficiency_metric.evaluate(latency_seconds, len(response_text))

    metric_scores = {
      "Schema Integrity": sji_score,
      "Grounding & Accuracy": gah_score,
      "Actionability": act_score,
      "Horizon Alignment": hal_score,
      "Tool Calling": tcp_score,
      "Operational Efficiency": oe_score,
    }

    # Calculate Weighted Composite Score (0 to 100)
    composite = sum(m.score * m.weight for m in metric_scores.values()) * 100.0
    composite = round(max(0.0, min(100.0, composite)), 2)

    has_error = bool(isinstance(response, dict) and response.get("error"))
    success = not has_error and sji_score.passed and gah_score.score >= 0.40

    return ScenarioResult(
      scenario_id=scenario.get("id", "unknown"),
      pipeline=scenario.get("pipeline", "general"),
      model=model_name,
      composite_score=composite,
      latency_seconds=round(latency_seconds, 2),
      success=success,
      metric_scores=metric_scores,
      raw_response=response,
      error=response.get("error") if isinstance(response, dict) else None,
    )

  def aggregate_report(self, model_name: str, results: list[ScenarioResult]) -> ModelEvaluationReport:
    """Aggregate individual scenario results into a comprehensive model evaluation report."""
    if not results:
      return ModelEvaluationReport(
        model=model_name,
        total_scenarios=0,
        successful_scenarios=0,
        average_composite_score=0.0,
        p50_latency=0.0,
        p95_latency=0.0,
        metric_breakdowns={},
        scenario_results=[],
      )

    total = len(results)
    successful = sum(1 for r in results if r.success)
    avg_score = round(sum(r.composite_score for r in results) / total, 2)

    latencies = sorted(r.latency_seconds for r in results)
    p50_lat = latencies[int(total * 0.50)]
    p95_lat = latencies[min(total - 1, int(total * 0.95))]

    metric_names = results[0].metric_scores.keys()
    breakdowns = {}
    for name in metric_names:
      avg_metric = sum(r.metric_scores[name].score for r in results) / total
      breakdowns[name] = round(avg_metric * 100.0, 1)

    return ModelEvaluationReport(
      model=model_name,
      total_scenarios=total,
      successful_scenarios=successful,
      average_composite_score=avg_score,
      p50_latency=round(p50_lat, 2),
      p95_latency=round(p95_lat, 2),
      metric_breakdowns=breakdowns,
      scenario_results=results,
    )
