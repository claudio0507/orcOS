# Design: Frontend CRUD Orçamentos — Fase 5

**Data:** 2026-05-13
**Status:** Aprovado
**Scope:** CRUD funcional de orçamentos com UX completa (Fase 5 do orcOS)

---

## Contexto

Frontend React + Vite + TS scaffoldado. Integração básica existe (login, listagem). Faltam telas de criação, edição, visualização e exclusão de orçamentos. Backend FastAPI funcionando em `http://127.0.0.1:8000/api/v1`.

Stack existente: React 18, React Router 6, React Query 5, Zod, react-hook-form, Axios, CSS customizado (sem Tailwind).

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Navegação | Sidebar fixa | Padrão ERP/gestão, escala para features futuras |
| Estrutura de arquivos | Flat ampliada | Menor fricção, compatível com estrutura existente |
| Toast | react-hot-toast | Leve, zero config |
| Auth state | localStorage (sem Context) | Suficiente para MVP |

---

## 1. Arquitetura e Rotas

### Rotas (App.tsx)

```
/login                    → LoginPage
/                         → redirect → /orcamentos
/orcamentos               → OrcamentosListPage      [protegida]
/orcamentos/novo          → OrcamentoCreatePage     [protegida]
/orcamentos/:id           → OrcamentoDetailPage     [protegida]
/orcamentos/:id/editar    → OrcamentoEditPage       [protegida]
```

### Proteção de Rotas

`ProtectedRoute` lê `localStorage.getItem('token')`. Se ausente, redireciona para `/login` com `<Navigate replace />`. Sem Context de auth — localStorage é a fonte de verdade.

### Layout

`AppLayout` envolve todas as rotas autenticadas:
- Sidebar esquerda fixa com links de navegação e botão logout
- Área de conteúdo principal com `<Outlet />`
- `LoginPage` fora do `AppLayout`

### Toast

`react-hot-toast` com `<Toaster />` em `App.tsx`. Posição: `top-right`. Usado em mutations para feedback de sucesso/erro.

---

## 2. Camada de Dados (Hooks)

Todos os hooks ficam em `src/hooks/useApi.ts`, expandindo o arquivo existente.

### Queries

```typescript
useOrcamentos()     // GET /orcamentos — já existe, mantém
useOrcamento(id)    // GET /orcamentos/:id — novo
```

### Mutations

```typescript
useCreateOrcamento()   // POST /orcamentos
useUpdateOrcamento()   // PATCH /orcamentos/:id
useDeleteOrcamento()   // DELETE /orcamentos/:id
```

### Padrão das Mutations

- `onSuccess`: invalida `['orcamentos']` + `['orcamento', id]` → refetch automático
- `onSuccess`: toast de sucesso + navegação (quando aplicável)
- `onError`: toast de erro com mensagem do backend (`error.response?.data?.detail`)

### Fichas

`OrcamentoDetailPage` exibe seção "Fichas" com placeholder. Hooks de fichas não implementados nesta fase.

---

## 3. Componentes

### Novos em `src/components/ui/`

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| `ProtectedRoute` | `ProtectedRoute.tsx` | Guard de rota, redireciona sem token |
| `AppLayout` | `AppLayout.tsx` | Sidebar + `<Outlet />` |
| `Sidebar` | `Sidebar.tsx` | Links de navegação + logout |
| `StatusBadge` | `StatusBadge.tsx` | Badge colorido por status do orçamento |
| `ConfirmDialog` | `ConfirmDialog.tsx` | Modal de confirmação para delete |
| `OrcamentoForm` | `OrcamentoForm.tsx` | Form Zod+RHF compartilhado (Create e Edit) |

### Componentes Existentes Reutilizados

- `Button` — sem alteração
- `Input` — reutilizado com props `label` e `error` já existentes
- `Card` — reutilizado nas páginas de detalhe

### Sem Novas Abstrações de Form

`InputField`, `TextAreaField`, `CurrencyInput` não serão criados separadamente. O `Input` existente atende. `CurrencyInput` = `Input` com `type="text"` e validação no schema Zod.

### Schema de Validação

```typescript
const orcamentoSchema = z.object({
  titulo: z.string().min(3, 'Mínimo 3 caracteres').max(100),
  descricao: z.string().max(500).optional(),
  custo_fixo_total: z.string().regex(/^\d+(\.\d{2})?$/, 'Formato: 100.00'),
})
type OrcamentoFormData = z.infer<typeof orcamentoSchema>
```

---

## 4. Páginas

### OrcamentosListPage (`/orcamentos`)

- Tabela: Título / Status (`StatusBadge`) / Custo Fixo / Ações
- Ações por linha: Visualizar (→ `/orcamentos/:id`), Editar (→ `/orcamentos/:id/editar`), Excluir (→ `ConfirmDialog`)
- Botão "Novo Orçamento" no topo direito → `/orcamentos/novo`
- Estado de loading: spinner centralizado
- Estado vazio: mensagem "Nenhum orçamento encontrado" + botão "Criar primeiro orçamento"
- Estado de erro: mensagem de erro da API

