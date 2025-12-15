"""
API Dependencies
Dependency injection for FastAPI routes
"""
from functools import lru_cache
from typing import Generator
import os
import tempfile
import shutil

from src.core.config import get_settings, Settings
from src.services.masterfile_service import MasterfileService
from src.services.json_service import JsonService
from src.services.dbn_service import DBNService


# Settings dependency
def get_settings_dep() -> Settings:
    """Get application settings"""
    return get_settings()


# Service dependencies
@lru_cache()
def get_masterfile_service() -> MasterfileService:
    """Get MasterfileService instance (cached)"""
    return MasterfileService()


@lru_cache()
def get_json_service() -> JsonService:
    """Get JsonService instance (cached)"""
    return JsonService()


@lru_cache()
def get_dbn_service() -> DBNService:
    """Get DBNService instance (cached)"""
    return DBNService()


# File handling dependencies
class TempFileManager:
    """Context manager for temporary file handling"""
    
    def __init__(self):
        self.temp_dir = None
        self.temp_files = []
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir
    
    def save_upload_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to temp directory"""
        if not self.temp_dir:
            self.create_temp_dir()
        
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        self.temp_files.append(file_path)
        return file_path
    
    def cleanup(self):
        """Remove temporary files and directories"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.temp_dir = None
        self.temp_files = []


def get_temp_file_manager() -> Generator[TempFileManager, None, None]:
    """Dependency for temporary file management"""
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()


# Job registry for async operations
class JobRegistry:
    """In-memory registry for async job tracking"""
    
    _jobs: dict = {}
    
    @classmethod
    def create_job(cls, job_id: str, output_path: str = None) -> dict:
        """Create a new job entry"""
        cls._jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Job created",
            "output_path": output_path,
            "result": None,
            "error": None
        }
        return cls._jobs[job_id]
    
    @classmethod
    def update_job(cls, job_id: str, **kwargs) -> dict:
        """Update job entry"""
        if job_id in cls._jobs:
            cls._jobs[job_id].update(kwargs)
        return cls._jobs.get(job_id)
    
    @classmethod
    def get_job(cls, job_id: str) -> dict:
        """Get job entry"""
        return cls._jobs.get(job_id)
    
    @classmethod
    def delete_job(cls, job_id: str) -> bool:
        """Delete job entry"""
        if job_id in cls._jobs:
            del cls._jobs[job_id]
            return True
        return False


def get_job_registry() -> JobRegistry:
    """Get job registry instance"""
    return JobRegistry()
