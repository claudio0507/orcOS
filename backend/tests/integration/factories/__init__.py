"""Factories factory_boy para testes de integração."""
from tests.integration.factories.tenant import TenantFactory
from tests.integration.factories.usuario import UsuarioFactory
from tests.integration.factories.orcamento import OrcamentoFactory
from tests.integration.factories.ficha import FichaFactory

__all__ = ["TenantFactory", "UsuarioFactory", "OrcamentoFactory", "FichaFactory"]
