# orcOS — Sistema de Gestão de Orçamentos e Precificação Alta Noroeste

Plataforma multi-tenant de orçamentação para serviços de sinalização viária e obras correlatas. Substitui planilhas Excel por um motor de cálculo auditável, com governança contábil, workflow de aprovação e inteligência decisória.

## Estado atual

Esta entrega corresponde ao **MVP Funcional**, incluindo:

- **Pricing Engine**: Motor matemático robusto com Markup, BDI (Manual/Clássico), Spreading e Depreciação.
- **Backend API**: FastAPI com persistência em PostgreSQL (via SQLAlchemy), autenticação JWT e suporte a MFA.
- **Frontend Scaffold**: React + Vite + TypeScript com estrutura de componentes, roteamento e integração de tipos.
- **E2E Testing**: Suíte de testes automatizados para o fluxo principal de orçamento.
- **Infraestrutura**: Docker Compose e scripts de deployment local/staging.

## Estrutura

```
orcOS/
├── backend/                FastAPI + SQLAlchemy 2 + Pydantic v2
│   ├── app/                Coração da aplicação (api, models, schemas, services)
│   │   └── pricing_engine/ Motor de cálculo financeiro
│   └── tests/              Unitários, Property-based e E2E
├── frontend/               React + Vite + TS (Scaffold inicial)
├── infra/                  Dockerfile, docker-compose, scripts de deploy
└── docs/                   Documentação técnica e PRD
```

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # Roda todos os testes (Unit + E2E)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Branch de desenvolvimento

Todas as mudanças desta iteração estão em `claude/project-analysis-improvements-rqi2e`.
