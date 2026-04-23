# GitHub Actions — Secrets e Variables (CI)

Este ficheiro lista **todos** os nomes referenciados em `.github/workflows/*.yml` (hoje: [`ci.yml`](workflows/ci.yml)), com o tipo no GitHub (**Secret** ou **Variable** de repositório/organização).

> **Como criar:** *Settings → Secrets and variables → Actions* — use **Secrets** para credenciais e tokens; use **Variables** para URLs e identificadores não sensíveis (ainda assim evite dados pessoais em claro).

## Tabela — referenciados no workflow

| Nome exato | Tipo | Valor esperado |
| ---------- | ---- | ---------------- |
| `CI_TEST_DATABASE_URL` | **Variable** | URL async do Postgres de teste para `pytest` (ex.: `postgresql+asyncpg://postgres:postgres@localhost:5433/test_odontobot` quando o job usa serviço em `5433`). |
| `CI_TEST_REDIS_URL` | **Variable** | URL do Redis de teste (ex.: `redis://localhost:6380/0`). |
| `CI_DATABASE_URL` | **Variable** | `DATABASE_URL` usada pelo backend durante os testes (mesmo padrão asyncpg; alinhada ao serviço Postgres do job). |
| `CI_REDIS_URL` | **Variable** | `REDIS_URL` usada pela aplicação nos testes (alinhada ao Redis do job). |
| `CI_OPENAI_API_KEY` | **Secret** | Chave OpenAI (`sk-...`) para testes que invocam a API; trate como segredo. |
| `CI_WHATSAPP_ACCESS_TOKEN` | **Secret** | Token long-lived da Graph API (testes/integração). |
| `CI_WHATSAPP_PHONE_NUMBER_ID` | **Variable** | ID do número WhatsApp Business (apenas identificador). |
| `CI_WHATSAPP_VERIFY_TOKEN` | **Secret** | Token de verificação GET do webhook (string definida por si). |
| `CI_WHATSAPP_APP_SECRET` | **Secret** | App Secret da Meta (HMAC do webhook). |
| `CI_HASH_SALT` | **Secret** | Salt longo e aleatório para hash de identificadores (igual conceito ao `HASH_SALT` do `.env`). |
| `CI_API_KEY` | **Secret** | Mesmo papel que `API_KEY` do backend — cabeçalho `X-API-Key` nas rotas protegidas. |
| `CI_SETTINGS_ENCRYPTION_KEY` | **Secret** | Chave Fernet em base64 URL-safe; no job é injetada como `SETTINGS_ENCRYPTION_KEY` para cifra de settings nos testes. |
| `CI_CLINIC_NAME` | **Variable** | Nome da clínica usado em contexto de testes (não sensível). |
| `CI_NEXTAUTH_SECRET` | **Secret** | Segredo NextAuth (≥32 caracteres), igual ao esperado em produção para o painel. |
| `CI_NEXTAUTH_URL` | **Variable** | URL canónica do painel no CI (ex.: `http://127.0.0.1:3000` para `next start` no runner). |
| `CI_ADMIN_PASSWORD_HASH` | **Secret** | Hash **bcrypt** da senha do admin do painel — no workflow é passado como env `ADMIN_PASSWORD` ao Next.js. |
| `E2E_ADMIN_PASSWORD` | **Secret** | Senha do painel **em texto plano** só para Playwright (`E2E_ADMIN_PASSWORD`); deve corresponder ao utilizador que valida o hash em `CI_ADMIN_PASSWORD_HASH`. Nunca commitar. |

## Variável recomendada — ainda não usada no `ci.yml`

O workflow atual **não** referencia CORS; o backend em produção usa `ALLOWED_ORIGINS`. Se no futuro um job compilar ou subir a API no CI e precisar de CORS explícito, defina no GitHub:

| Nome exato | Tipo | Valor esperado |
| ---------- | ---- | ---------------- |
| `ALLOWED_ORIGINS` | **Variable** (recomendado) | Lista separada por vírgulas de origens permitidas (ex.: `http://localhost:3000`). **Não** está hoje em `.github/workflows/ci.yml`; inclua manualmente no `env:` do job quando for necessário. |

Alternativa: nome `CI_ALLOWED_ORIGINS` como Variable, desde que o workflow passe `ALLOWED_ORIGINS=${{ vars.CI_ALLOWED_ORIGINS }}` ao processo que valida o backend.

## Resumo rápido (pedido na documentação do repositório)

| Nome | Tipo GitHub |
| ---- | ----------- |
| `CI_TEST_DATABASE_URL` | Variable |
| `CI_OPENAI_API_KEY` | Secret |
| `E2E_ADMIN_PASSWORD` | Secret |
| `CI_SETTINGS_ENCRYPTION_KEY` (→ env `SETTINGS_ENCRYPTION_KEY`) | Secret |
| `ALLOWED_ORIGINS` | Variable (não ligado ao YAML atual) |

## Manutenção

Ao adicionar novas referências `${{ secrets.* }}` ou `${{ vars.* }}` nos workflows, atualize esta tabela no mesmo PR.
