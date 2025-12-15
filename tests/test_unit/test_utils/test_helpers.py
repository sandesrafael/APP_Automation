# -*- coding: utf-8 -*-
"""Unit Tests for Helpers"""
import os
os.environ["TESTING"] = "1"

import pytest
import tempfile
from unittest.mock import Mock, patch

from src.utils.helpers import (
    ValidationHelper,
    TextHelper,
    PathHelper,
    ProgressHelper,
    DatabaseHelper,
    FormHelper,
    BaseService,
    AlertsAdapter
)


class TestValidationHelper:
    """Testes para ValidationHelper"""
    
    # ==================== check_duplicates ====================
    
    def test_check_duplicates_no_duplicates(self):
        """Verifica lista sem duplicatas"""
        has_dups, dups = ValidationHelper.check_duplicates(["a", "b", "c"])
        assert has_dups is False
        assert dups == []
    
    def test_check_duplicates_with_duplicates(self):
        """Verifica lista com duplicatas"""
        has_dups, dups = ValidationHelper.check_duplicates(["a", "b", "a", "c", "b"])
        assert has_dups is True
        assert set(dups) == {"a", "b"}
    
    def test_check_duplicates_empty_list(self):
        """Verifica lista vazia"""
        has_dups, dups = ValidationHelper.check_duplicates([])
        assert has_dups is False
        assert dups == []
    
    def test_check_duplicates_single_item(self):
        """Verifica lista com um item"""
        has_dups, dups = ValidationHelper.check_duplicates(["only_one"])
        assert has_dups is False
        assert dups == []
    
    def test_check_duplicates_all_same(self):
        """Verifica lista com todos iguais"""
        has_dups, dups = ValidationHelper.check_duplicates(["x", "x", "x"])
        assert has_dups is True
        assert dups == ["x"]
    
    # ==================== format_duplicate_message ====================
    
    def test_format_duplicate_message_single(self):
        """Formata mensagem para uma duplicata"""
        msg = ValidationHelper.format_duplicate_message(["item1"], "Inventory Name")
        assert "Inventory Name" in msg
        assert "item1" in msg
        assert "inserido mais de uma vez" in msg
    
    def test_format_duplicate_message_multiple(self):
        """Formata mensagem para múltiplas duplicatas"""
        msg = ValidationHelper.format_duplicate_message(["item1", "item2"], "elemento")
        assert "elementos" in msg  # Plural
        assert "item1" in msg
        assert "item2" in msg
    
    # ==================== check_missing_elements ====================
    
    def test_check_missing_elements_none_missing(self):
        """Verifica sem elementos faltando"""
        has_missing, missing = ValidationHelper.check_missing_elements(
            provided_items=["a", "b"],
            available_items=["a", "b", "c"]
        )
        assert has_missing is False
        assert missing == set()
    
    def test_check_missing_elements_with_missing(self):
        """Verifica com elementos faltando"""
        has_missing, missing = ValidationHelper.check_missing_elements(
            provided_items=["a", "b", "x", "y"],
            available_items=["a", "b", "c"]
        )
        assert has_missing is True
        assert missing == {"x", "y"}
    
    def test_check_missing_elements_all_missing(self):
        """Verifica quando todos estão faltando"""
        has_missing, missing = ValidationHelper.check_missing_elements(
            provided_items=["x", "y"],
            available_items=["a", "b"]
        )
        assert has_missing is True
        assert missing == {"x", "y"}
    
    # ==================== format_missing_message ====================
    
    def test_format_missing_message(self):
        """Formata mensagem de elementos faltando"""
        msg = ValidationHelper.format_missing_message({"item1", "item2"}, "Inventory")
        assert "Inventory" in msg
        assert "não encontrado" in msg
    
    # ==================== is_valid_excel_file ====================
    
    @pytest.mark.parametrize("filename,expected", [
        ("file.xlsx", True),
        ("file.xls", True),
        ("file.XLSX", True),
        ("file.XLS", True),
        ("file.csv", False),
        ("file.txt", False),
        ("", False),
        (None, False),
    ])
    def test_is_valid_excel_file(self, filename, expected):
        """Verifica validação de arquivo Excel"""
        result = ValidationHelper.is_valid_excel_file(filename)
        assert result == expected
    
    # ==================== is_valid_path ====================
    
    def test_is_valid_path_exists(self, temp_directory):
        """Verifica path existente"""
        assert ValidationHelper.is_valid_path(temp_directory) is True
    
    def test_is_valid_path_not_exists(self):
        """Verifica path inexistente"""
        assert ValidationHelper.is_valid_path("/nonexistent/path") is False
    
    def test_is_valid_path_empty(self):
        """Verifica path vazio"""
        assert ValidationHelper.is_valid_path("") is False
    
    def test_is_valid_path_none(self):
        """Verifica path None"""
        assert ValidationHelper.is_valid_path(None) is False
    
    # ==================== is_non_empty_list ====================
    
    @pytest.mark.parametrize("items,expected", [
        (["a", "b"], True),
        (["single"], True),
        ([], False),
        (None, False),
        ("not a list", False),
        (123, False),
    ])
    def test_is_non_empty_list(self, items, expected):
        """Verifica lista não vazia"""
        result = ValidationHelper.is_non_empty_list(items)
        assert result == expected
    
    # ==================== validate_inventory_names ====================
    
    def test_validate_inventory_names_cleans_whitespace(self):
        """Verifica limpeza de espaços"""
        result = ValidationHelper.validate_inventory_names(["  item1  ", "\titem2\t"])
        assert result == ["item1", "item2"]
    
    def test_validate_inventory_names_removes_empty(self):
        """Verifica remoção de itens vazios"""
        result = ValidationHelper.validate_inventory_names(["item1", "", "  ", "item2"])
        assert result == ["item1", "item2"]
    
    def test_validate_inventory_names_empty_list(self):
        """Verifica lista vazia"""
        result = ValidationHelper.validate_inventory_names([])
        assert result == []
    
    def test_validate_inventory_names_none(self):
        """Verifica None"""
        result = ValidationHelper.validate_inventory_names(None)
        assert result == []


