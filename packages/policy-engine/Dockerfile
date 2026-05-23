FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/policy-engine /workspace/packages/policy-engine
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-policy-engine --no-dev
WORKDIR /workspace/packages/policy-engine
CMD ["uv", "run", "--no-sync", "uvicorn", "mams_policy.main:app", "--host", "0.0.0.0", "--port", "8000"]
