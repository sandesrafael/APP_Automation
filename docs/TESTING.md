# Documentação de Testes - APP_Automation

## 📋 Visão Geral

Esta documentação explica a estrutura de testes do projeto APP_Automation, como executar os testes e como interpretar os resultados.

## 🏗️ Estrutura de Testes

```
tests/
├── __init__.py              # Pacote de testes
├── conftest.py              # Fixtures compartilhadas
├── pytest.ini               # Configuração do pytest
│
├── test_unit/               # Testes Unitários
│   ├── test_services/       # Testes de serviços
│   │   ├── test_masterfile_service.py
│   │   ├── test_json_service.py
│   │   └── test_dbn_service.py
│   ├── test_models/         # Testes de modelos
│   │   └── test_response_models.py
│   └── test_utils/          # Testes de utilitários
│       ├── test_helpers.py
│       └── test_dependencies.py
│
├── test_integration/        # Testes de Integração
│   ├── test_api_health.py   # Endpoints de saúde
│   ├── test_api_masterfiles.py
│   ├── test_api_jsons.py
│   └── test_api_dbn.py
│
├── test_e2e/                # Testes End-to-End
│   └── test_workflows.py
│
├── test_api/                # Testes de API (legado)
│   └── test_health.py
│
└── fixtures/                # Dados de teste
    └── __init__.py
```

## 📝 Tipos de Testes

### 1. Testes Unitários (`test_unit/`)

Testam componentes isolados sem dependências externas.

**O que testam:**
- Serviços (`MasterfileService`, `JsonService`, `DBNService`)
- Modelos de resposta (`ValidationResult`, `ProcessResult`, `FileGenerationResult`)
- Utilitários (`ValidationHelper`, `PathHelper`, `TextHelper`, etc.)
- Dependências (`TempFileManager`, `JobRegistry`)

**Características:**
- ✅ Rápidos (< 1 segundo cada)
- ✅ Não dependem de arquivos externos
- ✅ Usam mocks para isolar comportamento
- ✅ Alta cobertura de código

### 2. Testes de Integração (`test_integration/`)

Testam a comunicação entre componentes e APIs.

**O que testam:**
- Endpoints REST da API
- Validação de entrada
- Respostas HTTP
- Headers e CORS

**Endpoints cobertos:**
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/openapi.json` | GET | Schema OpenAPI |
| `/api/masterfiles/create_async` | POST | Criar masterfiles |
| `/api/masterfiles/progress/{job_id}` | GET | Progresso masterfiles |
| `/api/jsons/create_async` | POST | Criar JSONs |
| `/api/jsons/progress/{job_id}` | GET | Progresso JSONs |
| `/api/dbn/dbn0/create` | POST | Criar DBN0 |
| `/api/dbn/dbn1/create` | POST | Criar DBN1 |
| `/api/dbn/dbn1/rename` | POST | Renomear DBN1 |
| `/api/dbn/progress` | GET | Progresso DBN |

### 3. Testes End-to-End (`test_e2e/`)

Testam fluxos completos de usuário.

**O que testam:**
- Fluxo completo de criação de Masterfiles
- Fluxo completo de criação de JSONs
- Fluxo completo de criação de DBN
- Cenários de erro
- Fluxos concorrentes

---

## 🚀 Como Executar os Testes

### Pré-requisitos

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt
```

### Comandos Básicos

```bash
# Executar TODOS os testes
pytest

# Executar com output detalhado
pytest -v

# Executar com mais detalhes
pytest -vv
```

### Executar por Tipo

```bash
# Apenas testes unitários
pytest tests/test_unit/ -v

# Apenas testes de integração
pytest tests/test_integration/ -v

# Apenas testes E2E
pytest tests/test_e2e/ -v
```

### Executar por Marcador

```bash
# Testes marcados como 'unit'
pytest -m unit

# Testes marcados como 'integration'
pytest -m integration

# Testes marcados como 'e2e'
pytest -m e2e

# Testes marcados como 'api'
pytest -m api
```

### Executar Arquivo Específico

```bash
# Teste específico de serviço
pytest tests/test_unit/test_services/test_masterfile_service.py -v

# Teste específico de API
pytest tests/test_integration/test_api_health.py -v
```

### Executar Teste Específico

```bash
# Uma classe de teste específica
pytest tests/test_unit/test_services/test_masterfile_service.py::TestMasterfileServiceValidation -v

# Um teste específico
pytest tests/test_unit/test_services/test_masterfile_service.py::TestMasterfileServiceValidation::test_validate_empty_path -v
```

### Opções Úteis

```bash
# Parar no primeiro erro
pytest -x

# Parar após N erros
pytest --maxfail=3

# Mostrar output de print
pytest -s

# Executar testes que falharam na última execução
pytest --lf

# Executar testes novos ou modificados primeiro
pytest --nf
```

---

## 📊 Cobertura de Código

### Gerar Relatório de Cobertura

```bash
# Relatório no terminal
pytest --cov=src --cov-report=term-missing

# Relatório HTML (abre em htmlcov/index.html)
pytest --cov=src --cov-report=html

# Relatório XML (para CI/CD)
pytest --cov=src --cov-report=xml
```

### Meta de Cobertura

