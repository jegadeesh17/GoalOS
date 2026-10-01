"""Task-to-goal links: keys, resolution order, review queue, goal attention, storage and API."""

import json
import os
import sqlite3
import sys
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from api.main import app
from database.connection import get_db
from database.repositories.goal_repository import GoalRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLogCreate
from models.goal import Goal, GoalCreate, GoalUpdate
from models.task_link import TaskLink
from services.journal_helpers import task_key
from services.task_link_service import NO_GOAL, UNREVIEWED, Resolution, TaskLinkService, cue_matches, resolve_key


def _goal(goal_id: int, cues=None, status: str = "active") -> Goal:
  return Goal(id=goal_id, title=f"Goal {goal_id}", category="career", horizon="1-year", cues=cues, status=status)


def _link(key: str, kind: str, goal_id=None) -> TaskLink:
  return TaskLink(key=key, kind=kind, goal_id=goal_id)


def _add_goal(title="Getting a job", cues=None) -> Goal:
  return GoalRepository().create(GoalCreate(title=title, category="career", horizon="1-year", cues=cues))


def _log(day: date, done=(), undone=()) -> None:
  tasks = [{"text": t, "completed": True} for t in done] + [{"text": t, "completed": False} for t in undone]
  LogRepository().create(DailyLogCreate(date=day, planned_tasks=json.dumps(tasks)))


class TestTaskKey:
  def test_punctuation_case_and_spacing_do_not_change_the_key(self):
    assert task_key("Wash clothes.") == task_key(" wash  CLOTHES") == "wash clothes"


class TestCueMatching:
  def test_a_cue_is_a_prefix_of_a_word(self):
    assert cue_matches("appl", "apply for 10 companies")
    assert cue_matches("appl", "send applications")
    assert not cue_matches("appl", "reapply later")  # prefix of a word, not any substring

  def test_a_phrase_cue_must_match_whole_words(self):
    assert cue_matches("system design", "read system design notes")
    assert not cue_matches("system design", "systems designing")

  def test_empty_input_never_matches(self):
    assert not cue_matches("", "anything")
    assert not cue_matches("appl", "")


class TestResolve:
  def test_unique_cue_resolves_to_its_goal(self):
    goals = [_goal(1, ["appl"]), _goal(2, ["gym"])]
    assert resolve_key("apply for 10 companies", {}, goals) == Resolution("goal", 1)

  def test_two_goals_claiming_a_task_leave_it_unreviewed(self):
    goals = [_goal(1, ["appl"]), _goal(2, ["company"])]
    assert resolve_key("apply to a company", {}, goals) == UNREVIEWED

  def test_no_cues_means_unreviewed_not_misaligned(self):
    assert resolve_key("wash clothes", {}, [_goal(1)]) == UNREVIEWED

  def test_explicit_goal_link_beats_a_cue(self):
    goals = [_goal(1, ["appl"]), _goal(2)]
    links = {"apply for 10 companies": _link("apply for 10 companies", "goal", 2)}
    assert resolve_key("apply for 10 companies", links, goals) == Resolution("goal", 2)

  def test_explicit_none_beats_a_cue(self):
    links = {"apply for 10 companies": _link("apply for 10 companies", "none")}
    assert resolve_key("apply for 10 companies", links, [_goal(1, ["appl"])]) == NO_GOAL

  def test_cues_of_inactive_goals_are_ignored(self):
    assert resolve_key("apply", {}, [_goal(1, ["appl"], status="completed")]) == UNREVIEWED


class TestGoalCues:
  def test_cues_are_normalised_and_deduplicated(self):
    goal = GoalCreate(title="Job", category="career", horizon="1-year", cues=["Apply!", " apply ", "System  Design"])
    assert goal.cues == ["apply", "system design"]

  def test_a_cue_under_three_characters_is_rejected(self):
    with pytest.raises(ValidationError):
      GoalCreate(title="Job", category="career", horizon="1-year", cues=["ab"])
    with pytest.raises(ValidationError):
      GoalUpdate(cues=["go"])

  def test_cues_survive_a_round_trip_and_can_be_cleared(self, temp_db):
    goal = _add_goal(cues=["Apply", "interview"])
    assert GoalRepository().get_by_id(goal.id).cues == ["apply", "interview"]
    assert GoalRepository().update(goal.id, GoalUpdate(cues=[])).cues == []

  def test_a_goal_without_cues_reads_back_as_none(self, temp_db):
    assert _add_goal().cues is None


