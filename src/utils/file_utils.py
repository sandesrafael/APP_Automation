"""
File Utilities
Common file operations
"""
import os
import shutil
from datetime import datetime
from typing import Optional


def create_output_folder(
    base_path: str,
    prefix: str,
    with_timestamp: bool = True
) -> str:
    """
    Create output folder with optional timestamp.
    
    Args:
        base_path: Base directory path
        prefix: Folder name prefix
        with_timestamp: Add timestamp to folder name
        
    Returns:
        Created folder path
    """
    if with_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{prefix}{timestamp}"
    else:
        folder_name = prefix
    
    full_path = os.path.join(base_path, folder_name)
    os.makedirs(full_path, exist_ok=True)
    
    return full_path


def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than max_age_hours.
    
    Args:
        directory: Directory to clean
        max_age_hours: Max age in hours
        
    Returns:
        Number of files deleted
    """
    if not os.path.exists(directory):
        return 0
    
    deleted_count = 0
    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_hours * 3600
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        try:
            item_age = current_time - os.path.getmtime(item_path)
            
            if item_age > max_age_seconds:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                deleted_count += 1
                
        except Exception:
            continue
    
    return deleted_count


def get_file_size(path: str) -> Optional[int]:
    """Get file size in bytes"""
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def safe_delete(path: str) -> bool:
    """Safely delete file or directory"""
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        return True
    except Exception:
        return False
