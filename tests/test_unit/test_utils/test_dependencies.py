# -*- coding: utf-8 -*-
"""Unit Tests for API Dependencies"""
import os
os.environ["TESTING"] = "1"  # Must be set before any src imports

import pytest
import tempfile

from src.api.dependencies import (
    TempFileManager,
    JobRegistry,
    get_settings_dep,
    get_masterfile_service,
    get_json_service,
    get_dbn_service,
    get_temp_file_manager
)
from src.services.masterfile_service import MasterfileService
from src.services.json_service import JsonService
from src.services.dbn_service import DBNService


class TestTempFileManager:
    """Testes para TempFileManager"""
    
    def test_init(self):
        """Verifica inicialização"""
        manager = TempFileManager()
        assert manager.temp_dir is None
        assert manager.temp_files == []
    
    def test_create_temp_dir(self):
        """Verifica criação de diretório temporário"""
        manager = TempFileManager()
        temp_dir = manager.create_temp_dir()
        
        try:
            assert temp_dir is not None
            assert os.path.exists(temp_dir)
            assert manager.temp_dir == temp_dir
        finally:
            manager.cleanup()
    
    def test_save_upload_file(self):
        """Verifica salvamento de arquivo de upload"""
        manager = TempFileManager()
        
        try:
            content = b"test file content"
            file_path = manager.save_upload_file(content, "test.txt")
            
            assert os.path.exists(file_path)
            assert file_path in manager.temp_files
            
            with open(file_path, 'rb') as f:
                assert f.read() == content
        finally:
            manager.cleanup()
    
    def test_save_upload_file_creates_temp_dir_if_needed(self):
        """Verifica criação automática de diretório"""
        manager = TempFileManager()
        
        try:
            assert manager.temp_dir is None
            
            manager.save_upload_file(b"content", "test.txt")
            
            assert manager.temp_dir is not None
            assert os.path.exists(manager.temp_dir)
        finally:
            manager.cleanup()
    
    def test_cleanup_removes_files_and_dir(self):
        """Verifica limpeza completa"""
        manager = TempFileManager()
        
        # Cria arquivos
        manager.save_upload_file(b"content1", "file1.txt")
        manager.save_upload_file(b"content2", "file2.txt")
        
        temp_dir = manager.temp_dir
        temp_files = list(manager.temp_files)
        
        # Verifica que existem
        assert os.path.exists(temp_dir)
        for f in temp_files:
            assert os.path.exists(f)
        
        # Limpa
        manager.cleanup()
        
        # Verifica que foram removidos
        assert not os.path.exists(temp_dir)
        assert manager.temp_dir is None
        assert manager.temp_files == []
    
    def test_cleanup_handles_nonexistent_dir(self):
        """Verifica cleanup com diretório já removido"""
        manager = TempFileManager()
        manager.temp_dir = "/nonexistent/path"
        
        # Não deve lançar exceção
        manager.cleanup()
        assert manager.temp_dir is None
    
    def test_multiple_files(self):
        """Verifica múltiplos arquivos"""
        manager = TempFileManager()
        
        try:
            files = []
            for i in range(5):
                path = manager.save_upload_file(
                    f"content_{i}".encode(),
                    f"file_{i}.txt"
                )
                files.append(path)
            
            assert len(manager.temp_files) == 5
            for f in files:
                assert os.path.exists(f)
        finally:
            manager.cleanup()


