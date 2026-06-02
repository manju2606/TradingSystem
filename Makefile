.PHONY: up down build logs ps setup migrate migrate-create migrate-down \
        shell-api shell-db lint format test test-unit test-integration \
        api-dev ui-dev install

# ── Docker Desktop ────────────────────────────────────────────────────────────

setup:	## First-time setup: copy .env, build images, start stack
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example — fill in secrets before starting"; fi
	docker compose build
	docker compose up -d

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

# ── Database migrations (run inside the api container) ────────────────────────

migrate:
	docker compose exec api bash -c "cd /app/db/postgres && alembic upgrade head"

migrate-create:
	docker compose exec api bash -c "cd /app/db/postgres && alembic revision --autogenerate -m '$(msg)'"

migrate-down:
	docker compose exec api bash -c "cd /app/db/postgres && alembic downgrade -1"

# ── Shell access ──────────────────────────────────────────────────────────────

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U trading trading

# ── Local dev (outside Docker) ────────────────────────────────────────────────

install:
	pip install -r requirements.txt

api-dev:
	uvicorn backend.api.main:app --reload --port 8000

ui-dev:
	streamlit run frontend/streamlit/app.py --server.port 8501

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	ruff check backend/ frontend/ db/
	mypy backend/ --ignore-missing-imports

format:
	ruff format backend/ frontend/ db/

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v
