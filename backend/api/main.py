from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from backend.api.routers import backtest, paper, portfolio, prediction, signal
from db.postgres.database import engine
from db.postgres.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Trading Platform API",
    description="AI-powered NSE Futures trading platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(signal.router, prefix="/signal", tags=["signals"])
app.include_router(prediction.router, prefix="/prediction", tags=["predictions"])
app.include_router(paper.router, prefix="/paper", tags=["paper-trading"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {"status": "ok"}
