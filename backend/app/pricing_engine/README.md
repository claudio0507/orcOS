# Pricing Engine — orcOS

Este módulo contém o núcleo de inteligência financeira do orcOS, responsável por todos os cálculos de precificação, rateio e análise de rentabilidade.

## Visão Geral

O Pricing Engine foi desenhado para garantir **precisão matemática absoluta** em operações financeiras, utilizando o tipo `Decimal` do Python com 28 casas de precisão e seguindo normas técnicas (DNIT, leis de licitação).

### Princípios de Design
1.  **Imutabilidade:** As funções de cálculo não alteram o estado dos objetos; elas retornam novos resultados.
2.  **Precisão:** Uso mandatório de `Decimal`. Nunca use `float` para valores monetários.
3.  **Auditabilidade:** Todos os cálculos são determinísticos e suportam a rastreabilidade exigida pela "Audit Chain".

---

## Fórmulas Implementadas

### 1. Markup (Divisor)
Utilizado para calcular o preço de venda a partir de um custo unitário e percentuais de despesas.
-   **Fórmula:** `Preço = Custo / (1 − ∑%Despesas)`
-   **Parâmetros:** Tributos, Lucro, Despesas Indiretas.
-   **Local:** `markup.py`

### 2. BDI Clássico (Fórmula DNIT)
Segue a fórmula oficial do DNIT para cálculo de Benefícios e Despesas Indiretas.
-   **Fórmula:** `BDI = [((1 + AC + AF + R) * (1 + L)) / (1 - T)] - 1`
-   **Local:** `bdi.py`

### 3. Spreading (Rateio de Custos Fixos)
Distribui custos fixos (ex: mobilização, administração da obra) proporcionalmente ao peso das fichas.
-   **Invariante CA-001:** Garante que a soma das fichas após o rateio seja igual à soma original + custos fixos (± R$ 0,01).
-   **Local:** `spreading.py`

### 4. Depreciação
Cálculo de depreciação diária linear para equipamentos e ativos.
-   **Local:** `depreciação.py`

---

## Como Usar

### Exemplo Simples: Cálculo de Markup
```python
from decimal import Decimal
from app.pricing_engine.markup import compute_unit_price

# Custo de R$ 100,00 com 12% impostos, 10% lucro e 5% indiretas
resultado = compute_unit_price(
    unit_cost=Decimal("100.00"),
    tributes=Decimal("0.12"),
    profit=Decimal("0.10"),
    indirect=Decimal("0.05")
)

print(f"Preço Final: R$ {resultado.unit_price}")  # R$ 136.99
print(f"Divisor: {resultado.divisor}")            # 0.73
```

### Exemplo: Spreading (Rateio)
```python
from decimal import Decimal
from app.pricing_engine.spreading import spread_fixed_costs, SpreadingLine

lines = [
    SpreadingLine(id="item1", variable_unit_price=Decimal("100"), quantity=Decimal("10")),
    SpreadingLine(id="item2", variable_unit_price=Decimal("50"), quantity=Decimal("20")),
]

results = spread_fixed_costs(
    lines=lines,
    fixed_total=Decimal("500.00")
)

# O custo fixo de R$ 500 será distribuído 50/50 entre os itens (pois ambos pesam R$ 1000)
```

---

## Configurações de Precisão
O comportamento global de arredondamento e precisão é definido em `decimal_config.py` e `rounding.py`. Por padrão, o sistema utiliza o **Arredondamento Bancário** (Banker's Rounding / HALF_EVEN).
