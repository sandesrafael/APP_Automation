"""
Service para geração de modelos DBN - SEM dependências de UI
"""
import os
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from src.infrastructure.generators.modeloDBN0 import DBNModel
from src.utils.response_models import ProcessResult, StatusType, ValidationResult, FileGenerationResult


class DBNService:
    """Serviço de DBN desacoplado da UI"""
    
    def __init__(self):
        self.current_progress = 0
    
    def validate_inputs(
        self,
        dbn_names: List[str],
        schema: Optional[str],
        output_path: str,
        dbn_type: str,
        classe: Optional[str] = None
    ) -> ValidationResult:
        """Valida inputs para geração de DBN"""
        
        if not dbn_names:
            return ValidationResult(
                is_valid=False,
                message="Nenhum nome de DBN fornecido",
                status=StatusType.ERROR
            )
        
        if not output_path:
            return ValidationResult(
                is_valid=False,
                message="Caminho de saída não fornecido",
                status=StatusType.ERROR
            )
        
        if dbn_type not in ['DBN0', 'DBN1']:
            return ValidationResult(
                is_valid=False,
                message=f"Tipo de DBN inválido: {dbn_type}. Use 'DBN0' ou 'DBN1'",
                status=StatusType.ERROR
            )
        
        if dbn_type == 'DBN1' and not classe:
            return ValidationResult(
                is_valid=False,
                message="Classe é obrigatória para DBN1",
                status=StatusType.ERROR
            )
        
        return ValidationResult(
            is_valid=True,
            message="Validação bem-sucedida",
            status=StatusType.SUCCESS
        )
    
    def get_progress(self) -> int:
        return self.current_progress
    
    def create_dbn_model(
        self,
        dbn_names: List[str],
        schema: Optional[str],
        output_path: str,
        dbn_type: str = 'DBN0',
        classe: Optional[str] = None
    ) -> FileGenerationResult:
        """
        Cria modelo de exportação DBN
        
        Args:
            dbn_names: Lista de nomes DBN
            schema: Nome do schema
            output_path: Caminho de saída
            dbn_type: 'DBN0' ou 'DBN1'
            classe: Nome da classe (obrigatório para DBN1)
            
        Returns:
            FileGenerationResult
        """
        try:
            logger.info(f"DBNService.create_dbn_model iniciado")
            logger.info(f"DBN Type: {dbn_type}")
            logger.info(f"DBN Names: {dbn_names}")
            logger.info(f"Schema: {schema or 'Não definido'}")
            if classe:
                logger.info(f"Classe: {classe}")
            logger.info(f"Output Path: {output_path}")
            
            # Validação
            logger.info("Iniciando validação...")
            validation = self.validate_inputs(
                dbn_names,
                schema,
                output_path,
                dbn_type,
                classe
            )
            logger.info(f"Validação completa: {validation.is_valid}")
            
            if not validation.is_valid:
                return FileGenerationResult(
                    success=False,
                    message=validation.message,
                    status=StatusType.ERROR,
                    errors=[validation.message],
                    progress=self.current_progress
                )
            
            # Progresso inicial
            self.current_progress = 10
            
            logger.info(f"Gerando modelo {dbn_type}...")
            # Gera modelo (sem UI alerts)
            result = DBNModel.modelo_exportacao(
                dbn_names,
                schema,
                output_path,
                tipo=dbn_type,
                classe=classe,
                use_alerts=False
            )
            
            if result:
                file_path = os.path.join(output_path, f"MODELO_DE_EXPORTACAO_{dbn_type}.txt")
                logger.info(f"SUCESSO: MODELO {dbn_type} CRIADO")
                
                self.current_progress = 100
                return FileGenerationResult(
                    success=True,
                    message=f"Modelo {dbn_type} criado com sucesso!",
                    status=StatusType.SUCCESS,
                    files_created=[file_path],
                    total_files=1,
                    output_path=output_path,
                    progress=self.current_progress
                )
            else:
                return FileGenerationResult(
                    success=False,
                    message=f"Erro ao criar modelo {dbn_type}",
                    status=StatusType.ERROR,
                    errors=[f"Falha na geraÃ§Ã£o do modelo {dbn_type}"],
                    progress=self.current_progress
                )
                
        except Exception as e:
            return FileGenerationResult(
                success=False,
                message=f"Erro inesperado: {str(e)}",
                status=StatusType.ERROR,
                errors=[str(e)],
                progress=self.current_progress
            )



