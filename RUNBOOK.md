# RUNBOOK Operacional

Este documento cobre procedimentos de operacao para ambiente de producao.

## 1) Backup e Restore do PostgreSQL

### Backup (recomendado: diario + retenção de 30 dias)

- **Frequencia sugerida**
  - Backup completo: `1x por dia` (fora do horario de pico).
  - Backup adicional: antes de deploy com migracao e antes de rotacao de chave/token.
  - Teste de restore: `1x por semana`.

- **Comando (dump custom, recomendado)**
```bash
export PGPASSWORD='<DB_PASSWORD>'
export PGHOST='<DB_HOST>'
export PGPORT='5432'
export PGUSER='<DB_USER>'
export PGDATABASE='<DB_NAME>'

mkdir -p backups
pg_dump -Fc -f "backups/odontobot_$(date +%F_%H%M%S).dump" "$PGDATABASE"
```

- **Verificacao do arquivo**
```bash
pg_restore -l "backups/odontobot_YYYY-MM-DD_HHMMSS.dump" >/dev/null
```

### Restore

- **Passo 1: preparar base alvo (vazia)**
```bash
export PGPASSWORD='<DB_PASSWORD>'
createdb -h '<DB_HOST>' -p 5432 -U '<DB_USER>' '<DB_NAME_RESTORE>'
```

- **Passo 2: restaurar**
```bash
pg_restore \
  -h '<DB_HOST>' \
  -p 5432 \
  -U '<DB_USER>' \
  -d '<DB_NAME_RESTORE>' \
  --clean --if-exists --no-owner --no-privileges \
  "backups/odontobot_YYYY-MM-DD_HHMMSS.dump"
```

- **Passo 3: validacao minima**
```bash
psql -h '<DB_HOST>' -p 5432 -U '<DB_USER>' -d '<DB_NAME_RESTORE>' -c "SELECT COUNT(*) FROM settings;"
psql -h '<DB_HOST>' -p 5432 -U '<DB_USER>' -d '<DB_NAME_RESTORE>' -c "SELECT COUNT(*) FROM documents;"
```

---

## 2) Rotacao do `SETTINGS_ENCRYPTION_KEY` sem perda de dados

`SETTINGS_ENCRYPTION_KEY` protege segredos em `settings.value.v` para:
- `whatsapp.access_token`
- `whatsapp.verify_token`

### Estratégia segura (zero perda)

1. **Nao** troque a chave em runtime sem recriptografar os registros.
2. Com app **parado** (ou em janela de manutencao), execute recriptografia no banco.
3. Suba app com a nova chave.

### Passo a passo

#### 2.1 Gerar nova chave
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 2.2 Recriptografar no banco (OLD_KEY -> NEW_KEY)
```bash
export DATABASE_URL='postgresql+psycopg://<USER>:<PASS>@<HOST>:5432/<DB>'
export OLD_KEY='<FERNET_ANTIGA>'
export NEW_KEY='<FERNET_NOVA>'

python - <<'PY'
import json
import os
import psycopg
from cryptography.fernet import Fernet

PREFIX = "OBENC1:"
keys = ("whatsapp.access_token", "whatsapp.verify_token")

old = Fernet(os.environ["OLD_KEY"].encode("ascii"))
new = Fernet(os.environ["NEW_KEY"].encode("ascii"))

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, key, value FROM settings WHERE key IN (%s, %s) FOR UPDATE",
            keys,
        )
        rows = cur.fetchall()
        for _id, key, value in rows:
            if not isinstance(value, dict):
                continue
            v = value.get("v")
            if not isinstance(v, str) or not v.startswith(PREFIX):
                continue
            raw = v[len(PREFIX):]
            plaintext = old.decrypt(raw.encode("ascii")).decode("utf-8")
            recipher = PREFIX + new.encrypt(plaintext.encode("utf-8")).decode("ascii")
            value["v"] = recipher
            cur.execute("UPDATE settings SET value = %s WHERE id = %s", (json.dumps(value), _id))
    conn.commit()
print("OK: chaves recriptografadas")
PY
```

#### 2.3 Atualizar ambiente e validar
- Atualize `SETTINGS_ENCRYPTION_KEY` para `NEW_KEY`.
- Suba a API.
- Valide:
```bash
curl -fsS http://localhost:8000/health
```
- No painel/API admin, confirme que as configuracoes WhatsApp continuam legiveis.

---

## 3) Rotacao de tokens Meta/WhatsApp

### Quando rotacionar
- A cada 60-90 dias (ou menor conforme politica interna).
- Imediatamente em caso de suspeita de vazamento.

### Sequencia operacional

1. Gere novo token no Meta Business (Cloud API).
2. Atualize `WHATSAPP_ACCESS_TOKEN` no ambiente da API.
3. (Opcional, recomendado) rotacione tambem `WHATSAPP_VERIFY_TOKEN` e `WHATSAPP_APP_SECRET`.
4. Reinicie API/workers.
5. Revalide webhook e envio.

