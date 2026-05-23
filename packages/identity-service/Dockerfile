FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY packages/core /workspace/packages/core
COPY packages/identity-service /workspace/packages/identity-service
COPY pyproject.toml /workspace/pyproject.toml

WORKDIR /workspace
RUN uv sync --package mams-identity-service --no-dev

WORKDIR /workspace/packages/identity-service

CMD ["uv", "run", "--no-sync", "uvicorn", "mams_identity.main:app", "--host", "0.0.0.0", "--port", "8000"]
