"""Factories factory_boy para testes de integração."""
from tests.integration.factories.ficha import FichaFactory
from tests.integration.factories.orcamento import OrcamentoFactory
from tests.integration.factories.tenant import TenantFactory
from tests.integration.factories.usuario import UsuarioFactory

__all__ = ["FichaFactory", "OrcamentoFactory", "TenantFactory", "UsuarioFactory"]
