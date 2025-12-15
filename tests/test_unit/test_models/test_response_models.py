# -*- coding: utf-8 -*-
"""Unit Tests for Response Models"""
import os
os.environ["TESTING"] = "1"

import pytest
from dataclasses import fields

from src.utils.response_models import (
    StatusType,
    ValidationResult,
    ProcessResult,
    FileGenerationResult
)


class TestStatusType:
    """Testes para o enum StatusType"""
    
    def test_status_type_values(self):
        """Verifica valores do enum"""
        assert StatusType.SUCCESS.value == "success"
        assert StatusType.ERROR.value == "error"
        assert StatusType.WARNING.value == "warning"
        assert StatusType.INFO.value == "info"
    
    def test_status_type_has_all_expected_members(self):
        """Verifica membros esperados"""
        expected_members = {"SUCCESS", "ERROR", "WARNING", "INFO"}
        actual_members = {member.name for member in StatusType}
        assert actual_members == expected_members
    
    def test_status_type_comparison(self):
        """Verifica comparação entre status"""
        assert StatusType.SUCCESS == StatusType.SUCCESS
        assert StatusType.SUCCESS != StatusType.ERROR


class TestValidationResult:
    """Testes para ValidationResult"""
    
    def test_validation_result_creation_success(self):
        """Verifica criação de resultado de validação bem-sucedido"""
        result = ValidationResult(
            is_valid=True,
            message="Validação OK",
            status=StatusType.SUCCESS
        )
        
        assert result.is_valid is True
        assert result.message == "Validação OK"
        assert result.status == StatusType.SUCCESS
        assert result.details is None
    
    def test_validation_result_creation_failure(self):
        """Verifica criação de resultado de validação com falha"""
        result = ValidationResult(
            is_valid=False,
            message="Campo obrigatório",
            status=StatusType.ERROR,
            details={"field": "name"}
        )
        
        assert result.is_valid is False
        assert result.message == "Campo obrigatório"
        assert result.status == StatusType.ERROR
        assert result.details == {"field": "name"}
    
    def test_validation_result_bool_true(self):
        """Verifica conversão para bool quando válido"""
        result = ValidationResult(
            is_valid=True,
            message="OK",
            status=StatusType.SUCCESS
        )
        
        assert bool(result) is True
        # Uso em if
        if result:
            passed = True
        else:
            passed = False
        assert passed is True
    
    def test_validation_result_bool_false(self):
        """Verifica conversão para bool quando inválido"""
        result = ValidationResult(
            is_valid=False,
            message="Error",
            status=StatusType.ERROR
        )
        
        assert bool(result) is False
    
    def test_validation_result_with_details(self):
        """Verifica resultado com detalhes complexos"""
        details = {
            "duplicates": ["INV_A", "INV_B"],
            "count": 2,
            "nested": {"key": "value"}
        }
        result = ValidationResult(
            is_valid=False,
            message="Duplicatas encontradas",
            status=StatusType.ERROR,
            details=details
        )
        
        assert result.details == details
        assert result.details["count"] == 2


class TestProcessResult:
    """Testes para ProcessResult"""
    
    def test_process_result_creation_success(self):
        """Verifica criação de resultado de processo bem-sucedido"""
        result = ProcessResult(
            success=True,
            message="Processamento concluído",
            status=StatusType.SUCCESS
        )
        
        assert result.success is True
        assert result.message == "Processamento concluído"
        assert result.status == StatusType.SUCCESS
        assert result.progress == 100  # Default
    
    def test_process_result_creation_failure(self):
        """Verifica criação de resultado de processo com falha"""
        result = ProcessResult(
            success=False,
            message="Erro no processamento",
            status=StatusType.ERROR,
            errors=["Erro 1", "Erro 2"]
        )
        
        assert result.success is False
        assert len(result.errors) == 2
    
    def test_process_result_bool_true(self):
        """Verifica conversão para bool quando sucesso"""
        result = ProcessResult(
            success=True,
            message="OK",
            status=StatusType.SUCCESS
        )
        
        assert bool(result) is True
    
    def test_process_result_bool_false(self):
        """Verifica conversão para bool quando falha"""
        result = ProcessResult(
            success=False,
            message="Error",
            status=StatusType.ERROR
        )
        
        assert bool(result) is False
    
    def test_process_result_add_error(self):
        """Verifica adição de erro"""
        result = ProcessResult(
            success=False,
            message="Erro",
            status=StatusType.ERROR
        )
        
        assert result.errors is None
        
        result.add_error("Primeiro erro")
        assert result.errors == ["Primeiro erro"]
        
        result.add_error("Segundo erro")
        assert result.errors == ["Primeiro erro", "Segundo erro"]
    
    def test_process_result_add_warning(self):
        """Verifica adição de warning"""
        result = ProcessResult(
            success=True,
            message="OK",
            status=StatusType.SUCCESS
        )
        
        assert result.warnings is None
        
        result.add_warning("Aviso 1")
        assert result.warnings == ["Aviso 1"]
        
        result.add_warning("Aviso 2")
        assert result.warnings == ["Aviso 1", "Aviso 2"]
    
    def test_process_result_with_data(self):
        """Verifica resultado com dados adicionais"""
        result = ProcessResult(
            success=True,
            message="OK",
            status=StatusType.SUCCESS,
            data={"key": "value", "count": 10}
        )
        
        assert result.data["key"] == "value"
        assert result.data["count"] == 10
    
    def test_process_result_custom_progress(self):
        """Verifica progresso customizado"""
        result = ProcessResult(
            success=False,
            message="Em andamento",
            status=StatusType.INFO,
            progress=75
        )
        
        assert result.progress == 75


