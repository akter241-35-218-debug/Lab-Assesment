"""FastAPI entry point.  Run from the project root:

    uvicorn backend.app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (registers tables)
from .config import settings
from .database import Base, engine
from .routers import actions, alerts, companies, dashboard, medicines, sales
from .scheduler.daily_job import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)
    scheduler = start_scheduler()
    yield
    stop_scheduler(scheduler)


app = FastAPI(
    title="Pharmacy Shelf API",
    description="Expiry & dead-stock decision assistant for pharmacies",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

for r in (companies.router, medicines.router, sales.router, alerts.router, actions.router, dashboard.router):
    app.include_router(r)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
