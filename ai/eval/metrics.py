"""GoalOS Vision Metrics for Production AI Evaluation."""

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MetricScore:
  name: str
  score: float  # Normalized 0.0 to 1.0
  weight: float
  passed: bool
  feedback: str
  details: dict[str, Any]


class SchemaIntegrityMetric:
  """Evaluates structured JSON conformance and required keys."""

  def __init__(self, weight: float = 0.20):
    self.name = "Schema & JSON Integrity"
    self.weight = weight

  def evaluate(self, response: Any, expected_keys: list[str]) -> MetricScore:
    if not isinstance(response, dict):
      return MetricScore(
        name=self.name,
        score=0.0,
        weight=self.weight,
        passed=False,
        feedback="Response is not a valid JSON dictionary.",
        details={"type": str(type(response)), "raw": str(response)[:100]},
      )

    if response.get("error"):
      return MetricScore(
        name=self.name,
        score=0.0,
        weight=self.weight,
        passed=False,
        feedback=f"Response contains API or parsing error: {response.get('error')}",
        details=response,
      )

    present_keys = [k for k in expected_keys if k in response and response[k]]
    missing_keys = [k for k in expected_keys if k not in response or not response[k]]
    key_ratio = len(present_keys) / max(1, len(expected_keys))

    passed = len(missing_keys) == 0 and key_ratio >= 1.0
    feedback = "All required schema keys present." if passed else f"Missing keys: {missing_keys}"

    return MetricScore(
      name=self.name,
      score=round(key_ratio, 2),
      weight=self.weight,
      passed=passed,
      feedback=feedback,
      details={"present": present_keys, "missing": missing_keys},
    )


class GroundingAntiHallucinationMetric:
  """Evaluates whether the advice is grounded in the provided prompt context and penalizes ungrounded claims."""

  def __init__(self, weight: float = 0.25):
    self.name = "Grounding & Anti-Hallucination"
    self.weight = weight

  def evaluate(self, response_text: str, context_entities: list[str], prompt_context: str) -> MetricScore:
    if not response_text or not isinstance(response_text, str):
      return MetricScore(
        name=self.name,
        score=0.0,
        weight=self.weight,
        passed=False,
        feedback="Empty response text.",
        details={},
      )

    text_lower = response_text.lower()
    matched_entities = []
    for entity in context_entities:
      entity_words = [w.lower() for w in re.findall(r"\b\w{3,}\b", entity)]
      if any(w in text_lower for w in entity_words):
        matched_entities.append(entity)

    # Check entity overlap ratio
    entity_score = len(matched_entities) / max(1, min(len(context_entities), 4))
    entity_score = min(1.0, entity_score)

    # Check for generic hallucination red flags
    hallucination_penalties = 0.0
    red_flags = ["as an ai language model", "i don't have access to your personal", "you mentioned in your email", "according to your calendar event on zoom"]
    for flag in red_flags:
      if flag in text_lower:
        hallucination_penalties += 0.25

    final_score = max(0.0, round(entity_score - hallucination_penalties, 2))
    passed = final_score >= 0.60

    return MetricScore(
      name=self.name,
      score=final_score,
      weight=self.weight,
      passed=passed,
      feedback=f"Grounded on {len(matched_entities)}/{len(context_entities)} key context entities.",
      details={"matched_entities": matched_entities, "penalties": hallucination_penalties},
    )


class ActionabilityDirectnessMetric:
  """Evaluates whether advice provides clear, actionable, non-negotiable directives vs vague platitudes."""

  def __init__(self, weight: float = 0.20):
    self.name = "Actionability & Directness"
    self.weight = weight

  def evaluate(self, rule_text: str) -> MetricScore:
    if not rule_text or not isinstance(rule_text, str):
      return MetricScore(name=self.name, score=0.0, weight=self.weight, passed=False, feedback="Missing rule text.", details={})

    text_lower = rule_text.lower()

    # Vague platitude markers (penalized)
    platitudes = ["try your best", "stay positive", "remember to breathe", "balance is key", "be happy", "it is important to work hard"]
    platitude_count = sum(1 for p in platitudes if p in text_lower)

    # Actionable directive markers (rewarded)
    imperative_verbs = ["block", "execute", "build", "write", "eliminate", "complete", "stop", "ship", "refactor", "focus on", "commit", "review", "log", "prioritize"]
    has_imperative = any(re.search(rf"\b{v}\b", text_lower) for v in imperative_verbs)

    # Time or quantitative boundary markers (rewarded)
    has_boundary = bool(re.search(r"(\d+\s*(hours?|hrs?|mins?|minutes?|am|pm|blocks?)|before|after|first thing|by noon)", text_lower))

    # Sentence conciseness (ideal mentor rule is 10 to 35 words)
    words = text_lower.split()
    word_count = len(words)
    conciseness_score = 1.0 if 8 <= word_count <= 45 else 0.6

    score = 0.4 * (1.0 if has_imperative else 0.0) + 0.35 * (1.0 if has_boundary else 0.2) + 0.25 * conciseness_score - (0.3 * platitude_count)
    score = max(0.0, min(1.0, round(score, 2)))
    passed = score >= 0.65

    return MetricScore(
      name=self.name,
      score=score,
      weight=self.weight,
      passed=passed,
      feedback="Directive contains imperative verb & concrete boundary." if passed else "Rule is generic or lacks concrete execution boundaries.",
      details={"word_count": word_count, "has_imperative": has_imperative, "has_boundary": has_boundary},
    )


