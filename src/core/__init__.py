"""
Core module - Configurations, constants and exceptions
"""
from .config import get_settings, Settings
from .exceptions import (
    AutomationError,
    ValidationError,
    FileProcessingError,
    DuplicateError,
    ConfigurationError,
    MissingElementsError,
    ProcessingError,
    ExcelProcessingError,
    DatabaseConfigError,
    ExcelReadError,
    SheetNotFoundError,
    OutputGenerationError
)

__all__ = [
    "get_settings",
    "Settings",
    "AutomationError",
    "ValidationError",
    "FileProcessingError",
    "DuplicateError",
    "ConfigurationError",
    "MissingElementsError",
    "ProcessingError",
    "ExcelProcessingError",
    "DatabaseConfigError",
    "ExcelReadError",
    "SheetNotFoundError",
    "OutputGenerationError"
]
