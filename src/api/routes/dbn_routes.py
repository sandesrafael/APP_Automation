"""
Rotas para operações DBN
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import tempfile
import os
import logging

from src.services import DBNService
from src.infrastructure.generators.renomearDBN1 import RenameFiles

logger = logging.getLogger(__name__)

router = APIRouter()
dbn_service = DBNService()


@router.post("/dbn0/create")
async def create_dbn0(
    dbn_names: str = Form(...),
    output_path: str = Form(...),
    db_schema: str | None = Form(None, alias="schema"),
):
    """
    Cria modelo de exportação DBN0
    
    - **dbn_names**: Lista de nomes de DBN (JSON array ou CSV)
    - **output_path**: Caminho onde o arquivo será salvo (obrigatório)
    - **schema**: Nome do schema de conexão (opcional)
    """
    import json as json_lib
    
    # Parse dbn names
    try:
        names = json_lib.loads(dbn_names)
    except:
        names = [name.strip() for name in dbn_names.split(',') if name.strip()]
    
    # Garante diretório de saída informado pelo usuário
    os.makedirs(output_path, exist_ok=True)
    
    try:
        # Processa usando o service
        result = dbn_service.create_dbn_model(
            dbn_names=names,
            schema=db_schema,
            output_path=output_path,
            dbn_type='DBN0'
        )
        
        # Se falhou, lança exceção para o middleware capturar
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "total_files": result.total_files,
            "output_path": result.output_path,
            "errors": result.errors,
            "warnings": result.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dbn1/create")
async def create_dbn1(
    dbn_names: str = Form(...),
    output_path: str = Form(...),
    db_schema: str | None = Form(None, alias="schema"),
    classe: str = Form(...),
):
    """
    Cria modelo de exportação DBN1
    
    - **dbn_names**: Lista de nomes de DBN (JSON array ou CSV)
    - **output_path**: Caminho onde o arquivo será salvo (obrigatório)
    - **schema**: Nome do schema de conexão (opcional)
    - **classe**: Nome lógico da classe (obrigatório para DBN1)
    """
    import json as json_lib

    # Parse dbn names
    try:
        names = json_lib.loads(dbn_names)
    except:
        names = [name.strip() for name in dbn_names.split(',') if name.strip()]

    # Garante diretório de saída informado pelo usuário
    os.makedirs(output_path, exist_ok=True)

    try:
        # Processa usando o service
        result = dbn_service.create_dbn_model(
            dbn_names=names,
            schema=db_schema,
            output_path=output_path,
            dbn_type='DBN1',
            classe=classe
        )

        # Se falhou, lança exceção para o middleware capturar
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "total_files": result.total_files,
            "output_path": result.output_path,
            "errors": result.errors,
            "warnings": result.warnings
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dbn1/rename")
async def rename_dbn1(
    path: str = Form(...)
):
    """
    Renomeia arquivos DBN1
    
    - **path**: Caminho do diretório com arquivos DBN1
    """
    try:
        logger.info("RenameDBN1 iniciado")
        logger.info(f"Path: {path}")
        
        if not os.path.exists(path):
            raise HTTPException(
                status_code=404,
                detail=f"Diretório não encontrado: {path}"
            )
        
        logger.info("Renomeando arquivos DBN1...")
        # Usa a classe RenameFiles diretamente
        result = RenameFiles.renomeia_arquivos(path)
        
        if result:
            logger.info("SUCESSO: ARQUIVOS DBN1 RENOMEADOS")
            return {
                "success": True,
                "message": "Arquivos DBN1 renomeados com sucesso",
                "path": path
            }
        else:
            raise HTTPException(status_code=400, detail="Falha ao renomear arquivos DBN1")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_progress():
    """Retorna progresso atual do processamento DBN"""
    return {
        "progress": dbn_service.get_progress(),
        "status": "processing" if dbn_service.get_progress() < 100 else "completed"
    }