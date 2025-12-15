"""
Health Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data or "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "services" in data


def test_docs_available(client: TestClient):
    """Test OpenAPI docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
