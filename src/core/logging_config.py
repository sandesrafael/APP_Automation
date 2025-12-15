"""
Logging Configuration
Sistema centralizado de logs para a API
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from typing import Optional


class ReadableFileFormatter(logging.Formatter):
    """
    Formatter legível para arquivos de log.
    Formato simples: [data-hora] [LEVEL] mensagem
    Sem traceback - traceback completo fica apenas no log de debug (JSON)
    """
    
    LEVEL_LABELS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[INFO]',
        'WARNING': '[AVISO]',
        'ERROR': '[ERRO]',
        'CRITICAL': '[CRÍTICO]',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        level = self.LEVEL_LABELS.get(record.levelname, '[LOG]')
        message = record.getMessage()
        
        # Formato simples: [data-hora] [LEVEL] mensagem (sem traceback)
        log_line = f"[{timestamp}] {level} {message}"
        
        return log_line


class ErrorOnlyFormatter(logging.Formatter):
    """
    Formatter para arquivo de erros.
    Mostra apenas a mensagem principal, sem traceback completo.
    """
    
    LEVEL_LABELS = {
        'ERROR': '[ERRO]',
        'CRITICAL': '[CRÍTICO]',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        level = self.LEVEL_LABELS.get(record.levelname, '[ERRO]')
        message = record.getMessage()
        
        # Formato simples sem traceback: [data-hora] [LEVEL] mensagem
        log_line = f"[{timestamp}] {level} {message}"
        
        # Se houver exceção, mostra apenas o tipo e mensagem principal
        if record.exc_info and record.exc_info[1]:
            exc_type = record.exc_info[0].__name__ if record.exc_info[0] else 'Exception'
            exc_msg = str(record.exc_info[1])
            log_line += f" | {exc_type}: {exc_msg}"
        
        return log_line


class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON estruturado (para integrações)"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adiciona campos extras se existirem
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user'):
            log_data['user'] = record.user
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        if hasattr(record, 'error'):
            log_data['error'] = record.error
        if hasattr(record, 'payload'):
            log_data['payload'] = record.payload
            
        # Adiciona exceção se existir
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class MainLogErrorFilter(logging.Filter):
    """
    Filtro para o log principal (automation_api.log).
    Permite apenas mensagens de erro no formato de bloco (ERRO NA ...).
    Erros detalhados vão apenas para error e debug logs.
    """
    
    # Padrões de erro permitidos no log principal
    ALLOWED_ERROR_PATTERNS = (
        'ERRO NA ',
    )
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Permite todos os níveis exceto ERROR
        if record.levelno != logging.ERROR:
            return True
        
        # Para ERROR, permite apenas mensagens de bloco
        message = record.getMessage()
        for pattern in self.ALLOWED_ERROR_PATTERNS:
            if pattern in message:
                return True
        
        # Bloqueia outros erros detalhados
        return False


class AppErrorFilter(logging.Filter):
    """
    Filtro para capturar apenas erros da aplicação.
    Ignora erros de bibliotecas externas (uvicorn, starlette, etc.)
    """
    
    # Loggers externos para ignorar
    IGNORE_LOGGERS = (
        'uvicorn',
        'starlette',
        'fastapi',
        'httpcore',
        'httpx',
        'asyncio',
        'watchfiles',
    )
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Ignora loggers externos
        for ignore in self.IGNORE_LOGGERS:
            if record.name.startswith(ignore):
                return False
        
        # Aceita todos os outros (da aplicação)
        return True


class ConsoleFormatter(logging.Formatter):
    """Formatter legível para console"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Formato base
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        base = f"{color}[{timestamp}] [{record.levelname}]{self.RESET} {record.getMessage()}"
        
        # Adiciona detalhes extras
        extras = []
        if hasattr(record, 'request_id'):
            extras.append(f"req_id={record.request_id[:8]}")
        if hasattr(record, 'user') and record.user:
            extras.append(f"user={record.user}")
        if hasattr(record, 'endpoint'):
            extras.append(f"endpoint={record.endpoint}")
        if hasattr(record, 'method'):
            extras.append(f"method={record.method}")
        if hasattr(record, 'status_code'):
            extras.append(f"status={record.status_code}")
        if hasattr(record, 'duration_ms'):
            extras.append(f"duration={record.duration_ms:.2f}ms")
        if hasattr(record, 'client_ip'):
            extras.append(f"ip={record.client_ip}")
            
        if extras:
            base += f" | {' | '.join(extras)}"
            
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"
            
        return base


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    app_name: str = "automation_api"
) -> logging.Logger:
    """
    Configura o sistema de logging da aplicacao.
    
    Args:
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretorio para arquivos de log (None = ./logs)
        app_name: Nome da aplicacao para o arquivo de log
        
    Returns:
        Logger configurado
    """
    # Check if running in test mode
    is_testing = os.environ.get("TESTING", "").lower() in ("1", "true", "yes")
    
    # Configura logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para console (formato legivel)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)
    
    # Skip file handlers during testing
    if is_testing:
        return root_logger
    
    # Define diretorio de logs
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Handler para arquivo legivel (logs para humanos)
    log_file = log_dir / f"{app_name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ReadableFileFormatter())
    file_handler.addFilter(MainLogErrorFilter())  # Filtra erros detalhados
    root_logger.addHandler(file_handler)
    
    # Handler para arquivo técnico/debug (formato JSON estruturado)
    json_log_file = log_dir / f"{app_name}_debug.log"
    json_handler = RotatingFileHandler(
        json_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.DEBUG)
    json_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(json_handler)
    
    # Handler separado para erros (formato legível)
    # Captura apenas erros da aplicação, ignora bibliotecas externas
    error_log_file = log_dir / f"{app_name}_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(ErrorOnlyFormatter())  # Usa formatter sem traceback
    error_handler.addFilter(AppErrorFilter())  # Filtra apenas erros da aplicação
    root_logger.addHandler(error_handler)
    
    # Logger específico da API
    api_logger = logging.getLogger("api")
    
    return api_logger


