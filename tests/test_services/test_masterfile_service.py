"""
Masterfile Service Tests
"""
import pytest
from src.services.masterfile_service import MasterfileService
from src.core.exceptions import ValidationError


class TestMasterfileService:
    """Tests for MasterfileService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = MasterfileService()
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert self.service is not None
        assert self.service.current_progress == 0
    
    def test_create_masterfiles_validates_empty_path(self):
        """Test validation rejects empty path"""
        result = self.service.create_masterfiles(
            path_excel="",
                inventory_names=["INV_A"],
            db_type="oracle"
        )
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_create_masterfiles_validates_empty_inventory(self):
        """Test validation rejects empty inventory list"""
        result = self.service.create_masterfiles(
            path_excel="test.xlsx",
            inventory_names=[],
            db_type="oracle"
        )
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_progress_callback(self):
        """Test progress is updated correctly"""
        self.service.update_progress(50)
        
        assert self.service.current_progress == 50
        assert self.service.get_progress() == 50
