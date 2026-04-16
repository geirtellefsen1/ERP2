"""Tests for the onboarding wizard endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestGetInitialState:
    """GET /onboarding/state when no record exists yet."""

    def test_returns_step_one(self, client: TestClient):
        response = client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 1
        assert data["step_data"] is None
        assert data["completed_at"] is None
        assert len(data["step_names"]) == 5
        assert data["step_names"][0] == "Agency Setup"


class TestUpdateState:
    """PUT /onboarding/state — create and update progress."""

    def test_create_and_update(self, client: TestClient):
        # First update — creates the record
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 2, "step_data": {"agency_name": "Acme BPO"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 2
        assert data["step_data"]["agency_name"] == "Acme BPO"

        # Second update — updates the existing record
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 3, "step_data": {"invited": ["a@b.com"]}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 3
        assert data["step_data"]["invited"] == ["a@b.com"]

    def test_get_after_update(self, client: TestClient):
        client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 4, "step_data": {"bank": "FNB"}},
        )
        response = client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 4
        assert data["step_data"]["bank"] == "FNB"

    def test_complete_sets_completed_at(self, client: TestClient):
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_at"] is not None


class TestStepValidation:
    """PUT /onboarding/state — rejects out-of-range steps."""

    def test_reject_step_zero(self, client: TestClient):
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 0},
        )
        assert response.status_code == 422

    def test_reject_step_six(self, client: TestClient):
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 6},
        )
        assert response.status_code == 422

    def test_reject_negative_step(self, client: TestClient):
        response = client.put(
            "/api/v1/onboarding/state",
            json={"current_step": -1},
        )
        assert response.status_code == 422
