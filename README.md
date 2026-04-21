# OdontoBot - Assistente RAG para Clinica Odontologica

## Visao geral

O OdontoBot e um monorepo que combina:

- **Backend** em **FastAPI** com SQLAlchemy 2 (async), PostgreSQL + **pgvector** para embeddings, **Redis** para cache/rate limit, e integracao **OpenAI** para embeddings e geracao na cadeia RAG.
- **RAG** sobre documentos da clinica (PDF, DOCX, TXT), com indexacao assincrona e busca semantica.
- **WhatsApp Cloud API** (Meta): webhook com verificacao de token (GET) e assinatura HMAC (POST), processamento de mensagens e respostas automatizadas.
- **Painel administrativo** em **Next.js** (React), na mesma raiz do repositorio, para acompanhamento de conversas, conhecimento e configuracoes (UI em evolucao).

## Pre-requisitos

- **Docker 24+** e **Docker Compose v2**
- **Node.js 20+** e **pnpm** (alinhado ao **Next.js 16**, ao CI em `.github/workflows/ci.yml` e ao `Dockerfile.frontend`)
- Conta **OpenAI** com API key
- **App Meta** com **WhatsApp Cloud API** configurada

## Variaveis de ambiente

Copie `.env.example` para `.env` e preencha os valores. O ficheiro **`.env` esta no `.gitignore`** e nao deve ser versionado. Apenas `.env.example` e `.env.local.example` servem de modelo.

Definicoes completas alinhadas a `src/config.py` estao em `.env.example`. A tabela abaixo resume cada variavel do backend.

### Backend (`.env` na raiz — FastAPI, workers, Alembic)

| Variavel | Descricao | Exemplo | Obrigatoria |
| -------- | --------- | ------- | ----------- |
| `CORS_ORIGINS` | Origens CORS (lista separada por virgula). | `http://localhost:3000` | Nao (default no codigo) |
| `DATABASE_URL` | URL async PostgreSQL + asyncpg. No Docker, hostname `postgres`. | `postgresql+asyncpg://user:pass@postgres:5432/odontobot` | Sim |
| `REDIS_URL` | Redis (cache, rate limit, ARQ, metricas). No Docker, hostname `redis`. | `redis://redis:6379/0` | Sim |
| `OPENAI_API_KEY` | Chave OpenAI (embeddings e RAG). | `sk-...` | Sim |
| `MINIO_ENDPOINT` | Host:porta do MinIO (object storage). | `minio:9000` | Nao (default) |
| `MINIO_ACCESS_KEY` | Chave de acesso MinIO. | `minioadmin` | Nao (default) |
| `MINIO_SECRET_KEY` | Segredo MinIO. | `minioadmin` | Nao (default) |
| `MINIO_BUCKET` | Bucket dos documentos. | `documents` | Nao (default) |
| `WHATSAPP_ACCESS_TOKEN` | Token Graph API (envio de mensagens). | (token Meta) | Sim |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do numero WhatsApp Business. | `123456789012345` | Sim |
| `WHATSAPP_VERIFY_TOKEN` | Token definido por si para verificacao GET do webhook. | `meu-verify-token` | Sim |
| `WHATSAPP_APP_SECRET` | App Secret Meta (HMAC `X-Hub-Signature-256`). | (segredo Meta) | Sim |
| `HASH_SALT` | Salt para hash SHA-256 de identificadores. | (string longa aleatoria) | Sim |
| `API_KEY` | Rotas admin e `/metrics`: cabecalho `X-API-Key`. | (string aleatoria) | Sim |
| `PUBLIC_API_BASE_URL` | URL publica da API (sem barra final); usada para mostrar URL do webhook no painel. | `https://api.exemplo.com` | Nao |
| `SETTINGS_ENCRYPTION_KEY` | Chave Fernet (base64 URL-safe) para cifrar `whatsapp.access_token` e `whatsapp.verify_token` em repouso na tabela `settings` (coluna `value` JSONB). | Saida do comando abaixo | Sim |
| `CLINIC_NAME` | Nome da clinica em prompts/contexto. | `Clinica OdontoVida` | Nao (default) |
| `ESCALATION_THRESHOLD` | Limiar de confianca para escalar conversa (0-1). | `0.70` | Nao (default) |
| `TRUST_PROXY` | Confiar em `X-Forwarded-For` (rate limit atras de proxy). | `false` | Nao (default) |
| `LOG_LEVEL` | Nivel de log structlog. | `INFO` | Nao (default) |
| `ENVIRONMENT` | Ambiente logico (logs). | `development` | Nao (default) |
| `SERVICE_NAME` | Nome do servico em logs. | `odontobot-api` | Nao (default) |
| `SERVICE_VERSION` | Versao em logs. | `0.1.0` | Nao (default) |
| `TEST_DATABASE_URL` | Apenas pytest / CI: Postgres de testes. | `postgresql+asyncpg://...@localhost:5433/test_odontobot` | Nao |
| `TEST_REDIS_URL` | Apenas pytest / CI: Redis de testes. | `redis://localhost:6380/0` | Nao |

Gere `SETTINGS_ENCRYPTION_KEY` uma vez por ambiente (guarde-a com o mesmo cuidado que uma password):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Painel Next.js (`.env.local` na raiz)

Usadas em `lib/auth.ts` e `app/api/proxy/[...path]/route.ts`. Nao ha `NEXT_PUBLIC_*` obrigatorias no codigo atual.

| Variavel | Descricao | Exemplo | Obrigatoria |
| -------- | --------- | ------- | ----------- |
| `API_URL` | URL base da API para o proxy server-side. | `http://localhost:8000` | Sim |
| `API_KEY` | Mesmo valor que `API_KEY` do backend. | (igual ao `.env`) | Sim |
| `ADMIN_PASSWORD` | Hash bcrypt da senha do painel. | Ver `.env.local.example` | Sim |
| `NEXTAUTH_SECRET` | Segredo NextAuth (min. 32 caracteres). | (string aleatoria) | Sim |
| `NEXTAUTH_URL` | URL canonica do painel. | `http://localhost:3000` | Sim |

### Docker Compose

O `docker-compose.yml` injeta `MINIO_*` nos servicos `app`, `worker` e `cleanup-worker` a partir do `.env`. O servico `frontend` usa `API_URL=http://app:8000` fixo e le `API_KEY`, `ADMIN_PASSWORD`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL` do ambiente (defina-as no `.env` antes de subir o stack completo).

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

Instale **Node.js 20 ou superior** (use `node -v` para confirmar). Versões anteriores nao sao suportadas pelo Next.js 16 usado neste projeto.

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

**Nota:** pare o `docker compose` principal se a porta do Postgres de testes conflitar no host, ou ajuste portas e variaveis. Volte a definir `DATABASE_URL` para o ambiente normal antes de subir a API.

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
