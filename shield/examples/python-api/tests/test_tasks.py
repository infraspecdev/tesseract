"""Basic task tests — intentionally incomplete coverage."""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_create_task():
    response = client.post("/tasks/", json={"title": "Test task"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test task"


# Missing: tests for 404, invalid input, update, delete, auth
