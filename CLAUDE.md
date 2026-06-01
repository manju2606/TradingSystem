# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered multi-timeframe trading platform for Indian markets (NSE Futures: NIFTY, BANKNIFTY). Paper trading first, live broker execution later. See `readme.md` for full specification.

## Repository Layout

```
backend/
  api/            # FastAPI app (main.py, routers/, schemas/, dependencies.py, config.py)
  agents/         # LangGraph nodes + orchestrator
  market/         # yfinance data fetch + technical indicators (ta library)
  strategy/       # Rule-based + ML signal generation
  prediction/     # Model dispatch engine + XGBoost/LightGBM/LSTM/Transformer models
  paper/          # Paper order fill + position tracking
  risk/           # Risk rule engine (position sizing, circuit breakers)
  execution/      # BrokerAdapter interface + PaperBrokerAdapter + ZerodhaAdapter (stub)
db/
  postgres/       # SQLAlchemy models, Alembic migrations (alembic.ini lives here)
  cache/redis/    # Async Redis client (get/set/publish helpers)
frontend/streamlit/
  app.py          # Entry point; pages/ has 5 numbered Streamlit pages
infra/
  docker/         # Dockerfile.api, Dockerfile.streamlit
  k8s/            # Deployment, Service, Ingress, HPA manifests (namespace: trading)
monitoring/
  prometheus/     # prometheus.yml + alert_rules.yml
  grafana/        # Datasource + dashboard provisioning
tests/unit/       # Pure-Python unit tests (no DB/network)
tests/integration/
```

## Architecture Data Flow

```
Streamlit UI → FastAPI Gateway → Agent Orchestrator → Trading Engine
                                                     → Prediction Engine
                                                     → Risk Engine
                                                     → Paper/Execution
                                        ↕                ↕
                                      Redis          PostgreSQL
```

## Key Design Decisions

- **Market data**: yfinance via `backend/market/service.py`; `_SYMBOL_MAP` translates NIFTY→`^NSEI`. Replace with broker WebSocket in Phase 5.
- **Prediction routing**: `backend/prediction/engine.py` selects model by timeframe (`_MODEL_MAP`). All models return `{"probability": float}`. Untrained models return 0.5 (neutral) until `.train()` is called.
- **Signal generation**: EMA crossover rule-based layer + ML confidence boost in `backend/strategy/signal_generator.py`. RSI overbought/oversold overrides to HOLD.
- **Risk engine**: Pure Python/Decimal, no I/O — safe to call synchronously. `check_order` enforces all three circuit breakers; `calculate_position_size` gives the Kelly-like sizing.
- **Paper trading**: `PaperTradingEngine` fills at live market price. Uses upsert-style position tracking (open position updated on each fill, closed when qty=0).
- **Broker abstraction**: `BrokerAdapter` ABC in `backend/execution/broker_adapter.py`. `ZerodhaAdapter` is a stub for Phase 5. `PaperBrokerAdapter` is the default.
- **Auth**: JWT via `python-jose`. `get_current_user` dependency injected into all protected routes.
- **Config**: All settings via `backend/api/config.py` (pydantic-settings); reads `.env` automatically.

**FastAPI endpoints**: `POST /signal`, `GET /prediction`, `POST /paper/order`, `GET /portfolio/positions`, `GET /portfolio/summary`, `GET /backtest`, `POST /backtest/run`

## Agentic AI Layer (LangGraph)

`backend/agents/orchestrator.py` builds a `StateGraph` over `TradingState`. The pipeline is:

```
market_analyst → signal_validator →(approved?)→ risk_agent →(approved?)→ execution_agent → journal_agent
```

Each node is a separate file. `cost_reviewer.py` is a standalone Claude Haiku agent (Anthropic SDK, not LangGraph) for Terraform cost analysis.

## Database Schema (PostgreSQL)

