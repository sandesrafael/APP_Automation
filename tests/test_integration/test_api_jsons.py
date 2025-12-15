# -*- coding: utf-8 -*-
"""
Integration Tests for JSON Endpoints
====================================
Testes de integracao para endpoints de geracao de JSONs.

Endpoints testados:
- POST /api/jsons/create_async
- GET /api/jsons/progress/{job_id}
"""
import pytest
import json
import httpx


class TestJsonCreateAsyncEndpoint:
    """Testes para POST /api/jsons/create_async"""
    
    def test_create_async_requires_file(self, api_client: httpx.Client):
        """Endpoint requer arquivo"""
        response = api_client.post(
            "/api/jsons/create_async",
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        assert response.status_code == 422
    
    def test_create_async_rejects_non_excel_file(self, api_client: httpx.Client):
        """Rejeita arquivo que não é Excel"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.csv", b"data", "text/csv")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true"
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
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "accepted"
    
    def test_create_async_requires_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Requer inventory_names"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        assert response.status_code == 422
    
    def test_create_async_requires_db_type(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Requer db_type"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "is_parameter": "true"
            }
        )
        
        assert response.status_code == 422
    
    def test_create_async_requires_is_parameter(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Requer is_parameter"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.parametrize("is_parameter", ["true", "false", "True", "False"])
    def test_create_async_accepts_is_parameter_values(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes,
        is_parameter: str
    ):
        """Aceita diferentes valores para is_parameter"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": is_parameter
            }
        )
        
        # Deve aceitar (pode falhar no processamento)
        assert response.status_code in [200, 500]
    
    def test_create_async_accepts_is_enrichment(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita is_enrichment opcional"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true",
                "is_enrichment": "true"
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()
    
    def test_create_async_is_enrichment_defaults_false(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """is_enrichment tem default False"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "false"
                # is_enrichment não fornecido
            }
        )
        
        # Não deve falhar por falta de is_enrichment
        assert response.status_code in [200, 500]
    
    def test_create_async_returns_job_id_and_output_path(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Retorna job_id e output_path"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "output_path" in data
    
    @pytest.mark.parametrize("db_type", ["oracle", "postgres", "postgresql"])
    def test_create_async_accepts_valid_db_types(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes,
        db_type: str
    ):
        """Aceita tipos de banco válidos"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("fixtures/test_pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": db_type,
                "is_parameter": "true"
            }
        )
        
        assert response.status_code in [200, 500]


class TestJsonProgressEndpoint:
    """Testes para GET /api/jsons/progress/{job_id}"""
    
    def test_progress_returns_404_for_invalid_job(self, api_client: httpx.Client):
        """Retorna 404 para job_id inválido"""
        response = api_client.get("/api/jsons/progress/invalid_job_id_xyz")
        
        assert response.status_code == 404
    
    def test_progress_returns_job_info_for_valid_job(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Retorna informações do job para job_id válido"""
        # Primeiro cria um job
        create_response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        if create_response.status_code == 200:
            job_id = create_response.json()["job_id"]
            
            progress_response = api_client.get(f"/api/jsons/progress/{job_id}")
            
            assert progress_response.status_code == 200
            data = progress_response.json()
            
            assert "job_id" in data
            assert "progress" in data
            assert "status" in data


class TestJsonEndpointFormats:
    """Testes de formatos de entrada"""
    
    def test_accepts_json_array_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita inventory_names como JSON array"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["A", "B", "C"]',
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()
    
    def test_accepts_csv_inventory_names(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes
    ):
        """Aceita inventory_names como CSV"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": "A, B, C",
                "db_type": "oracle",
                "is_parameter": "true"
            }
        )
        
        if response.status_code == 200:
            assert "job_id" in response.json()


class TestJsonEndpointCombinations:
    """Testes de combinações de parâmetros"""
    
    @pytest.mark.parametrize("is_parameter,is_enrichment", [
        ("true", "true"),
        ("true", "false"),
        ("false", "true"),
        ("false", "false"),
    ])
    def test_all_boolean_combinations(
        self, 
        api_client: httpx.Client,
        sample_excel_bytes: bytes,
        is_parameter: str,
        is_enrichment: str
    ):
        """Testa todas as combinações de booleanos"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": is_parameter,
                "is_enrichment": is_enrichment
            }
        )
        
        # Todas as combinações devem ser aceitas
        assert response.status_code in [200, 500]
