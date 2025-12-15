# -*- coding: utf-8 -*-
"""Unit Tests for MasterfileService"""
import os
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.services.masterfile_service import MasterfileService
from src.utils.response_models import StatusType, ValidationResult, FileGenerationResult


class TestMasterfileServiceInit:
    """Testes de inicialização do MasterfileService"""
    
    def test_service_initialization(self, masterfile_service: MasterfileService):
        """Verifica inicialização correta do serviço"""
        assert masterfile_service is not None
        assert masterfile_service.current_progress == 0
        assert masterfile_service.errors == []
        assert masterfile_service.warnings == []
    
    def test_service_has_required_methods(self, masterfile_service: MasterfileService):
        """Verifica existência de métodos essenciais"""
        assert hasattr(masterfile_service, 'validate_inputs')
        assert hasattr(masterfile_service, 'create_masterfiles')
        assert hasattr(masterfile_service, 'get_progress')
        assert hasattr(masterfile_service, 'update_progress')
        assert hasattr(masterfile_service, 'update_progress')
    
    def test_multiple_instances_are_independent(self):
        """Verifica que múltiplas instâncias são independentes"""
        service1 = MasterfileService()
        service2 = MasterfileService()
        
        service1.errors.append("error1")
        service1.update_progress(50)
        
        assert service2.errors == []
        assert service2.current_progress == 0


