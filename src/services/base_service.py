"""
Base Service
Abstract base class for all services
"""
from abc import ABC
from typing import Callable, Optional
import logging

from src.models.responses import FileGenerationResult


class BaseService(ABC):
    """
    Base service with common functionality.
    All services should inherit from this class.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._progress_callback: Optional[Callable[[int, str], None]] = None
        self._current_progress: int = 0
    
    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Set callback for progress updates"""
        self._progress_callback = callback
    
    def update_progress(self, progress: int, message: str = "") -> None:
        """Update current progress"""
        self._current_progress = progress
        self.logger.info(f"Progress: {progress}% - {message}")
        
        if self._progress_callback:
            self._progress_callback(progress, message)
    
    @property
    def current_progress(self) -> int:
        """Get current progress value"""
        return self._current_progress
    
    def _success_result(
        self,
        message: str,
        files_created: list,
        output_path: str,
        warnings: list = None
    ) -> FileGenerationResult:
        """Create success result"""
        return FileGenerationResult.success_result(
            message=message,
            files_created=files_created,
            output_path=output_path,
            warnings=warnings
        )
    
    def _error_result(
        self,
        message: str,
        errors: list,
        output_path: str = None
    ) -> FileGenerationResult:
        """Create error result"""
        return FileGenerationResult.error_result(
            message=message,
            errors=errors,
            output_path=output_path
        )