### Verificacoes

- Health:
```bash
curl -fsS http://localhost:8000/health
```

- Conexao WhatsApp (requer API key):
```bash
curl -fsS \
  -H "X-API-Key: <API_KEY>" \
  http://localhost:8000/whatsapp/admin/connection
```

- Teste de webhook GET (token de verificacao):
```bash
curl -i "https://<API_PUBLICA>/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<WHATSAPP_VERIFY_TOKEN>&hub.challenge=12345"
```

---

## 4) Monitoramento de custos OpenAI (alerta de threshold)

### Politica sugerida

- Definir teto mensal e alertas em:
  - `50%` (informativo)
  - `80%` (atencao)
  - `100%` (acao imediata)

### Acao minima obrigatoria

1. Configurar budget/alerts no painel da OpenAI (org/projeto).
2. Direcionar alerta para e-mail operacional + canal on-call (Slack/Teams/Pager).

### Rotina diaria (manual ou cron)

- Conferir consumo do dia e acumulado no painel OpenAI.
- Se >80%:
  - reduzir `max_tokens`,
  - aumentar `escalation_threshold` com cautela,
  - revisar consultas de maior custo.

---

## Rate limit e Redis

### Comportamento atual (Redis indisponivel no middleware)

O `RateLimitMiddleware` usa o cliente Redis em `app.state.redis_client` para contar pedidos por IP e escopo (`global`, `admin`, `webhook`).

- **Se `redis_client` nao estiver no `app.state`:** o middleware regista um evento **`rate_limit_skipped`** em nivel **critical**, com `reason=redis_client_missing`, `ip` e `path`, e **deixa a requisicao passar** (**fail-open**): nao ha rate limit ate o estado da aplicacao voltar a incluir o cliente Redis.
- **Se o Redis falhar durante `incr`/`expire`:** o middleware regista `rate_limit_redis_error` e tambem **fail-open** (requisicao segue sem limite).

Isto prioriza **disponibilidade** da API em incidentes de Redis; a contrapartida e **menos protecao** contra abuso enquanto o limite estiver inativo.

### Como monitorar

- **Logs agregados:** alertar quando aparecerem picos de `rate_limit_skipped` com `reason=redis_client_missing` (ou taxa > 0 em producao).
- **Infra:** alertas nativos no Redis (instancia fora, conexoes recusadas) e correlacao com o horario dos logs acima.
- **Opcional:** expor um contador Prometheus (ex.: `rate_limit_redis_unavailable_total`) se no futuro instrumentarem o middleware — hoje o sinal principal e o log estruturado.

### Fail-closed (opcional)

Se a politica for **recusar trafego** quando nao for possivel aplicar rate limit (seguranca acima de disponibilidade), altere o ramo em que `redis is None` para devolver **503** em vez de `call_next`, por exemplo:

```python
# Exemplo: fail-closed — nao usar sem alinhar com o time (health checks e webhooks podem ser afetados).
return JSONResponse(
    status_code=503,
    content={'detail': 'Rate limiting unavailable: Redis client not configured'},
)
```

Avalie excecoes por rota (ex.: manter `GET /health` isento) antes de ativar isto em producao.

---

## 5) Checklist de health check pós-deploy

Execute na ordem:

1. **API up**
```bash
curl -fsS http://localhost:8000/health
```
Esperado: `status=ok` e `db/redis/vector_store=ok`.

2. **Migracao aplicada**
```bash
alembic current
alembic heads
```
Esperado: revisao atual alinhada ao head.

3. **Métricas básicas**
```bash
curl -fsS -H "X-API-Key: <API_KEY>" http://localhost:8000/metrics
```
Verificar especialmente:
- `indexing_job_failed`
- `whatsapp_handler_failed`
- `webhook_signature_failed`

4. **WhatsApp admin connection**
```bash
curl -fsS -H "X-API-Key: <API_KEY>" http://localhost:8000/whatsapp/admin/connection
```
Esperado: `connected=true` (ou sem erro operacional).

5. **Frontend login**
- Acessar `/login`, autenticar, abrir Dashboard.
- Verificar carregamento de:
  - Base de Conhecimento
  - Configuracoes
  - Conversas

6. **Fluxo funcional minimo**
- Upload de 1 documento pequeno (PDF/TXT) e confirmar processamento.
- Envio de 1 mensagem de teste e resposta do bot.

7. **Rollback readiness**
- Confirmar backup mais recente disponivel.
- Confirmar comando de restore validado.

---

## Comandos de resposta rápida (incidente)

- Reiniciar API (Docker Compose):
```bash
docker compose restart app worker cleanup-worker
```

- Ver logs recentes:
```bash
docker compose logs --since=10m app worker cleanup-worker
```

- Testar dependencias direto no Postgres:
```bash
psql "<DATABASE_URL_SYNC_OR_PSQL>" -c "SELECT 1;"
psql "<DATABASE_URL_SYNC_OR_PSQL>" -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```