class HorizonAlignmentMetric:
  """Evaluates whether guidance bridges daily execution to 1-month sprints, 1-year milestones, and 5-year visions."""

  def __init__(self, weight: float = 0.15):
    self.name = "Horizon & Strategic Alignment"
    self.weight = weight

  def evaluate(self, response_dict: dict, active_horizon_goals: list[str]) -> MetricScore:
    if not isinstance(response_dict, dict):
      return MetricScore(name=self.name, score=0.0, weight=self.weight, passed=False, feedback="Invalid response object.", details={})

    combined_text = " ".join(str(v) for v in response_dict.values()).lower()

    # Check connection to goals
    has_goal_connection = bool(response_dict.get("goal_connection") or response_dict.get("horizon_impact") or response_dict.get("strategic_alignment"))
    goal_mentions = [g for g in active_horizon_goals if any(w.lower() in combined_text for w in g.split() if len(w) > 3)]

    score = 0.5 * (1.0 if has_goal_connection else 0.0) + 0.5 * (min(1.0, len(goal_mentions) / max(1, min(len(active_horizon_goals), 2))))
    score = round(score, 2)
    passed = score >= 0.50

    return MetricScore(
      name=self.name,
      score=score,
      weight=self.weight,
      passed=passed,
      feedback=f"Aligned with {len(goal_mentions)} active life horizons.",
      details={"has_goal_connection_field": has_goal_connection, "matched_goals": goal_mentions},
    )


class ToolCallingPrecisionMetric:
  """Evaluates whether agentic pipelines invoked the right tools with valid arguments."""

  def __init__(self, weight: float = 0.10):
    self.name = "Tool-Calling Precision"
    self.weight = weight

  def evaluate(self, tools_used: list[dict], expected_tools: list[str]) -> MetricScore:
    if not expected_tools:
      # If scenario doesn't require tools, grant full credit
      return MetricScore(name=self.name, score=1.0, weight=self.weight, passed=True, feedback="Tool calling not required for static pipeline.", details={})

    if not tools_used or not isinstance(tools_used, list):
      return MetricScore(
        name=self.name,
        score=0.0,
        weight=self.weight,
        passed=False,
        feedback=f"Agent failed to call any tools (expected {expected_tools}).",
        details={"tools_used": []},
      )

    used_names = [t.get("name") if isinstance(t, dict) else str(t) for t in tools_used]
    correct_calls = [t for t in expected_tools if t in used_names]
    precision_score = len(correct_calls) / max(1, len(expected_tools))

    score = round(min(1.0, precision_score), 2)
    passed = score >= 0.50

    return MetricScore(
      name=self.name,
      score=score,
      weight=self.weight,
      passed=passed,
      feedback=f"Invoked {len(correct_calls)}/{len(expected_tools)} expected tools.",
      details={"tools_used": used_names, "expected": expected_tools},
    )


class OperationalEfficiencyMetric:
  """Evaluates response latency and token conciseness."""

  def __init__(self, weight: float = 0.10):
    self.name = "Operational Efficiency"
    self.weight = weight

  def evaluate(self, latency_seconds: float, response_length_chars: int) -> MetricScore:
    # Latency score: < 2.0s = 1.0, 2-4s = 0.8, 4-7s = 0.6, > 7s = 0.3
    if latency_seconds <= 2.0:
      lat_score = 1.0
    elif latency_seconds <= 4.0:
      lat_score = 0.85
    elif latency_seconds <= 7.0:
      lat_score = 0.65
    else:
      lat_score = 0.35

    # Conciseness score: 200 - 1500 chars is ideal for structured coaching
    if 200 <= response_length_chars <= 1800:
      len_score = 1.0
    elif response_length_chars < 200:
      len_score = 0.5
    else:
      len_score = 0.7

    score = round(0.6 * lat_score + 0.4 * len_score, 2)
    passed = latency_seconds <= 6.5

    return MetricScore(
      name=self.name,
      score=score,
      weight=self.weight,
      passed=passed,
      feedback=f"Latency: {latency_seconds:.2f}s | Output: {response_length_chars} chars",
      details={"latency_seconds": latency_seconds, "char_count": response_length_chars},
    )