class APILogger:
    """Classe helper para logging estruturado da API"""
    
    # Mapeamento de endpoints para nomes amigáveis de operação
    ENDPOINT_NAMES = {
        # Masterfiles
        '/api/masterfiles/create_async': 'criação de Masterfiles',
        '/api/masterfiles/progress': 'consulta de progresso de Masterfiles',
        # JSONs
        '/api/jsons/create_async': 'criação de JSONs',
        '/api/jsons/progress': 'consulta de progresso de JSONs',
        # DBN
        '/api/dbn/dbn0/create': 'criação de DBN0',
        '/api/dbn/dbn1/create': 'criação de DBN1',
        '/api/dbn/dbn1/rename': 'renomeação de DBN1',
        '/api/dbn/progress': 'consulta de progresso de DBN',
    }
    
    # Endpoints assíncronos - middleware só loga bloco de erro (task loga sucesso)
    ASYNC_ENDPOINTS = {
        '/api/masterfiles/create_async',
        '/api/jsons/create_async',
    }
    
    # Operações assíncronas (bloco é logado na task, não no middleware)
    ASYNC_OPERATIONS = {
        'masterfiles': 'CRIAÇÃO DE MASTERFILES',
        'jsons': 'CRIAÇÃO DE JSONS',
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("api")
        self.startup_time: Optional[datetime] = None
        self.startup_user: Optional[str] = None
    
    def _get_operation_name(self, endpoint: str) -> Optional[str]:
        """
        Obtém o nome amigável da operação baseado no endpoint.
        Suporta endpoints com parâmetros dinâmicos (ex: /progress/{job_id}).
        """
        # Tenta match exato primeiro
        if endpoint in self.ENDPOINT_NAMES:
            return self.ENDPOINT_NAMES[endpoint]
        
        # Tenta match parcial para endpoints com parâmetros
        for pattern, name in self.ENDPOINT_NAMES.items():
            if endpoint.startswith(pattern.rstrip('/')):
                return name
        
        return None
    
    def log_block_start(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        client_ip: str,
        user: Optional[str] = None
    ):
        """
        Loga início de um bloco de operação com separadores visuais.
        Para endpoints async, não loga início (a task faz isso).
        """
        # Para endpoints async, não loga início - a background task faz isso
        if endpoint in self.ASYNC_ENDPOINTS:
            return
        
        operation_name = self._get_operation_name(endpoint)
        if not operation_name:
            return  # Não loga bloco para endpoints não mapeados
        
        extra = {
            'request_id': request_id,
            'user': user or 'anonymous',
            'endpoint': endpoint,
            'method': method,
            'client_ip': client_ip
        }
        separator = "=" * 60
        self.logger.info(separator, extra=extra)
        self.logger.info(f"INICIANDO {operation_name.upper()}", extra=extra)
        self.logger.info(separator, extra=extra)
    
    def log_block_end(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Loga fim de um bloco de operação com separadores visuais.
        Para endpoints async, só loga se houver erro (a task loga sucesso).
        """
        # Para endpoints async, só loga se houver erro
        # Sucesso é logado pela background task
        if endpoint in self.ASYNC_ENDPOINTS and status_code < 400 and not error:
            return
        
        operation_name = self._get_operation_name(endpoint)
        if not operation_name:
            return  # Não loga bloco para endpoints não mapeados
        
        extra = {
            'request_id': request_id,
            'user': user or 'anonymous',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'client_ip': client_ip
        }
        
        separator = "=" * 60
        
        if error:
            extra['error'] = error
            self.logger.info(separator, extra=extra)
            # Log simples para automation_api.log (filtro permite "ERRO NA")
            self.logger.error(f"ERRO NA {operation_name.upper()}", extra=extra)
            # Log detalhado para error/debug logs (filtro bloqueia do log principal)
            self.logger.error(f"Detalhe do erro: {error}", extra=extra)
            self.logger.info(separator, extra=extra)
        elif status_code >= 400:
            self.logger.info(separator, extra=extra)
            self.logger.warning(f"FINALIZADA {operation_name.upper()} COM ERRO (STATUS {status_code})", extra=extra)
            self.logger.info(separator, extra=extra)
        else:
            self.logger.info(separator, extra=extra)
            self.logger.info(f"FINALIZADA {operation_name.upper()}", extra=extra)
            self.logger.info(separator, extra=extra)
    
    def log_async_block_start(self, operation_type: str):
        """
        Loga início de bloco para operações assíncronas (background tasks).
        
        Args:
            operation_type: 'masterfiles' ou 'jsons'
        """
        operation_name = self.ASYNC_OPERATIONS.get(operation_type)
        if not operation_name:
            return
        
        separator = "=" * 60
        self.logger.info(separator)
        self.logger.info(f"INICIANDO {operation_name}")
        self.logger.info(separator)
    
    def log_async_block_end(self, operation_type: str, success: bool = True, error: Optional[str] = None):
        """
        Loga fim de bloco para operações assíncronas (background tasks).
        
        Args:
            operation_type: 'masterfiles' ou 'jsons'
            success: Se a operação foi bem sucedida
            error: Mensagem de erro se houver
        """
        operation_name = self.ASYNC_OPERATIONS.get(operation_type)
        if not operation_name:
            return
        
        separator = "=" * 60
        
        if error or not success:
            self.logger.info(separator)
            # Log simples para automation_api.log (filtro permite "ERRO NA")
            self.logger.error(f"ERRO NA {operation_name}")
            # Log detalhado para error/debug logs (filtro bloqueia do log principal)
            if error:
                self.logger.error(f"Detalhe do erro: {error}")
            self.logger.info(separator)
        else:
            self.logger.info(separator)
            self.logger.info(f"FINALIZADA {operation_name}")
            self.logger.info(separator)
    
    def log_startup(self, host: str, port: int, user: Optional[str] = None):
        """Loga início da API"""
        self.startup_time = datetime.now()
        self.startup_user = user
        
        extra = {
            'user': user or 'system',
            'endpoint': 'STARTUP',
            'method': 'SYSTEM'
        }
        self.logger.info(
            f"API iniciada em http://{host}:{port} | Usuario: {user or 'Nao identificado'}",
            extra=extra
        )
    
    def log_shutdown(self):
        """Loga encerramento da API"""
        uptime = None
        if self.startup_time:
            uptime = (datetime.now() - self.startup_time).total_seconds()
        
        extra = {
            'user': self.startup_user or 'system',
            'endpoint': 'SHUTDOWN',
            'method': 'SYSTEM',
            'duration_ms': uptime * 1000 if uptime else 0
        }
        self.logger.info(
            f"API encerrada | Tempo de execucao: {uptime:.2f}s" if uptime else "API encerrada",
            extra=extra
        )
    
    def log_request(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        client_ip: str,
        user: Optional[str] = None,
        payload: Optional[dict] = None
    ):
        """Loga início de uma requisição"""
        extra = {
            'request_id': request_id,
            'user': user or 'anonymous',
            'endpoint': endpoint,
            'method': method,
            'client_ip': client_ip,
            'payload': payload
        }
        self.logger.info(
            f"Request iniciado: {method} {endpoint}",
            extra=extra
        )
    
    def log_response(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Loga resposta de uma requisição - apenas sucesso, erros vão no log_block_end"""
        extra = {
            'request_id': request_id,
            'user': user or 'anonymous',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'client_ip': client_ip
        }
        
        # Não loga erros aqui - log_block_end cuida disso
        if not error and status_code < 400:
            self.logger.info(
                f"Request concluido: {method} {endpoint} -> {status_code}",
                extra=extra
            )
    
    def log_endpoint_start(
        self,
        request_id: str,
        endpoint_name: str,
        params: Optional[dict] = None
    ):
        """Loga início de processamento de um endpoint específico"""
        extra = {
            'request_id': request_id,
            'endpoint': endpoint_name,
            'payload': params
        }
        self.logger.info(
            f"Processando: {endpoint_name}",
            extra=extra
        )
    
    def log_endpoint_success(
        self,
        request_id: str,
        endpoint_name: str,
        result: Optional[dict] = None
    ):
        """Loga sucesso de um endpoint"""
        extra = {
            'request_id': request_id,
            'endpoint': endpoint_name,
            'payload': result
        }
        self.logger.info(
            f"Sucesso: {endpoint_name}",
            extra=extra
        )
    
    def log_endpoint_error(
        self,
        request_id: str,
        endpoint_name: str,
        error: str,
        exc_info: bool = False
    ):
        """Loga erro em um endpoint"""
        extra = {
            'request_id': request_id,
            'endpoint': endpoint_name,
            'error': error
        }
        self.logger.error(
            f"Erro: {endpoint_name} - {error}",
            extra=extra,
            exc_info=exc_info
        )


def shutdown_logging():
    """
    Fecha todos os handlers de logging corretamente.
    Deve ser chamado no shutdown da aplicação para liberar os arquivos.
    """
    root_logger = logging.getLogger()
    
    # Fecha e remove todos os handlers
    handlers = root_logger.handlers[:]
    for handler in handlers:
        try:
            handler.flush()
            handler.close()
            root_logger.removeHandler(handler)
        except Exception:
            pass
    
    # Também fecha handlers do logger 'api'
    api_log = logging.getLogger("api")
    handlers = api_log.handlers[:]
    for handler in handlers:
        try:
            handler.flush()
            handler.close()
            api_log.removeHandler(handler)
        except Exception:
            pass


# Instância global do logger da API
api_logger = APILogger()
