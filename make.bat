@echo off
setlocal

set TARGET=%1
set MSG=%2

if "%TARGET%"=="up"              goto up
if "%TARGET%"=="down"            goto down
if "%TARGET%"=="build"           goto build
if "%TARGET%"=="logs"            goto logs
if "%TARGET%"=="ps"              goto ps
if "%TARGET%"=="setup"           goto setup
if "%TARGET%"=="migrate"         goto migrate
if "%TARGET%"=="migrate-create"  goto migrate-create
if "%TARGET%"=="migrate-down"    goto migrate-down
if "%TARGET%"=="shell-api"       goto shell-api
if "%TARGET%"=="shell-db"        goto shell-db
if "%TARGET%"=="test"            goto test
if "%TARGET%"=="test-unit"       goto test-unit
if "%TARGET%"=="lint"            goto lint
if "%TARGET%"=="format"          goto format
if "%TARGET%"=="api-dev"         goto api-dev
if "%TARGET%"=="ui-dev"          goto ui-dev
if "%TARGET%"==""                goto help

echo Unknown target: %TARGET%
goto help

:setup
if not exist .env copy .env.example .env && echo Created .env from .env.example
docker compose build
docker compose up -d
goto end

:up
docker compose up -d
goto end

:down
docker compose down
goto end

:build
docker compose build
goto end

:logs
docker compose logs -f
goto end

:ps
docker compose ps
goto end

:migrate
docker compose exec api bash -c "cd /app/db/postgres && alembic upgrade head"
goto end

:migrate-create
docker compose exec api bash -c "cd /app/db/postgres && alembic revision --autogenerate -m '%MSG%'"
goto end

:migrate-down
docker compose exec api bash -c "cd /app/db/postgres && alembic downgrade -1"
goto end

:shell-api
docker compose exec api bash
goto end

:shell-db
docker compose exec postgres psql -U trading trading
goto end

:test
pytest tests/ -v
goto end

:test-unit
pytest tests/unit/ -v
goto end

:lint
ruff check backend/ frontend/ db/
mypy backend/ --ignore-missing-imports
goto end

:format
ruff format backend/ frontend/ db/
goto end

:api-dev
uvicorn backend.api.main:app --reload --port 8080
goto end

:ui-dev
streamlit run frontend/streamlit/app.py --server.port 8501
goto end

:help
echo Usage: make ^<target^>
echo.
echo Targets:
echo   setup           First-time setup: copy .env, build, start stack
echo   up              Start all services
echo   down            Stop all services
echo   build           Rebuild images
echo   logs            Tail all logs
echo   ps              Show running containers
echo   migrate         Run alembic upgrade head (inside container)
echo   migrate-create  Generate new migration  (pass msg=^"description^")
echo   migrate-down    Downgrade one migration
echo   shell-api       Bash into api container
echo   shell-db        psql into postgres
echo   test            Run all tests
echo   test-unit       Run unit tests only
echo   lint            ruff + mypy
echo   format          ruff format
goto end

:end
endlocal
