FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/api-gateway /workspace/packages/api-gateway
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-api-gateway --no-dev
WORKDIR /workspace/packages/api-gateway
CMD ["uv", "run", "--no-sync", "uvicorn", "mams_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
