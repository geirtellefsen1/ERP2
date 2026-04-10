from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_tasks_requires_auth():
    response = client.get("/tasks")
    assert response.status_code == 401


def test_create_task_requires_auth():
    response = client.post("/tasks", json={"title": "Test", "client_id": 1})
    assert response.status_code == 401


def test_update_task_requires_auth():
    response = client.put("/tasks/1", json={"status": "completed"})
    assert response.status_code == 401
