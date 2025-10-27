"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_create_notification(client: TestClient) -> None:
    """Test creating notification via API."""
    payload = {
        "recipient": "test@example.com",
        "message": "Test notification",
        "channels": ["email"],
    }

    response = client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["recipient"] == "test@example.com"
    assert data["message"] == "Test notification"
    assert data["status"] in ["pending", "sent", "failed"]
    assert "attempts" in data
    assert "created_at" in data


def test_get_notification(client: TestClient) -> None:
    """Test retrieving notification by ID."""
    # Create notification
    payload = {
        "recipient": "test@example.com",
        "message": "Test",
        "channels": ["email"],
    }
    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201
    notification_id = create_response.json()["id"]

    # Retrieve it
    get_response = client.get(f"/api/v1/notifications/{notification_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == notification_id


def test_get_notification_not_found(client: TestClient) -> None:
    """Test 404 for non-existent notification."""
    from uuid import uuid4

    fake_id = str(uuid4())
    response = client.get(f"/api/v1/notifications/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_notification_validation_error(client: TestClient) -> None:
    """Test validation error (empty message)."""
    payload = {
        "recipient": "test@example.com",
        "message": "",  # Invalid: too short
        "channels": ["email"],
    }

    response = client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 422  # Validation error

