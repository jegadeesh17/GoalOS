import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


@pytest.fixture
def client(temp_db):
    mock_result = {
        "mentor_rule": "Protect a 90-minute deep work block before meetings.",
        "why_this_rule": "Meetings fragmented focus yesterday.",
        "confidence": 0.82,
        "source": "agent_morning",
        "tools_used": ["search_memories", "get_active_goals"],
    }
    mock_log = MagicMock()
    mock_log.id = 1
    with patch("api.main.LogRepository") as log_repo_cls, patch(
        "api.main.CoachService"
    ) as coach_cls:
        log_repo_cls.return_value.upsert_by_date.return_value = mock_log
        log_repo_cls.return_value.count.return_value = 1
        coach_cls.return_value.get_morning_coaching.return_value = mock_result
        with patch("api.main.MemoryService") as mem_cls:
            mem_cls.return_value.count.return_value = 5
            from api.main import app

            yield TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body == {"status": "ok"}


def test_coach_morning_schema(client):
    response = client.post(
        "/coach/morning",
        json={
            "gratitude": "Focused morning",
            "tasks": [{"text": "Deep work", "priority": 1}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "mentor_rule" in body
    assert body["tools_used"] == ["search_memories", "get_active_goals"]


def test_coach_morning_invalid_mood(client):
    response = client.post(
        "/coach/morning",
        json={"tasks": [{"text": "Task"}], "mood_morning": 10},
    )
    assert response.status_code == 422