| Componente | Meta | Descrição |
|------------|------|-----------|
| Services | 80%+ | Lógica de negócio crítica |
| Models | 90%+ | Estruturas de dados simples |
| Utils | 85%+ | Funções utilitárias |
| API Routes | 70%+ | Endpoints REST |

---

## 🔧 Fixtures Disponíveis

Fixtures são funções que fornecem dados e configurações para os testes.

### Fixtures de Cliente

```python
# Cliente de teste para API
def test_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

### Fixtures de Diretório

```python
# Diretório temporário com cleanup automático
def test_files(temp_directory):
    # temp_directory é limpo após o teste
    file_path = os.path.join(temp_directory, "test.txt")
```

### Fixtures de Dados

```python
# Dados de teste pré-definidos
def test_inventory(sample_inventory_names):
    # sample_inventory_names = ["INV_TEST_A", "INV_TEST_B"]
    assert len(sample_inventory_names) == 2
```

### Fixtures de Serviços

```python
# Instâncias de serviços
def test_service(masterfile_service):
    result = masterfile_service.validate_inputs(...)
```

### Lista Completa de Fixtures

| Fixture | Tipo | Descrição |
|---------|------|-----------|
| `client` | API | Cliente de teste FastAPI |
| `temp_directory` | Arquivo | Diretório temporário |
| `output_directory` | Arquivo | Subdiretório de saída |
| `sample_excel_file` | Arquivo | Arquivo Excel de teste |
| `sample_excel_bytes` | Dados | Bytes de arquivo Excel |
| `sample_inventory_names` | Dados | Lista de inventory names |
| `sample_dbn_names` | Dados | Lista de DBN names |
| `masterfile_service` | Serviço | Instância do serviço |
| `json_service` | Serviço | Instância do serviço |
| `dbn_service` | Serviço | Instância do serviço |
| `mock_masterfile_creator` | Mock | Mock do processador |
| `mock_json_creator` | Mock | Mock do processador |
| `mock_dbn_model` | Mock | Mock do modelo |
| `temp_file_manager` | Dependência | Gerenciador de arquivos |
| `job_registry` | Dependência | Registro de jobs |

---

## 📌 Marcadores (Markers)

Marcadores permitem categorizar e filtrar testes.

| Marcador | Descrição | Uso |
|----------|-----------|-----|
| `@pytest.mark.unit` | Teste unitário | Automático em `test_unit/` |
| `@pytest.mark.integration` | Teste de integração | Automático em `test_integration/` |
| `@pytest.mark.e2e` | Teste end-to-end | Automático em `test_e2e/` |
| `@pytest.mark.slow` | Teste demorado | Manual |
| `@pytest.mark.api` | Teste de API | Automático em `test_api/` |

### Exemplo de Uso

```python
import pytest

@pytest.mark.slow
def test_processamento_grande():
    # Este teste demora mais
    pass

@pytest.mark.parametrize("db_type", ["oracle", "postgres"])
def test_com_parametros(db_type):
    # Executa para cada valor de db_type
    pass
```

---

## ❌ Solução de Problemas

### Erro: "Module not found"

```bash
# Certifique-se de estar na raiz do projeto
cd APP_Automation-refactor

# Instale o projeto em modo de desenvolvimento
pip install -e .
```

### Erro: "Fixture not found"

```bash
# Verifique se conftest.py está na pasta tests/
# A fixture deve estar definida em conftest.py
```

### Testes Travando

```bash
# Execute com timeout
pytest --timeout=30

# Ou pare no primeiro erro
pytest -x
```

### Testes Falhando por Arquivo Excel

Os testes de integração e E2E podem falhar se não houver um arquivo Excel válido. 
Use os mocks para testes que não precisam de processamento real:

```python
def test_com_mock(mock_masterfile_creator):
    # O processador real não será chamado
    pass
```

---

## 📈 Boas Práticas

### 1. Nomenclatura

```python
# Use nomes descritivos
def test_validate_empty_path_returns_error():
    pass

# NÃO use nomes vagos
def test_validation():
    pass
```

### 2. Estrutura AAA

```python
def test_example():
    # Arrange (Preparar)
    service = MasterfileService()
    
    # Act (Agir)
    result = service.validate_inputs(...)
    
    # Assert (Verificar)
    assert result.is_valid is False
```

### 3. Um Assert por Conceito

```python
# BOM: Testa um conceito
def test_validation_returns_error_for_empty_path():
    result = service.validate_inputs(path_excel="", ...)
    assert result.is_valid is False

# EVITE: Múltiplos conceitos
def test_validation():
    result1 = service.validate_inputs(path_excel="", ...)
    assert result1.is_valid is False
    result2 = service.validate_inputs(path_excel="test.txt", ...)
    assert result2.is_valid is False
```

### 4. Use Fixtures

```python
# BOM: Usa fixture
def test_service(masterfile_service):
    result = masterfile_service.validate_inputs(...)

# EVITE: Cria objetos manualmente
def test_service():
    service = MasterfileService()  # Repetitivo
    result = service.validate_inputs(...)
```

---

## 🔄 Integração Contínua (CI/CD)

### GitHub Actions (exemplo)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📞 Suporte

Se tiver dúvidas sobre os testes:

1. Verifique esta documentação
2. Leia os docstrings nos arquivos de teste
3. Execute `pytest --help` para opções
4. Consulte a [documentação do pytest](https://docs.pytest.org/)
