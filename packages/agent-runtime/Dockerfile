FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY packages/core /workspace/packages/core
COPY packages/agent-runtime /workspace/packages/agent-runtime
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace
RUN uv sync --package mams-agent-runtime --no-dev
WORKDIR /workspace/packages/agent-runtime
CMD ["uv", "run", "--no-sync", "python", "-m", "mams_agent.main"]
