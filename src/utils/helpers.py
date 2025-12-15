"""
Funções utilitárias compartilhadas entre os módulos do projeto
"""
from collections import Counter
import os
import json
from typing import List, Optional, Tuple, Set, Any, Dict
from datetime import datetime


class ValidationHelper:
    """Helper para validações comuns"""
    
    @staticmethod
    def check_duplicates(items, item_name="elemento") -> Tuple[bool, List]:
        """
        Verifica se há itens duplicados em uma lista.
        
        Args:
            items: Lista de itens para verificar
            item_name: Nome do tipo de item (mantido para compatibilidade)
            
        Returns:
            tuple: (bool: tem_duplicatas, list: itens_duplicados)
        """
        counter = Counter(items)
        duplicates = [item for item, count in counter.items() if count > 1]
        return len(duplicates) > 0, duplicates
    
    @staticmethod
    def format_duplicate_message(duplicates, item_name="elemento") -> str:
        """
        Formata mensagem de duplicatas.
        
        Args:
            duplicates: Lista de itens duplicados
            item_name: Nome do tipo de item
            
        Returns:
            str: Mensagem formatada
        """
        elementos = '\n'.join(str(d) for d in duplicates)
        
        if len(duplicates) > 1:
            return f"Os seguintes {item_name}s foram inseridos mais de uma vez:\n{elementos}"
        return f"O seguinte {item_name} foi inserido mais de uma vez:\n{elementos}"
    
    @staticmethod
    def check_missing_elements(provided_items, available_items, item_name="elemento") -> Tuple[bool, Set]:
        """
        Verifica se há itens fornecidos que não estão disponíveis.
        
        Args:
            provided_items: Itens fornecidos pelo usuário
            available_items: Itens disponíveis no sistema
            item_name: Nome do tipo de item
            
        Returns:
            tuple: (bool: tem_faltando, set: itens_faltando)
        """
        missing = set(provided_items) - set(available_items)
        return len(missing) > 0, missing
    
    @staticmethod
    def format_missing_message(missing, item_name="elemento") -> str:
        """
        Formata mensagem de elementos faltando.
        
        Args:
            missing: Set ou lista de itens faltando
            item_name: Nome do tipo de item
            
        Returns:
            str: Mensagem formatada
        """
        sorted_elements = sorted(missing)
        elements_str = '\n'.join(str(e) for e in sorted_elements)
        return f"{item_name.capitalize()}(s) não encontrado(s) no pack:\n{elements_str}"
    
    @staticmethod
    def is_valid_excel_file(path: str) -> bool:
        """Check if file is valid Excel"""
        if not path:
            return False
        return path.lower().endswith(('.xlsx', '.xls'))
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """Check if path exists"""
        return os.path.exists(path) if path else False
    
    @staticmethod
    def is_non_empty_list(items: list) -> bool:
        """Check if list is not empty"""
        return isinstance(items, list) and len(items) > 0
    
    @staticmethod
    def validate_inventory_names(names: List[str]) -> List[str]:
        """Validate and clean inventory names"""
        if not names:
            return []
        return [name.strip() for name in names if name and name.strip()]


class TextHelper:
    """Helper para processamento de texto"""
    
    @staticmethod
    def processar_descricao(descricao):
        """Remove aspas simples de descrições"""
        if isinstance(descricao, str) and "'" in descricao:
            return descricao.replace("'", "")
        return descricao
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caracteres inválidos de nomes de arquivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    @staticmethod
    def to_upper_snake_case(text: str) -> str:
        """Convert text to UPPER_SNAKE_CASE"""
        import re
        return re.sub(r'\s+', '_', text.strip()).upper()
    
    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


