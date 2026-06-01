.PHONY: up down build migrate lint test

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

# Database
migrate:
	cd db/postgres && alembic upgrade head

migrate-create:
	cd db/postgres && alembic revision --autogenerate -m "$(msg)"

migrate-down:
	cd db/postgres && alembic downgrade -1

# Dev
install:
	pip install -r requirements.txt

lint:
	ruff check backend/ frontend/ db/
	mypy backend/ --ignore-missing-imports

format:
	ruff format backend/ frontend/ db/

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# API
api-dev:
	uvicorn backend.api.main:app --reload --port 8000

# Streamlit
ui-dev:
	streamlit run frontend/streamlit/app.py --server.port 8501