### OrcamentoCreatePage (`/orcamentos/novo`)

- `OrcamentoForm` em branco
- Submit → `useCreateOrcamento` → toast "Orçamento criado!" → navega para `/orcamentos/:newId`
- Botão "Cancelar" → volta para `/orcamentos`
- Botão submit desabilitado + spinner durante loading

### OrcamentoDetailPage (`/orcamentos/:id`)

- Exibe: Título, Descrição, Status (`StatusBadge`), Custo Fixo Total, datas created_at/updated_at
- Botões: "Editar" → `/orcamentos/:id/editar`, "Excluir" → `ConfirmDialog`
- Delete: `useDeleteOrcamento` → toast "Orçamento excluído" → navega para `/orcamentos`
- Seção "Fichas": placeholder "Em breve — Fase 6"
- Loading: spinner durante fetch inicial

### OrcamentoEditPage (`/orcamentos/:id/editar`)

- `OrcamentoForm` pré-preenchido com dados de `useOrcamento(id)`
- Submit → `useUpdateOrcamento` → toast "Alterações salvas!" → navega para `/orcamentos/:id`
- Botão "Cancelar" → volta para `/orcamentos/:id`
- Loading inicial enquanto carrega dados do orçamento

### LoginPage (melhoria)

- Centralizada verticalmente e horizontalmente
- Estilo consistente com AppLayout (mesmas CSS vars)
- MFA: condicional — exibe `MFAForm` apenas quando `mfa_required: true` na resposta

---

## 5. UX Transversal

- **Loading nos botões:** todos os botões de submit ficam `disabled` + mostram spinner durante mutations
- **Erros da API:** toast vermelho com `error.response?.data?.detail` ou mensagem genérica
- **Navegação:** sidebar destaca a rota ativa com estilo visual
- **Mobile:** sidebar fica oculta em telas < 768px (`display: none`) — sem hamburger nesta fase (fora do escopo de "mobile básico")

---

## 6. Estrutura de Arquivos Final

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx      (existente, sem mudança)
│   │   ├── MFAForm.tsx        (existente, sem mudança)
│   │   └── LogoutButton.tsx   (existente, sem mudança)
│   └── ui/
│       ├── Button.tsx         (existente)
│       ├── Input.tsx          (existente)
│       ├── Card.tsx           (existente)
│       ├── AppLayout.tsx      (NOVO)
│       ├── Sidebar.tsx        (NOVO)
│       ├── ProtectedRoute.tsx (NOVO)
│       ├── StatusBadge.tsx    (NOVO)
│       ├── ConfirmDialog.tsx  (NOVO)
│       └── OrcamentoForm.tsx  (NOVO)
├── hooks/
│   ├── useAuth.ts             (existente, pequena melhoria MFA)
│   └── useApi.ts              (existente + novos hooks)
├── pages/
│   ├── LoginPage.tsx          (existente, melhorado)
│   ├── DashboardPage.tsx      (DELETADO — substituído por OrcamentosListPage)
│   ├── OrcamentosListPage.tsx (NOVO)
│   ├── OrcamentoCreatePage.tsx (NOVO)
│   ├── OrcamentoDetailPage.tsx (NOVO)
│   └── OrcamentoEditPage.tsx  (NOVO)
├── services/
│   └── api.ts                 (existente, sem mudança)
├── types/
│   └── index.ts               (existente, sem mudança)
├── App.tsx                    (atualizado: rotas + Toaster)
└── index.css                  (atualizado: estilos sidebar, tabela, badge, dialog)
```

---

## 7. Dependência Nova

```bash
npm install react-hot-toast
```

Única dependência nova. Tudo mais já está instalado.

---

## Critérios de Aceitação

- [ ] Criar orçamento funciona (form + API + redirect)
- [ ] Listar orçamentos funciona (tabela + estados loading/vazio/erro)
- [ ] Visualizar orçamento funciona (detalhe + status badge)
- [ ] Editar orçamento funciona (form pré-preenchido + save)
- [ ] Excluir orçamento funciona (confirm dialog + redirect)
- [ ] Feedback visual em todas as ações (toast sucesso/erro)
- [ ] Tratamento de erros da API (toast com mensagem)
- [ ] Navegação via sidebar funcional
- [ ] Rotas protegidas (redirect para /login sem token)

---

## Fora de Escopo

- CRUD de fichas (Fase 6)
- Calcular / Spreading (Fase 6)
- Paginação e filtros na listagem
- Testes E2E do frontend
- Offline/PWA (CA-007)
- Design final polido (funcionalidade primeiro)
