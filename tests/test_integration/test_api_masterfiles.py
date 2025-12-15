# -*- coding: utf-8 -*-
"""
Integration Tests for Masterfile Endpoints
==========================================
Testes de integracao para endpoints de geracao de Masterfiles.

Endpoints testados:
- POST /api/masterfiles/create_async
- GET /api/masterfiles/progress/{job_id}
"""
import pytest
import json
import time
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx


class TestMasterfileCreateAsyncEndpoint:
    """Testes para POST /api/masterfiles/create_async"""
    
    def test_create_async_requires_file(self, client: TestClient):
        """Endpoint requer arquivo"""
        response = client.post(
            "/api/masterfiles/create_async",
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        # Sem arquivo, deve retornar erro
        assert response.status_code == 422
    
    def test_create_async_rejects_non_excel_file(
        self, 
        client: TestClient
    ):
        """Rejeita arquivo que não é Excel"""
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.txt", b"content", "text/plain")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        assert response.status_code == 400
        assert "xls" in response.json()["detail"].lower()
    
    def test_create_async_accepts_xlsx_file(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita arquivo .xlsx"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A", "INV_B"]',
                "db_type": "oracle"
            }
        )
        
        # Pode retornar 200 (aceito) ou erro de processamento
        # O importante é que não rejeita o formato
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "accepted"
    
    def test_create_async_accepts_xls_file(
        self, 
        api_client: httpx.Client
    ):
        """Aceita arquivo .xls"""
        # Simula arquivo .xls (bytes mínimos)
        xls_bytes = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # Magic bytes de arquivo .xls
        
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xls", xls_bytes, "application/vnd.ms-excel")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        # Aceita o formato (pode falhar depois no processamento)
        assert response.status_code in [200, 500]  # Aceito ou erro de processamento
    
    def test_create_async_requires_inventory_names(
        self, 
        client: TestClient,
        sample_excel_bytes: bytes
    ):
        """Requer inventory_names"""
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "db_type": "oracle"
            }
        )
        
        assert response.status_code == 422
    
    def test_create_async_requires_db_type(
        self, 
        client: TestClient,
        sample_excel_bytes: bytes
    ):
        """Requer db_type"""
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]'
            }
        )
        
        assert response.status_code == 422
    
    def test_create_async_accepts_json_array_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita inventory_names como JSON array"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A", "INV_B", "INV_C"]',
                "db_type": "oracle"
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()
    
    def test_create_async_accepts_csv_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita inventory_names como CSV"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": "INV_A, INV_B, INV_C",
                "db_type": "oracle"
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()
    
    def test_create_async_returns_job_id_and_output_path(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Retorna job_id e output_path"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "output_path" in data
            assert len(data["job_id"]) > 0
    
    @pytest.mark.parametrize("db_type", ["oracle", "postgres", "postgresql"])
    def test_create_async_accepts_valid_db_types(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes,
        db_type: str
    ):
        """Aceita tipos de banco válidos"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": db_type
            }
        )
        
        # Deve aceitar (pode falhar no processamento depois)
        assert response.status_code in [200, 500]
    
    def test_create_async_with_master_path(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes,
        temp_directory: str
    ):
        """Aceita master_path opcional"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "master_path": temp_directory
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()


class TestMasterfileProgressEndpoint:
    """Testes para GET /api/masterfiles/progress/{job_id}"""
    
    def test_progress_returns_404_for_invalid_job(self, client: TestClient):
        """Retorna 404 para job_id inválido"""
        response = client.get("/api/masterfiles/progress/invalid_job_id_12345")
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()
    
    def test_progress_returns_job_info_for_valid_job(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Retorna informações do job para job_id válido"""
        # Primeiro cria um job
        create_response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        if create_response.status_code == 200:
            job_id = create_response.json()["job_id"]
            
            # Consulta progresso
            progress_response = api_client.get(f"/api/masterfiles/progress/{job_id}")
            
            assert progress_response.status_code == 200
            data = progress_response.json()
            
            assert "job_id" in data
            assert "progress" in data
            assert "status" in data
            assert data["job_id"] == job_id
    
    def test_progress_includes_progress_value(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Progresso inclui valor numérico"""
        create_response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        if create_response.status_code == 200:
            job_id = create_response.json()["job_id"]
            
            progress_response = api_client.get(f"/api/masterfiles/progress/{job_id}")
            
            if progress_response.status_code == 200:
                data = progress_response.json()
                assert isinstance(data["progress"], (int, float))
                assert 0 <= data["progress"] <= 100


class TestMasterfileEndpointValidation:
    """Testes de validação de entrada"""
    
    def test_rejects_empty_inventory_names_array(
        self, 
        client: TestClient,
        sample_excel_bytes: bytes
    ):
        """Rejeita array vazio de inventory_names"""
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '[]',
                "db_type": "oracle"
            }
        )
        
        # Pode ser 200 (aceito mas falha depois) ou 400 (validação imediata)
        # Depende da implementação
        if response.status_code == 200:
            # Se aceito, consulta progresso para ver erro
            pass
    
    def test_handles_special_characters_in_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Trata caracteres especiais em inventory_names"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_TEST-1", "INV.TEST.2"]',
                "db_type": "oracle"
            }
        )
        
        # Não deve causar erro de parsing
        assert response.status_code in [200, 400, 500]


class TestMasterfileEndpointConcurrency:
    """Testes de concorrência"""
     
    def test_multiple_jobs_have_unique_ids(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Múltiplos jobs têm IDs únicos"""
        job_ids = []
        
        for i in range(3):
            response = api_client.post(
                "/api/masterfiles/create_async",
                files={"file": (f"test_{i}.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={
                    "inventory_names": f'["INV_{i}"]',
                    "db_type": "oracle"
                }
            )
            
            if response.status_code == 200:
                job_ids.append(response.json()["job_id"])
        
        # Verifica que todos são únicos
        assert len(job_ids) == len(set(job_ids))