class TestMasterfileServiceValidation:
    """Testes de validação de inputs"""
    
    def test_validate_empty_path(self, masterfile_service: MasterfileService):
        """Valida rejeição de path vazio"""
        result = masterfile_service.validate_inputs(
            path_excel="",
            inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "arquivo" in result.message.lower() or "selecionado" in result.message.lower()
    
    def test_validate_none_path(self, masterfile_service: MasterfileService):
        """Valida rejeição de path None"""
        result = masterfile_service.validate_inputs(
            path_excel=None,
            inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    def test_validate_invalid_extension(self, masterfile_service: MasterfileService):
        """Valida rejeição de extensão inválida"""
        result = masterfile_service.validate_inputs(
            path_excel="arquivo.txt",
            inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "xls" in result.message.lower()
    
    def test_validate_file_not_found(self, masterfile_service: MasterfileService):
        """Valida rejeição de arquivo inexistente"""
        result = masterfile_service.validate_inputs(
            path_excel="arquivo_inexistente.xlsx",
            inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "encontrado" in result.message.lower()
    
    def test_validate_empty_inventory_list(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Valida rejeição de lista de inventory vazia"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=[],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "inventory" in result.message.lower()
    
    def test_validate_whitespace_only_inventory_list(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Valida rejeição de lista com apenas espaços em branco"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["  ", "\t", "\n"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    def test_validate_duplicate_inventory_names(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Valida rejeição de inventory names duplicados"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A", "INV_B", "INV_A"],
            db_type="oracle"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "mais de uma vez" in result.message.lower()
    
    @pytest.mark.parametrize("invalid_db", ["mysql", "sqlite", "mongodb", "", "INVALID"])
    def test_validate_invalid_db_type(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        invalid_db: str
    ):
        """Valida rejeição de tipo de banco inválido"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type=invalid_db
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    @pytest.mark.parametrize("valid_db", ["oracle", "postgres", "postgresql"])
    def test_validate_valid_db_types(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        valid_db: str
    ):
        """Valida aceitação de tipos de banco válidos"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type=valid_db
        )
        
        assert result.is_valid is True
        assert result.status == StatusType.SUCCESS
    
    def test_validate_success_returns_details(
        self, 
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Valida retorno de detalhes em sucesso"""
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=["INV_A", "INV_B"],
            db_type="oracle"
        )
        
        assert result.is_valid is True
        assert result.details is not None
        assert result.details["inventory_count"] == 2
        assert result.details["db_type"] == "oracle"


class TestMasterfileServiceProgress:
    """Testes de progresso e callbacks"""
    
    def test_initial_progress_is_zero(self, masterfile_service: MasterfileService):
        """Verifica progresso inicial em zero"""
        assert masterfile_service.get_progress() == 0
    
    def test_update_progress(self, masterfile_service: MasterfileService):
        """Verifica atualização de progresso"""
        masterfile_service.update_progress(50)
        assert masterfile_service.current_progress == 50
    
    def test_progress_callback_is_called(self, masterfile_service: MasterfileService):
        """Verifica que progress pode ser obtido"""
        masterfile_service.update_progress(25)
        assert masterfile_service.get_progress() == 25
        
        masterfile_service.update_progress(75)
        assert masterfile_service.get_progress() == 75
    
    def test_progress_without_callback(self, masterfile_service: MasterfileService):
        """Verifica progresso sem callback definido"""
        # Não deve lançar exceção
        masterfile_service.update_progress(50)
        assert masterfile_service.current_progress == 50
    
    @pytest.mark.parametrize("progress_value", [0, 25, 50, 75, 100])
    def test_valid_progress_values(
        self, 
        masterfile_service: MasterfileService,
        progress_value: int
    ):
        """Verifica valores válidos de progresso"""
        masterfile_service.update_progress(progress_value)
        assert masterfile_service.current_progress == progress_value


class TestMasterfileServiceCreateMasterfiles:
    """Testes de criação de masterfiles"""
    
    def test_create_masterfiles_validates_empty_path(
        self, 
        masterfile_service: MasterfileService
    ):
        """Verifica validação de path vazio ao criar"""
        result = masterfile_service.create_masterfiles(
            path_excel="",
            inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.success is False
        assert result.status == StatusType.ERROR
        assert len(result.errors) > 0
    
    def test_create_masterfiles_validates_empty_inventory(
        self, 
        masterfile_service: MasterfileService
    ):
        """Verifica validação de inventory vazio ao criar"""
        result = masterfile_service.create_masterfiles(
            path_excel="test.xlsx",
            inventory_names=[],
            db_type="oracle"
        )
        
        assert result.success is False
        assert result.status == StatusType.ERROR
        assert len(result.errors) > 0
    
    def test_create_masterfiles_with_valid_inputs_and_mock(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        output_directory: str,
        mock_masterfile_creator
    ):
        """Verifica criação com inputs válidos usando mock"""
        result = masterfile_service.create_masterfiles(
            path_excel=sample_excel_file,
            inventory_names=["INV_A", "INV_B"],
            db_type="oracle",
            output_path=output_directory
        )
        
        # Com mock, deve ter sucesso
        assert result.success is True
        assert result.status == StatusType.SUCCESS
        assert result.output_path == output_directory
    
    def test_create_masterfiles_normalizes_postgres_db_type(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        output_directory: str,
        mock_masterfile_creator
    ):
        """Verifica normalização de 'postgresql' para 'postgres'"""
        result = masterfile_service.create_masterfiles(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="postgresql",
            output_path=output_directory
        )
        
        assert result.success is True
    
    def test_create_masterfiles_handles_exception(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        output_directory: str
    ):
        """Verifica tratamento de exceção"""
        with patch(
            'src.services.masterfile_service.MasterfileCreator',
            side_effect=Exception("Test error")
        ):
            result = masterfile_service.create_masterfiles(
                path_excel=sample_excel_file,
                inventory_names=["INV_A"],
                db_type="oracle",
                output_path=output_directory
            )
            
            assert result.success is False
            assert "Test error" in result.message or "erro" in result.message.lower()
    
    def test_create_masterfiles_updates_progress(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str,
        output_directory: str,
        mock_masterfile_creator
    ):
        """Verifica atualização de progresso durante criação"""
        progress_values = []
        
        def track_progress(progress: int):
            progress_values.append(progress)
        
        # Simula callback de progresso no mock
        def simulate_progress(callback):
            callback(25)
            callback(50)
            callback(75)
            callback(100)
            return True
        
        mock_instance = mock_masterfile_creator.return_value
        mock_instance.create_masterfiles.side_effect = simulate_progress
        
        result = masterfile_service.create_masterfiles(
            path_excel=sample_excel_file,
            inventory_names=["INV_A"],
            db_type="oracle",
            output_path=output_directory,
            progress_callback=track_progress
        )
        
        assert len(progress_values) >= 1


class TestMasterfileServiceEdgeCases:
    """Testes de casos de borda"""
    
    def test_very_long_inventory_list(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Verifica validação com lista muito grande de inventories"""
        long_list = [f"INV_{i}" for i in range(1000)]
        
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=long_list,
            db_type="oracle"
        )
        
        assert result.is_valid is True
        assert result.details["inventory_count"] == 1000
    
    def test_inventory_names_with_special_characters(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Verifica validação com caracteres especiais"""
        special_names = ["INV_TEST_1", "INV-TEST-2", "INV.TEST.3"]
        
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=special_names,
            db_type="oracle"
        )
        
        assert result.is_valid is True
    
    def test_db_type_case_insensitive(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Verifica que db_type é case-insensitive"""
        for db_type in ["ORACLE", "Oracle", "oracle", "POSTGRES", "Postgres"]:
            result = masterfile_service.validate_inputs(
                path_excel=sample_excel_file,
                inventory_names=["INV_A"],
                db_type=db_type
            )
            assert result.is_valid is True, f"Failed for db_type: {db_type}"
    
    def test_inventory_names_trimmed(
        self,
        masterfile_service: MasterfileService,
        sample_excel_file: str
    ):
        """Verifica que inventory names são trimados"""
        names_with_spaces = ["  INV_A  ", "\tINV_B\t", " INV_C "]
        
        result = masterfile_service.validate_inputs(
            path_excel=sample_excel_file,
            inventory_names=names_with_spaces,
            db_type="oracle"
        )
        
        assert result.is_valid is True
        assert result.details["inventory_count"] == 3
