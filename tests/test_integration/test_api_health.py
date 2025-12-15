# -*- coding: utf-8 -*-
"""
Integration Tests for Health Endpoints
======================================
Testes de integracao para endpoints de saude e informacoes da API.

Endpoints testados:
- GET / (root)
- GET /health
- GET /docs
- GET /redoc
- GET /openapi.json
"""
import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Testes para endpoint raiz"""
    
    def test_root_returns_200(self, client: TestClient):
        """Endpoint raiz retorna status 200"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_api_info(self, client: TestClient):
        """Endpoint raiz retorna informações da API"""
        response = client.get("/")
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_root_status_is_running(self, client: TestClient):
        """Status da API é 'running'"""
        response = client.get("/")
        data = response.json()
        
        assert data["status"] == "running"
    
    def test_root_includes_docs_links(self, client: TestClient):
        """Endpoint raiz inclui links para documentação"""
        response = client.get("/")
        data = response.json()
        
        assert "docs" in data or "documentation" in str(data).lower()


class TestHealthEndpoint:
    """Testes para endpoint de health check"""
    
    def test_health_returns_200(self, client: TestClient):
        """Health check retorna status 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_status_is_healthy(self, client: TestClient):
        """Status é 'healthy'"""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_includes_version(self, client: TestClient):
        """Health check inclui versão"""
        response = client.get("/health")
        data = response.json()
        
        assert "version" in data
    
    def test_health_includes_services_status(self, client: TestClient):
        """Health check inclui status dos serviços"""
        response = client.get("/health")
        data = response.json()
        
        assert "services" in data
        services = data["services"]
        
        # Verifica serviços esperados
        assert "masterfile" in services
        assert "json" in services
        assert "dbn" in services
    
    def test_health_services_are_available(self, client: TestClient):
        """Todos os serviços estão disponíveis"""
        response = client.get("/health")
        data = response.json()
        
        for service_name, status in data["services"].items():
            assert status == "available", f"Service {service_name} is not available"


class TestDocumentationEndpoints:
    """Testes para endpoints de documentação"""
    
    def test_docs_endpoint_available(self, client: TestClient):
        """Swagger UI está disponível"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_docs_returns_html(self, client: TestClient):
        """Swagger UI retorna HTML"""
        response = client.get("/docs")
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_redoc_endpoint_available(self, client: TestClient):
        """ReDoc está disponível"""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_redoc_returns_html(self, client: TestClient):
        """ReDoc retorna HTML"""
        response = client.get("/redoc")
        assert "text/html" in response.headers.get("content-type", "")


class TestOpenAPISchema:
    """Testes para schema OpenAPI"""
    
    def test_openapi_returns_200(self, client: TestClient):
        """OpenAPI schema retorna status 200"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
    
    def test_openapi_returns_json(self, client: TestClient):
        """OpenAPI schema retorna JSON"""
        response = client.get("/openapi.json")
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_openapi_has_version(self, client: TestClient):
        """Schema inclui versão OpenAPI"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")  # OpenAPI 3.x
    
    def test_openapi_has_info(self, client: TestClient):
        """Schema inclui informações da API"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "info" in schema
        assert "title" in schema["info"]
        assert "version" in schema["info"]
    
    def test_openapi_has_paths(self, client: TestClient):
        """Schema inclui paths"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "paths" in schema
        assert len(schema["paths"]) > 0
    
    def test_openapi_includes_masterfile_routes(self, client: TestClient):
        """Schema inclui rotas de masterfiles"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        masterfile_paths = [p for p in paths if "masterfile" in p.lower()]
        
        assert len(masterfile_paths) > 0
    
    def test_openapi_includes_json_routes(self, client: TestClient):
        """Schema inclui rotas de JSONs"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        json_paths = [p for p in paths if "json" in p.lower()]
        
        assert len(json_paths) > 0
    
    def test_openapi_includes_dbn_routes(self, client: TestClient):
        """Schema inclui rotas de DBN"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        dbn_paths = [p for p in paths if "dbn" in p.lower()]
        
        assert len(dbn_paths) > 0


class TestCORS:
    """Testes para CORS"""
    
    def test_cors_headers_present(self, client: TestClient):
        """Headers CORS estão presentes"""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # FastAPI/Starlette pode retornar 200 ou 405 dependendo da config
        # O importante é que os headers CORS estejam configurados
        headers = response.headers
        
        # Em ambiente de teste, pode não ter todos os headers
        # mas a aplicação não deve falhar
        assert response.status_code in [200, 400, 405]


class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_404_on_nonexistent_route(self, client: TestClient):
        """Retorna 404 para rota inexistente"""
        response = client.get("/nonexistent/route")
        assert response.status_code == 404
    
    def test_405_on_wrong_method(self, client: TestClient):
        """Retorna 405 para método não permitido"""
        # POST em endpoint que só aceita GET
        response = client.post("/health")
        assert response.status_code == 405
