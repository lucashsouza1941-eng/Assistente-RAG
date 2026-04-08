FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --system -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .
EXPOSE 8000
CMD ['uvicorn', 'src.main:app', '--host', '0.0.0.0', '--port', '8000']

