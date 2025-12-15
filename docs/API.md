# API Documentation

## Visão Geral

REST API para automação de geração de Masterfiles, JSONs e modelos DBN para Oracle/PostgreSQL.

## Arquitetura

```
src/api/
├── main.py              # Entry point FastAPI + lifespan + exception handlers
├── dependencies.py      # Injeção de dependências
├── middleware/          # Middlewares
│   └── logging_middleware.py  # Logging estruturado com request_id
└── routes/
    ├── masterfile_routes.py   # Rotas de Masterfiles
    ├── json_routes.py         # Rotas de JSONs
    └── dbn_routes.py          # Rotas de DBN0/DBN1
```

## Base URL

```
http://localhost:8080
```

## Executando a API

```bash
# Via run.py
python run.py

# Via uvicorn diretamente
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

## Autenticação

Sem autenticação implementada. Em produção, adicionar conforme necessário (JWT, OAuth2, etc).

---

## Endpoints

### Health & Info

#### GET /
Endpoint raiz com informações da API.

**Response:**
```json
{
  "message": "Automation API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET /health
Health check endpoint para monitoramento.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "masterfile": "available",
    "json": "available",
    "dbn": "available",
    "rename_dbn1": "available"
  }
}
```

---

### Masterfiles

#### POST /api/masterfiles/create_async
Cria masterfiles de forma assíncrona. Retorna um `job_id` para acompanhamento.

**Form Data:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| file | File | Sim | Arquivo Excel do pack (.xls ou .xlsx) |
| inventory_names | string | Sim | JSON array ou CSV de inventory names |
| db_type | string | Sim | Tipo de banco: "oracle" ou "postgres" |
| master_path | string | Não | Caminho do masterfile (opcional) |

**Exemplo:**
```bash
curl -X POST http://localhost:8080/api/masterfiles/create_async \
  -F "file=@pack.xlsx" \
  -F 'inventory_names=["INV_A","INV_B"]' \
  -F "db_type=postgres"
```

**Response (202 Accepted):**
```json
{
  "job_id": "abc123def456",
  "status": "accepted",
  "output_path": "/app/output/MASTERFILES_pack_20241215_120000"
}
```

#### GET /api/masterfiles/progress/{job_id}
Retorna progresso e resultado do job assíncrono.

**Path Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| job_id | string | ID do job retornado pelo create_async |

**Response (em processamento):**
```json
{
  "job_id": "abc123def456",
  "progress": 50,
  "status": "processing"
}
```

**Response (concluído com sucesso):**
```json
{
  "job_id": "abc123def456",
  "progress": 100,
  "status": "completed",
  "completed": true,
  "success": true,
  "message": "Masterfiles e ACX criados com sucesso! (10 arquivos)",
  "files_created": ["/path/file1.mas", "/path/file2.acx"],
  "total_files": 10,
  "output_path": "/app/output/MASTERFILES_pack_20241215_120000",
  "errors": null,
  "warnings": null
}
```

**Response (erro):**
```json
{
  "job_id": "abc123def456",
  "progress": 100,
  "status": "completed",
  "completed": true,
  "success": false,
  "message": "Erro: Arquivo Excel inválido"
}
```

---

### JSONs

#### POST /api/jsons/create_async
Cria arquivos JSON de forma assíncrona.

**Form Data:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| file | File | Sim | Arquivo Excel do pack (.xls ou .xlsx) |
| inventory_names | string | Sim | JSON array ou CSV de inventory names |
| db_type | string | Sim | Tipo de banco: "oracle" ou "postgres" |
| is_parameter | boolean | Sim | Incluir dados de parâmetros |
| is_enrichment | boolean | Não | Incluir dados de enrichment (default: false) |

**Exemplo:**
```bash
curl -X POST http://localhost:8080/api/jsons/create_async \
  -F "file=@pack.xlsx" \
  -F 'inventory_names=["INV_A","INV_B"]' \
  -F "db_type=oracle" \
  -F "is_parameter=true" \
  -F "is_enrichment=false"
