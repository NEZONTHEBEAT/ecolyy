"""
Ecolyy API entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000

Swagger docs at /docs once running.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Ecolyy API",
    description="Backend API for Ecolyy — India's organized recycling platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"name": "Ecolyy API", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
