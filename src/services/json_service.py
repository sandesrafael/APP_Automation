"""
Service para geração de JSONs - SEM dependências de UI
"""
import os
import logging
from typing import List, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from src.utils.helpers import PathHelper, BaseService, ValidationHelper
from src.utils.response_models import ProcessResult, StatusType, ValidationResult, FileGenerationResult
from src.infrastructure.repositories.file_repository import FileRepository
from src.domain.processors.json_criador import JsonCreator
from src.core.exceptions import ValidationError, DuplicateError


class JsonService(BaseService):
    """Serviço de JSON desacoplado da UI"""
    
    def __init__(self, file_repo=None):
        super().__init__()
        self.errors = []
        self.warnings = []
        self.file_repo = file_repo or FileRepository()
    
    def validate_inputs(
        self,
        path_excel: str,
        inventory_names: List[str],
        db_type: str,
        is_parameter: bool,
        output_path: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida inputs antes do processamento
        
        Args:
            path_excel: Caminho para arquivo .xls ou .xlsx
            inventory_names: Lista de inventory names
            db_type: 'oracle' ou 'postgres'
            is_parameter: True para parâmetros, False para contadores
            output_path: Caminho de saída
            
        Returns:
            ValidationResult com status da validação
        """
        
        # Validação de arquivo
        if not path_excel:
            return ValidationResult(
                is_valid=False,
                message="Nenhum arquivo selecionado",
                status=StatusType.ERROR
            )
        
        if not (path_excel.endswith('.xls') or path_excel.endswith('.xlsx')):
            return ValidationResult(
                is_valid=False,
                message="Arquivo inválido. Selecione um arquivo .xls ou .xlsx",
                status=StatusType.ERROR
            )
        
        if not os.path.exists(path_excel):
            return ValidationResult(
                is_valid=False,
                message=f"Arquivo não encontrado: {path_excel}",
                status=StatusType.ERROR
            )
        
        # Validação de inventory names
        if not inventory_names:
            return ValidationResult(
                is_valid=False,
                message="Nenhum Inventory Name fornecido",
                status=StatusType.ERROR
            )
        
        # Remove linhas vazias
        inventory_names = [name.strip() for name in inventory_names if name.strip()]
        
        if not inventory_names:
            return ValidationResult(
                is_valid=False,
                message="Lista de Inventory Names está vazia",
                status=StatusType.ERROR
            )
        
        # Validação de duplicatas
        has_duplicates, duplicates = ValidationHelper.check_duplicates(inventory_names)
        if has_duplicates:
            msg = ValidationHelper.format_duplicate_message(duplicates, "Inventory Name")
            return ValidationResult(
                is_valid=False,
                message=msg,
                status=StatusType.ERROR,
                details={"duplicates": list(duplicates)}
            )
        
        # Validação de tipo de banco
        if db_type.lower() not in ['oracle', 'postgres', 'postgresql']:
            return ValidationResult(
                is_valid=False,
                message=f"Tipo de banco inválido: {db_type}",
                status=StatusType.ERROR
            )
        
        return ValidationResult(
            is_valid=True,
            message="Validação bem-sucedida",
            status=StatusType.SUCCESS,
            details={
                "inventory_count": len(inventory_names),
                "db_type": db_type,
                "type": "parameters" if is_parameter else "counters"
            }
        )
    
    def create_jsons(
        self,
        path_excel: str,
        inventory_names: List[str],
        db_type: str,
        is_parameter: bool,
        is_enrichment: bool,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        original_filename: Optional[str] = None
    ) -> FileGenerationResult:
        """
        Cria JSONs sem acoplamento com UI
        
        Args:
            path_excel: Caminho do arquivo Excel
            inventory_names: Lista de inventory names
            db_type: 'oracle' ou 'postgres'
            is_parameter: True para parâmetros, False para contadores
            is_enrichment: True para enriquecimento, False para não enriquecimento
            output_path: Caminho de saída
            progress_callback: Função de callback para progresso
            
        Returns:
            FileGenerationResult com resultado do processamento
        """
        self.errors = []
        self.warnings = []
        
        try:
            logger.info("JsonService.create_jsons iniciado")
            display_filename = original_filename if original_filename else os.path.basename(path_excel)
            logger.info(f"Arquivo: {display_filename}")
            logger.info(f"Inventories: {inventory_names}")
            logger.info(f"DB Type: {db_type}")
            logger.info(f"Tipo: {'Parâmetros' if is_parameter else 'Contadores'}")
            logger.info(f"Enriquecimento: {'Sim' if is_enrichment else 'Não'}")
            
            # Validação
            logger.info("Iniciando validação...")
            validation = self.validate_inputs(
                path_excel,
                inventory_names,
                db_type,
                is_parameter,
                output_path
            )
            logger.info(f"Validação completa: {validation.is_valid}")
            
            if not validation.is_valid:
                return FileGenerationResult(
                    success=False,
                    message=validation.message,
                    status=StatusType.ERROR,
                    errors=[validation.message]
                )
            
            # Limpa inventory names
            inventory_names = [name.strip() for name in inventory_names if name.strip()]
            
            # Normaliza db_type
            db_type_normalized = db_type.lower()
            if db_type_normalized == 'postgresql':
                db_type_normalized = 'postgres'
            
            # Processamento
            is_oracle = db_type_normalized == 'oracle'
            
            logger.info(f"Criando JsonCreator (is_oracle={is_oracle})...")
            # Usa o output_path informado pela rota (JSON_<excel>)
            creator = JsonCreator(
                path_excel,
                inventory_names,
                output_path,
                is_oracle,
                is_enrichment,
                is_parameter,
                use_alerts=False
            )
            logger.info("JsonCreator criado com sucesso")
            
            # Wrapper do callback
            def internal_callback(value):
                self.current_progress = value
                if progress_callback:
                    progress_callback(value)
            
            # Executa criação
            logger.info("Iniciando criação de JSONs...")
            result = creator.create_json(internal_callback)
            
            if result:
                logger.info("SUCESSO: JSONS CRIADOS")
                # Coleta arquivos criados
                files_created = self.file_repo.list_files(output_path, ['.json'])
                
                tipo = "parâmetros" if is_parameter else "contadores"
                
                return FileGenerationResult(
                    success=True,
                    message=f"JSONs de {tipo} gerados com sucesso! ({len(files_created)} arquivos)",
                    status=StatusType.SUCCESS,
                    data={"output_path": output_path, "type": tipo},
                    files_created=files_created,
                    total_files=len(files_created),
                    output_path=output_path,
                    progress=100
                )
            else:
                return FileGenerationResult(
                    success=False,
                    message="Erro ao gerar JSONs",
                    status=StatusType.ERROR,
                    errors=self.errors if self.errors else ["Falha no processamento"],
                    progress=self.current_progress
                )
                
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            return FileGenerationResult(
                success=False,
                message=error_msg,
                status=StatusType.ERROR,
                errors=[error_msg],
                progress=self.current_progress
            )
    
    def get_progress(self) -> int:
        """Retorna progresso atual"""
        return self.current_progress