class TestJobRegistry:
    """Testes para JobRegistry"""
    
    def setup_method(self):
        """Limpa registry antes de cada teste"""
        JobRegistry._jobs.clear()
    
    def test_create_job(self):
        """Verifica criação de job"""
        job = JobRegistry.create_job("job_123", "/output/path")
        
        assert job["status"] == "pending"
        assert job["progress"] == 0
        assert job["message"] == "Job created"
        assert job["output_path"] == "/output/path"
        assert job["result"] is None
        assert job["error"] is None
    
    def test_create_job_without_output_path(self):
        """Verifica criação sem output_path"""
        job = JobRegistry.create_job("job_456")
        
        assert job["output_path"] is None
    
    def test_get_job(self):
        """Verifica recuperação de job"""
        JobRegistry.create_job("job_789")
        
        job = JobRegistry.get_job("job_789")
        
        assert job is not None
        assert job["status"] == "pending"
    
    def test_get_job_nonexistent(self):
        """Verifica recuperação de job inexistente"""
        job = JobRegistry.get_job("nonexistent")
        assert job is None
    
    def test_update_job(self):
        """Verifica atualização de job"""
        JobRegistry.create_job("job_update")
        
        updated = JobRegistry.update_job(
            "job_update",
            status="processing",
            progress=50,
            message="Halfway done"
        )
        
        assert updated["status"] == "processing"
        assert updated["progress"] == 50
        assert updated["message"] == "Halfway done"
    
    def test_update_job_nonexistent(self):
        """Verifica atualização de job inexistente"""
        result = JobRegistry.update_job("nonexistent", status="done")
        assert result is None
    
    def test_delete_job(self):
        """Verifica deleção de job"""
        JobRegistry.create_job("job_to_delete")
        
        result = JobRegistry.delete_job("job_to_delete")
        
        assert result is True
        assert JobRegistry.get_job("job_to_delete") is None
    
    def test_delete_job_nonexistent(self):
        """Verifica deleção de job inexistente"""
        result = JobRegistry.delete_job("nonexistent")
        assert result is False
    
    def test_multiple_jobs(self):
        """Verifica múltiplos jobs"""
        JobRegistry.create_job("job_1")
        JobRegistry.create_job("job_2")
        JobRegistry.create_job("job_3")
        
        assert JobRegistry.get_job("job_1") is not None
        assert JobRegistry.get_job("job_2") is not None
        assert JobRegistry.get_job("job_3") is not None
    
    def test_job_lifecycle(self):
        """Verifica ciclo de vida completo de um job"""
        # Criação
        job = JobRegistry.create_job("lifecycle_job", "/output")
        assert job["status"] == "pending"
        
        # Atualização para processando
        JobRegistry.update_job("lifecycle_job", status="processing", progress=25)
        job = JobRegistry.get_job("lifecycle_job")
        assert job["status"] == "processing"
        assert job["progress"] == 25
        
        # Atualização de progresso
        JobRegistry.update_job("lifecycle_job", progress=75)
        job = JobRegistry.get_job("lifecycle_job")
        assert job["progress"] == 75
        
        # Conclusão
        JobRegistry.update_job(
            "lifecycle_job",
            status="completed",
            progress=100,
            result={"files_created": 5}
        )
        job = JobRegistry.get_job("lifecycle_job")
        assert job["status"] == "completed"
        assert job["result"]["files_created"] == 5
        
        # Deleção
        JobRegistry.delete_job("lifecycle_job")
        assert JobRegistry.get_job("lifecycle_job") is None


class TestServiceDependencies:
    """Testes para dependências de serviços"""
    
    def test_get_masterfile_service(self):
        """Verifica obtenção de MasterfileService"""
        # Limpa cache
        get_masterfile_service.cache_clear()
        
        service = get_masterfile_service()
        
        assert service is not None
        assert isinstance(service, MasterfileService)
    
    def test_get_masterfile_service_cached(self):
        """Verifica que MasterfileService é cacheado"""
        get_masterfile_service.cache_clear()
        
        service1 = get_masterfile_service()
        service2 = get_masterfile_service()
        
        assert service1 is service2  # Mesma instância
    
    def test_get_json_service(self):
        """Verifica obtenção de JsonService"""
        get_json_service.cache_clear()
        
        service = get_json_service()
        
        assert service is not None
        assert isinstance(service, JsonService)
    
    def test_get_json_service_cached(self):
        """Verifica que JsonService é cacheado"""
        get_json_service.cache_clear()
        
        service1 = get_json_service()
        service2 = get_json_service()
        
        assert service1 is service2
    
    def test_get_dbn_service(self):
        """Verifica obtenção de DBNService"""
        get_dbn_service.cache_clear()
        
        service = get_dbn_service()
        
        assert service is not None
        assert isinstance(service, DBNService)
    
    def test_get_dbn_service_cached(self):
        """Verifica que DBNService é cacheado"""
        get_dbn_service.cache_clear()
        
        service1 = get_dbn_service()
        service2 = get_dbn_service()
        
        assert service1 is service2


class TestTempFileManagerDependency:
    """Testes para a dependência get_temp_file_manager"""
    
    def test_get_temp_file_manager_generator(self):
        """Verifica que é um generator"""
        gen = get_temp_file_manager()
        
        manager = next(gen)
        assert isinstance(manager, TempFileManager)
        
        # Simula uso
        manager.save_upload_file(b"test", "test.txt")
        temp_dir = manager.temp_dir
        
        # Finaliza generator (simula finally)
        try:
            next(gen)
        except StopIteration:
            pass
        
        # Deve ter sido limpo
        assert not os.path.exists(temp_dir)


class TestSettingsDependency:
    """Testes para dependência de settings"""
    
    def test_get_settings_dep(self):
        """Verifica obtenção de settings"""
        from src.core.config import Settings
        
        settings = get_settings_dep()
        
        assert settings is not None
        assert isinstance(settings, Settings)
