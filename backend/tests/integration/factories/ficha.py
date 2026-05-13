"""Factory: Ficha — build-only."""
from __future__ import annotations

import factory

from app.models.ficha import Ficha, TipoPrecificacao


class FichaFactory(factory.Factory):
    class Meta:
        model = Ficha

    descricao = factory.Sequence(lambda n: f"Serviço de Teste {n}")
    unidade = "m²"
    quantidade = "10.00"
    custo_unitario = "500.00"
    tipo_precificacao = TipoPrecificacao.MARKUP
    parametros_precificacao = '{"tributes": "0.12", "profit": "0.10", "indirect": "0.05"}'
    preco_unitario_calculado = None
    ordem = factory.Sequence(lambda n: n)