```

**Response:**
```json
{
  "job_id": "xyz789abc123",
  "status": "accepted",
  "output_path": "/app/output/JSON_pack_20241215_120000"
}
```

#### GET /api/jsons/progress/{job_id}
Retorna progresso e resultado do job de JSON.

**Response:**
```json
{
  "job_id": "xyz789abc123",
  "progress": 100,
  "status": "completed",
  "completed": true,
  "success": true,
  "message": "JSONs criados com sucesso! (5 arquivos)",
  "files_created": ["/path/file1.json", "/path/file2.json"],
  "total_files": 5,
  "output_path": "/app/output/JSON_pack_20241215_120000"
}
```

---

### DBN (Modelos de Exportação)

#### POST /api/dbn/dbn0/create
Cria modelo de exportação DBN0.

**Form Data:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| dbn_names | string | Sim | JSON array ou CSV de nomes DBN |
| output_path | string | Sim | Caminho do diretório de saída |
| schema | string | Não | Schema do banco (default: null) |

**Exemplo:**
```bash
curl -X POST http://localhost:8080/api/dbn/dbn0/create \
  -F 'dbn_names=["DBN0_A","DBN0_B"]' \
  -F "output_path=/caminho/saida" \
  -F "schema=PUBLIC"
```

**Response:**
```json
{
  "success": true,
  "message": "Modelo DBN0 criado com sucesso! (1 arquivo)",
  "files_created": ["/caminho/saida/MODELO_DE_EXPORTACAO_DBN0.txt"],
  "total_files": 1,
  "output_path": "/caminho/saida",
  "errors": null,
  "warnings": null
}
```

#### POST /api/dbn/dbn1/create
Cria modelo de exportação DBN1.

**Form Data:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| dbn_names | string | Sim | JSON array ou CSV de nomes DBN |
| output_path | string | Sim | Caminho do diretório de saída |
| schema | string | Não | Schema do banco (default: null) |
| classe | string | Sim | Nome lógico da classe |

**Exemplo:**
```bash
curl -X POST http://localhost:8080/api/dbn/dbn1/create \
  -F 'dbn_names=["DBN1_A","DBN1_B"]' \
  -F "output_path=/caminho/saida" \
  -F "schema=PUBLIC" \
  -F "classe=MinhaClasseLogica"
```

**Response:**
```json
{
  "success": true,
  "message": "Modelo DBN1 criado com sucesso! (1 arquivo)",
  "files_created": ["/caminho/saida/MODELO_DE_EXPORTACAO_DBN1.txt"],
  "total_files": 1,
  "output_path": "/caminho/saida",
  "errors": null,
  "warnings": null
}
```

#### POST /api/dbn/dbn1/rename
Renomeia arquivos DBN1 em um diretório.

**Form Data:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| path | string | Sim | Caminho do diretório com arquivos DBN1 |

**Exemplo:**
```bash
curl -X POST http://localhost:8080/api/dbn/dbn1/rename \
  -F "path=/caminho/para/pasta"
```

**Response:**
```json
{
  "success": true,
  "message": "Arquivos DBN1 renomeados com sucesso",
  "path": "/caminho/para/pasta"
}
```

#### GET /api/dbn/progress
Retorna progresso atual do processamento DBN.

**Response:**
```json
{
  "progress": 100,
  "status": "completed"
}
```

---

## Formato de Resposta Padrão

### Sucesso

```json
{
  "success": true,
  "message": "Descrição do sucesso",
  "files_created": ["lista", "de", "arquivos"],
  "total_files": 3,
  "output_path": "/caminho/saida",
  "errors": null,
  "warnings": null
}
```

### Erro

```json
{
  "success": false,
  "message": "Descrição do erro",
  "error": "TipoDoErro",
  "request_id": "uuid-para-rastreamento"
}
```

---

## Códigos HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 202 | Aceito (jobs assíncronos) |
| 400 | Bad Request / Erro de validação |
| 404 | Não encontrado (job_id inválido) |
| 422 | Erro de validação de entrada |
| 500 | Erro interno do servidor |

---

## Sistema de Jobs Assíncronos

Os endpoints `create_async` utilizam `BackgroundTasks` do FastAPI:

- **TTL**: Jobs expiram após 3600 segundos (1 hora)
- **Máximo**: 200 jobs simultâneos em memória
- **Limpeza**: Automática ao atingir limites

### Fluxo típico:

1. `POST /api/masterfiles/create_async` → recebe `job_id`
2. Poll em `GET /api/masterfiles/progress/{job_id}` até `completed: true`
3. Verificar `success` para resultado final

---

## Documentação Interativa

| Recurso | URL |
|---------|-----|
| **Swagger UI** | http://localhost:8080/docs |
| **ReDoc** | http://localhost:8080/redoc |
| **OpenAPI JSON** | http://localhost:8080/openapi.json |

---

## Logging

Todas as requisições são logadas com:

- **request_id**: UUID único para rastreamento
- **Método e path**
- **Status code e tempo de resposta**
- **Erros detalhados quando aplicável**

Logs salvos em: `logs/automation_api.log`
