"""
Request Models
Pydantic schemas for API request validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from src.core.constants import DatabaseType


class MasterfileCreateRequest(BaseModel):
    """Request model for creating masterfiles"""
    inventory_names: List[str] = Field(
        ...,
        description="List of inventory names to process",
        min_length=1
    )
    db_type: DatabaseType = Field(
        default=DatabaseType.POSTGRES,
        description="Target database type"
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Custom output path (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "inventory_names": ["INV_A", "INV_B"],
                "db_type": "postgres",
                "output_path": None
            }
        }


class JsonCreateRequest(BaseModel):
    """Request model for creating JSON files"""
    inventory_names: List[str] = Field(
        ...,
        description="List of inventory names to process",
        min_length=1
    )
    db_type: DatabaseType = Field(
        default=DatabaseType.ORACLE,
        description="Target database type"
    )
    is_parameter: bool = Field(
        default=True,
        description="Include parameter data"
    )
    is_enrichment: bool = Field(
        default=False,
        description="Include enrichment data"
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Custom output path (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "inventory_names": ["INV_A", "INV_B"],
                "db_type": "oracle",
                "is_parameter": True,
                "is_enrichment": False
            }
        }


class DBN0CreateRequest(BaseModel):
    """Request model for creating DBN0 files"""
    dbn_names: List[str] = Field(
        ...,
        description="List of DBN names",
        min_length=1
    )
    output_path: str = Field(
        ...,
        description="Output directory path"
    )
    schema: str = Field(
        default="PUBLIC",
        description="Database schema"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dbn_names": ["DBN0_A", "DBN0_B"],
                "output_path": "/output/dbn0",
                "schema": "PUBLIC"
            }
        }


class DBN1CreateRequest(BaseModel):
    """Request model for creating DBN1 files"""
    dbn_names: List[str] = Field(
        ...,
        description="List of DBN names",
        min_length=1
    )
    output_path: str = Field(
        ...,
        description="Output directory path"
    )
    schema: str = Field(
        default="PUBLIC",
        description="Database schema"
    )
    classe: str = Field(
        ...,
        description="Logic class name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dbn_names": ["DBN1_A", "DBN1_B"],
                "output_path": "/output/dbn1",
                "schema": "PUBLIC",
                "classe": "MyLogicClass"
            }
        }


class DBN1RenameRequest(BaseModel):
    """Request model for renaming DBN1 files"""
    path: str = Field(
        ...,
        description="Directory path containing DBN1 files to rename"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/output/dbn1"
            }
        }
