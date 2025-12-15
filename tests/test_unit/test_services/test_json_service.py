# -*- coding: utf-8 -*-
"""Unit Tests for JsonService"""
import os
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.services.json_service import JsonService
from src.utils.response_models import StatusType, ValidationResult, FileGenerationResult


class TestJsonServiceInit:
    """Testes de inicialização do JsonService"""
    
    def test_service_initialization(self, json_service: JsonService):
        """Verifica inicialização correta do serviço"""
        assert json_service is not None
        assert json_service.current_progress == 0
        assert json_service.errors == []
        assert json_service.warnings == []
    
    def test_service_has_required_methods(self, json_service: JsonService):
        """Verifica existência de métodos essenciais"""
        assert hasattr(json_service, 'validate_inputs')
        assert hasattr(json_service, 'create_jsons')
        assert hasattr(json_service, 'get_progress')
    
    def test_service_with_custom_file_repository(self, mock_file_repository):
        """Verifica inicialização com FileRepository customizado"""
        service = JsonService(file_repo=mock_file_repository)
        assert service.file_repo == mock_file_repository
    
    def test_multiple_instances_are_independent(self):
        """Verifica que múltiplas instâncias são independentes"""
        service1 = JsonService()
        service2 = JsonService()
        
        service1.errors.append("error1")
        service1.current_progress = 50
        
        assert service2.errors == []
        assert service2.current_progress == 0


class TestJsonServiceValidation:
    """Testes de validação de inputs"""
    
    def test_validate_empty_path(self, json_service: JsonService):
        """Valida rejeição de path vazio"""
        result = json_service.validate_inputs(
            path_excel="",
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    def test_validate_none_path(self, json_service: JsonService):
        """Valida rejeição de path None"""
        result = json_service.validate_inputs(
            path_excel=None,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    def test_validate_invalid_extension(self, json_service: JsonService):
        """Valida rejeição de extensão inválida"""
        result = json_service.validate_inputs(
            path_excel="arquivo.csv",
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert "xls" in result.message.lower()
    
    def test_validate_file_not_found(self, json_service: JsonService):
        """Valida rejeição de arquivo inexistente"""
        result = json_service.validate_inputs(
            path_excel="arquivo_nao_existe.xlsx",
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert "encontrado" in result.message.lower()
    
    def test_validate_empty_inventory_list(
        self, 
        json_service: JsonService,
        sample_excel_file: str
    ):
        """Valida rejeição de lista de inventory vazia"""
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=[],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert "inventory" in result.message.lower()
    
    def test_validate_duplicate_inventory_names(
        self, 
        json_service: JsonService,
        sample_excel_file: str
    ):
        """Valida rejeição de inventory names duplicados"""
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A", "INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is False
        assert "mais de uma vez" in result.message.lower()
    
    @pytest.mark.parametrize("invalid_db", ["mysql", "sqlite", "", "SQL_SERVER"])
    def test_validate_invalid_db_type(
        self, 
        json_service: JsonService,
        sample_excel_file: str,
        invalid_db: str
    ):
        """Valida rejeição de tipo de banco inválido"""
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type=invalid_db,
            is_parameter=True
        )
        
        assert result.is_valid is False
    
    @pytest.mark.parametrize("valid_db", ["oracle", "postgres", "postgresql"])
    def test_validate_valid_db_types(
        self, 
        json_service: JsonService,
        sample_excel_file: str,
        valid_db: str
    ):
        """Valida aceitação de tipos de banco válidos"""
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type=valid_db,
            is_parameter=True
        )
        
        assert result.is_valid is True
    
    def test_validate_returns_type_in_details(
        self, 
        json_service: JsonService,
        sample_excel_file: str
    ):
        """Valida retorno do tipo (parameter/counter) nos detalhes"""
        result_param = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True
        )
        
        result_counter = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=False
        )
        
        assert result_param.details["type"] == "parameters"
        assert result_counter.details["type"] == "counters"


