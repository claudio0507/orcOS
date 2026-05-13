# orcOS — Sistema de Gestão de Orçamentos e Precificação Alta Noroeste

Plataforma multi-tenant de orçamentação para serviços de sinalização viária e obras correlatas. Substitui planilhas Excel por um motor de cálculo auditável, com governança contábil, workflow de aprovação e inteligência decisória.

## Estado atual

Esta entrega corresponde ao **scaffold inicial + módulo `pricing_engine`** implementado com TDD. O motor matemático cobre os conceitos formalizados no PRD v2.0:

- Markup divisor com guards de segurança
- BDI em **dois modos** coexistentes (Manual da Empresa + Clássico TCU)
- Spreading de custos fixos com invariante de conservação (testado por Hypothesis)
- Depreciação linear de ferramental/EPI/frota
- Detecção de ciclos no BOM via DFS

API HTTP, persistência, auth, frontend e infra completos serão materializados em iterações subsequentes do MVP.

## Estrutura

```
orcOS/
├── backend/                FastAPI + SQLAlchemy 2 + Pydantic v2 (Python 3.11+)
│   ├── app/
│   │   └── pricing_engine/ Motor de cálculo financeiro (Decimal-only)
│   └── tests/
│       ├── unit/           Testes unitários determinísticos
│       └── property/       Testes property-based (Hypothesis)
├── frontend/               Placeholder Vite + React + TS (próxima iteração)
├── infra/                  Dockerfile, docker-compose, K8s helm (próxima iteração)
└── docs/                   PRD v2.0 e documentação técnica
```

## Quick start (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # roda todos os testes
pytest --cov=app/pricing_engine --cov-report=term-missing
ruff check .
mypy app
```

## Conceitos matemáticos do motor

Ver `docs/PRICING_ENGINE.md` (gerado nesta iteração) para a especificação formal com fórmulas, guards e invariantes property-tested.

## Branch de desenvolvimento

Todas as mudanças desta iteração vão para `claude/project-analysis-improvements-rqi2e`.
