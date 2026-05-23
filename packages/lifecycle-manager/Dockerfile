FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/lifecycle-manager /workspace/packages/lifecycle-manager
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-lifecycle-manager --no-dev
WORKDIR /workspace/packages/lifecycle-manager
CMD ["uv", "run", "--no-sync", "uvicorn", "mams_lifecycle.main:app", "--host", "0.0.0.0", "--port", "8000"]