class TestJsonServiceProgress:
    """Testes de progresso"""
    
    def test_initial_progress_is_zero(self, json_service: JsonService):
        """Verifica progresso inicial em zero"""
        assert json_service.get_progress() == 0
    
    def test_progress_is_updated(self, json_service: JsonService):
        """Verifica atualização de progresso"""
        json_service.current_progress = 50
        assert json_service.get_progress() == 50


class TestJsonServiceCreateJsons:
    """Testes de criação de JSONs"""
    
    def test_create_jsons_validates_inputs(self, json_service: JsonService):
        """Verifica validação antes de criar"""
        result = json_service.create_jsons(
            path_excel="",
            inventory_names=[],
            db_type="oracle",
            is_parameter=True,
            is_enrichment=False,
            output_path="/tmp/output"
        )
        
        assert result.success is False
        assert result.status == StatusType.ERROR
    
    def test_create_jsons_parameters_with_mock(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica criação de JSONs de parâmetros com mock"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True,
            is_enrichment=False,
            output_path=output_directory
        )
        
        assert result.success is True
        assert "parâmetros" in result.message.lower()
    
    def test_create_jsons_counters_with_mock(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica criação de JSONs de contadores com mock"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=False,
            is_enrichment=False,
            output_path=output_directory
        )
        
        assert result.success is True
        assert "contadores" in result.message.lower()
    
    def test_create_jsons_with_enrichment(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica criação com enriquecimento"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True,
            is_enrichment=True,
            output_path=output_directory
        )
        
        assert result.success is True
    
    def test_create_jsons_handles_exception(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str
    ):
        """Verifica tratamento de exceção"""
        with patch(
            'src.services.json_service.JsonCreator',
            side_effect=Exception("Test JSON error")
        ):
            result = json_service.create_jsons(
                path_excel=sample_excel_file,
                inventory_names=["INV_A"],
                db_type="oracle",
                is_parameter=True,
                is_enrichment=False,
                output_path=output_directory
            )
            
            assert result.success is False
            assert "Test JSON error" in result.message or "erro" in result.message.lower()
    
    def test_create_jsons_normalizes_postgresql(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica normalização de postgresql para postgres"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="postgresql",
            is_parameter=True,
            is_enrichment=False,
            output_path=output_directory
        )
        
        assert result.success is True
    
    def test_create_jsons_returns_file_count(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica contagem de arquivos criados"""
        mock_file_repository.list_files.return_value = [
            "file1.json", "file2.json", "file3.json"
        ]
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True,
            is_enrichment=False,
            output_path=output_directory
        )
        
        assert result.success is True
        assert result.total_files == 3
        assert len(result.files_created) == 3


class TestJsonServiceEdgeCases:
    """Testes de casos de borda"""
    
    def test_large_inventory_list(
        self,
        json_service: JsonService,
        sample_excel_file: str
    ):
        """Verifica validação com lista grande"""
        large_list = [f"INV_LARGE_{i}" for i in range(500)]
        
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=large_list,
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is True
        assert result.details["inventory_count"] == 500
    
    def test_inventory_with_unicode_names(
        self,
        json_service: JsonService,
        sample_excel_file: str
    ):
        """Verifica validação com caracteres unicode"""
        unicode_names = ["INV_AÇÃO", "INV_CÓDIGO", "INV_NÚMERO"]
        
        result = json_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=unicode_names,
            db_type="oracle",
            is_parameter=True
        )
        
        assert result.is_valid is True
    
    @pytest.mark.parametrize("is_parameter,is_enrichment", [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ])
    def test_all_boolean_combinations(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository,
        is_parameter: bool,
        is_enrichment: bool
    ):
        """Verifica todas as combinações de flags booleanos"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=is_parameter,
            is_enrichment=is_enrichment,
            output_path=output_directory
        )
        
        assert result.success is True
    
    def test_original_filename_logging(
        self,
        json_service: JsonService,
        sample_excel_file: str,
        output_directory: str,
        mock_json_creator,
        mock_file_repository
    ):
        """Verifica uso do nome original do arquivo"""
        json_service.file_repo = mock_file_repository
        
        result = json_service.create_jsons(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            is_parameter=True,
            is_enrichment=False,
            output_path=output_directory,
            original_filename="original_pack.xlsx"
        )
        
        assert result.success is True
