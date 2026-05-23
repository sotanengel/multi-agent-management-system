FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/audit-service /workspace/packages/audit-service
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-audit-service --no-dev
WORKDIR /workspace/packages/audit-service
CMD ["uv", "run", "--no-sync", "uvicorn", "mams_audit.main:app", "--host", "0.0.0.0", "--port", "8000"]
