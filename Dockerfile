FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
# Resolve dependências no build (rede). Sem lock válido no repo, não usar --frozen.
RUN uv sync --no-dev --no-install-project

FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.venv /app/.venv
RUN useradd -m appuser
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
COPY src/ /app/src/
RUN chmod +x /app/docker-entrypoint.sh && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=5 CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["/app/docker-entrypoint.sh"]
