# -*- coding: utf-8 -*-
"""Unit Tests for DBNService"""
import os
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.services.dbn_service import DBNService
from src.utils.response_models import StatusType, ValidationResult, FileGenerationResult


class TestDBNServiceInit:
    """Testes de inicialização do DBNService"""
    
    def test_service_initialization(self, dbn_service: DBNService):
        """Verifica inicialização correta do serviço"""
        assert dbn_service is not None
        assert dbn_service.current_progress == 0
    
    def test_service_has_required_methods(self, dbn_service: DBNService):
        """Verifica existência de métodos essenciais"""
        assert hasattr(dbn_service, 'validate_inputs')
        assert hasattr(dbn_service, 'create_dbn_model')
        assert hasattr(dbn_service, 'get_progress')
    
    def test_multiple_instances_are_independent(self):
        """Verifica que múltiplas instâncias são independentes"""
        service1 = DBNService()
        service2 = DBNService()
        
        service1.current_progress = 75
        
        assert service2.current_progress == 0


class TestDBNServiceValidation:
    """Testes de validação de inputs"""
    
    def test_validate_empty_dbn_names(
        self, 
        dbn_service: DBNService,
        output_directory: str
    ):
        """Valida rejeição de lista de nomes vazia"""
        result = dbn_service.validate_inputs(
            dbn_names=[],
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
        assert "dbn" in result.message.lower() or "nome" in result.message.lower()
    
    def test_validate_none_dbn_names(
        self, 
        dbn_service: DBNService,
        output_directory: str
    ):
        """Valida rejeição de None para dbn_names"""
        result = dbn_service.validate_inputs(
            dbn_names=None,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.is_valid is False
        assert result.status == StatusType.ERROR
    
    def test_validate_empty_output_path(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list
    ):
        """Valida rejeição de output_path vazio"""
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path="",
            dbn_type="DBN0"
        )
        
        assert result.is_valid is False
        assert "saída" in result.message.lower() or "path" in result.message.lower()
    
    def test_validate_invalid_dbn_type(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Valida rejeição de tipo DBN inválido"""
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN99"
        )
        
        assert result.is_valid is False
        assert "dbn0" in result.message.lower() or "dbn1" in result.message.lower()
    
    @pytest.mark.parametrize("valid_type", ["DBN0", "DBN1"])
    def test_validate_valid_dbn_types(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        valid_type: str
    ):
        """Valida aceitação de tipos DBN válidos"""
        # Para DBN1, precisa de classe
        classe = "TEST_CLASS" if valid_type == "DBN1" else None
        
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema="TEST_SCHEMA",
            output_path=output_directory,
            dbn_type=valid_type,
            classe=classe
        )
        
        assert result.is_valid is True
        assert result.status == StatusType.SUCCESS
    
    def test_validate_dbn1_requires_classe(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Valida que DBN1 requer classe"""
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN1",
            classe=None
        )
        
        assert result.is_valid is False
        assert "classe" in result.message.lower()
    
    def test_validate_dbn1_with_classe(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Valida DBN1 com classe fornecida"""
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN1",
            classe="MY_CLASS"
        )
        
        assert result.is_valid is True
    
    def test_validate_dbn0_without_classe(
        self, 
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Valida DBN0 não requer classe"""
        result = dbn_service.validate_inputs(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0",
            classe=None
        )
        
        assert result.is_valid is True


class TestDBNServiceProgress:
    """Testes de progresso"""
    
    def test_initial_progress_is_zero(self, dbn_service: DBNService):
        """Verifica progresso inicial em zero"""
        assert dbn_service.get_progress() == 0
    
    def test_progress_is_updated(self, dbn_service: DBNService):
        """Verifica atualização de progresso"""
        dbn_service.current_progress = 50
        assert dbn_service.get_progress() == 50


class TestDBNServiceCreateModel:
    """Testes de criação de modelos DBN"""
    
    def test_create_dbn0_validates_inputs(
        self, 
        dbn_service: DBNService
    ):
        """Verifica validação antes de criar DBN0"""
        result = dbn_service.create_dbn_model(
            dbn_names=[],
            schema=None,
            output_path="/tmp/output",
            dbn_type="DBN0"
        )
        
        assert result.success is False
        assert result.status == StatusType.ERROR
    
    def test_create_dbn0_with_mock(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação de DBN0 com mock"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema="TEST_SCHEMA",
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.success is True
        assert result.status == StatusType.SUCCESS
        assert "DBN0" in result.message
        assert result.total_files == 1
    
    def test_create_dbn1_with_mock(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação de DBN1 com mock"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema="TEST_SCHEMA",
            output_path=output_directory,
            dbn_type="DBN1",
            classe="MY_TEST_CLASS"
        )
        
        assert result.success is True
        assert "DBN1" in result.message
    
    def test_create_dbn_handles_exception(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Verifica tratamento de exceção"""
        with patch(
            'src.services.dbn_service.DBNModel.modelo_exportacao',
            side_effect=Exception("Test DBN error")
        ):
            result = dbn_service.create_dbn_model(
                dbn_names=sample_dbn_names,
                schema=None,
                output_path=output_directory,
                dbn_type="DBN0"
            )
            
            assert result.success is False
            assert "Test DBN error" in result.message
    
    def test_create_dbn_returns_output_path(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica retorno do output_path"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.output_path == output_directory
    
    def test_create_dbn_updates_progress(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica atualização de progresso"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        # Após sucesso, progresso deve ser 100
        assert dbn_service.current_progress == 100
    
    def test_create_dbn_with_schema_none(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação com schema None"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.success is True
    
    def test_create_dbn_model_failure(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str
    ):
        """Verifica tratamento de falha do modelo"""
        with patch(
            'src.services.dbn_service.DBNModel.modelo_exportacao',
            return_value=False
        ):
            result = dbn_service.create_dbn_model(
                dbn_names=sample_dbn_names,
                schema=None,
                output_path=output_directory,
                dbn_type="DBN0"
            )
            
            assert result.success is False
            assert result.status == StatusType.ERROR


class TestDBNServiceEdgeCases:
    """Testes de casos de borda"""
    
    def test_large_dbn_names_list(
        self,
        dbn_service: DBNService,
        output_directory: str
    ):
        """Verifica validação com lista grande"""
        large_list = [f"DBN_{i:04d}" for i in range(100)]
        
        result = dbn_service.validate_inputs(
            dbn_names=large_list,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.is_valid is True
    
    def test_dbn_names_with_special_characters(
        self,
        dbn_service: DBNService,
        output_directory: str
    ):
        """Verifica validação com caracteres especiais"""
        special_names = ["DBN_TEST-1", "DBN.TEST.2", "DBN_TEST_3"]
        
        result = dbn_service.validate_inputs(
            dbn_names=special_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.is_valid is True
    
    def test_single_dbn_name(
        self,
        dbn_service: DBNService,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação com apenas um nome"""
        result = dbn_service.create_dbn_model(
            dbn_names=["SINGLE_DBN"],
            schema=None,
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.success is True
    
    def test_schema_with_special_characters(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação com schema contendo caracteres especiais"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema="SCHEMA_TEST-1",
            output_path=output_directory,
            dbn_type="DBN0"
        )
        
        assert result.success is True
    
    def test_classe_with_spaces(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model
    ):
        """Verifica criação de DBN1 com classe contendo espaços"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type="DBN1",
            classe="MY TEST CLASS"
        )
        
        assert result.success is True
    
    @pytest.mark.parametrize("dbn_type,classe", [
        ("DBN0", None),
        ("DBN0", "IGNORED_CLASS"),
        ("DBN1", "REQUIRED_CLASS"),
    ])
    def test_dbn_type_and_classe_combinations(
        self,
        dbn_service: DBNService,
        sample_dbn_names: list,
        output_directory: str,
        mock_dbn_model,
        dbn_type: str,
        classe: str
    ):
        """Verifica combinações válidas de tipo e classe"""
        result = dbn_service.create_dbn_model(
            dbn_names=sample_dbn_names,
            schema=None,
            output_path=output_directory,
            dbn_type=dbn_type,
            classe=classe
        )
        
        assert result.success is True
