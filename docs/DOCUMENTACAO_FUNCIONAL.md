# Manual Funcional — Automation API

## O que é este projeto

Automação da criação de arquivos a partir de um "pack" Excel padrão:

- **Masterfiles** (.mas) e **ACX** (.acx)
- **Arquivos JSON** para Oracle ou PostgreSQL
- **Modelos de exportação** DBN0 e DBN1
- **Renomeação** de arquivos DBN1

## Como usar

- **Via API Web**: para integração com outros sistemas ou uso por ferramentas externas
- **Via Desktop** (PyQt5): interface gráfica para uso direto

## Para quem é

Analistas, engenheiros de dados e times de integração que precisam transformar planilhas Excel padronizadas em artefatos — sem programar.

## Pré-requisitos

- **Python 3.11+** instalado
- O "pack" Excel no padrão esperado, com abas:
  - `3. Data Sources`
  - `3. Data Sources Attr & Count`
  - Para Masterfiles: também `3. Data Sources Map`
- **Atenção**: os cabeçalhos devem estar na **4ª linha** das abas

## Instalação

```bash
# Clone ou acesse a pasta do projeto
cd APP_Automation-refactor

# Instale as dependências
pip install -r requirements.txt
```

## Executando a API

```bash
# Iniciar o servidor
python run.py

# A API estará disponível em:
# http://localhost:8000
```

Acesse a documentação interativa:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Executando o Desktop (opcional)

```bash
cd desktop
python app.py
```

## Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações da API |
| GET | `/health` | Health check |
| POST | `/api/masterfiles/create_async` | Criar masterfiles |
| GET | `/api/masterfiles/progress/{job_id}` | Progresso do job |
| POST | `/api/jsons/create_async` | Criar JSONs |
| GET | `/api/jsons/progress/{job_id}` | Progresso do job |
| POST | `/api/dbn/dbn0/create` | Criar DBN0 |
| POST | `/api/dbn/dbn1/create` | Criar DBN1 |
| POST | `/api/dbn/dbn1/rename` | Renomear DBN1 |

## Estrutura do Projeto

```
APP_Automation-refactor/
├── src/                    # Código fonte da API
│   ├── api/                # FastAPI routes
│   ├── services/           # Lógica de negócio
│   ├── domain/             # Processadores
│   └── infrastructure/     # Geradores e I/O
├── desktop/                # App Desktop PyQt5
├── tests/                  # Testes
├── docs/                   # Documentação
├── run.py                  # Entry point
└── requirements.txt        # Dependências
```

## Suporte

Para dúvidas técnicas, consulte:
- [API.md](./API.md) — Documentação da API
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Arquitetura
- [DOCUMENTACAO_TECNICA.md](./DOCUMENTACAO_TECNICA.md) — Detalhes técnicos