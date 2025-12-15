# Documentação Técnica — Automation API

## 1. Escopo e visão técnica

Automação da geração de artefatos a partir de um "pack" Excel:
- **Masterfiles** (.mas) e **ACX** (.acx)
- **JSONs** (Oracle/PostgreSQL), incluindo modo parâmetros
- **Modelos de exportação** DBN0/DBN1 (.txt)
- **Renomeação** de arquivos DBN1

Frontends disponíveis:
- **Desktop**: PyQt5 (`desktop/`)
- **API REST**: FastAPI (`src/api/`)

**Regra de ouro**: lógica desacoplada da UI (camada `src/services/`)

## 2. Stack e dependências principais

- **Python** 3.11+
- **FastAPI** 0.115.0, **Uvicorn** 0.32.0
- **PyQt5** 5.15.11 (desktop)
- **Pandas** 2.3.2, **NumPy** 2.3.2
- **python_calamine** 0.5.3 (leitura de Excel)
- **Pydantic** 2.9.2, **pydantic-settings** (configuração)

Instalação:
```bash
pip install -r requirements.txt
```

## 3. Estrutura e camadas

```
src/
├── api/                    # Camada de apresentação (FastAPI)
│   ├── main.py             # Entry point, CORS, exception handlers
│   ├── dependencies.py     # Injeção de dependências
│   └── routes/             # Rotas organizadas por domínio
│
├── core/                   # Configurações centrais
│   ├── config.py           # Pydantic BaseSettings
│   ├── constants.py        # Enums e constantes
│   └── exceptions.py       # Exceções customizadas
│
├── services/               # Lógica de negócio (desacoplada)
│   ├── masterfile_service.py
│   ├── json_service.py
│   └── dbn_service.py
│
├── domain/processors/      # Processamento de dados Excel
│   ├── masterfile_processor.py
│   ├── masterfile_data_processor.py
│   ├── json_criador.py
│   └── json_processa_dados_excel.py
│
├── infrastructure/         # I/O e geração de arquivos
│   ├── generators/         # Geradores (mas/acx/json/dbn)
│   └── repositories/       # Acesso a arquivos/Excel
│
└── utils/                  # Utilitários compartilhados
    ├── helpers.py          # ValidationHelper, PathHelper, etc.
    └── response_models.py  # ProcessResult, FileGenerationResult

desktop/                    # App Desktop PyQt5 (separado)
tests/                      # Testes pytest
docs/                       # Documentação

## 4. Fluxos de alto nível
- Masterfiles (UI): [view.py](./view.py) → [masterfile_processor.py](./masterfile_processor.py) → [domain/processors/masterfile_data_processor.py](./domain/processors/masterfile_data_processor.py) → [infrastructure/generators/masterfile_generator.py](./infrastructure/generators/masterfile_generator.py) + [infrastructure/generators/acx_generator.py](./infrastructure/generators/acx_generator.py).
- Masterfiles (API): `POST /api/masterfiles/create_async` → [services/masterfile_service.py](./services/masterfile_service.py) ([create_masterfiles](./masterfile_processor.py)) com BackgroundTasks, progresso e `JOBS`.
- JSONs (UI): [json_criador.py](./json_criador.py) → [domain/processors/json_processa_dados_excel.py](./domain/processors/json_processa_dados_excel.py) → [infrastructure/generators/json_montador_unificado.py](./infrastructure/generators/json_montador_unificado.py).
- JSONs (API): `POST /api/jsons/create_async` → [services/json_service.py](./services/json_service.py) ([create_jsons](./services/json_service.py)) com BackgroundTasks e `JOBS`.
- DBN0/DBN1 (API): [services/dbn_service.py](./services/dbn_service.py) → [infrastructure/generators/modeloDBN0.py](./infrastructure/generators/modeloDBN0.py).
- Renomear DBN1 (UI/API): [renomearDBN1.py](./renomearDBN1.py).

## 5. API (FastAPI)
- Raiz: [api/main.py](./api/main.py)
  - CORS aberto em dev (`allow_origins=["*"]`).
  - Logs: `logging.basicConfig(level=INFO)`.
  - Handler global de exceções: retorna JSON 500 `{success: False, message, error}`.

- Masterfiles: [api/routes/masterfile_routes.py](./api/routes/masterfile_routes.py)
  - `POST /api/masterfiles/create_async`
    - Form-data:
      - `file`: UploadFile (.xls/.xlsx)
      - `inventory_names`: JSON array ou CSV
      - `db_type`: `oracle` ou `postgres`
      - `master_path` (opcional)
    - Output:
      - Cria pasta `MASTERFILES_<excel>_<timestamp>` na raiz do projeto.
      - Retorna `{job_id, status: "accepted", output_path}`.
    - Background job: executa [MasterfileService.create_masterfiles](./services/masterfile_service.py).
  - `GET /api/masterfiles/progress/{job_id}`
    - Lê o progresso via [service.get_progress()](./api/routes/dbn_routes.py).
    - Quando `completed`, inclui o [FileGenerationResult](./response_models.py) no retorno.

- JSONs: [api/routes/json_routes.py](./api/routes/json_routes.py)
  - `POST /api/jsons/create_async`
    - Form-data:
      - `file` (.xls/.xlsx)
      - `inventory_names` (JSON/CSV)
      - `db_type` (`oracle` | `postgres`)
      - `is_parameter` (`true`/`false`)
      - `is_enrichment` (opcional)
    - Output: cria `JSON_<excel>_<timestamp>` na raiz do projeto.
    - Background job: [JsonService.create_jsons](./services/json_service.py).
  - `GET /api/jsons/progress/{job_id}`: idêntico ao de masterfiles.

- DBN: [api/routes/dbn_routes.py](./api/routes/dbn_routes.py)
  - `POST /api/dbn/dbn0/create`
    - Form-data: `dbn_names` (JSON/CSV), `output_path`, `schema` (opcional).
  - `POST /api/dbn/dbn1/create`
    - Form-data: idem ao DBN0 + `classe` (obrigatório).
  - `POST /api/dbn/dbn1/rename`
    - Form-data: `path` (pasta com arquivos a renomear).

- Orquestração de jobs (rotas masterfile/json):
  - `JOBS: dict[job_id -> {service, output_dir, completed, created_at, result?}]`.
  - TTL: 3600s; limpeza periódica. Máximo: 200 jobs.

## 6. Services (desacoplados de UI)
- [services/masterfile_service.py](./services/masterfile_service.py) — [create_masterfiles(...) -> FileGenerationResult](./masterfile_processor.py)
  - Validações:
    - Arquivo presente e extensão `.xls|.xlsx`.
    - `inventory_names` não vazio e sem duplicatas (ValidationHelper).
    - `db_type` ∈ {oracle, postgres, postgresql} (normaliza `postgresql` → `postgres`).
  - Saída:
    - Lista `.mas` e `.acx` gerados (varre `output_path`).
    - `progress` atualizado via callback e `BaseService.current_progress`.

- [services/json_service.py](./services/json_service.py) — [create_jsons(...) -> FileGenerationResult](./services/json_service.py)
  - Similar em validações.
  - Usa [FileRepository](./infrastructure/repositories/file_repository.py) para listar `.json` gerados em `output_path`.
  - `is_parameter=True` liga modo de parâmetros.

- [services/dbn_service.py](./services/dbn_service.py) — [create_dbn_model(...) -> FileGenerationResult](./services/dbn_service.py)
  - `dbn_type` ∈ {DBN0, DBN1}; `classe` obrigatório para DBN1.
  - Gera `MODELO_DE_EXPORTACAO_<tipo>.txt`.

## 7. Processamento de Excel (Domain)
- Leitura via [helpers.ExcelHelper](./helpers.py) (pandas/engine='calamine').
- Padrão do cabeçalho: 4ª linha do Excel (são lidas 4 linhas para validar, header na linha de índice 2).
- [SheetConstants](./helpers.py) define:
  - Abas, colunas de interesse e checagens de cabeçalho para Masterfiles e JSONs.
- Pipeline [BaseDataProcessor.process_data()](./domain/processors/masterfile_data_processor.py):
  - Carrega DataFrames.
  - Valida cabeçalhos esperados.
  - Extrai índices de colunas e lê dados.
  - Filtra por `inventory_name`.
  - Pós-processamento:
    - Masterfiles: `data_sources_list`, `data_sources_attr_list`, `data_sources_map_list`, `pk_list`, `table_name_dic`.
    - JSONs: `data_sources_list`, `data_sources_attr_list`.

## 8. Geração de artefatos (Infrastructure)
- [infrastructure/generators/masterfile_generator.py](./infrastructure/generators/masterfile_generator.py)
  - Ajusta casing e `SUFFIX` via [DatabaseHelper](./helpers.py) (Oracle: upper/`SQLORA`; Postgres: lower/`SQLPSTGR`).
  - Escreve `SEGMENT`, `SEGTYPE`, `PARENT`, `CRFILE`, `JOIN_WHERE` para joins (Data Sources Map).
- [infrastructure/generators/acx_generator.py](./infrastructure/generators/acx_generator.py)
  - Gera `.acx` por inventário, usando schema e chaves (PKs) quando presentes.
- [infrastructure/generators/json_montador_unificado.py](./infrastructure/generators/json_montador_unificado.py)
  - Config específica por banco (tipos SQL, casing), modo `is_parameter`, conversões de tempo, validações.
- [infrastructure/generators/modeloDBN0.py](./infrastructure/generators/modeloDBN0.py)
  - Cria arquivo de modelo (`.txt`) para DBN0/DBN1 (append por item).
- Compatibilidade: [infrastructure/generators/modeloDBN1.py](./infrastructure/generators/modeloDBN1.py) reexporta [DBNModel](./infrastructure/generators/modeloDBN0.py).

## 9. Helpers e utilidades
- [helpers.py](./helpers.py)
  - [ValidationHelper](./helpers.py): duplicatas e faltantes (sem UI).
  - [ProgressHelper](./helpers.py): wrapper para callbacks de progresso.
  - [PathHelper](./helpers.py): raiz do projeto, montagem de paths e diretórios.
  - [FormHelper](./helpers.py): parse de listas (JSON/CSV) nas rotas.
  - [DatabaseHelper](./helpers.py): parâmetros por banco (casing, suffix, origem do conteúdo).
  - [ExcelHelper](./helpers.py): [read_sheets](./helpers.py), [read_columns](./helpers.py), validação de cabeçalho.
  - [AlertsAdapter](./helpers.py) e [alerta.py](./alerta.py): abstração de mensagens (UI vs. logs).
- UI helper: [utils.py](./utils.py) — [CreateAndDeleteFolder](./utils.py) (pasta de saída da UI).

## 10. Modelos de resposta e exceções
- [response_models.py](./response_models.py)
  - [StatusType](./response_models.py): SUCCESS | ERROR | WARNING | INFO.
  - [ValidationResult](./response_models.py), [ProcessResult](./response_models.py), [FileGenerationResult](./response_models.py).
- [exceptions.py](./exceptions.py)
  - [AutomationError](./exceptions.py), [ValidationError](./exceptions.py), [DuplicateError](./exceptions.py), [MissingElementsError](./exceptions.py), [ProcessingError](./exceptions.py), etc.

## 11. Saída e convenções de pasta
- API: [PathHelper.get_project_root()](./helpers.py) + `MASTERFILES_<excel>_<ts>` / `JSON_<excel>_<ts>`.
- UI: ao lado do Excel via [CreateAndDeleteFolder](./utils.py) (`MASTERFILES_*` / `JSON_*`).

## 12. Logging, segurança e CORS
- Logs: nível INFO, handler global 500 com JSON.
- CORS: liberado em dev. Em produção, restringir domínios confiáveis.

## 13. Build e execução
- Desktop:
  - `python desktop/app.py`
  - PyInstaller (Windows) — consulte documentação específica
- API:
  - `python run.py` ou `uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload`
  - Docs: http://localhost:8080/docs e http://localhost:8080/redoc

## 14. Testes
- [test_architecture.py](./test_architecture.py)
  - Verifica imports críticos, serviços e helpers.
  - Execução: `python test_architecture.py` (main imprime relatório e exit code).

## 15. Limitações e pontos de atenção
- Excel precisa seguir rigorosamente o padrão (abas e cabeçalhos na 4ª linha).
- `is_enrichment` é aceito na rota de JSON; o uso no service pode ser estendido conforme necessidade.
- Não há modelos Pydantic nas respostas das rotas; retornos são dicts compatíveis com os modelos de resposta.

## 16. Extensões recomendadas
- Padronizar respostas das rotas com Pydantic.
- Cobertura de testes unitários para Services e Generators.
- Parâmetros de build/paths via variáveis de ambiente (12-factor).