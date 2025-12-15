"""
Response Models
Pydantic schemas for API responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )


class ProcessResult(BaseResponse):
    """Result of a processing operation"""
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Processed data"
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="List of errors if any"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="List of warnings if any"
    )


class ValidationResult(BaseResponse):
    """Result of a validation operation"""
    is_valid: bool = Field(..., description="Validation status")
    errors: Optional[List[str]] = Field(
        default=None,
        description="Validation errors"
    )
    field_errors: Optional[Dict[str, str]] = Field(
        default=None,
        description="Field-specific errors"
    )


class FileGenerationResult(BaseResponse):
    """Result of file generation operation"""
    files_created: List[str] = Field(
        default_factory=list,
        description="List of created file paths"
    )
    total_files: int = Field(
        default=0,
        description="Total number of files created"
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Output directory path"
    )
    errors: Optional[List[str]] = Field(
        default=None,
        description="List of errors if any"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="List of warnings if any"
    )

    @classmethod
    def success_result(
        cls,
        message: str,
        files_created: List[str],
        output_path: str,
        warnings: List[str] = None
    ) -> "FileGenerationResult":
        """Factory method for successful result"""
        return cls(
            success=True,
            message=message,
            files_created=files_created,
            total_files=len(files_created),
            output_path=output_path,
            warnings=warnings
        )

    @classmethod
    def error_result(
        cls,
        message: str,
        errors: List[str],
        output_path: str = None
    ) -> "FileGenerationResult":
        """Factory method for error result"""
        return cls(
            success=False,
            message=message,
            files_created=[],
            total_files=0,
            output_path=output_path,
            errors=errors
        )


class JobResponse(BaseModel):
    """Response for async job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    output_path: Optional[str] = Field(
        default=None,
        description="Expected output path"
    )


class JobProgressResponse(BaseModel):
    """Response for job progress check"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    progress: int = Field(
        default=0,
        description="Progress percentage (0-100)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Current status message"
    )
    result: Optional[FileGenerationResult] = Field(
        default=None,
        description="Final result when completed"
    )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Service availability status"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = Field(default=False)
    message: str = Field(..., description="Error message")
    error: str = Field(..., description="Error type")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
