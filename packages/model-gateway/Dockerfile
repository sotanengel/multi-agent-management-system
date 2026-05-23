FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/model-gateway /workspace/packages/model-gateway
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-model-gateway --no-dev
WORKDIR /workspace/packages/model-gateway
CMD ["uv", "run", "--no-sync", "uvicorn", "mams_model_gw.main:app", "--host", "0.0.0.0", "--port", "8000"]
