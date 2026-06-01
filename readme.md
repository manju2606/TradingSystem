AI Multi-Trading Platform — NSE Futures (Paper Trading First)
Objective
Build an AI-powered multi-timeframe trading platform for Indian markets focused initially on:
•	NSE Futures
•	NIFTY Futures
•	BANKNIFTY Futures
•	Optional future expansion:
o	MCX
o	Options
o	Multi-broker execution
Core capabilities:
•	Multi-timeframe prediction
•	Signal generation
•	Paper trading
•	Agentic AI analysis
•	Portfolio management
•	Backtesting
•	Live deployment
________________________________________
Architecture
Streamlit UI
↓
FastAPI Gateway
↓
Agent Orchestrator
↓
Trading Engine
↓
Prediction Engine
↓
Redis
↓
PostgreSQL
↓
Broker Adapter
↓
Kubernetes
________________________________________
Technology Stack
Frontend
•	Streamlit
•	Plotly
Backend
•	FastAPI
•	Python
Data
•	PostgreSQL
•	Redis
ML
•	XGBoost
•	LightGBM
•	LSTM
•	Transformer
Observability
•	Prometheus
•	Grafana
Deployment
•	Docker
•	Kubernetes
Automation
•	Airflow
Agent Framework
•	LangGraph
•	OpenAI SDK
•	MCP
________________________________________
Repository Structure
trading-platform/
frontend/
streamlit/
backend/
api/
agents/
market/
strategy/
prediction/
execution/
paper/
risk/
db/
postgres/
cache/
redis/
infra/
terraform/
docker/
k8s/
monitoring/
prometheus/
grafana/
________________________________________
Core Services
market-data-service
Responsibilities:
•	Candle ingestion
•	Live feeds
•	Indicator generation
Endpoints:
GET /ohlc
GET /ticks
________________________________________
signal-service
Responsibilities:
•	Generate BUY
•	SELL
•	HOLD
Output:
{
"symbol":"NIFTY",
"tf":"15m",
"signal":"BUY",
"confidence":78
}
________________________________________
prediction-service
Models:
15m–1h:
•	XGBoost
•	LightGBM
4h–1D:
•	LSTM
1W–1M:
•	Transformer
Outputs:
Probability
Direction
Target
Stop Loss
________________________________________
paper-trading-service
Responsibilities:
•	Simulate execution
•	Maintain positions
Features:
•	Virtual wallet
•	Order history
•	PnL
________________________________________
risk-engine
Rules:
Risk per trade ≤2%
Daily loss ≤3%
Max drawdown ≤10%
Exposure limits
Circuit breaker
________________________________________
agentic-ai-layer
Agent 1:
Market Analyst
Tasks:
•	Trend detection
•	Regime classification
Agent 2:
Signal Validator
Tasks:
•	Reject weak signals
Agent 3:
Risk Agent
Tasks:
•	Dynamic SL
•	Position sizing
Agent 4:
Execution Agent
Tasks:
•	Route orders
Agent 5:
Trade Journal Agent
Tasks:
•	Summaries
•	Lessons

Agent 6:
Cost-Reviewer 
Estimates monthly AWS costs for the infrastructure by analysing Terraform configurations. Compares dev vs prod, identifies top cost drivers, and suggests optimization opportunities. Use when reviewing infrastructure costs or planning budget.
tools: Read, Grep, Glob
model: haiku

________________________________________
Prediction Horizons
15m
30m
1h
4h
6h
8h
1D
1W
1M
Output:
BUY
SELL
HOLD
Confidence
Entry
SL
Target
________________________________________
Database Schema
users
symbols
candles
signals
predictions
orders
positions
backtests
agent_logs
________________________________________
FastAPI Endpoints
POST /signal
GET /prediction
POST /paper/order
GET /positions
GET /backtest
GET /portfolio
________________________________________
Docker
docker-compose
services:
postgres
redis
api
streamlit
prometheus
grafana
________________________________________
Kubernetes
Deployments
signal-engine
prediction-engine
api
streamlit
Ingress
HPA
Karpenter
________________________________________
Observability
Metrics:
•	Win Rate
•	Sharpe
•	Drawdown
Tools:
•	Prometheus
•	Grafana
•	OpenTelemetry
________________________________________
Security
JWT
RBAC
Secrets
Vault
IRSA
________________________________________
Deployment Phases
Phase 1
Historical ingestion
Phase 2
Prediction engine
Phase 3
Paper trading
Phase 4
Agentic AI
Phase 5
Broker execution
Phase 6
Production rollout
________________________________________
Success Metrics
Sharpe >1.5
Drawdown <10%
Win Rate >55%
Latency <500ms

