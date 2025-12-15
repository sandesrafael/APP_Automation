"""
Modelos de resposta padronizados para desacoplar lógica de UI
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum


class StatusType(Enum):
    """Tipos de status para respostas"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Resultado de validação de inputs"""
    is_valid: bool
    message: str
    status: StatusType
    details: Optional[Dict[str, Any]] = None
    
    def __bool__(self):
        """Permite usar if validation_result:"""
        return self.is_valid


@dataclass
class ProcessResult:
    """Resultado de processamento genérico"""
    success: bool
    message: str
    status: StatusType
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None
    progress: int = 100
    
    def __bool__(self):
        """Permite usar if result:"""
        return self.success
    
    def add_error(self, error: str):
        """Adiciona um erro à lista"""
        if self.errors is None:
            self.errors = []
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Adiciona um aviso à lista"""
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)


@dataclass
class FileGenerationResult(ProcessResult):
    """Resultado específico para geração de arquivos"""
    files_created: List[str] = field(default_factory=list)
    files_failed: List[str] = field(default_factory=list)
    total_files: int = 0
    output_path: Optional[str] = None
    
    def add_created_file(self, filepath: str):
        """Adiciona arquivo criado com sucesso"""
        self.files_created.append(filepath)
        self.total_files += 1
    
    def add_failed_file(self, filepath: str, error: str):
        """Adiciona arquivo que falhou"""
        self.files_failed.append(filepath)
        self.add_error(f"{filepath}: {error}")
