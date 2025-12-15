"""
Rotas para geração de JSONs
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Optional
import tempfile
import os
import json as json_lib
from datetime import datetime
from uuid import uuid4
from time import time

from src.services import JsonService
from src.utils.helpers import PathHelper, FormHelper
from src.core.logging_config import api_logger
from src.core.config import get_settings

router = APIRouter()
json_service = JsonService()

JOBS = {}
JOB_TTL_SECONDS = 3600
MAX_JOBS = 200

def _cleanup_jobs():
    now = time()
    keys = list(JOBS.keys())
    for k in keys:
        job = JOBS.get(k)
        if not job:
            continue
        created_at = job.get('created_at', now)
        completed = job.get('completed', False)
        if (now - created_at) > JOB_TTL_SECONDS:
            JOBS.pop(k, None)
        elif completed and (now - created_at) > (JOB_TTL_SECONDS / 6):
            JOBS.pop(k, None)
    if len(JOBS) > MAX_JOBS:
        oldest = sorted(JOBS.items(), key=lambda kv: kv[1].get('created_at', 0))
        for k, _ in oldest[: max(0, len(JOBS) - MAX_JOBS)]:
            JOBS.pop(k, None)

def _run_job_json(job_id: str, service: JsonService, tmp_path: str, inventory_list, db_type: str, is_parameter: bool, is_enrichment: bool, output_dir: str, original_filename: str = None):
    # Log início do bloco
    api_logger.log_async_block_start('jsons')
    
    error_occurred = None
    success = False
    
    try:
        result = service.create_jsons(
            path_excel=tmp_path,
            inventory_names=inventory_list,
            db_type=db_type,
            is_parameter=is_parameter,
            is_enrichment=is_enrichment,
            output_path=output_dir,
            original_filename=original_filename
        )
        JOBS[job_id]['result'] = {
            "success": result.success,
            "message": result.message,
            "files_created": result.files_created,
            "total_files": result.total_files,
            "output_path": result.output_path,
            "errors": result.errors,
            "warnings": result.warnings
        }
        success = result.success
        # Captura mensagem de erro se não teve sucesso
        if not success:
            error_occurred = result.message
    except Exception as e:
        JOBS[job_id]['error'] = str(e)
        error_occurred = str(e)
    finally:
        JOBS[job_id]['completed'] = True
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        
        # Remove pasta de saída se houve erro e está vazia
        if not success and os.path.exists(output_dir):
            try:
                if not os.listdir(output_dir):  # Pasta vazia
                    os.rmdir(output_dir)
            except Exception:
                pass
        
        # Log fim do bloco
        api_logger.log_async_block_end('jsons', success=success, error=error_occurred)


@router.post("/create_async")
async def create_jsons_async(
    file: UploadFile = File(...),
    inventory_names: str = Form(...),
    db_type: str = Form(...),
    is_parameter: bool = Form(...),
    is_enrichment: bool = Form(False),
    background_tasks: BackgroundTasks = None
):
    import json as json_local

    if not (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xls ou .xlsx")

    inventory_list = FormHelper.parse_list_field(inventory_names)

    file_extension = '.xlsx' if file.filename.endswith('.xlsx') else '.xls'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    input_base = os.path.splitext(os.path.basename(file.filename))[0]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    settings = get_settings()
    base_path = settings.output_base_path or PathHelper.get_project_root()
    output_dir = os.path.join(base_path, f"JSON_{input_base}_{ts}")
    os.makedirs(output_dir, exist_ok=True)

    _cleanup_jobs()
    job_id = uuid4().hex
    service = JsonService()
    JOBS[job_id] = {"service": service, "output_dir": output_dir, "completed": False, "created_at": time()}

    if background_tasks is None:
        raise HTTPException(status_code=500, detail="BackgroundTasks não disponível")

    background_tasks.add_task(_run_job_json, job_id, service, tmp_path, inventory_list, db_type, is_parameter, is_enrichment, output_dir, file.filename)

    return {"job_id": job_id, "status": "accepted", "output_path": output_dir}

@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """Retorna progresso e, quando concluído, o resultado do job especificado por job_id."""
    _cleanup_jobs()
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_id não encontrado")
    svc = job["service"]
    progress = svc.get_progress()
    response = {
        "job_id": job_id,
        "progress": progress,
        "status": "processing" if progress < 100 else "completed"
    }
    if job.get("completed"):
        response["completed"] = True
        if "result" in job:
            response.update(job["result"])
        elif "error" in job:
            response["success"] = False
            response["message"] = job["error"]
    return response