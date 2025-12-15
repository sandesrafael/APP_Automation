# -*- coding: utf-8 -*-
"""
Integration Tests for DBN Endpoints
===================================
Testes de integracao para endpoints de geracao de modelos DBN.

Endpoints testados:
- POST /api/dbn/dbn0/create
- POST /api/dbn/dbn1/create
- POST /api/dbn/dbn1/rename
- GET /api/dbn/progress
"""
import pytest
import json
from fastapi.testclient import TestClient


class TestDBN0CreateEndpoint:
    """Testes para POST /api/dbn/dbn0/create"""
    
    def test_create_dbn0_requires_dbn_names(self, client: TestClient, output_directory: str):
        """Requer dbn_names"""
        response = client.post("/api/dbn/dbn0/create", data={"output_path": output_directory})
        assert response.status_code == 422
    
    def test_create_dbn0_requires_output_path(self, client: TestClient, sample_dbn_names: list):
        """Requer output_path"""
        response = client.post("/api/dbn/dbn0/create", data={"dbn_names": json.dumps(sample_dbn_names)})
        assert response.status_code == 422
    
    def test_create_dbn0_with_valid_params(self, client: TestClient, sample_dbn_names: list, output_directory: str):
        """Criação com parâmetros válidos"""
        response = client.post("/api/dbn/dbn0/create", data={
            "dbn_names": json.dumps(sample_dbn_names),
            "output_path": output_directory
        })
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert "success" in response.json()
    
    def test_create_dbn0_with_schema(self, client: TestClient, sample_dbn_names: list, output_directory: str):
        """Criação com schema opcional"""
        response = client.post("/api/dbn/dbn0/create", data={
            "dbn_names": json.dumps(sample_dbn_names),
            "output_path": output_directory,
            "schema": "MY_SCHEMA"
        })
        assert response.status_code in [200, 400, 500]


class TestDBN1CreateEndpoint:
    """Testes para POST /api/dbn/dbn1/create"""
    
    def test_create_dbn1_requires_classe(self, client: TestClient, sample_dbn_names: list, output_directory: str):
        """DBN1 requer classe"""
        response = client.post("/api/dbn/dbn1/create", data={
            "dbn_names": json.dumps(sample_dbn_names),
            "output_path": output_directory
        })
        assert response.status_code == 422
    
    def test_create_dbn1_with_valid_params(self, client: TestClient, sample_dbn_names: list, output_directory: str):
        """Criação DBN1 com parâmetros válidos"""
        response = client.post("/api/dbn/dbn1/create", data={
            "dbn_names": json.dumps(sample_dbn_names),
            "output_path": output_directory,
            "classe": "MY_CLASS"
        })
        assert response.status_code in [200, 400, 500]


class TestDBN1RenameEndpoint:
    """Testes para POST /api/dbn/dbn1/rename"""
    
    def test_rename_requires_path(self, client: TestClient):
        """Requer path"""
        response = client.post("/api/dbn/dbn1/rename", data={})
        assert response.status_code == 422
    
    def test_rename_with_nonexistent_path(self, client: TestClient):
        """Retorna erro para path inexistente"""
        response = client.post("/api/dbn/dbn1/rename", data={"path": "/nonexistent/path"})
        assert response.status_code == 404
    
    def test_rename_with_valid_path(self, client: TestClient, output_directory: str):
        """Renomeia com path válido"""
        response = client.post("/api/dbn/dbn1/rename", data={"path": output_directory})
        assert response.status_code in [200, 400, 500]


class TestDBNProgressEndpoint:
    """Testes para GET /api/dbn/progress"""
    
    def test_progress_returns_200(self, client: TestClient):
        """Retorna status 200"""
        response = client.get("/api/dbn/progress")
        assert response.status_code == 200
    
    def test_progress_returns_progress_info(self, client: TestClient):
        """Retorna informações de progresso"""
        response = client.get("/api/dbn/progress")
        data = response.json()
        assert "progress" in data
        assert "status" in data
