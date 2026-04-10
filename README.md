# OdontoBot - Assistente RAG para Clinica Odontologica

## Visao geral

O OdontoBot e um monorepo que combina:

- **Backend** em **FastAPI** com SQLAlchemy 2 (async), PostgreSQL + **pgvector** para embeddings, **Redis** para cache/rate limit, e integracao **OpenAI** para embeddings e geracao na cadeia RAG.
- **RAG** sobre documentos da clinica (PDF, DOCX, TXT), com indexacao assincrona e busca semantica.
- **WhatsApp Cloud API** (Meta): webhook com verificacao de token (GET) e assinatura HMAC (POST), processamento de mensagens e respostas automatizadas.
- **Painel administrativo** em **Next.js** (React), na mesma raiz do repositorio, para acompanhamento de conversas, conhecimento e configuracoes (UI em evolucao).

## Pre-requisitos

- **Docker 24+** e **Docker Compose v2**
- **Node.js 18+** e **pnpm**
- Conta **OpenAI** com API key
- **App Meta** com **WhatsApp Cloud API** configurada

## Variaveis de ambiente

Copie `.env.example` para `.env` e preencha os valores. Referencia (inclui tambem `SERVICE_NAME` e `SERVICE_VERSION` presentes no exemplo):

| Variavel | Descricao | Obrigatorio |
| -------- | --------- | ----------- |
| `DATABASE_URL` | URL async do PostgreSQL (`postgresql+asyncpg://...`). No Docker da API, use o hostname `postgres`. | Sim |
| `REDIS_URL` | URL do Redis (`redis://...`). No Docker da API, use o hostname `redis`. | Sim |
| `OPENAI_API_KEY` | Chave da API OpenAI (`sk-...`). | Sim |
| `WHATSAPP_ACCESS_TOKEN` | Token de acesso do Graph API para envio de mensagens. | Sim |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do numero WhatsApp Business no Meta. | Sim |
| `WHATSAPP_VERIFY_TOKEN` | Token que voce define e replica no painel do webhook (GET verify). | Sim |
| `WHATSAPP_APP_SECRET` | App Secret do app Meta (validacao HMAC do webhook). | Sim |
| `HASH_SALT` | Salt para hash SHA-256 de identificadores de numero em BD/logs. | Sim |
| `API_KEY` | Chave para proteger rotas administrativas (`X-API-Key`). | Sim |
| `CLINIC_NAME` | Nome exibido em contexto/prompts. | Nao (ha default) |
| `ESCALATION_THRESHOLD` | Limiar de confianca para escalar conversa. | Nao (ha default) |
| `LOG_LEVEL` | Nivel de log (ex.: `INFO`). | Nao (ha default) |
| `ENVIRONMENT` | Ambiente logico (ex.: `development`). | Nao (ha default) |
| `SERVICE_NAME` | Nome do servico em logs/metadados. | Nao (ha default) |
| `SERVICE_VERSION` | Versao do servico em logs/metadados. | Nao (ha default) |

## Como subir tudo (desenvolvimento)

### 1. Clonar e configurar

```bash
git clone <url-do-repositorio>
cd <pasta-do-projeto>
cp .env.example .env
# Editar .env com suas chaves (OpenAI, Meta, API_KEY, HASH_SALT, etc.)
```

Para a API dentro do Docker, ajuste `DATABASE_URL` e `REDIS_URL` para apontar a `postgres` e `redis`.

### 2. Subir backend + banco + Redis

```bash
docker compose up --build -d
```

O contentor `app` aplica migracoes no arranque (`alembic upgrade head` via entrypoint). Se precisar aplicar migracoes manualmente:

```bash
docker compose exec app alembic upgrade head
```

### 3. Verificar saude da API

```bash
curl http://localhost:8000/health
```

### 4. Subir frontend (Next.js)

Neste repositorio o painel Next.js fica na **raiz** (pastas `app/`, `components/`), nao em uma subpasta `frontend`.

Copie `.env.local.example` para **`.env.local`** e preencha `API_URL`, `API_KEY` (mesma chave do backend), `ADMIN_PASSWORD` (hash bcrypt da senha do painel), `NEXTAUTH_SECRET` e `NEXTAUTH_URL` (ex.: `http://localhost:3000`).

```bash
pnpm install
pnpm dev
```

Acesse **<http://localhost:3000/login>**, informe a senha do painel e use o dashboard (a API e chamada via `/api/proxy` no servidor; a chave nao vai para o browser).

## Documentacao da API

- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>

## Rodar testes

Suba Postgres e Redis de teste (portas **5432** e **6380**, alinhadas a `src/tests/conftest.py`):

```bash
docker compose -f docker-compose.test.yml up -d
```

Na primeira vez, aplique o schema na base de testes. O Alembic usa **`DATABASE_URL`** (nao `TEST_DATABASE_URL`):

```bash
# Windows (cmd)
set DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_odontobot
alembic upgrade head
set TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_odontobot
set TEST_REDIS_URL=redis://localhost:6380/0
```

```bash
# Linux / macOS
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_odontobot
alembic upgrade head
export TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_odontobot
export TEST_REDIS_URL=redis://localhost:6380/0
```

Depois:

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

**Nota:** pare o `docker compose` principal se o Postgres publicar a porta `5432` no host em conflito, ou ajuste portas e variaveis. Volte a definir `DATABASE_URL` para o ambiente normal antes de subir a API.

## Estrutura do projeto

### Backend (`src/`)

```text
src/
  main.py
  config.py
  dependencies.py
  db/
    base.py
  core/
    exceptions.py
    logging.py
    middleware.py
    security.py
  schemas/
    pagination.py
  modules/
    analytics/
    chat/
    knowledge/
    settings/
    whatsapp/
  workers/
    cleanup_worker.py
    indexing_worker.py
  tests/
    conftest.py
    factories.py
    integration/
    unit/
```

### Painel Next.js (`app/`, `components/`)

```text
app/
  layout.tsx
  page.tsx
  globals.css
  conversations/
  knowledge/
  settings/

components/
  admin-layout.tsx
  admin-sidebar.tsx
  theme-provider.tsx
  conversations/
  dashboard/
  knowledge/
  settings/
  ui/
```

## Decisoes arquiteturais

- **Webhook WhatsApp** sem `X-API-Key`: a Meta nao envia cabecalhos customizados arbitrarios no fluxo padrao; a seguranca do POST e feita com **HMAC SHA-256** (`X-Hub-Signature-256`) usando `WHATSAPP_APP_SECRET`.
- **Numeros WhatsApp** nao sao armazenados em claro: usa-se hash **SHA-256 com salt** (`HASH_SALT`) para identificacao em base de dados e em logs onde aplicavel.
- **Alembic** no **entrypoint** do contentor `app` facilita desenvolvimento local com Docker; em **producao** prefira um **job separado** ou **init container** so para migracoes.
- **Migracao em producao:** executar `alembic upgrade head` como **init container** (ou Job Kubernetes) **antes** de subir replicas da aplicacao, para evitar corridas e falhas em health checks.
