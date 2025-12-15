"""
Custom Exceptions
Centralized exception definitions for the application
"""


class AutomationError(Exception):
    """Base exception for all automation errors"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AutomationError):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        self.field = field
        super().__init__(message, details)
    
    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        return result


class FileProcessingError(AutomationError):
    """Raised when file processing fails"""
    
    def __init__(self, message: str, file_path: str = None, details: dict = None):
        self.file_path = file_path
        super().__init__(message, details)
    
    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.file_path:
            result["file_path"] = self.file_path
        return result


class DuplicateError(AutomationError):
    """Raised when duplicate entries are found"""
    
    def __init__(self, message: str, duplicates: list = None, details: dict = None):
        self.duplicates = duplicates or []
        super().__init__(message, details)
    
    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.duplicates:
            result["duplicates"] = self.duplicates
        return result


class ConfigurationError(AutomationError):
    """Raised when configuration is invalid"""
    pass


class ExcelReadError(FileProcessingError):
    """Raised when Excel file cannot be read"""
    pass


class SheetNotFoundError(FileProcessingError):
    """Raised when required sheet is not found"""
    
    def __init__(self, message: str, sheet_name: str = None, details: dict = None):
        self.sheet_name = sheet_name
        super().__init__(message, details=details)


class OutputGenerationError(AutomationError):
    """Raised when output generation fails"""
    pass


class MissingElementsError(ValidationError):
    """Erro quando elementos esperados não são encontrados"""
    
    def __init__(self, missing, item_name="elemento"):
        self.missing = missing
        self.item_name = item_name
        
        sorted_elements = sorted(missing)
        elements_str = '\n'.join(str(e) for e in sorted_elements)
        message = f"{item_name.capitalize()}(s) não encontrado(s) no pack:\n{elements_str}"
        
        super().__init__(message, details={"missing": list(missing), "item_name": item_name})


class ProcessingError(AutomationError):
    """Erro durante processamento de dados"""
    pass


class ExcelProcessingError(FileProcessingError):
    """Erro ao processar arquivos Excel"""
    pass


class DatabaseConfigError(AutomationError):
    """Erro de configuração de banco de dados"""
    pass
