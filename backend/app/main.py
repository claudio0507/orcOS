"""Aplicação FastAPI principal — orcOS backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import fichas, orcamentos, orcamentos_spreading
from app.core.config import settings

app = FastAPI(
    title="orcOS API",
    version="0.1.0",
    description="Sistema de Orçamentação Alta Noroeste — API REST multi-tenant",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orcamentos.router, prefix="/api/v1")
app.include_router(fichas.router, prefix="/api/v1")
app.include_router(orcamentos_spreading.router, prefix="/api/v1")


@app.get("/health", tags=["Sistema"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
