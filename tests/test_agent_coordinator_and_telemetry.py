"""Comprehensive unit and integration tests for multi-agent coordinator, sessions, and telemetry."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ai.pipelines.coordinator import CoordinatorPipeline
from ai.tools import execute_tool, get_scoped_tool_definitions
from api.main import app
from database.repositories.coach_session_repository import CoachSessionRepository
from database.repositories.goal_repository import GoalRepository
from models.coach_session import CoachChatRequest
from models.goal import GoalCreate
from services.observability_service import ObservabilityService

client = TestClient(app)


def test_coach_session_repository_crud(temp_db):
  repo = CoachSessionRepository()
  session = repo.create_session(title="Q3 Strategy Review", intent="goals_pacing", blackboard={"focus": "Q3 Goals"})
  assert session.id.startswith("sess_")
  assert session.title == "Q3 Strategy Review"
  assert session.blackboard == {"focus": "Q3 Goals"}

  # Append messages
  m1 = repo.append_message(session.id, role="user", content="How am I pacing on Q3?")
  m2 = repo.append_message(
    session.id,
    role="assistant",
    content="You are at 65% completion.",
    agent_name="CoordinatorAgent",
    tool_calls=[{"tool": "get_active_goals"}],
  )
  assert m1.role == "user"
  assert m2.role == "assistant"
  assert m2.agent_name == "CoordinatorAgent"

  # Fetch session with messages
  fetched = repo.get_session(session.id)
  assert fetched is not None
  assert len(fetched.messages) == 2
  assert fetched.messages[0].content == "How am I pacing on Q3?"
  assert fetched.messages[1].tool_calls == [{"tool": "get_active_goals"}]

  # Update blackboard
  repo.update_blackboard(session.id, {"focus": "Q3 Goals", "completion_rate": 0.65})
  updated = repo.get_session(session.id)
  assert updated.blackboard.get("completion_rate") == 0.65

  # List sessions
  sessions = repo.list_sessions(limit=10)
  assert any(s.id == session.id for s in sessions)

  # Delete session
  assert repo.delete_session(session.id) is True
  assert repo.get_session(session.id) is None


def test_telemetry_recording_and_cost_calculation(temp_db):
  obs = ObservabilityService()

  # Test Cost calculation
  cost_free = obs.calculate_cost("nvidia/nemotron-3-super-120b:free", 1000, 500)
  assert cost_free == 0.0

  cost_claude = obs.calculate_cost("anthropic/claude-3.5-sonnet", 10_000, 2_000)
  assert cost_claude > 0.0  # 10k * $3/1M ($0.03) + 2k * $15/1M ($0.03) = $0.06

  cost_gemini = obs.calculate_cost("google/gemini-2.5-flash", 10_000, 2_000)
  assert cost_gemini > 0.0

  # Record spans
  s1 = obs.record_span(
    span_name="coordinator_goals",
    model="anthropic/claude-3.5-sonnet",
    prompt_tokens=1000,
    completion_tokens=200,
    latency_ms=450.5,
  )
  assert s1.id is not None
  assert s1.total_tokens == 1200
  assert s1.status == "success"

  # Fetch summary
  summary = obs.get_summary(days=1)
  assert summary.total_calls >= 1
  assert summary.total_tokens >= 1200
  assert summary.total_cost_usd > 0.0
  assert "anthropic/claude-3.5-sonnet" in summary.model_breakdown

  # Fetch recent traces
  traces = obs.get_recent_traces(limit=5)
  assert len(traces) >= 1
  assert traces[0].span_name == "coordinator_goals"


def test_domain_toolkits_partitioning(temp_db):
  # Calendar toolkit
  cal_tools = get_scoped_tool_definitions(["calendar"])
  names = {t["function"]["name"] for t in cal_tools}
  assert "get_lifespan_stats" in names
  assert "search_memories" not in names  # Properly scoped

  res_cal = execute_tool("get_lifespan_stats", {})
  assert "weeks_lived" in res_cal
  assert "weeks_remaining" in res_cal

  # Goals toolkit
  goal_repo = GoalRepository()
  goal_repo.create(GoalCreate(title="Test Pacing", category="career", horizon="quarterly"))
  res_goals = execute_tool("get_active_goals", {}, goal_repo=goal_repo)
  assert res_goals["count"] >= 1


def test_coordinator_intent_classification():
  pipe = CoordinatorPipeline()
  intent_exec, domains_exec = pipe.classify_intent("How should I plan my morning routine today?")
  assert intent_exec == "execution_coaching"
  assert "journal" in domains_exec

  intent_goals, domains_goals = pipe.classify_intent("Check my active milestones and horizon progress")
  assert intent_goals == "goals_pacing"
  assert "goals" in domains_goals

  intent_life, domains_life = pipe.classify_intent("How many weeks do I have left in my life calendar?")
  assert intent_life == "lifespan_awareness"
  assert "calendar" in domains_life


def test_coordinator_deterministic_fallback(temp_db):
  pipe = CoordinatorPipeline()
  req = CoachChatRequest(
    message="What should I focus on this morning?",
    remote_ai_consent=False,
  )
  resp = pipe.chat(req)
  assert resp.source == "deterministic_rules"
  assert "GoalOS Local Executive Rule Engine" in resp.reply
  assert resp.session_id is not None

  # Verify persisted message history
  sess = CoachSessionRepository().get_session(resp.session_id)
  assert len(sess.messages) == 2
  assert sess.messages[0].role == "user"
  assert sess.messages[1].role == "assistant"


def test_coordinator_api_endpoints(temp_db):
  # 1. Test POST /coach/chat
  chat_payload = {
    "message": "Give me an executive focus check for today",
    "remote_ai_consent": False,
  }
  res = client.post("/coach/chat", json=chat_payload)
  assert res.status_code == 200
  data = res.json()
  assert "session_id" in data
  assert data["source"] == "deterministic_rules"
  session_id = data["session_id"]

  # 2. Test GET /coach/sessions
  res_list = client.get("/coach/sessions")
  assert res_list.status_code == 200
  sessions = res_list.json()
  assert any(s["id"] == session_id for s in sessions)

  # 3. Test GET /coach/sessions/{session_id}
  res_get = client.get(f"/coach/sessions/{session_id}")
  assert res_get.status_code == 200
  session_detail = res_get.json()
  assert len(session_detail["messages"]) >= 2

  # 4. Test GET /coach/telemetry/summary
  res_tel = client.get("/coach/telemetry/summary")
  assert res_tel.status_code == 200
  summary = res_tel.json()
  assert "total_calls" in summary

  # 5. Test GET /coach/telemetry/traces
  res_traces = client.get("/coach/telemetry/traces")
  assert res_traces.status_code == 200
  traces = res_traces.json()
  assert isinstance(traces, list)

  # 6. Test DELETE /coach/sessions/{session_id}
  res_del = client.delete(f"/coach/sessions/{session_id}")
  assert res_del.status_code == 200
  assert client.get(f"/coach/sessions/{session_id}").status_code == 404
