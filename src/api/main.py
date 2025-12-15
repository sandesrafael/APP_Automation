"""
FastAPI Application
API REST para automação de geração de Masterfiles e JSONs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configura sistema de logging
from src.core.logging_config import setup_logging, api_logger, shutdown_logging
from src.api.middleware import LoggingMiddleware, get_request_id

# Inicializa logging estruturado
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação (startup/shutdown)"""
    # Startup
    api_logger.log_startup(host="127.0.0.1", port=8080, user=None)
    yield
    # Shutdown
    api_logger.log_shutdown()
    # Fecha handlers de log para liberar arquivos
    shutdown_logging()

# Cria aplicação FastAPI
app = FastAPI(
    title="Automation API",
    description="API para automação de geração de Masterfiles e JSONs Oracle/PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware de Logging (deve vir antes do CORS)
app.add_middleware(LoggingMiddleware)

# CORS - permite acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importa rotas
from src.api.routes import masterfile_routes, json_routes, dbn_routes

# Registra rotas
app.include_router(
    masterfile_routes.router,
    prefix="/api/masterfiles",
    tags=["Masterfiles"]
)

app.include_router(
    json_routes.router,
    prefix="/api/jsons",
    tags=["JSONs"]
)

app.include_router(
    dbn_routes.router,
    prefix="/api/dbn",
    tags=["DBN"]
)


@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "Automation API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "masterfile": "available",
            "json": "available",
            "dbn": "available",
            "rename_dbn1": "available"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções - erros são logados pelo middleware"""
    request_id = get_request_id(request)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Erro interno do servidor",
            "error": str(exc),
            "request_id": request_id
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print("Iniciando Automation API...")
    print("Documentacao: http://127.0.0.1:8080/docs")
    print("ReDoc: http://127.0.0.1:8080/redoc")
    
    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,  # Auto-reload em desenvolvimento
        log_level="info"
    )