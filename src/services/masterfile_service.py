"""
Service para geração de Masterfiles - SEM dependências de UI
"""
import os
import logging
from typing import List, Callable, Optional
from pathlib import Path

from src.utils.helpers import PathHelper, BaseService, ValidationHelper
from src.utils.response_models import ProcessResult, StatusType, ValidationResult, FileGenerationResult
from src.domain.processors.masterfile_processor import MasterfileCreator
from src.core.exceptions import ValidationError, DuplicateError, MissingElementsError

logger = logging.getLogger(__name__)

# Importa processadores existentes


class MasterfileService(BaseService):
    """Serviço de Masterfiles desacoplado da UI"""
    
    def __init__(self):
        super().__init__()
        self.errors = []
        self.warnings = []
    
    def validate_inputs(
        self, 
        path_excel: str, 
        inventory_names: List[str],
        db_type: str,
        output_path: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida inputs antes do processamento
        
        Args:
            path_excel: Caminho para arquivo .xls ou .xlsx
            inventory_names: Lista de inventory names
            db_type: 'oracle' ou 'postgres'
            output_path: Caminho de saída (opcional)
            
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
                message=f"Tipo de banco inválido: {db_type}. Use 'oracle' ou 'postgres'",
                status=StatusType.ERROR
            )
        
        return ValidationResult(
            is_valid=True,
            message="Validação bem-sucedida",
            status=StatusType.SUCCESS,
            details={
                "inventory_count": len(inventory_names),
                "db_type": db_type
            }
        )
    
    def create_masterfiles(
        self,
        path_excel: str,
        inventory_names: List[str],
        db_type: str,
        master_path: Optional[str] = None,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        original_filename: Optional[str] = None
    ) -> FileGenerationResult:
        """
        Cria masterfiles sem acoplamento com UI
        
        Args:
            path_excel: Caminho do arquivo Excel
            inventory_names: Lista de inventory names
            db_type: 'oracle' ou 'postgres'
            master_path: Caminho para masterfiles (opcional)
            output_path: Caminho de saída
            progress_callback: Função de callback para progresso
            original_filename: Nome original do arquivo (opcional)
            
        Returns:
            FileGenerationResult com resultado do processamento
        """
        self.errors = []
        self.warnings = []
        
        try:
            logger.info("MasterfileService.create_masterfiles iniciado")
            # Mantém saída fornecida pela rota; se não vier, usa raiz do projeto
            if not output_path:
                output_path = PathHelper.get_project_root()
            # Mostra nome original do arquivo se fornecido
            display_filename = original_filename if original_filename else path_excel
            logger.info(f"Arquivo: {display_filename}")
            logger.info(f"Inventories: {inventory_names}")
            logger.info(f"DB Type: {db_type}")
            
            # Validação
            logger.info("Iniciando validação...")
            validation = self.validate_inputs(
                path_excel, 
                inventory_names, 
                db_type,
                output_path
            )
            logger.info(f"Validação completa: {validation.is_valid}")
            
            if not validation.is_valid:
                return FileGenerationResult(
                    success=False,
                    message=validation.message,
                    status=StatusType.ERROR,
                    errors=[validation.message],
                    details=validation.details
                )
            
            # Limpa inventory names
            inventory_names = [name.strip() for name in inventory_names if name.strip()]
            
            # Normaliza db_type
            db_type_normalized = db_type.lower()
            if db_type_normalized == 'postgresql':
                db_type_normalized = 'postgres'
            
            # Processamento
            is_oracle = db_type_normalized == 'oracle'
            
            logger.info(f"Criando MasterfileCreator (is_oracle={is_oracle})...")
            creator = MasterfileCreator(
                path_excel,
                inventory_names,
                is_oracle,
                master_path,
                output_path
            )
            logger.info("MasterfileCreator criado com sucesso")
            
            # Wrapper do callback para capturar progresso
            def internal_callback(value):
                self.update_progress(value)
                if progress_callback:
                    progress_callback(value)
            
            # Executa criação
            logger.info("Iniciando criação de masterfiles...")
            result = creator.create_masterfiles(internal_callback)
            
            if result:
                # Coleta arquivos criados
                files_created = self.list_files(output_path, ['.mas', '.acx'])
                
                return FileGenerationResult(
                    success=True,
                    message=f"Masterfiles e ACX criados com sucesso! ({len(files_created)} arquivos)",
                    status=StatusType.SUCCESS,
                    data={"output_path": output_path},
                    files_created=files_created,
                    total_files=len(files_created),
                    output_path=output_path,
                    progress=100
                )
            else:
                return FileGenerationResult(
                    success=False,
                    message="Erro ao criar masterfiles",
                    status=StatusType.ERROR,
                    errors=self.errors if self.errors else ["Falha no processamento"],
                    progress=self.current_progress
                )
                
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
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