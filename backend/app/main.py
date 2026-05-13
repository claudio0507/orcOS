"""Aplicação FastAPI principal — orcOS backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1 import admin, admin_audit, auth, auth_mfa, fichas, orcamentos, orcamentos_spreading
from app.core.config import settings

# ── Metadados dos grupos de tags (exibidos em /docs e /redoc) ────────────
TAGS_METADATA = [
    {
        "name": "Sistema",
        "description": "Endpoints de infraestrutura: health-check, versão.",
    },
    {
        "name": "Autenticação",
        "description": "Login JWT, Refresh Tokens e Logout.",
    },
    {
        "name": "Autenticação MFA",
        "description": "Configuração e Verificação de TOTP (Time-Based One-Time Password).",
    },
    {
        "name": "Administração",
        "description": "Endpoints restritos para administradores (Auditoria, etc).",
    },
    {
        "name": "Orçamentos",
        "description": (
            "CRUD completo de orçamentos de obra. "
            "Cada orçamento pertence a um **tenant** e contém fichas (linhas de serviço). "
            "O campo `custo_fixo_total` armazena os custos fixos para o spreading."
        ),
    },
    {
        "name": "Fichas",
        "description": (
            "CRUD de fichas (linhas de serviço/insumo) dentro de um orçamento. "
            "Inclui endpoint de **cálculo de preço** via pricing engine "
            "(Markup, BDI Manual, BDI Clássico)."
        ),
    },
    {
        "name": "Spreading",
        "description": (
            "Rateio de custos fixos sobre as fichas de um orçamento.\n\n"
            "O algoritmo distribui os custos fixos proporcionalmente ao peso "
            "(preço variável × quantidade) de cada ficha, garantindo a invariante **CA-001**:\n\n"
            "```\n"
            "Σ(preço_final × qty) == Σ(preço_variável × qty) + custos_fixos ± R$0,01\n"
            "```\n\n"
            "O resíduo de arredondamento monetário é absorvido pela linha de maior peso."
        ),
    },
]

# ── Descrição principal da API (exibida no topo de /docs e /redoc) ───────
API_DESCRIPTION = """
## 🏗️ orcOS — Sistema de Orçamentação para Engenharia

API REST multi-tenant para criação, precificação e análise de orçamentos de obras
de infraestrutura e sinalização viária.

### 🔐 Autenticação por Tenant

Todas as requisições exigem o header `X-Tenant-ID` com um UUID v4 válido.
O sistema aplica **Row Level Security (RLS)** — cada tenant só acessa seus dados.

```
X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000
```

### 💰 Motor de Precificação

O backend inclui um motor de cálculo que suporta três modos:

| Modo | Descrição |
|------|-----------|
| **Markup** | Divisor = 1 − (tributos + lucro + despesas indiretas) |
| **BDI Manual** | Componentes arbitrários sobre receita ou custo |
| **BDI Clássico** | Fórmula DNIT: (1+AC+AF+R)(1+L) / (1−T) |

### 📊 Spreading (Rateio de Custos Fixos)

Após precificar as fichas individualmente, o endpoint de **spreading**
distribui os custos fixos (estrutura operacional, mobilização)
proporcionalmente ao peso de cada linha, preservando a invariante:

> **CA-001:** Σ(preço_final × qty) = Σ(preço_variável × qty) + custos_fixos ± R$0,01

### 🔢 Precisão Numérica

- Todos os valores monetários usam `Decimal` (nunca `float`)
- Arredondamento padrão: **Banker's rounding** (ROUND_HALF_EVEN)
- Opção de arredondamento comercial (ROUND_HALF_UP) por endpoint
"""

from contextlib import asynccontextmanager
from app.audit.job import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan_app(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    lifespan=lifespan_app,
    title="orcOS API",
    version="0.1.0",
    summary="Sistema de Orçamentação para Engenharia de Infraestrutura e Sinalização Viária",
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "orcOS Team",
        "url": "https://github.com/claudio0507/orcOS",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_mfa.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(admin_audit.router, prefix="/api/v1")
app.include_router(orcamentos.router, prefix="/api/v1")
app.include_router(fichas.router, prefix="/api/v1")
app.include_router(orcamentos_spreading.router, prefix="/api/v1")


@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health check do serviço",
    description="Retorna status operacional e versão da API. Útil para load balancers e monitoramento.",
    response_description="Status OK com versão atual.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "ok", "version": "0.1.0"}
                }
            }
        }
    },
)
async def health() -> dict[str, str]:
    """Retorna status e versão da API."""
    return {"status": "ok", "version": "0.1.0"}
