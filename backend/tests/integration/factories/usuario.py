"""Factory: Usuario — build-only."""
from __future__ import annotations

import factory

from app.models.usuario import RoleUsuario, Usuario


class UsuarioFactory(factory.Factory):
    class Meta:
        model = Usuario

    email = factory.Sequence(lambda n: f"usuario{n}@example.com")
    nome = factory.Sequence(lambda n: f"Usuario Teste {n}")
    hashed_password = "$2b$12$placeholder_hash_for_tests"
    role = RoleUsuario.ORCAMENTISTA
    ativo = True