class TestStorage:
  def test_migration_creates_the_table_and_column(self, temp_db):
    with get_db() as conn:
      assert "cues" in [r["name"] for r in conn.execute("PRAGMA table_info(goals)")]
      assert [r["name"] for r in conn.execute("PRAGMA table_info(task_links)")] == [
        "task_key", "kind", "goal_id", "updated_at"
      ]

  def test_a_goal_kind_needs_a_goal_and_none_must_not_have_one(self, temp_db):
    with pytest.raises(sqlite3.IntegrityError):
      with get_db() as conn:
        conn.execute("INSERT INTO task_links (task_key, kind) VALUES ('a', 'goal')")
    with pytest.raises(sqlite3.IntegrityError):
      with get_db() as conn:
        conn.execute("INSERT INTO task_links (task_key, kind, goal_id) VALUES ('a', 'none', 1)")

  def test_deleting_a_goal_returns_its_tasks_to_the_review_queue(self, temp_db):
    goal = _add_goal()
    _log(date(2026, 9, 1), done=["Apply for jobs"])
    service = TaskLinkService()
    service.set_link("Apply for jobs", "goal", goal.id)
    assert service.review_queue()["unreviewed_completed_keys"] == 0
    GoalRepository().delete(goal.id)
    assert [i["key"] for i in service.review_queue()["items"]] == ["apply for jobs"]


class TestService:
  def test_set_link_validates_input(self, temp_db):
    service = TaskLinkService()
    with pytest.raises(ValueError):
      service.set_link("   ", "none", None)
    with pytest.raises(ValueError):
      service.set_link("x task", "goal", None)
    with pytest.raises(ValueError):
      service.set_link("x task", "none", 1)
    with pytest.raises(LookupError):
      service.set_link("x task", "goal", 999)

  def test_one_decision_applies_to_every_wording_of_the_task(self, temp_db):
    service = TaskLinkService()
    service.set_link("Wash clothes.", "none", None)
    assert service.resolver()("wash   CLOTHES") == NO_GOAL

  def test_review_queue_lists_only_completed_unreviewed_tasks_most_repeated_first(self, temp_db):
    _add_goal(cues=["gym"])
    _log(date(2026, 9, 1), done=["Leetcode", "Gym session", "Read book"], undone=["Never done"])
    _log(date(2026, 9, 2), done=["leetcode."], undone=["Read book"])
    _log(date(2026, 9, 3), done=["Leetcode"])
    queue = TaskLinkService().review_queue()
    assert queue["unreviewed_completed_keys"] == 2
    assert [(i["key"], i["done"], i["planned"], i["last_date"]) for i in queue["items"]] == [
      ("leetcode", 3, 3, "2026-09-03"),
      ("read book", 1, 2, "2026-09-02"),
    ]

  def test_review_queue_limit(self, temp_db):
    _log(date(2026, 9, 1), done=["a task", "b task", "c task"])
    queue = TaskLinkService().review_queue(limit=2)
    assert queue["unreviewed_completed_keys"] == 3 and len(queue["items"]) == 2

  def test_goal_attention_counts_completed_tasks_per_goal(self, temp_db):
    busy = _add_goal("Getting a job", cues=["appl"])
    quiet = _add_goal("Getting fit", cues=["gym"])
    _log(date(2026, 9, 1), done=["Gym"])  # 29 days before as_of
    for offset in (0, 3, 5):
      _log(date(2026, 9, 30) - timedelta(days=offset), done=["Apply"], undone=["Apply again"])
    rows = {r["goal_id"]: r for r in TaskLinkService().goal_attention(days=14)}
    assert rows[busy.id]["done_recent"] == 3 and rows[busy.id]["days_quiet"] == 0
    assert rows[busy.id]["last_done_date"] == "2026-09-30" and rows[busy.id]["as_of"] == "2026-09-30"
    assert rows[quiet.id]["done_recent"] == 0 and rows[quiet.id]["done_30d"] == 1
    assert rows[quiet.id]["days_quiet"] == 29

  def test_a_goal_never_worked_on_has_no_quiet_days(self, temp_db):
    goal = _add_goal(cues=["appl"])
    _log(date(2026, 9, 1), done=["Wash clothes"])
    row = TaskLinkService().goal_attention()[0]
    assert row["goal_id"] == goal.id and row["done_30d"] == 0
    assert row["last_done_date"] is None and row["days_quiet"] is None

  def test_goal_attention_is_empty_without_logs(self, temp_db):
    _add_goal()
    assert TaskLinkService().goal_attention() == []


