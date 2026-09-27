import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


@pytest.fixture
def client(temp_db):
    mock_result = {
        "pacing_status": "On Track — High Execution",
        "monthly_goal_evaluated": "Ship V2",
        "progress_narrative": "Solid pacing against the monthly goal.",
        "critical_bottleneck": "None detected",
        "actionable_coaching_advice": "Protect the morning deep work block.",
        "confidence": 0.82,
        "source": "ai",
    }
    with patch("api.main.CoachService") as coach_cls:
        coach_cls.return_value.get_progress_coaching.return_value = mock_result
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


def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_coach_progress_schema(client):
    response = client.post("/coach/progress", json={"date": "2026-01-15"})
    assert response.status_code == 200
    body = response.json()
    assert "actionable_coaching_advice" in body
    assert body["monthly_goal_evaluated"] == "Ship V2"


def test_api_coach_progress_schema(client):
    response = client.post("/api/coach/progress", json={})
    assert response.status_code == 200
    body = response.json()
    assert "actionable_coaching_advice" in body
