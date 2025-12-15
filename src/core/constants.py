"""
Application Constants
Centralized constants used across the application
"""
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""
    ORACLE = "oracle"
    POSTGRES = "postgres"


class FileType(str, Enum):
    """Supported file types"""
    EXCEL = "xlsx"
    JSON = "json"
    SQL = "sql"
    TXT = "txt"


class SheetConstants:
    """Excel sheet constants"""
    HEADER_ROW = 2  # 0-indexed, headers on row 3 (1-indexed)
    DATA_START_ROW = 3
    
    # Required sheets
    REQUIRED_SHEETS = ["INVENTORY", "PARAMETER", "ENRICHMENT"]
    
    # Column mappings
    INVENTORY_COLUMNS = {
        "name": "INVENTORY_NAME",
        "description": "DESCRIPTION",
        "type": "TYPE"
    }


class OutputFolders:
    """Output folder naming patterns"""
    MASTERFILES_PREFIX = "MASTERFILES_"
    JSON_PREFIX = "JSON_"
    DBN_PREFIX = "DBN_"


class APIRoutes:
    """API route prefixes"""
    MASTERFILES = "/api/masterfiles"
    JSONS = "/api/jsons"
    DBN = "/api/dbn"
    HEALTH = "/health"


class JobStatus(str, Enum):
    """Async job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