@pytest.fixture
def client(temp_db):
  return TestClient(app)


class TestApi:
  def test_review_queue_endpoint(self, client):
    _log(date(2026, 9, 1), done=["Leetcode", "Read"])
    _log(date(2026, 9, 2), done=["Leetcode"])
    body = client.get("/tasks/review", params={"limit": 1}).json()
    assert body["unreviewed_completed_keys"] == 2
    assert [i["key"] for i in body["items"]] == ["leetcode"]
    assert client.get("/tasks/review", params={"limit": 0}).status_code == 422

  def test_saving_a_link_changes_the_stored_alignment_and_removes_the_task_from_the_queue(self, client):
    goal = _add_goal()
    for offset in range(5):
      _log(date(2026, 9, 1) + timedelta(days=offset), done=["Apply"])
    assert ScoreRepository().get_by_date(date(2026, 9, 5)) is None
    response = client.put("/tasks/links", json={"key": "Apply", "kind": "goal", "goal_id": goal.id})
    assert response.status_code == 200 and response.json()["key"] == "apply"
    assert ScoreRepository().get_by_date(date(2026, 9, 5)).goal_alignment_score == 100.0
    assert client.get("/tasks/review").json()["unreviewed_completed_keys"] == 0
    client.put("/tasks/links", json={"key": "apply", "kind": "none"})
    assert ScoreRepository().get_by_date(date(2026, 9, 5)).goal_alignment_score == 0.0
    assert client.delete("/tasks/links/Apply").json() == {"success": True}
    assert ScoreRepository().get_by_date(date(2026, 9, 5)).goal_alignment_score is None
    assert client.delete("/tasks/links/apply").status_code == 404

  def test_link_validation(self, client):
    assert client.put("/tasks/links", json={"key": "x", "kind": "maybe"}).status_code == 422
    assert client.put("/tasks/links", json={"key": "x", "kind": "goal"}).status_code == 422
    assert client.put("/tasks/links", json={"key": "x", "kind": "goal", "goal_id": 999}).status_code == 404
    assert client.put("/tasks/links", json={"key": "  ", "kind": "none"}).status_code == 422

  def test_changing_a_goals_cues_recomputes_scores(self, client):
    goal = _add_goal()
    for offset in range(5):
      _log(date(2026, 9, 1) + timedelta(days=offset), done=["Apply"])
    client.post("/analytics/monthly/recompute")
    assert client.put(f"/goals/{goal.id}", json={"cues": ["appl"]}).json()["cues"] == ["appl"]
    assert ScoreRepository().get_by_date(date(2026, 9, 5)).goal_alignment_score == 100.0

  def test_a_short_cue_is_rejected(self, client):
    goal = _add_goal()
    assert client.put(f"/goals/{goal.id}", json={"cues": ["ab"]}).status_code == 422
    body = {"title": "x", "category": "c", "horizon": "1-year", "cues": ["a"]}
    assert client.post("/goals", json=body).status_code == 422

  def test_goal_attention_endpoint(self, client):
    goal = _add_goal(cues=["appl"])
    _log(date(2026, 9, 30), done=["Apply"])
    rows = client.get("/goals/attention", params={"days": 14}).json()
    assert rows[0]["goal_id"] == goal.id and rows[0]["done_recent"] == 1
    assert client.get("/goals/attention", params={"days": 0}).status_code == 422
