"""Factory: Tenant — build-only (persist manual com session.add + flush)."""
from __future__ import annotations

import factory

from app.models.tenant import Tenant
from app.pricing_engine.rounding import RoundingMode


class TenantFactory(factory.Factory):
    class Meta:
        model = Tenant

    nome = factory.Sequence(lambda n: f"Empresa Teste {n}")
    slug = factory.Sequence(lambda n: f"empresa-teste-{n}")
    rounding_mode = RoundingMode.BANKER
    ativo = True
