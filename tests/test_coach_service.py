"""CoachService vision-derivation tests."""

from models.goal import GoalCreate
from services.coach_service import CoachService


class TestGetUserVision:
  def test_derives_vision_narrative_from_goal_records(self, temp_db):
    service = CoachService()
    service.goal_repo.create(GoalCreate(
      title="Get a 12 LPA job", category="career", horizon="1-year", reason="Financial stability",
    ))
    service.goal_repo.create(GoalCreate(
      title="8 crore net worth", category="finance", horizon="5-year",
    ))
    service.goal_repo.create(GoalCreate(
      title="Financially independent", category="finance", horizon="10-year",
    ))

    vision = service._get_user_vision()

    assert vision["one_year_vision"] == "Get a 12 LPA job (Financial stability)"
    assert vision["five_year_vision"] == "8 crore net worth"
    assert vision["ten_year_vision"] == "Financially independent"

  def test_empty_horizon_yields_empty_string_not_none(self, temp_db):
    service = CoachService()
    vision = service._get_user_vision()
    assert vision == {"one_year_vision": "", "five_year_vision": "", "ten_year_vision": ""}

  def test_multiple_goals_in_same_horizon_join_into_one_narrative(self, temp_db):
    service = CoachService()
    service.goal_repo.create(GoalCreate(title="Partner", category="personal", horizon="5-year"))
    service.goal_repo.create(GoalCreate(title="Career", category="finance", horizon="5-year"))

    vision = service._get_user_vision()

    assert vision["five_year_vision"] == "Partner; Career"