class PathHelper:
    """Helper para manipulação de caminhos"""
    
    @staticmethod
    def build_file_path(base_path: str, filename: str, extension: str) -> str:
        """Constrói caminho completo para um arquivo"""
        if not extension.startswith('.'):
            extension = f'.{extension}'
        return os.path.join(base_path, f"{filename}{extension}")
    
    @staticmethod
    def ensure_dir_exists(path: str) -> str:
        """Garante que um diretório existe, criando se necessário"""
        os.makedirs(path, exist_ok=True)
        return path
    
    @staticmethod
    def get_project_root() -> str:
        """Get project root directory"""
        return os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    
    @staticmethod
    def get_input_basename(input_path: str) -> str:
        """Get sanitized basename from input path"""
        base = os.path.splitext(os.path.basename(input_path))[0]
        return TextHelper.sanitize_filename(base)
    
    @staticmethod
    def get_output_dir(prefix: str, input_path: str) -> str:
        """Get output directory path"""
        root = PathHelper.get_project_root()
        base = PathHelper.get_input_basename(input_path)
        folder = f"{prefix}_{base}"
        return os.path.join(root, folder)
    
    @staticmethod
    def generate_timestamped_folder(base_path: str, prefix: str) -> str:
        """Generate folder name with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(base_path, f"{prefix}{timestamp}")


class ProgressHelper:
    """Helper para gerenciamento de progresso"""
    
    @staticmethod
    def update(callback, value):
        """Atualiza progresso de forma segura"""
        if callback:
            callback(value)
    
    @staticmethod
    def create_progress_tracker(callback, total_steps):
        """Cria um rastreador de progresso"""
        def update_step(current_step):
            if callback:
                progress = int((current_step / total_steps) * 100)
                callback(progress)
        return update_step


class DatabaseHelper:
    """Helper para configurações de banco de dados"""
    
    @staticmethod
    def get_db_config(db_type: str) -> Dict[str, Any]:
        """Retorna configuração para um tipo de banco de dados"""
        configs = {
            'oracle': {
                'case_transform': str.upper,
                'suffix': 'SQLORA',
                'uses_source_content': False
            },
            'postgres': {
                'case_transform': str.lower,
                'suffix': 'SQLPSTGR',
                'uses_source_content': True
            }
        }
        return configs.get(db_type.lower(), configs['postgres'])


class ExcelHelper:
    """Helper para leitura de arquivos Excel"""
    
    @staticmethod
    def read_sheets(path_name_excel, sheet_names, nrows=4, engine='calamine'):
        import pandas as pd
        return pd.read_excel(path_name_excel, sheet_name=sheet_names, nrows=nrows, engine=engine)
    
    @staticmethod
    def read_columns(path_name_excel, sheet_name, col_indexes, skiprows=3, engine='calamine'):
        import pandas as pd
        return pd.read_excel(
            path_name_excel,
            sheet_name=sheet_name,
            usecols=col_indexes,
            skiprows=skiprows,
            header=0,
            engine=engine
        )
    
    @staticmethod
    def validate_header(df, col_index, expected_value):
        try:
            found = str(df.iloc[2, col_index]).strip()
        except Exception as e:
            raise ValueError(f"Não foi possível acessar a linha do cabeçalho: {e}")
        if found != expected_value:
            raise ValueError(f"Esperado: '{expected_value}', Encontrado: '{found}'")


class SheetConstants:
    """Constantes para abas do Excel"""
    
    # Configuração de abas/colunas para JSON
    JSON_SHEET_INFO = {
        'data_sources': {
            'sheet_name': '3. Data Sources',
            'header_validation': {
                'col_index': 1,
                'expected_value': 'Inventory Name',
                'error_msg': "O cabeçalho deve ficar na 4ª linha (Data Sources)"
            },
            'columns_of_interest': [
                'Inventory Name', 'Table Name', 'Schema', 'Description',
                'Period', 'Delay', 'Vendor', 'Tecnologia/Grupo de Contadores', 'Table Group'
            ],
            'filter_col_index': 0
        },
        'data_sources_attr': {
            'sheet_name': '3. Data Sources Attr & Count',
            'header_validation': {
                'col_index': 1,
                'expected_value': 'Source Name',
                'error_msg': "O cabeçalho deve ficar na 4ª linha (Data Sources Attr)"
            },
            'columns_of_interest': [
                'Source Name', 'Attribute/Counter Name', 'Attribute/Counter Physical Name',
                'Data Type', 'Mediation Type', 'Metrics Attribute Type', 'Altaia Attribute Type',
                'Description', 'Example'
            ],
            'filter_col_index': 0
        }
    }
    
    # Configuração de abas/colunas para MASTERFILES
    MASTER_SHEET_INFO = {
        'data_sources': {
            'sheet_name': '3. Data Sources',
            'header_validation': {
                'col_index': 1,
                'expected_value': 'Inventory Name',
                'error_msg': "O cabeçalho deve ficar na 4ª linha (Data Sources)"
            },
            'columns_of_interest': ['Inventory Name', 'Table Name', 'Schema', 'Description'],
            'filter_col_index': 0
        },
        'data_sources_attr': {
            'sheet_name': '3. Data Sources Attr & Count',
            'header_validation': {
                'col_index': 1,
                'expected_value': 'Source Name',
                'error_msg': "O cabeçalho deve ficar na 4ª linha (Data Sources Attr)"
            },
            'columns_of_interest': [
                'Source Name', 'Attribute/Counter Name', 'Attribute/Counter Physical Name',
                'Data Type', 'Mediation Type', 'Metrics Attribute Type', 'Description'
            ],
            'filter_col_index': 0
        },
        'data_sources_map': {
            'sheet_name': '3. Data Sources Map',
            'header_validation': {
                'col_index': 1,
                'expected_value': 'Enrichment Table Name',
                'error_msg': "O cabeçalho deve ficar na 4ª linha (Data Sources Map)"
            },
            'columns_of_interest': [
                'Enrichment Table Name', 'Enrichment Attribute Name', 'DBNO Table Name',
                'DBN0 Attribute Name', 'AdHoc Join Type'
            ],
            'filter_col_index': 2
        }
    }


class BaseService:
    """Classe base para services"""
    
    def __init__(self):
        self.current_progress = 0
    
    def get_progress(self) -> int:
        return self.current_progress
    
    def update_progress(self, value):
        try:
            self.current_progress = int(value)
        except Exception:
            self.current_progress = 0
    
    def list_files(self, output_path: str, extensions: List[str]) -> List[str]:
        if not output_path or not os.path.exists(output_path):
            return []
        exts = [e.lower() for e in extensions]
        return [
            os.path.join(output_path, f)
            for f in os.listdir(output_path)
            if any(f.lower().endswith(ext) for ext in exts)
        ]


class FormHelper:
    """Helper para parsing de formulários"""
    
    @staticmethod
    def parse_list_field(value: str) -> List[str]:
        try:
            data = json.loads(value)
            if isinstance(data, list):
                return [str(i).strip() for i in data if str(i).strip()]
        except Exception:
            pass
        return [s.strip() for s in value.split(',') if s.strip()]


class AlertsAdapter:
    """Adapter para alertas (UI ou logging)"""
    
    def __init__(self, use_alerts: bool = True):
        self.use_alerts = use_alerts
    
    def error(self, title: str, message: str):
        if self.use_alerts:
            try:
                from alerta import msg_alerta_erro
                msg_alerta_erro(title, message)
            except Exception:
                import logging
                logging.error(f"{title}: {message}")
        else:
            import logging
            logging.error(f"{title}: {message}")
    
    def success(self, title: str, message: str):
        if self.use_alerts:
            try:
                from alerta import msg_alerta_sucesso
                msg_alerta_sucesso(title, message)
            except Exception:
                import logging
                logging.info(f"{title}: {message}")
        else:
            import logging
            logging.info(f"{title}: {message}")
