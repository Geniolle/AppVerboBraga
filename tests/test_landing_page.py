import pytest
from fastapi.testclient import TestClient

from appgenesis.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_landing_page_returns_200(client):
    """Test that landing page renders successfully with 200 status."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_landing_page_returns_html_content(client):
    """Test that landing page contains HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    # Check for basic HTML structure
    assert response.text  # Should have content
    assert len(response.text) > 100  # Should be substantial HTML


def test_health_endpoint_still_works(client):
    """Regression test: health endpoint should continue working."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
