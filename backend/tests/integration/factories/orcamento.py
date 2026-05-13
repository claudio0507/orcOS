"""Factory: Orcamento — build-only."""
from __future__ import annotations

import factory
import factory.fuzzy

from app.models.orcamento import Orcamento, StatusOrcamento


class OrcamentoFactory(factory.Factory):
    class Meta:
        model = Orcamento

    titulo = factory.Sequence(lambda n: f"Orçamento de Teste {n}")
    descricao = "Descrição de teste do orçamento"
    status = StatusOrcamento.RASCUNHO
    custo_fixo_total = "0"
    criado_por_id = None
