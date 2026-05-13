# Arquitetura orcOS

## Visão Geral
O orcOS é uma plataforma distribuída composta por um backend robusto em Python (FastAPI) e um frontend moderno em React.

## Componentes

### 1. Backend (Python/FastAPI)
- **Cálculo (Pricing Engine)**: Implementado com foco em precisão (Decimal) e auditabilidade.
- **API**: Endpoints RESTful para gestão de orçamentos, fichas e composições.
- **Autenticação**: OAuth2 com JWT e suporte a Multi-Factor Authentication (MFA).
- **Persistência**: PostgreSQL via SQLAlchemy 2.0.

### 2. Frontend (React/Vite)
- **Framework**: React com TypeScript.
- **Estado**: TanStack Query (React Query) para sincronização com a API.
- **Formulários**: React Hook Form + Zod para validação robusta.
- **UI**: Vanilla CSS com um design system responsivo e premium.

### 3. Infraestrutura
- **Containerização**: Docker e Docker Compose.
- **CI/CD**: Scripts de deploy automatizado para ambientes local e staging.
- **Qualidade**: Testes unitários, de propriedade (Hypothesis) e E2E.
