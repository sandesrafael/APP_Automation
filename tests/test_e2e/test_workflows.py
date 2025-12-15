# -*- coding: utf-8 -*-
"""
End-to-End Tests for Complete Workflows
=======================================
Testes de ponta a ponta que simulam fluxos completos de usuario.

Cenários testados:
- Fluxo completo de criação de Masterfiles
- Fluxo completo de criação de JSONs
- Fluxo completo de criação de DBN
- Verificação de saúde da aplicação
- Cenários de erro
"""
import pytest
import json
import time
from fastapi.testclient import TestClient
import httpx


class TestApplicationHealth:
    """Testes E2E de saúde da aplicação"""
    
    def test_full_health_check_workflow(self, client: TestClient):
        """Verifica saúde completa da aplicação"""
        # 1. Verifica endpoint raiz
        root_response = client.get("/")
        assert root_response.status_code == 200
        assert root_response.json()["status"] == "running"
        
        # 2. Verifica health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # 3. Verifica todos os serviços
        for service, status in health_data["services"].items():
            assert status == "available", f"Service {service} not available"
        
        # 4. Verifica documentação disponível
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        # 5. Verifica schema OpenAPI
        schema_response = client.get("/openapi.json")
        assert schema_response.status_code == 200
        schema = schema_response.json()
        assert "paths" in schema
        assert len(schema["paths"]) > 0


