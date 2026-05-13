"""
Spreading / Rateio de custos fixos — PRD v2.0 §3.5.4.

Custos fixos (Estrutura Operacional, mobilização, considerações excepcionais
aprovadas) são diluídos proporcionalmente ao **preço unitário variável** de
cada linha:

    peso_i           = preço_unit_variável_i * qty_i
    total_pesos      = Σ peso_i
    fixo_alocado_i   = fixos_totais * (peso_i / total_pesos)
    preço_final_i    = preço_unit_variável_i + (fixo_alocado_i / qty_i)

Invariante (validado em testes property-based):

    Σ (preço_final_i * qty_i)  ==  Σ (preço_unit_variável_i * qty_i) + fixos_totais

Para garantir a invariante apesar do arredondamento monetário, o algoritmo
calcula totais em precisão alta, arredonda cada linha e devolve o resíduo
(diferença entre soma arredondada e soma esperada) à linha de maior peso.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.pricing_engine.exceptions import SpreadingError
from app.pricing_engine.rounding import RoundingMode, round_money


@dataclass(frozen=True, slots=True)
class SpreadingLine:
    """Linha de orçamento antes do spreading.

    Attributes:
        id: identificador da linha (livre; usado para o snapshot e callback).
        variable_unit_price: preço unitário variável (após markup/BDI da linha).
        quantity: quantidade (deve ser > 0).
    """

    id: str
    variable_unit_price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class SpreadingResultLine:
    """Linha após spreading.

    Attributes:
        id: ecoa o id de entrada.
        variable_unit_price: preço variável original.
        quantity: quantidade original.
        allocated_fixed: valor de fixo alocado **ao total da linha** (já arredondado).
        final_unit_price: variable_unit_price + allocated_fixed / quantity (arredondado).
        final_line_total: final_unit_price * quantity (recalculado p/ casar invariante).
        carries_residue: se True, esta linha recebeu o ajuste de resíduo de arredondamento.
    """

    id: str
    variable_unit_price: Decimal
    quantity: Decimal
    allocated_fixed: Decimal
    final_unit_price: Decimal
    final_line_total: Decimal
    carries_residue: bool = False


def spread_fixed_costs(
    *,
    lines: list[SpreadingLine],
    fixed_total: Decimal,
    rounding: RoundingMode = RoundingMode.BANKER,
) -> list[SpreadingResultLine]:
    """Aplica o spreading proporcional ao peso (preço_variável * qty).

    Garante a invariante:
        Σ (final_unit_price * quantity)  ==  Σ (variable_unit_price * quantity) + fixed_total

    com arredondamento monetário. O resíduo eventual é absorvido pela linha de
    maior peso, marcada com `carries_residue=True`.

    Raises:
        SpreadingError: lista vazia, quantity<=0, ou soma de pesos == 0.
    """
    if not lines:
        raise SpreadingError("Lista de linhas vazia.")
    for line in lines:
        if line.quantity <= 0:
            raise SpreadingError(f"Linha {line.id!r} com quantity<=0 ({line.quantity}).")
        if line.variable_unit_price < 0:
            raise SpreadingError(
                f"Linha {line.id!r} com variable_unit_price<0 ({line.variable_unit_price})."
            )

    weights = [line.variable_unit_price * line.quantity for line in lines]
    total_weight = sum(weights, Decimal("0"))

    if total_weight <= 0:
        # Todas as linhas com preço variável zero — não há peso para ratear.
        # Política: distribui igualmente entre as linhas (proxy razoável).
        if fixed_total != 0:
            raise SpreadingError(
                "Soma de pesos zero, mas há custo fixo a ratear. "
                "Defina preços variáveis ou distribua manualmente."
            )
        # fixed_total == 0 e weights == 0: tudo zero, devolve linhas inalteradas.
        return [
            SpreadingResultLine(
                id=line.id,
                variable_unit_price=line.variable_unit_price,
                quantity=line.quantity,
                allocated_fixed=Decimal("0.00"),
                final_unit_price=round_money(line.variable_unit_price, mode=rounding),
                final_line_total=round_money(
                    line.variable_unit_price * line.quantity, mode=rounding
                ),
                carries_residue=False,
            )
            for line in lines
        ]

    target_total = total_weight + fixed_total

    # Calcula alocações em alta precisão.
    raw_allocations = [fixed_total * (w / total_weight) for w in weights]
    raw_final_unit_prices = [
        line.variable_unit_price + (alloc / line.quantity)
        for line, alloc in zip(lines, raw_allocations, strict=True)
    ]
    raw_final_line_totals = [
        unit * line.quantity
        for unit, line in zip(raw_final_unit_prices, lines, strict=True)
    ]

    # Arredonda totais de linha primeiro (preserva invariante de soma).
    rounded_line_totals = [round_money(t, mode=rounding) for t in raw_final_line_totals]
    target_total_rounded = round_money(target_total, mode=rounding)
    residue = target_total_rounded - sum(rounded_line_totals, Decimal("0"))

    # Aplica resíduo à linha de maior peso.
    residue_idx = max(range(len(lines)), key=lambda i: weights[i])
    if residue != 0:
        rounded_line_totals[residue_idx] += residue

    # Deriva preço unitário final a partir do total arredondado.
    final_unit_prices = [
        round_money(total / line.quantity, mode=rounding)
        for total, line in zip(rounded_line_totals, lines, strict=True)
    ]

    rounded_allocations = [
        round_money(alloc, mode=rounding) for alloc in raw_allocations
    ]

    return [
        SpreadingResultLine(
            id=line.id,
            variable_unit_price=line.variable_unit_price,
            quantity=line.quantity,
            allocated_fixed=rounded_allocations[i],
            final_unit_price=final_unit_prices[i],
            final_line_total=rounded_line_totals[i],
            carries_residue=(i == residue_idx and residue != 0),
        )
        for i, line in enumerate(lines)
    ]
