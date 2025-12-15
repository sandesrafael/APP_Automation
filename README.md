# 🚀 Automation API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)

**REST API para automação de geração de Masterfiles, JSONs e modelos DBNO e DBN1 para Oracle/PostgreSQL**

[Início Rápido](#-início-rápido) •
[Documentação](#-documentação) •
[Docker](#-docker) •
[API](#-endpoints-da-api) •
[Testes](#-testes)

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Pré-requisitos](#-pré-requisitos)
- [Início Rápido](#-início-rápido)
- [Docker](#-docker)
- [Endpoints da API](#-endpoints-da-api)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Configuração](#-configuração)
- [Testes](#-testes)
- [Documentação](#-documentação)
- [Contribuição](#-contribuição)

---

## 📖 Sobre o Projeto

API REST desenvolvida em **FastAPI** para automação de geração de artefatos a partir de arquivos Excel (packs):

- **Masterfiles** (.mas) e **ACX** (.acx) para inventários
- **JSONs** para Oracle e PostgreSQL (modo parâmetros e enrichment)
- **Modelos de exportação** DBN0/DBN1 (.txt)

### Arquitetura

O projeto segue uma **arquitetura em camadas** desacoplada:

```
┌─────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                    │  ← Rotas REST + Middleware
├─────────────────────────────────────────────────────┤
│              Service Layer                          │  ← Lógica de negócio
├─────────────────────────────────────────────────────┤
│              Domain Layer                           │  ← Processadores de dados
├─────────────────────────────────────────────────────┤
│           Infrastructure Layer                      │  ← Geradores + Repositórios
└─────────────────────────────────────────────────────┘
```

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|----------------|-----------|
| **Masterfiles** | Geração de arquivos .mas e .acx a partir de Excel |
| **JSONs** | Criação de JSONs Oracle/PostgreSQL com modo parâmetros |
| **DBN0/DBN1** | Modelos de exportação para diferentes schemas |
| **Async Jobs** | Processamento assíncrono com acompanhamento de progresso |
| **Logging** | Sistema de logs estruturado com request tracking |
| **Docker** | Containerização pronta para produção |

---

## 📦 Pré-requisitos

- **Python** 3.11 ou superior
- **pip** (gerenciador de pacotes Python)
- **Docker** e **Docker Compose** (opcional, para containerização)

---

## 🚀 Início Rápido

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/APP_Automation.git
cd APP_Automation/APP_Automation-refactor
```

### 2. Criar ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente (opcional)

```bash
# Copiar template
cp .env.example .env

# Editar conforme necessário
# Exemplo de .env:
# HOST=0.0.0.0
# PORT=8080
# DEBUG=false
```

### 5. Executar a API

```bash
# Via script principal
python run.py

# OU via uvicorn diretamente
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

### 6. Acessar a documentação

| Recurso | URL |
|---------|-----|
| **Swagger UI** | http://localhost:8080/docs |
| **ReDoc** | http://localhost:8080/redoc |
| **OpenAPI JSON** | http://localhost:8080/openapi.json |

---

## 🐳 Docker

### Build e execução com Docker Compose (Recomendado)

```bash
# Build e iniciar em background
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Build manual com Docker

```bash
# Build da imagem
docker build -t automation-api .

# Executar container
docker run -d \
  --name automation-api \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/output:/app/output \
  automation-api
```

### Variáveis de ambiente Docker

| Variável | Default | Descrição |
|----------|---------|-----------|
| `HOST` | 0.0.0.0 | Host do servidor |
| `PORT` | 8080 | Porta do servidor |
| `RELOAD` | false | Hot-reload (apenas dev) |
| `OUTPUT_BASE_PATH` | /app/output | Pasta de saída |
| `LOG_LEVEL` | INFO | Nível de log |

### Volumes

```yaml
volumes:
  - ./logs:/app/logs      # Logs persistentes
  - ./output:/app/output  # Arquivos gerados
```

---

## 📡 Endpoints da API

### Health & Info

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações da API |
| GET | `/health` | Health check |

### Masterfiles

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/masterfiles/create_async` | Criar masterfiles (assíncrono) |
| GET | `/api/masterfiles/progress/{job_id}` | Verificar progresso do job |

**Exemplo de requisição:**

```bash
curl -X POST http://localhost:8080/api/masterfiles/create_async \
  -F "file=@pack.xlsx" \
  -F 'inventory_names=["INV_A","INV_B"]' \
  -F "db_type=postgres"
```

**Resposta:**

```json
{
  "job_id": "abc123def456",
  "status": "accepted",
  "output_path": "/app/output/MASTERFILES_pack_20241215_120000"
}
```

### JSONs

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/jsons/create_async` | Criar JSONs (assíncrono) |
| GET | `/api/jsons/progress/{job_id}` | Verificar progresso do job |

**Exemplo de requisição:**

```bash
curl -X POST http://localhost:8080/api/jsons/create_async \
  -F "file=@pack.xlsx" \
  -F 'inventory_names=["INV_A","INV_B"]' \
  -F "db_type=oracle" \
  -F "is_parameter=true" \
  -F "is_enrichment=false"
```

### DBN (Modelos de Exportação)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/dbn/dbn0/create` | Criar modelo DBN0 |
| POST | `/api/dbn/dbn1/create` | Criar modelo DBN1 |
| POST | `/api/dbn/dbn1/rename` | Renomear arquivos DBN1 |
| GET | `/api/dbn/progress` | Verificar progresso |

**Exemplo DBN0:**

```bash
curl -X POST http://localhost:8080/api/dbn/dbn0/create \
  -F 'dbn_names=["DBN0_A","DBN0_B"]' \
  -F "output_path=/caminho/saida" \
  -F "schema=PUBLIC"
```

**Exemplo DBN1:**

```bash
curl -X POST http://localhost:8080/api/dbn/dbn1/create \
  -F 'dbn_names=["DBN1_A"]' \
  -F "output_path=/caminho/saida" \
  -F "schema=PUBLIC" \
  -F "classe=MinhaClasse"
```

### Formato de Resposta

Todas as rotas retornam JSON padronizado:

```json
{
  "success": true,
  "message": "Masterfiles criados com sucesso! (5 arquivos)",
  "files_created": ["/path/file1.mas", "/path/file2.acx"],
  "total_files": 5,
  "output_path": "/path/output",
  "errors": null,
  "warnings": null
}
```

---

## 📁 Estrutura do Projeto

```
APP_Automation-refactor/
│
├── src/                              # Código fonte principal
│   ├── api/                          # FastAPI Application
│   │   ├── main.py                   # Entry point + middleware
│   │   ├── dependencies.py           # Injeção de dependências
│   │   ├── middleware/               # Middlewares (logging)
│   │   └── routes/                   # Rotas organizadas por domínio
│   │       ├── masterfile_routes.py
│   │       ├── json_routes.py
│   │       └── dbn_routes.py
│   │
│   ├── core/                         # Configurações centrais
│   │   ├── config.py                 # Pydantic Settings
│   │   ├── constants.py              # Constantes e enums
│   │   ├── exceptions.py             # Exceções customizadas
│   │   └── logging_config.py         # Configuração de logs
│   │
│   ├── services/                     # Lógica de negócio
│   │   ├── base_service.py           # Classe base com progresso
│   │   ├── masterfile_service.py
│   │   ├── json_service.py
│   │   └── dbn_service.py
│   │
│   ├── domain/processors/            # Processadores de dados Excel
│   │   ├── masterfile_processor.py
│   │   ├── masterfile_data_processor.py
│   │   ├── json_criador.py
│   │   └── json_processa_dados_excel.py
│   │
│   ├── infrastructure/               # I/O e geração de arquivos
│   │   ├── generators/               # Geradores de artefatos
│   │   │   ├── masterfile_generator.py
│   │   │   ├── acx_generator.py
│   │   │   ├── json_montador_unificado.py
│   │   │   ├── modeloDBN0.py
│   │   │   └── renomearDBN1.py
│   │   └── repositories/             # Acesso a arquivos/Excel
│   │       ├── file_repository.py
│   │       └── excel_repository.py
│   │
│   ├── models/                       # Schemas Pydantic
│   └── utils/                        # Utilitários
│       ├── helpers.py                # ValidationHelper, PathHelper, etc.
│       └── response_models.py        # ProcessResult, FileGenerationResult
│
├── desktop/                          # App Desktop PyQt5 (opcional)
├── tests/                            # Testes (unit, integration, e2e)
├── docs/                             # Documentação detalhada
├── logs/                             # Logs da aplicação
├── output/                           # Arquivos gerados
│
├── run.py                            # Entry point da API
├── Dockerfile                        # Build da imagem Docker
├── docker-compose.yml                # Orquestração Docker
├── requirements.txt                  # Dependências produção
├── requirements-dev.txt              # Dependências desenvolvimento
├── pytest.ini                        # Configuração pytest
└── .env.example                      # Template de variáveis
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário:

| Variável | Default | Descrição |
|----------|---------|-----------|
| `APP_NAME` | Automation API | Nome da aplicação |
| `VERSION` | 1.0.0 | Versão |
| `HOST` | 0.0.0.0 | Host do servidor |
| `PORT` | 8080 | Porta do servidor |
| `RELOAD` | true | Hot-reload (dev) |
| `DEBUG` | false | Modo debug |
| `CORS_ORIGINS` | ["*"] | Origens permitidas |
| `DEFAULT_DB_TYPE` | postgres | Tipo de banco padrão |
| `OUTPUT_BASE_PATH` | (raiz do projeto) | Pasta de saída |

### Configuração de Logs

Os logs são salvos em `logs/` com rotação automática:

- `automation_api.log` - Logs gerais da API
- Formato estruturado com request_id para rastreamento

---

## 🧪 Testes

### Instalar dependências de desenvolvimento

```bash
pip install -r requirements-dev.txt
```

### Executar todos os testes

```bash
pytest
```

### Executar por tipo

```bash
# Testes unitários
pytest tests/test_unit/ -v

# Testes de integração
pytest tests/test_integration/ -v

# Testes E2E
pytest tests/test_e2e/ -v
```

### Cobertura de código

```bash
# Relatório no terminal
pytest --cov=src --cov-report=term-missing

# Relatório HTML
pytest --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

### Comandos úteis

```bash
# Modo verboso
pytest -v

# Parar no primeiro erro
pytest -x

# Testes específicos
pytest tests/test_integration/test_api_health.py -v

# Por marcador
pytest -m integration
```

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [API.md](docs/API.md) | Referência completa da API REST |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura e design do projeto |
| [DOCUMENTACAO_TECNICA.md](docs/DOCUMENTACAO_TECNICA.md) | Detalhes técnicos de implementação |
| [DOCUMENTACAO_FUNCIONAL.md](docs/DOCUMENTACAO_FUNCIONAL.md) | Guia funcional para usuários |
| [TESTING.md](docs/TESTING.md) | Guia completo de testes |

---

## 🔒 Segurança

- **CORS**: Configurado como `*` por padrão. **Restrinja em produção!**
- **Autenticação**: Não implementada. Adicione conforme necessário.
- **Uploads**: Valide tipos de arquivo em produção.
- **Logs**: Sensível a dados? Configure mascaramento.

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Padrões de código

```bash
# Formatação
black src/ tests/

# Ordenação de imports
isort src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/
```

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 📞 Suporte

- Consulte a [documentação](docs/)
- Abra uma [issue](https://github.com/seu-usuario/APP_Automation/issues)

---

<div align="center">

**Desenvolvido com ❤️ usando FastAPI**

</div>
