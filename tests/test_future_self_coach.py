"""Future-self coach: age-from-birth_date computation and the pacing fallback."""

from datetime import date

from ai.pipelines._base import fallback_future_self
from database.connection import get_db
from models.goal import GoalCreate
from services.coach_service import CoachService


class TestCurrentAgeInTenYears:
  def test_computed_from_real_birth_date_not_hardcoded(self, temp_db):
    with get_db() as conn:
      conn.execute("UPDATE user SET birth_date = ? WHERE id = 1", ("2000-01-01",))
    service = CoachService()

    context = service.build_context(date.today())

    expected_current_age = (date.today() - date(2000, 1, 1)).days / 365.25
    assert context["current_age_in_10_years"] == round(expected_current_age) + 10

  def test_is_none_not_guessed_when_birth_date_missing(self, temp_db):
    with get_db() as conn:
      conn.execute("UPDATE user SET birth_date = NULL WHERE id = 1")
    service = CoachService()

    context = service.build_context(date.today())

    assert context["current_age_in_10_years"] is None


class TestFallbackFutureSelf:
  def test_reports_off_pace_below_40_percent_completion(self):
    context = {
      "current_age_in_10_years": 34,
      "user_vision": {"five_year_vision": "Net worth target", "ten_year_vision": "Financial independence"},
      "recent_logs": [{"task_completion_rate": 20.0}, {"task_completion_rate": 10.0}],
    }
    result = fallback_future_self(context)
    assert result["written_from_age"] == 34
    assert "Off pace" in result["five_year_pacing"]
    assert "Net worth target" in result["five_year_pacing"]
    assert "Financial independence" in result["ten_year_pacing"]

  def test_reports_on_pace_at_or_above_40_percent_completion(self):
    context = {
      "current_age_in_10_years": 34,
      "user_vision": {"five_year_vision": "Net worth target", "ten_year_vision": "Financial independence"},
      "recent_logs": [{"task_completion_rate": 80.0}, {"task_completion_rate": 70.0}],
    }
    result = fallback_future_self(context)
    assert "On pace" in result["five_year_pacing"]

  def test_names_missing_goals_instead_of_inventing_them(self):
    context = {"current_age_in_10_years": 34, "user_vision": {}, "recent_logs": []}
    result = fallback_future_self(context)
    assert "No 5-year goals defined yet" in result["five_year_pacing"]
    assert "No 10-year goals defined yet" in result["ten_year_pacing"]
    assert result["key_things_referenced"] == []

  def test_missing_ten_year_goal_does_not_get_quoted_as_a_real_goal(self):
    # Regression: one horizon has a goal, the other doesn't - the "no goals
    # defined yet" placeholder must never be treated as a real goal name.
    context = {
      "current_age_in_10_years": 34,
      "user_vision": {"five_year_vision": "Net worth target", "ten_year_vision": ""},
      "recent_logs": [{"task_completion_rate": 80.0}],
    }
    result = fallback_future_self(context)
    assert "Net worth target" in result["five_year_pacing"]
    assert "No 10-year goals defined yet" in result["ten_year_pacing"]
    assert "defined yet" not in result["message"]
    assert result["key_things_referenced"] == ["Net worth target"]

  def test_end_to_end_pacing_reflects_real_goal_records(self, temp_db):
    service = CoachService()
    service.goal_repo.create(GoalCreate(title="Financially independent", category="finance", horizon="10-year"))
    service.goal_repo.create(GoalCreate(title="8 crore net worth", category="finance", horizon="5-year"))

    context = service.build_context(date.today())
    result = fallback_future_self(context)

    assert "Financially independent" in result["ten_year_pacing"]
    assert "8 crore net worth" in result["five_year_pacing"]


class TestFallbackFutureSelfWithoutAge:
  def test_does_not_invent_an_age_when_unknown(self):
    context = {"current_age_in_10_years": None, "user_vision": {}, "recent_logs": []}

    result = fallback_future_self(context)

    assert result["written_from_age"] is None
    assert "years old" not in result["message"]
    assert "ten years from now" in result["message"]
