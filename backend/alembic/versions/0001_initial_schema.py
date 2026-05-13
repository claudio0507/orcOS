"""Initial schema — tenants, usuarios, orcamentos, fichas, composicoes + RLS.

Revision ID: 0001
Revises:
Create Date: 2026-05-13
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Tabelas com RLS multi-tenant (exceto tenants, que não tem tenant_id)
_RLS_TABLES = ["usuarios", "orcamentos", "fichas", "composicoes"]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enum types
    # ------------------------------------------------------------------
    op.execute("CREATE TYPE rounding_mode_enum AS ENUM ('banker', 'commercial')")

    # ------------------------------------------------------------------
    # tenants
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("rounding_mode", sa.Enum("banker", "commercial", name="rounding_mode_enum", create_type=False), nullable=False, server_default="banker"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # ------------------------------------------------------------------
    # usuarios
    # ------------------------------------------------------------------
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="orcamentista"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_usuarios_tenant_email"),
    )
    op.create_index("ix_usuarios_tenant_id", "usuarios", ["tenant_id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    # ------------------------------------------------------------------
    # orcamentos
    # ------------------------------------------------------------------
    op.create_table(
        "orcamentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("criado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="rascunho"),
        sa.Column("custo_fixo_total", sa.String(30), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orcamentos_tenant_id", "orcamentos", ["tenant_id"])
    op.create_index("ix_orcamentos_status", "orcamentos", ["status"])
    op.create_index("ix_orcamentos_criado_por_id", "orcamentos", ["criado_por_id"])

    # ------------------------------------------------------------------
    # fichas
    # ------------------------------------------------------------------
    op.create_table(
        "fichas",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orcamento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("descricao", sa.String(500), nullable=False),
        sa.Column("unidade", sa.String(50), nullable=False, server_default="un"),
        sa.Column("quantidade", sa.String(30), nullable=False),
        sa.Column("custo_unitario", sa.String(30), nullable=False),
        sa.Column("tipo_precificacao", sa.String(50), nullable=False, server_default="markup"),
        sa.Column("parametros_precificacao", sa.Text(), nullable=True),
        sa.Column("preco_unitario_calculado", sa.String(30), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["orcamento_id"], ["orcamentos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fichas_tenant_id", "fichas", ["tenant_id"])
    op.create_index("ix_fichas_orcamento_id", "fichas", ["orcamento_id"])
    op.create_index("ix_fichas_tipo_precificacao", "fichas", ["tipo_precificacao"])
    op.create_index("ix_fichas_ordem", "fichas", ["ordem"])

    # ------------------------------------------------------------------
    # composicoes
    # ------------------------------------------------------------------
    op.create_table(
        "composicoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ficha_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pai_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("descricao", sa.String(500), nullable=False),
        sa.Column("codigo", sa.String(100), nullable=True),
        sa.Column("tipo", sa.String(50), nullable=False, server_default="material"),
        sa.Column("unidade", sa.String(50), nullable=False, server_default="un"),
        sa.Column("quantidade", sa.String(30), nullable=False),
        sa.Column("custo_unitario", sa.String(30), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ficha_id"], ["fichas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pai_id"], ["composicoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_composicoes_tenant_id", "composicoes", ["tenant_id"])
    op.create_index("ix_composicoes_ficha_id", "composicoes", ["ficha_id"])
    op.create_index("ix_composicoes_pai_id", "composicoes", ["pai_id"])
    op.create_index("ix_composicoes_tipo", "composicoes", ["tipo"])
    op.create_index("ix_composicoes_codigo", "composicoes", ["codigo"])

    # ------------------------------------------------------------------
    # Row-Level Security (CA-005)
    # Política: cada row só é visível se tenant_id == app.tenant_id da sessão
    # ------------------------------------------------------------------
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )

    # updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    for table in ["tenants", *_RLS_TABLES]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)


def downgrade() -> None:
    for table in ["tenants", *_RLS_TABLES]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    for table in _RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")

    op.drop_table("composicoes")
    op.drop_table("fichas")
    op.drop_table("orcamentos")
    op.drop_table("usuarios")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS rounding_mode_enum")
