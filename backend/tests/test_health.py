from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the /health endpoint returns a 200 status and healthy payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "BCG AI Financial Analyst" in data["service"]
