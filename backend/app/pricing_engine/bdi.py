"""
BDI — Bonificação e Despesas Indiretas, dois modos (PRD v2.0 §3.5.5).

Modo A — Manual da Empresa (DEFAULT, orientação do sponsor).
    Composição livre de componentes sobre faturamento e sobre custo, espelhando
    a expertise tributária interna da Alta Noroeste. Atende cenários atípicos
    (regimes especiais, substituição tributária, obras públicas).

        T_fat   = Σ %_i  (sobre faturamento)
        T_custo = Σ %_j  (sobre custo)
        custo_ajustado = custo_direto * (1 + T_custo)
        markup_divisor = 1 - T_fat
        preço_unit     = custo_ajustado / markup_divisor

Modo B — BDI Clássico (recomendado como alternativa).
    Fórmula consagrada (Acórdão TCU 2622/2013):

        BDI = ((1 + AC + DF + R) * (1 + L)) / (1 - T) - 1
        preço_unit = custo_direto * (1 + BDI)

Guards comuns:
    - T_fat (Modo A) ou T (Modo B) >= 0.95  → BdiGuardError
    - Denominador `1 - T..` <= 0            → BdiGuardError
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Final

from app.pricing_engine.exceptions import BdiGuardError
from app.pricing_engine.rounding import RoundingMode, round_money

DEFAULT_BDI_GUARD: Final[Decimal] = Decimal("0.95")
DEFAULT_BDI_ALERT: Final[Decimal] = Decimal("0.70")


class BdiMode(StrEnum):
    MANUAL = "manual"  # Modo A — Manual da Empresa (default por sponsor)
    CLASSIC = "classic"  # Modo B — Clássico TCU


# ---------------------------------------------------------------------------
# Modo A — Manual da Empresa
# ---------------------------------------------------------------------------


class ComponentBase(StrEnum):
    """Onde o percentual incide."""

    REVENUE = "revenue"  # sobre faturamento (no denominador 1-Σ)
    COST = "cost"  # sobre custo (multiplica o custo direto)


@dataclass(frozen=True, slots=True)
class BdiComponent:
    """Componente de cenário manual.

    Attributes:
        name: rótulo legível (ex: "PIS", "COFINS", "Lucro Líquido", "ISS").
        percent: alíquota em forma fracionária (0.0925 == 9.25%).
        base: REVENUE para componentes sobre faturamento; COST para componentes
              sobre custo (encargos adicionais, contingência, etc).
        legal_reference: texto livre da base legal (opcional, registrado no snapshot).
    """

    name: str
    percent: Decimal
    base: ComponentBase
    legal_reference: str = ""


@dataclass(frozen=True, slots=True)
class ManualScenarioResult:
    mode: BdiMode = BdiMode.MANUAL
    t_revenue: Decimal = Decimal("0")  # soma de componentes sobre faturamento
    t_cost: Decimal = Decimal("0")  # soma de componentes sobre custo
    adjusted_cost: Decimal = Decimal("0")  # custo_direto * (1 + t_cost)
    divisor: Decimal = Decimal("1")  # 1 - t_revenue
    unit_price: Decimal = Decimal("0")  # arredondado
    is_alert: bool = False
    components_snapshot: tuple[BdiComponent, ...] = field(default_factory=tuple)


def compute_price_manual(
    *,
    unit_cost: Decimal,
    components: list[BdiComponent],
    guard: Decimal = DEFAULT_BDI_GUARD,
    alert: Decimal = DEFAULT_BDI_ALERT,
    rounding: RoundingMode = RoundingMode.BANKER,
) -> ManualScenarioResult:
    """
    Calcula o preço unitário usando o Modo A (Manual da Empresa).

    Aplica a fórmula: preço = custo * (1 + T_custo) / (1 - T_fat).

    Args:
        unit_cost: Custo unitário direto.
        components: Lista de componentes (tributos, lucro, etc).
        guard: Limite máximo para a soma de componentes sobre faturamento.
        alert: Limite para disparar flag de alerta.
        rounding: Modo de arredondamento a ser aplicado.

    Returns:
        ManualScenarioResult contendo o preço calculado e metadados.

    Raises:
        BdiGuardError: Se a soma dos componentes sobre faturamento atingir o guard.
    """
    t_rev = sum((c.percent for c in components if c.base is ComponentBase.REVENUE), Decimal("0"))
    t_cost = sum((c.percent for c in components if c.base is ComponentBase.COST), Decimal("0"))

    if t_rev >= guard:
        raise BdiGuardError(
            f"Soma de componentes sobre faturamento ({t_rev}) excede guard ({guard}).",
            total=t_rev,
            guard=guard,
        )
    divisor = Decimal("1") - t_rev
    if divisor <= 0:  # pragma: no cover - defensive; guard<=1 already prevents this.
        raise BdiGuardError(
            f"Denominador do markup (1 - {t_rev}) <= 0.", total=t_rev, guard=guard
        )

    adjusted = unit_cost * (Decimal("1") + t_cost)
    raw_price = adjusted / divisor

    return ManualScenarioResult(
        t_revenue=t_rev,
        t_cost=t_cost,
        adjusted_cost=adjusted,
        divisor=divisor,
        unit_price=round_money(raw_price, mode=rounding),
        is_alert=t_rev >= alert,
        components_snapshot=tuple(components),
    )


# ---------------------------------------------------------------------------
# Modo B — Clássico TCU
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClassicBdiInputs:
    """Parâmetros do BDI Clássico (Acórdão TCU 2622/2013).

    Todos os valores são fracionários (0.04 == 4%).
    """

    administration: Decimal  # AC — Administração Central
    financial: Decimal  # DF — Despesas Financeiras
    risk: Decimal  # R  — Riscos / contingência
    profit: Decimal  # L  — Lucro
    tributes: Decimal  # T  — Tributos sobre faturamento


@dataclass(frozen=True, slots=True)
class ClassicScenarioResult:
    mode: BdiMode = BdiMode.CLASSIC
    bdi: Decimal = Decimal("0")  # BDI em forma fracionária
    unit_price: Decimal = Decimal("0")  # arredondado
    is_alert: bool = False
    inputs_snapshot: ClassicBdiInputs | None = None


def compute_price_classic(
    *,
    unit_cost: Decimal,
    inputs: ClassicBdiInputs,
    guard: Decimal = DEFAULT_BDI_GUARD,
    alert: Decimal = DEFAULT_BDI_ALERT,
    rounding: RoundingMode = RoundingMode.BANKER,
) -> ClassicScenarioResult:
    """
    Calcula o preço unitário usando o Modo B (Clássico TCU).

    Aplica a fórmula: BDI = ((1 + AC + DF + R) * (1 + L)) / (1 - T) - 1.

    Args:
        unit_cost: Custo unitário direto.
        inputs: Parâmetros AC, DF, R, L e T.
        guard: Limite máximo para tributos (T).
        alert: Limite para disparar flag de alerta.
        rounding: Modo de arredondamento a ser aplicado.

    Returns:
        ClassicScenarioResult contendo o BDI e o preço final.

    Raises:
        BdiGuardError: Se os tributos (T) atingirem o guard.
    """
    t = inputs.tributes
    if t >= guard:
        raise BdiGuardError(
            f"Tributos ({t}) excedem guard ({guard}).", total=t, guard=guard
        )
    divisor = Decimal("1") - t
    if divisor <= 0:  # pragma: no cover - defensive; guard<=1 already prevents this.
        raise BdiGuardError(
            f"Denominador do BDI (1 - {t}) <= 0.", total=t, guard=guard
        )

    numerator = (Decimal("1") + inputs.administration + inputs.financial + inputs.risk) * (
        Decimal("1") + inputs.profit
    )
    bdi = numerator / divisor - Decimal("1")
    raw_price = unit_cost * (Decimal("1") + bdi)

    return ClassicScenarioResult(
        bdi=bdi,
        unit_price=round_money(raw_price, mode=rounding),
        is_alert=t >= alert,
        inputs_snapshot=inputs,
    )
