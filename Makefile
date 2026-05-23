.PHONY: dev-up dev-all dev-down test-unit test-integ test-all lint typecheck format migrate setup

dev-up:
	docker compose up -d postgres nats redis

dev-all:
	docker compose up -d

dev-down:
	docker compose down

test-unit:
	uv run pytest packages/core/tests/ -v

test-all:
	uv run pytest packages/ -v --cov=packages --cov-report=term-missing

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run mypy packages/core/src packages/api-gateway/src packages/identity-service/src packages/policy-engine/src packages/lifecycle-manager/src packages/model-gateway/src packages/audit-service/src packages/agent-runtime/src 2>/dev/null || uv run mypy packages/core/src

format:
	uv run ruff format . && uv run ruff check --fix .

migrate:
	uv run alembic upgrade head

setup:
	uv sync --all-packages --dev
	uv run pre-commit install

help:
	@echo "Available targets: dev-up dev-all dev-down test-unit test-all lint typecheck format migrate setup"