class TestTextHelper:
    """Testes para TextHelper"""
    
    # ==================== processar_descricao ====================
    
    def test_processar_descricao_removes_quotes(self):
        """Remove aspas simples"""
        result = TextHelper.processar_descricao("It's a test")
        assert result == "Its a test"
    
    def test_processar_descricao_no_quotes(self):
        """Mantém texto sem aspas"""
        result = TextHelper.processar_descricao("No quotes here")
        assert result == "No quotes here"
    
    def test_processar_descricao_not_string(self):
        """Retorna não-string inalterado"""
        result = TextHelper.processar_descricao(123)
        assert result == 123
    
    # ==================== sanitize_filename ====================
    
    def test_sanitize_filename_removes_invalid_chars(self):
        """Remove caracteres inválidos"""
        result = TextHelper.sanitize_filename('file<>:"/\\|?*name.txt')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_sanitize_filename_valid_chars(self):
        """Mantém caracteres válidos"""
        result = TextHelper.sanitize_filename("valid_filename-123.txt")
        assert result == "valid_filename-123.txt"
    
    # ==================== to_upper_snake_case ====================
    
    @pytest.mark.parametrize("input_text,expected", [
        ("hello world", "HELLO_WORLD"),
        ("  hello  world  ", "HELLO_WORLD"),
        ("already_snake", "ALREADY_SNAKE"),
        ("MixedCase", "MIXEDCASE"),
    ])
    def test_to_upper_snake_case(self, input_text, expected):
        """Converte para UPPER_SNAKE_CASE"""
        result = TextHelper.to_upper_snake_case(input_text)
        assert result == expected
    
    # ==================== truncate ====================
    
    def test_truncate_short_text(self):
        """Não trunca texto curto"""
        result = TextHelper.truncate("short", max_length=100)
        assert result == "short"
    
    def test_truncate_long_text(self):
        """Trunca texto longo"""
        long_text = "a" * 200
        result = TextHelper.truncate(long_text, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")
    
    def test_truncate_exact_length(self):
        """Não trunca texto com tamanho exato"""
        text = "a" * 100
        result = TextHelper.truncate(text, max_length=100)
        assert result == text


class TestPathHelper:
    """Testes para PathHelper"""
    
    # ==================== build_file_path ====================
    
    def test_build_file_path_with_dot(self):
        """Constrói path com extensão com ponto"""
        result = PathHelper.build_file_path("/base", "file", ".txt")
        assert result == os.path.join("/base", "file.txt")
    
    def test_build_file_path_without_dot(self):
        """Constrói path com extensão sem ponto"""
        result = PathHelper.build_file_path("/base", "file", "txt")
        assert result == os.path.join("/base", "file.txt")
    
    # ==================== ensure_dir_exists ====================
    
    def test_ensure_dir_exists_creates_dir(self, temp_directory):
        """Cria diretório se não existe"""
        new_dir = os.path.join(temp_directory, "new_subdir")
        result = PathHelper.ensure_dir_exists(new_dir)
        
        assert os.path.exists(new_dir)
        assert result == new_dir
    
    def test_ensure_dir_exists_already_exists(self, temp_directory):
        """Não falha se diretório já existe"""
        result = PathHelper.ensure_dir_exists(temp_directory)
        assert result == temp_directory
    
    # ==================== get_project_root ====================
    
    def test_get_project_root_returns_path(self):
        """Retorna caminho válido"""
        result = PathHelper.get_project_root()
        assert result is not None
        assert os.path.isabs(result)
    
    # ==================== get_input_basename ====================
    
    def test_get_input_basename_simple(self):
        """Extrai basename simples"""
        result = PathHelper.get_input_basename("/path/to/file.xlsx")
        assert result == "file"
    
    def test_get_input_basename_sanitizes(self):
        """Sanitiza basename"""
        result = PathHelper.get_input_basename("/path/to/file<test>.xlsx")
        assert '<' not in result
        assert '>' not in result
    
    # ==================== generate_timestamped_folder ====================
    
    def test_generate_timestamped_folder(self, temp_directory):
        """Gera pasta com timestamp"""
        result = PathHelper.generate_timestamped_folder(temp_directory, "TEST_")
        assert result.startswith(os.path.join(temp_directory, "TEST_"))
        # Verifica formato do timestamp (YYYYMMDD_HHMMSS)
        timestamp_part = os.path.basename(result).replace("TEST_", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS


class TestProgressHelper:
    """Testes para ProgressHelper"""
    
    def test_update_with_callback(self):
        """Atualiza com callback"""
        values = []
        callback = lambda v: values.append(v)
        
        ProgressHelper.update(callback, 50)
        
        assert values == [50]
    
    def test_update_without_callback(self):
        """Atualiza sem callback (não deve falhar)"""
        ProgressHelper.update(None, 50)  # Não deve lançar exceção
    
    def test_create_progress_tracker(self):
        """Cria rastreador de progresso"""
        values = []
        callback = lambda v: values.append(v)
        
        tracker = ProgressHelper.create_progress_tracker(callback, 4)
        
        tracker(1)  # 25%
        tracker(2)  # 50%
        tracker(3)  # 75%
        tracker(4)  # 100%
        
        assert values == [25, 50, 75, 100]


class TestDatabaseHelper:
    """Testes para DatabaseHelper"""
    
    def test_get_db_config_oracle(self):
        """Configuração Oracle"""
        config = DatabaseHelper.get_db_config("oracle")
        
        assert config["suffix"] == "SQLORA"
        assert config["uses_source_content"] is False
        # Testa transformação
        assert config["case_transform"]("test") == "TEST"
    
    def test_get_db_config_postgres(self):
        """Configuração PostgreSQL"""
        config = DatabaseHelper.get_db_config("postgres")
        
        assert config["suffix"] == "SQLPSTGR"
        assert config["uses_source_content"] is True
        # Testa transformação
        assert config["case_transform"]("TEST") == "test"
    
    def test_get_db_config_case_insensitive(self):
        """Configuração é case-insensitive"""
        config1 = DatabaseHelper.get_db_config("ORACLE")
        config2 = DatabaseHelper.get_db_config("oracle")
        
        assert config1["suffix"] == config2["suffix"]
    
    def test_get_db_config_unknown_defaults_postgres(self):
        """Tipo desconhecido usa postgres como default"""
        config = DatabaseHelper.get_db_config("unknown")
        assert config["suffix"] == "SQLPSTGR"


class TestFormHelper:
    """Testes para FormHelper"""
    
    def test_parse_list_field_json_array(self):
        """Parse de array JSON"""
        result = FormHelper.parse_list_field('["item1", "item2", "item3"]')
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_list_field_csv(self):
        """Parse de CSV"""
        result = FormHelper.parse_list_field("item1,item2,item3")
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_list_field_csv_with_spaces(self):
        """Parse de CSV com espaços"""
        result = FormHelper.parse_list_field(" item1 , item2 , item3 ")
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_list_field_empty_items(self):
        """Remove itens vazios"""
        result = FormHelper.parse_list_field("item1,,item2,  ,item3")
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_list_field_invalid_json(self):
        """Fallback para CSV em JSON inválido"""
        result = FormHelper.parse_list_field("not json")
        assert result == ["not json"]
    
    def test_parse_list_field_json_numbers(self):
        """Parse de array JSON com números"""
        result = FormHelper.parse_list_field('[1, 2, 3]')
        assert result == ["1", "2", "3"]


class TestBaseService:
    """Testes para BaseService"""
    
    def test_initial_progress(self):
        """Progresso inicial é zero"""
        service = BaseService()
        assert service.get_progress() == 0
    
    def test_update_progress(self):
        """Atualiza progresso"""
        service = BaseService()
        service.update_progress(50)
        assert service.get_progress() == 50
    
    def test_update_progress_invalid_value(self):
        """Valor inválido resulta em zero"""
        service = BaseService()
        service.update_progress("invalid")
        assert service.get_progress() == 0
    
    def test_list_files_existing_dir(self, temp_directory):
        """Lista arquivos de diretório existente"""
        # Cria arquivos de teste
        open(os.path.join(temp_directory, "file1.txt"), 'w').close()
        open(os.path.join(temp_directory, "file2.txt"), 'w').close()
        open(os.path.join(temp_directory, "file3.json"), 'w').close()
        
        service = BaseService()
        
        txt_files = service.list_files(temp_directory, [".txt"])
        assert len(txt_files) == 2
        
        json_files = service.list_files(temp_directory, [".json"])
        assert len(json_files) == 1
        
        all_files = service.list_files(temp_directory, [".txt", ".json"])
        assert len(all_files) == 3
    
    def test_list_files_nonexistent_dir(self):
        """Lista arquivos de diretório inexistente"""
        service = BaseService()
        result = service.list_files("/nonexistent", [".txt"])
        assert result == []
    
    def test_list_files_empty_path(self):
        """Lista arquivos com path vazio"""
        service = BaseService()
        result = service.list_files("", [".txt"])
        assert result == []


class TestAlertsAdapter:
    """Testes para AlertsAdapter"""
    
    def test_alerts_adapter_init(self):
        """Inicialização do adapter"""
        adapter_with_alerts = AlertsAdapter(use_alerts=True)
        adapter_without = AlertsAdapter(use_alerts=False)
        
        assert adapter_with_alerts.use_alerts is True
        assert adapter_without.use_alerts is False
    
    def test_error_without_alerts_logs(self):
        """Error sem alerts usa logging"""
        adapter = AlertsAdapter(use_alerts=False)
        
        with patch('logging.error') as mock_log:
            adapter.error("Test Title", "Test Message")
            mock_log.assert_called_once()
    
    def test_success_without_alerts_logs(self):
        """Success sem alerts usa logging"""
        adapter = AlertsAdapter(use_alerts=False)
        
        with patch('logging.info') as mock_log:
            adapter.success("Test Title", "Test Message")
            mock_log.assert_called_once()