Tables: `users`, `symbols`, `candles`, `signals`, `predictions`, `orders`, `positions`, `backtests`, `agent_logs`

## Commands

```bash
# Start all services (postgres, redis, api, streamlit, prometheus, grafana)
make up                          # docker-compose up -d
make down

# API dev server (hot-reload)
make api-dev                     # uvicorn backend.api.main:app --reload --port 8000

# Streamlit UI
make ui-dev                      # streamlit run frontend/streamlit/app.py

# Database migrations
make migrate                     # alembic upgrade head (run from db/postgres/)
make migrate-create msg="desc"   # generate new migration

# Tests
make test                        # all tests
make test-unit                   # tests/unit/ only
pytest tests/unit/test_risk_engine.py -v   # single test file

# Lint / format
make lint    # ruff check + mypy
make format  # ruff format
```

## Terraform Infrastructure (`infra/terraform/`)

**Region**: `ap-south-1` (Mumbai — low latency to NSE)

```
infra/terraform/
  bootstrap/          # Run once to create S3 state bucket + DynamoDB lock table
  versions.tf         # Provider version constraints
  backend.hcl.example # Copy → backend.hcl, fill account ID, then terraform init -backend-config=backend.hcl
  modules/
    vpc/              # 3-AZ VPC, public/private/db subnets, NAT GW (single in dev, per-AZ in prod)
    eks/              # EKS 1.30, managed system node group, OIDC provider, core add-ons
    iam_roles/        # Pre-EKS cluster + node IAM roles (no OIDC dependency)
    iam/              # IRSA roles (API pod, EBS CSI), Secrets Manager secrets, S3 model bucket
    rds/              # PostgreSQL 16, gp3, parameter group, slow-query logging
    elasticache/      # Redis 7, TLS + auth token, LRU eviction
    ecr/              # trading-api + trading-streamlit repos, lifecycle policy
    karpenter/        # Controller IRSA, SQS interruption queue, EC2NodeClass, NodePool
  environments/
    dev/              # t3.micro RDS, cache.t3.micro Redis, single NAT, 2 system nodes
    prod/             # r6g.large RDS Multi-AZ, r6g.large Redis replica, 3-AZ NAT, 3 system nodes
```

**Deployment order**:
```bash
# 1. Bootstrap (once per AWS account)
terraform -chdir=infra/terraform/bootstrap apply -var="account_id=<id>"

# 2. Copy and fill secrets
cp infra/terraform/environments/dev/terraform.tfvars.example infra/terraform/environments/dev/terraform.tfvars
cp infra/terraform/backend.hcl.example infra/terraform/backend.hcl  # fill bucket/key

# 3. Deploy dev
cd infra/terraform/environments/dev
terraform init -backend-config=../../backend.hcl
terraform apply

# 4. Connect kubectl
aws eks update-kubeconfig --region ap-south-1 --name trading-dev
```

**Key design decisions**:
- `iam_roles` module is separate from `iam` module — cluster/node roles must exist before EKS is created, IRSA roles require the OIDC provider which only exists after EKS is up.
- DB and Redis credentials written to Secrets Manager (`trading/<env>/db`, `trading/<env>/redis`) by the `iam` module. API pods access them via IRSA (no static credentials in pods).
- Karpenter node pool targets `spot` + `on-demand` across `c`, `m`, `r` instance families; system workloads (CoreDNS, Karpenter) are tainted `CriticalAddonsOnly` on the managed node group.
- `single_nat_gateway = true` in dev to reduce costs (~$32/month per NAT GW).

## Security Model

JWT auth, RBAC, credentials in AWS Secrets Manager, IRSA for pod-level AWS access (no static keys in pods).

## Success Targets

Sharpe > 1.5 | Max Drawdown < 10% | Win Rate > 55% | API Latency < 500ms

## Deployment Phases

1. Historical data ingestion
2. Prediction engine
3. Paper trading
4. Agentic AI
5. Broker execution (live)
6. Production rollout