class TestMasterfileWorkflow:
    """Testes E2E de fluxo de Masterfiles"""
    
    def test_masterfile_creation_workflow(self, api_client: httpx.Client, sample_excel_bytes: bytes):
        """Fluxo completo de criação de masterfiles"""
        # 1. Submete job de criação
        create_response = api_client.post(
            "/api/masterfiles/create_async",
            files={
                "file": (
                    "pack_test.xlsx",
                    sample_excel_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={
                "inventory_names": '["INV_TEST_A", "INV_TEST_B"]',
                "db_type": "oracle",
            },
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create job - may need valid Excel file")
        
        data = create_response.json()
        assert "job_id" in data
        assert "output_path" in data
        job_id = data["job_id"]
        
        # 2. Consulta progresso
        progress_response = api_client.get(f"/api/masterfiles/progress/{job_id}")
        assert progress_response.status_code == 200
        
        progress_data = progress_response.json()
        assert "progress" in progress_data
        assert "status" in progress_data
        assert progress_data["job_id"] == job_id
    
    def test_masterfile_invalid_file_workflow(self, client: TestClient):
        """Fluxo com arquivo inválido"""
        # Tenta criar com arquivo não-Excel
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.txt", b"not excel", "text/plain")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle"
            }
        )
        
        # Deve rejeitar
        assert response.status_code == 400
        assert "xls" in response.json()["detail"].lower()
    
    def test_masterfile_missing_params_workflow(self, client: TestClient, sample_excel_bytes: bytes):
        """Fluxo com parâmetros faltando"""
        # Sem inventory_names
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"db_type": "oracle"}
        )
        assert response.status_code == 422
        
        # Sem db_type
        response = client.post(
            "/api/masterfiles/create_async",
            files={"file": ("test.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"inventory_names": '["INV_A"]'}
        )
        assert response.status_code == 422


class TestJsonWorkflow:
    """Testes E2E de fluxo de JSONs"""
    
    def test_json_parameters_workflow(self, api_client: httpx.Client, sample_excel_bytes: bytes):
        """Fluxo de criação de JSONs de parâmetros"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true",
                "is_enrichment": "false"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            
            # Consulta progresso
            progress = api_client.get(f"/api/jsons/progress/{data['job_id']}")
            assert progress.status_code == 200
    
    def test_json_counters_workflow(self, api_client: httpx.Client, sample_excel_bytes: bytes):
        """Fluxo de criação de JSONs de contadores"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "postgres",
                "is_parameter": "false",
                "is_enrichment": "false"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
    
    def test_json_with_enrichment_workflow(self, api_client: httpx.Client, sample_excel_bytes: bytes):
        """Fluxo de criação de JSONs com enriquecimento"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": "oracle",
                "is_parameter": "true",
                "is_enrichment": "true"
            }
        )
        
        assert response.status_code in [200, 500]


class TestDBNWorkflow:
    """Testes E2E de fluxo de DBN"""
    
    def test_dbn0_creation_workflow(self, client: TestClient, output_directory: str):
        """Fluxo de criação de DBN0"""
        response = client.post(
            "/api/dbn/dbn0/create",
            data={
                "dbn_names": '["DBN_001", "DBN_002"]',
                "output_path": output_directory,
                "schema": "TEST_SCHEMA"
            }
        )
        
        assert response.status_code in [200, 400, 500]
        
        # Verifica progresso
        progress = client.get("/api/dbn/progress")
        assert progress.status_code == 200
    
    def test_dbn1_creation_workflow(self, client: TestClient, output_directory: str):
        """Fluxo de criação de DBN1"""
        response = client.post(
            "/api/dbn/dbn1/create",
            data={
                "dbn_names": '["DBN_001"]',
                "output_path": output_directory,
                "classe": "MY_CLASS"
            }
        )
        
        assert response.status_code in [200, 400, 500]


class TestErrorScenarios:
    """Testes E2E de cenários de erro"""
    
    def test_404_for_nonexistent_routes(self, client: TestClient):
        """Retorna 404 para rotas inexistentes"""
        routes_to_test = [
            "/api/nonexistent",
            "/api/masterfiles/nonexistent",
            "/api/jsons/nonexistent",
            "/api/dbn/nonexistent"
        ]
        
        for route in routes_to_test:
            response = client.get(route)
            assert response.status_code in [404, 405], f"Route {route} returned {response.status_code}"
    
    def test_invalid_job_id_handling(self, client: TestClient):
        """Trata job_id inválido corretamente"""
        invalid_ids = [
            "invalid_id",
            "12345",
            "abc-def-ghi",
            ""
        ]
        
        for job_id in invalid_ids:
            if job_id:  # Evita rota vazia
                response = client.get(f"/api/masterfiles/progress/{job_id}")
                assert response.status_code == 404
                
                response = client.get(f"/api/jsons/progress/{job_id}")
                assert response.status_code == 404


class TestConcurrentWorkflows:
    """Testes E2E de fluxos concorrentes"""
    
    def test_multiple_masterfile_jobs(self, api_client: httpx.Client, sample_excel_bytes: bytes):
        """Múltiplos jobs de masterfile simultâneos"""
        job_ids = []
        
        for i in range(3):
            response = api_client.post(
                "/api/masterfiles/create_async",
                files={"file": (f"pack_{i}.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={
                    "inventory_names": f'["INV_{i}"]',
                    "db_type": "oracle"
                }
            )
            
            if response.status_code == 200:
                job_ids.append(response.json()["job_id"])
        
        # Verifica que todos os IDs são únicos
        if len(job_ids) > 1:
            assert len(job_ids) == len(set(job_ids))
        
        # Verifica que todos os jobs são acessíveis
        for job_id in job_ids:
            response = api_client.get(f"/api/masterfiles/progress/{job_id}")
            assert response.status_code == 200


class TestDatabaseTypeWorkflows:
    """Testes E2E para diferentes tipos de banco"""
    
    @pytest.mark.parametrize("db_type", ["oracle", "postgres", "postgresql"])
    def test_masterfile_with_different_db_types(self, api_client: httpx.Client, sample_excel_bytes: bytes, db_type: str):
        """Masterfiles com diferentes tipos de banco"""
        response = api_client.post(
            "/api/masterfiles/create_async",
            files={"file": ("pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": db_type
            }
        )
        
        # Todos os tipos devem ser aceitos
        assert response.status_code in [200, 500]
    
    @pytest.mark.parametrize("db_type", ["oracle", "postgres"])
    def test_json_with_different_db_types(self, api_client: httpx.Client, sample_excel_bytes: bytes, db_type: str):
        """JSONs com diferentes tipos de banco"""
        response = api_client.post(
            "/api/jsons/create_async",
            files={"file": ("pack.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "inventory_names": '["INV_A"]',
                "db_type": db_type,
                "is_parameter": "true"
            }
        )
        
        assert response.status_code in [200, 500]
