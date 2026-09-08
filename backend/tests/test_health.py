from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the /health endpoint returns a 200 status and healthy payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "BCG AI Financial Analyst" in data["service"]


def test_api_health_alias(client: TestClient) -> None:
    """Test the /api/health alias endpoint returns identical healthy payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "BCG AI Financial Analyst" in data["service"]


def test_openapi_json_endpoints(client: TestClient) -> None:
    """Test that both /openapi.json and /api/v1/openapi.json serve the OpenAPI schema."""
    res_root = client.get("/openapi.json")
    assert res_root.status_code == 200
    assert "openapi" in res_root.json()

    res_v1 = client.get("/api/v1/openapi.json")
    assert res_v1.status_code == 200
    assert "openapi" in res_v1.json()


def test_api_docs_redirect(client: TestClient) -> None:
    """Test that /api/docs redirects to /docs."""
    response = client.get("/api/docs", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/docs"
