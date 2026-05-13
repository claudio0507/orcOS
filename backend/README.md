# orcOS — Backend

FastAPI + SQLAlchemy 2 + Pydantic v2. Esta iteração entrega apenas o módulo `pricing_engine` com cobertura completa de testes. API HTTP, modelos ORM, auth e migrations entram na próxima iteração.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Comandos

```bash
pytest                                         # rodar todos os testes
pytest --cov=app/pricing_engine                # com cobertura
pytest tests/unit                              # apenas unit
pytest tests/property                          # apenas property-based
ruff check .                                   # lint
ruff format .                                  # formatar
mypy app                                       # type-check estrito
```

## Módulo `app/pricing_engine`

Motor isolado, Decimal-only, sem efeitos colaterais. Pode ser usado standalone, embutido num worker Celery ou exposto via FastAPI.

Submódulos:

| Arquivo | Responsabilidade |
|---|---|
| `decimal_config.py` | Contexto Decimal global (precisão 28) e quantizadores monetário/percentual |
| `rounding.py` | Banker's vs comercial (configurável por tenant) |
| `exceptions.py` | Hierarquia de erros de domínio |
| `markup.py` | Markup divisor com guards (`T + L + D < 0.95`) |
| `bdi.py` | **Dois modos**: Manual da Empresa (sponsor) + Clássico TCU |
| `spreading.py` | Rateio de custos fixos com **invariante de conservação** |
| `depreciation.py` | Depreciação linear (extensível para outros métodos) |
| `bom_dag.py` | Detecção de ciclo em BOM via DFS |

Veja `tests/` para exemplos de uso.
