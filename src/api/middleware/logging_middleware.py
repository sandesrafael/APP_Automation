"""
Logging Middleware
Middleware para logging automático de todas as requisições
"""
import time
import uuid
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.logging_config import api_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que automaticamente loga todas as requisições e respostas.
    
    Captura:
    - Request ID único para cada requisição
    - Método HTTP e endpoint
    - IP do cliente
    - Tempo de resposta
    - Status code
    - Erros se ocorrerem
    """
    
    # Endpoints para ignorar no log (docs, healthcheck, static, etc)
    SKIP_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/health",
        "/favicon.ico",
        "/openapi.json"
    }
    
    def __init__(self, app: ASGIApp, skip_paths: Optional[set] = None):
        super().__init__(app)
        if skip_paths:
            self.skip_paths = skip_paths
        else:
            self.skip_paths = self.SKIP_PATHS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignora paths específicos
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Gera ID único para a requisição
        request_id = str(uuid.uuid4())
        
        # Adiciona request_id ao state para uso nos endpoints
        request.state.request_id = request_id
        request.state.user = self._get_user(request)
        
        # Obtém informações da requisição
        method = request.method
        endpoint = request.url.path
        client_ip = self._get_client_ip(request)
        user = request.state.user
        
        # Captura payload para POST/PUT/PATCH (skip multipart/form-data to avoid consuming body)
        payload = None
        content_type = request.headers.get("Content-Type", "")
        if method in {"POST", "PUT", "PATCH"} and "multipart/form-data" not in content_type:
            payload = await self._get_payload(request)
        
        # Log de início do bloco (Iniciando a X)
        api_logger.log_block_start(
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            client_ip=client_ip,
            user=user
        )
        
        # Log de início da requisição
        api_logger.log_request(
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            client_ip=client_ip,
            user=user,
            payload=payload
        )
        
        # Processa a requisição
        start_time = time.perf_counter()
        error_message = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Para HTTPException (status >= 400), tenta extrair mensagem de erro do response
            if status_code >= 400:
                # Lê o corpo da resposta para extrair a mensagem de erro
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                
                # Reconstrói o response com o corpo lido
                from starlette.responses import Response
                response = Response(
                    content=body_bytes,
                    status_code=status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                # Tenta extrair mensagem de erro do JSON
                try:
                    import json
                    body_json = json.loads(body_bytes.decode('utf-8'))
                    error_message = body_json.get('detail') or body_json.get('message') or body_json.get('error')
                except:
                    pass
                    
        except Exception as e:
            error_message = str(e)
            status_code = 500
            raise
        finally:
            # Calcula tempo de resposta
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log de resposta
            api_logger.log_response(
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user=user,
                error=error_message
            )
            
            # Log de fim do bloco (Finalizada a X)
            api_logger.log_block_end(
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user=user,
                error=error_message
            )
        
        # Adiciona request_id ao header da resposta
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP do cliente, considerando proxies"""
        # Verifica headers de proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback para IP direto
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user(self, request: Request) -> Optional[str]:
        """
        Obtém usuário da requisição.
        Por enquanto retorna None, será implementado com autenticação.
        """
        # TODO: Implementar captura de usuário via header/token
        # Exemplo futuro:
        # auth_header = request.headers.get("Authorization")
        # user_header = request.headers.get("X-User-ID")
        return request.headers.get("X-User-ID")
    
    async def _get_payload(self, request: Request) -> Optional[dict]:
        """
        Tenta capturar o payload da requisição.
        Limita tamanho para evitar logs muito grandes.
        """
        try:
            # Lê o body
            body = await request.body()
            
            if not body:
                return None
            
            # Limita tamanho do log (máximo 1KB)
            if len(body) > 1024:
                return {"_truncated": True, "_size": len(body)}
            
            # Tenta decodificar como JSON
            import json
            try:
                return json.loads(body.decode())
            except:
                # Se não for JSON, retorna indicação do tipo
                content_type = request.headers.get("Content-Type", "")
                if "multipart/form-data" in content_type:
                    return {"_type": "multipart/form-data"}
                return {"_type": content_type, "_size": len(body)}
        except:
            return None


def get_request_id(request: Request) -> str:
    """Helper para obter request_id do state"""
    return getattr(request.state, 'request_id', 'unknown')


def get_current_user(request: Request) -> Optional[str]:
    """Helper para obter usuário do state"""
    return getattr(request.state, 'user', None)