class TestFileGenerationResult:
    """Testes para FileGenerationResult"""
    
    def test_file_generation_result_creation(self):
        """Verifica criação básica"""
        result = FileGenerationResult(
            success=True,
            message="Arquivos criados",
            status=StatusType.SUCCESS
        )
        
        assert result.success is True
        assert result.files_created == []  # Default
        assert result.files_failed == []  # Default
        assert result.total_files == 0  # Default
        assert result.output_path is None  # Default
    
    def test_file_generation_result_with_files(self):
        """Verifica resultado com arquivos"""
        result = FileGenerationResult(
            success=True,
            message="Arquivos criados",
            status=StatusType.SUCCESS,
            files_created=["file1.txt", "file2.txt"],
            total_files=2,
            output_path="/tmp/output"
        )
        
        assert len(result.files_created) == 2
        assert result.total_files == 2
        assert result.output_path == "/tmp/output"
    
    def test_file_generation_result_add_created_file(self):
        """Verifica adição de arquivo criado"""
        result = FileGenerationResult(
            success=True,
            message="OK",
            status=StatusType.SUCCESS
        )
        
        result.add_created_file("/path/to/file1.txt")
        
        assert result.files_created == ["/path/to/file1.txt"]
        assert result.total_files == 1
        
        result.add_created_file("/path/to/file2.txt")
        
        assert len(result.files_created) == 2
        assert result.total_files == 2
    
    def test_file_generation_result_add_failed_file(self):
        """Verifica adição de arquivo com falha"""
        result = FileGenerationResult(
            success=False,
            message="Alguns arquivos falharam",
            status=StatusType.WARNING
        )
        
        result.add_failed_file("/path/to/failed.txt", "Erro de permissão")
        
        assert result.files_failed == ["/path/to/failed.txt"]
        assert result.errors is not None
        assert "/path/to/failed.txt: Erro de permissão" in result.errors
    
    def test_file_generation_result_inherits_process_result(self):
        """Verifica herança de ProcessResult"""
        result = FileGenerationResult(
            success=True,
            message="OK",
            status=StatusType.SUCCESS
        )
        
        # Deve ter métodos herdados
        assert hasattr(result, 'add_error')
        assert hasattr(result, 'add_warning')
        
        # Deve funcionar
        result.add_error("Test error")
        result.add_warning("Test warning")
        
        assert result.errors == ["Test error"]
        assert result.warnings == ["Test warning"]
    
    def test_file_generation_result_mixed_success_and_failure(self):
        """Verifica resultado misto (alguns sucesso, alguns falha)"""
        result = FileGenerationResult(
            success=True,
            message="Parcialmente concluído",
            status=StatusType.WARNING
        )
        
        # Adiciona arquivos bem-sucedidos
        result.add_created_file("success1.txt")
        result.add_created_file("success2.txt")
        
        # Adiciona arquivos com falha
        result.add_failed_file("failed1.txt", "Erro 1")
        result.add_failed_file("failed2.txt", "Erro 2")
        
        assert len(result.files_created) == 2
        assert len(result.files_failed) == 2
        assert result.total_files == 2  # Só conta criados
        assert len(result.errors) == 2
    
    def test_file_generation_result_full_workflow(self):
        """Teste de fluxo completo de uso"""
        result = FileGenerationResult(
            success=True,
            message="Iniciando processamento",
            status=StatusType.INFO,
            output_path="/output/path"
        )
        
        # Simula processamento de arquivos
        files_to_process = [
            ("file1.txt", True),
            ("file2.txt", True),
            ("file3.txt", False),
            ("file4.txt", True),
        ]
        
        for filename, success in files_to_process:
            if success:
                result.add_created_file(f"/output/path/{filename}")
            else:
                result.add_failed_file(f"/output/path/{filename}", "Erro no arquivo")
        
        # Verifica estado final
        assert result.total_files == 3
        assert len(result.files_failed) == 1
        assert len(result.errors) == 1


class TestDataclassFields:
    """Testes de estrutura dos dataclasses"""
    
    def test_validation_result_fields(self):
        """Verifica campos de ValidationResult"""
        field_names = {f.name for f in fields(ValidationResult)}
        expected = {"is_valid", "message", "status", "details"}
        assert field_names == expected
    
    def test_process_result_fields(self):
        """Verifica campos de ProcessResult"""
        field_names = {f.name for f in fields(ProcessResult)}
        expected = {
            "success", "message", "status", "data",
            "errors", "warnings", "details", "progress"
        }
        assert field_names == expected
    
    def test_file_generation_result_fields(self):
        """Verifica campos de FileGenerationResult"""
        field_names = {f.name for f in fields(FileGenerationResult)}
        # Deve incluir campos herdados + próprios
        assert "files_created" in field_names
        assert "files_failed" in field_names
        assert "total_files" in field_names
        assert "output_path" in field_names
        # E também os herdados
        assert "success" in field_names
        assert "message" in field_names
