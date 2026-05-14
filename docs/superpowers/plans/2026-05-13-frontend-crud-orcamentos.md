# Frontend CRUD Orçamentos — Fase 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar CRUD completo de orçamentos no frontend React com sidebar, formulários validados, feedback visual e integração total com a API FastAPI.

**Architecture:** Estrutura flat ampliada — novas páginas em `src/pages/`, novos hooks em `src/hooks/useApi.ts`, novos componentes em `src/components/ui/`. Sidebar fixa envolve todas as rotas autenticadas via `AppLayout`. React Query gerencia cache e invalidações. `react-hot-toast` para feedback.

**Tech Stack:** React 18, React Router 6, React Query 5, Zod, react-hook-form, Axios (já configurado), CSS customizado, react-hot-toast (nova dep).

**Working directory:** `G:\Meu Drive\orcOS\frontend`

---

## File Map

| Ação | Arquivo | Responsabilidade |
|---|---|---|
| Install | `package.json` | Adicionar react-hot-toast |
| Modify | `src/index.css` | Estilos de sidebar, tabela, badge, dialog, textarea |
| Create | `src/components/ui/ProtectedRoute.tsx` | Guard de rota — redireciona sem token |
| Create | `src/components/ui/AppLayout.tsx` | Sidebar + `<Outlet />` wrapper |
| Create | `src/components/ui/Sidebar.tsx` | Links de navegação + logout |
| Modify | `src/App.tsx` | Novas rotas, AppLayout, Toaster |
| Create | `src/components/ui/StatusBadge.tsx` | Badge colorido por status |
| Create | `src/components/ui/ConfirmDialog.tsx` | Modal de confirmação para delete |
| Create | `src/components/ui/OrcamentoForm.tsx` | Form Zod+RHF compartilhado |
| Modify | `src/hooks/useApi.ts` | useOrcamento, useCreate/Update/DeleteOrcamento |
| Create | `src/pages/OrcamentosListPage.tsx` | Listagem com tabela e ações |
| Create | `src/pages/OrcamentoCreatePage.tsx` | Form de criação |
| Create | `src/pages/OrcamentoDetailPage.tsx` | Visualização detalhada |
| Create | `src/pages/OrcamentoEditPage.tsx` | Form de edição pré-preenchido |
| Modify | `src/pages/LoginPage.tsx` | Melhorar estilo + MFA condicional |
| Delete | `src/pages/DashboardPage.tsx` | Substituído por OrcamentosListPage |
| Delete | `src/pages/OrcamentoPage.tsx` | Substituído por OrcamentoDetailPage |

---

## Task 1: Instalar react-hot-toast + Estilos CSS

**Files:**
- Modify: `package.json` (via npm install)
- Modify: `src/index.css`

- [ ] **Step 1: Instalar dependência**

```bash
cd "G:\Meu Drive\orcOS\frontend"
npm install react-hot-toast
```

Esperado: `added 1 package` sem erros.

- [ ] **Step 2: Adicionar estilos ao final de `src/index.css`**

Append ao final do arquivo (não substituir o conteúdo existente):

```css
/* ── App Layout ────────────────────────────────────────────── */
.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  background: var(--background);
  min-width: 0;
}

/* ── Sidebar ─────────────────────────────────────────────────── */
.sidebar {
  width: 240px;
  background: #1e293b;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-logo {
  padding: 1.25rem 1rem;
  color: #6366f1;
  font-weight: 700;
  font-size: 1.125rem;
  border-bottom: 1px solid #334155;
}

.sidebar-nav {
  flex: 1;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.sidebar-link:hover {
  background: #334155;
  color: #f8fafc;
}

.sidebar-link.active {
  background: #6366f1;
  color: #ffffff;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #334155;
}

.sidebar-footer button {
  width: 100%;
  background: transparent;
  border: 1px solid #334155;
  color: #94a3b8;
  padding: 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.15s;
}

.sidebar-footer button:hover {
  background: #334155;
  color: #f8fafc;
}

@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-content { padding: 1rem; }
}

/* ── Page Header ─────────────────────────────────────────────── */
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--foreground);
}

/* ── Table ───────────────────────────────────────────────────── */
.table-container {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--background);
}

th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

td {
  padding: 0.875rem 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.875rem;
  vertical-align: middle;
}

tr:hover td {
  background: var(--background);
}

.table-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  color: var(--muted);
  font-size: 0.75rem;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
}

.action-btn:hover { background: var(--border); color: var(--foreground); }
.action-btn.danger:hover { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }

/* ── Status Badge ────────────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.badge-gray   { background: #f1f5f9; color: #64748b; }
.badge-green  { background: #dcfce7; color: #16a34a; }
.badge-red    { background: #fee2e2; color: #dc2626; }
.badge-blue   { background: #dbeafe; color: #2563eb; }
.badge-yellow { background: #fef9c3; color: #ca8a04; }

/* ── Confirm Dialog ──────────────────────────────────────────── */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.dialog {
  background: var(--card);
  border-radius: var(--radius);
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-lg);
}

.dialog-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--foreground);
  margin-bottom: 0.5rem;
}

.dialog-message {
  color: var(--muted);
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.dialog-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* ── Form ────────────────────────────────────────────────────── */
.textarea-field {
  padding: 0.625rem 0.875rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--foreground);
  font-size: 0.875rem;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.textarea-field:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--ring);
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* ── Detail Page ─────────────────────────────────────────────── */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.detail-field p {
  font-size: 0.875rem;
  color: var(--foreground);
}

.detail-section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--foreground);
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

/* ── Loading Spinner ─────────────────────────────────────────── */
.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem;
}
```

- [ ] **Step 3: Verificar CSS compilado**

Iniciar dev server e confirmar que não há erros de syntax no console:

```bash
npm run dev
```

Abrir http://localhost:5173. O browser não deve mostrar erros.

- [ ] **Step 4: Commit**

```bash
git add package.json package-lock.json src/index.css
git commit -m "feat: instala react-hot-toast e adiciona estilos de layout/sidebar/tabela/badge/dialog"
```

---

## Task 2: ProtectedRoute

**Files:**
- Create: `src/components/ui/ProtectedRoute.tsx`

- [ ] **Step 1: Criar o componente**

```tsx
// src/components/ui/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -20
```

Esperado: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/ProtectedRoute.tsx
git commit -m "feat: ProtectedRoute redireciona para /login sem token"
```

---

## Task 3: AppLayout + Sidebar

**Files:**
- Create: `src/components/ui/Sidebar.tsx`
- Create: `src/components/ui/AppLayout.tsx`

- [ ] **Step 1: Criar Sidebar**

```tsx
// src/components/ui/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function Sidebar() {
  const { logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">orcOS</div>
      <nav className="sidebar-nav">
        <NavLink
          to="/orcamentos"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          📋 Orçamentos
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <button onClick={logout}>Sair</button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Criar AppLayout**

```tsx
// src/components/ui/AppLayout.tsx
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Verificar compilação**

```bash
npm run build 2>&1 | head -20
```

Esperado: sem erros.

- [ ] **Step 4: Commit**

```bash
git add src/components/ui/Sidebar.tsx src/components/ui/AppLayout.tsx
git commit -m "feat: AppLayout com sidebar fixa e Outlet para conteúdo"
```

---

## Task 4: Atualizar App.tsx

**Files:**
- Modify: `src/App.tsx`
- Delete: `src/pages/DashboardPage.tsx`
- Delete: `src/pages/OrcamentoPage.tsx`

- [ ] **Step 1: Sobrescrever App.tsx**

```tsx
// src/App.tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from './components/ui/AppLayout';
import { ProtectedRoute } from './components/ui/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { OrcamentosListPage } from './pages/OrcamentosListPage';
import { OrcamentoCreatePage } from './pages/OrcamentoCreatePage';
import { OrcamentoDetailPage } from './pages/OrcamentoDetailPage';
import { OrcamentoEditPage } from './pages/OrcamentoEditPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/orcamentos" replace />} />
            <Route path="/orcamentos" element={<OrcamentosListPage />} />
            <Route path="/orcamentos/novo" element={<OrcamentoCreatePage />} />
            <Route path="/orcamentos/:id" element={<OrcamentoDetailPage />} />
            <Route path="/orcamentos/:id/editar" element={<OrcamentoEditPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

**Nota:** As páginas ainda não existem — o TypeScript vai reclamar até a Task 9. Avance assim mesmo; o `npm run build` será validado após todas as páginas existirem.

- [ ] **Step 2: Deletar arquivos substituídos**

```bash
rm "src/pages/DashboardPage.tsx"
rm "src/pages/OrcamentoPage.tsx"
```

- [ ] **Step 3: Commit**

```bash
git add src/App.tsx
git rm src/pages/DashboardPage.tsx src/pages/OrcamentoPage.tsx
git commit -m "feat: atualiza App.tsx com novas rotas, ProtectedRoute e Toaster"
```

---

## Task 5: StatusBadge

**Files:**
- Create: `src/components/ui/StatusBadge.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// src/components/ui/StatusBadge.tsx
interface StatusBadgeProps {
  status: string;
}

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  rascunho: { label: 'Rascunho', className: 'badge-gray' },
  ativo:    { label: 'Ativo',    className: 'badge-green' },
  cancelado:{ label: 'Cancelado',className: 'badge-red' },
  pendente: { label: 'Pendente', className: 'badge-yellow' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const entry = STATUS_MAP[status] ?? { label: status, className: 'badge-blue' };
  return <span className={`badge ${entry.className}`}>{entry.label}</span>;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/StatusBadge.tsx
git commit -m "feat: StatusBadge com cores por status do orçamento"
```

---

## Task 6: ConfirmDialog

**Files:**
- Create: `src/components/ui/ConfirmDialog.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// src/components/ui/ConfirmDialog.tsx
import { Button } from './Button';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirmar',
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3 className="dialog-title">{title}</h3>
        <p className="dialog-message">{message}</p>
        <div className="dialog-actions">
          <Button variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancelar
          </Button>
          <Button onClick={onConfirm} disabled={isLoading}>
            {isLoading ? <span className="spinner" /> : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/ConfirmDialog.tsx
git commit -m "feat: ConfirmDialog modal para confirmação de exclusão"
```

---

## Task 7: OrcamentoForm

**Files:**
- Create: `src/components/ui/OrcamentoForm.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// src/components/ui/OrcamentoForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './Button';
import { Input } from './Input';

const orcamentoSchema = z.object({
  titulo: z.string().min(3, 'Mínimo 3 caracteres').max(100, 'Máximo 100 caracteres'),
  descricao: z.string().max(500, 'Máximo 500 caracteres').optional(),
  custo_fixo_total: z
    .string()
    .regex(/^\d+(\.\d{2})?$/, 'Formato inválido. Use: 100.00'),
});

export type OrcamentoFormData = z.infer<typeof orcamentoSchema>;

interface OrcamentoFormProps {
  defaultValues?: Partial<OrcamentoFormData>;
  onSubmit: (data: OrcamentoFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  submitLabel?: string;
}

export function OrcamentoForm({
  defaultValues,
  onSubmit,
  onCancel,
  isLoading = false,
  submitLabel = 'Salvar',
}: OrcamentoFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrcamentoFormData>({
    resolver: zodResolver(orcamentoSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input
        label="Título *"
        placeholder="Ex: Sinalização Rodovia BR-101 Trecho KM 23-45"
        error={errors.titulo?.message}
        {...register('titulo')}
      />

      <div className="input-group">
        <label className="input-label">Descrição</label>
        <textarea
          className={`textarea-field w-full${errors.descricao ? ' input-error' : ''}`}
          placeholder="Descrição opcional do orçamento..."
          {...register('descricao')}
        />
        {errors.descricao && (
          <span className="error-message">{errors.descricao.message}</span>
        )}
      </div>

      <Input
        label="Custo Fixo Total *"
        placeholder="Ex: 1500.00"
        error={errors.custo_fixo_total?.message}
        {...register('custo_fixo_total')}
      />

      <div className="form-actions">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? <span className="spinner" /> : submitLabel}
        </Button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/OrcamentoForm.tsx
git commit -m "feat: OrcamentoForm com validação Zod+RHF para criar/editar"
```

---

## Task 8: Expandir useApi.ts com hooks CRUD

**Files:**
- Modify: `src/hooks/useApi.ts`

- [ ] **Step 1: Substituir conteúdo de useApi.ts**

```typescript
// src/hooks/useApi.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { api } from '../services/api';
import { Orcamento } from '../types';

// ── Helpers ──────────────────────────────────────────────────────
function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  }
  return 'Erro inesperado. Tente novamente.';
}

// ── Queries ──────────────────────────────────────────────────────
export function useOrcamentos() {
  return useQuery({
    queryKey: ['orcamentos'],
    queryFn: async () => {
      const response = await api.get<{ items: Orcamento[]; total: number }>('/orcamentos');
      return response.data;
    },
  });
}

export function useOrcamento(id: string) {
  return useQuery({
    queryKey: ['orcamento', id],
    queryFn: async () => {
      const response = await api.get<Orcamento>(`/orcamentos/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// ── Mutations ─────────────────────────────────────────────────────
interface OrcamentoPayload {
  titulo: string;
  descricao?: string;
  custo_fixo_total: string;
}

export function useCreateOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: OrcamentoPayload) => {
      const response = await api.post<Orcamento>('/orcamentos', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useUpdateOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<OrcamentoPayload> }) => {
      const response = await api.patch<Orcamento>(`/orcamentos/${id}`, payload);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] });
      queryClient.invalidateQueries({ queryKey: ['orcamento', id] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useDeleteOrcamento() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/orcamentos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orcamentos'] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}
```

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -30
```

Esperado: erros apenas de imports das páginas ainda não criadas (`OrcamentosListPage`, etc.) — OK por enquanto.

- [ ] **Step 3: Commit**

```bash
git add src/hooks/useApi.ts
git commit -m "feat: hooks CRUD completos — useOrcamento, useCreate/Update/DeleteOrcamento"
```

---

## Task 9: OrcamentosListPage

**Files:**
- Create: `src/pages/OrcamentosListPage.tsx`

- [ ] **Step 1: Criar página**

```tsx
// src/pages/OrcamentosListPage.tsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useDeleteOrcamento, useOrcamentos } from '../hooks/useApi';

function formatCurrency(value: string) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(
    Number(value),
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR');
}

export function OrcamentosListPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useOrcamentos();
  const deleteMutation = useDeleteOrcamento();

  const [deleteTarget, setDeleteTarget] = useState<{ id: string; titulo: string } | null>(null);

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id, {
      onSuccess: () => {
        toast.success('Orçamento excluído.');
        setDeleteTarget(null);
      },
    });
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Orçamentos</h1>
        <Button onClick={() => navigate('/orcamentos/novo')}>+ Novo Orçamento</Button>
      </div>

      {isLoading && (
        <div className="loading-center">
          <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
        </div>
      )}

      {error && (
        <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
          Erro ao carregar orçamentos. Tente novamente.
        </p>
      )}

      {data && data.items.length === 0 && (
        <div className="empty-state">
          <p style={{ marginBottom: '1rem' }}>Nenhum orçamento encontrado.</p>
          <Button onClick={() => navigate('/orcamentos/novo')}>Criar primeiro orçamento</Button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Título</th>
                <th>Status</th>
                <th>Custo Fixo</th>
                <th>Criado em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((orc) => (
                <tr key={orc.id}>
                  <td style={{ fontWeight: 500 }}>{orc.titulo}</td>
                  <td><StatusBadge status={orc.status} /></td>
                  <td>{formatCurrency(orc.custo_fixo_total)}</td>
                  <td className="muted">{formatDate(orc.created_at)}</td>
                  <td>
                    <div className="table-actions">
                      <Link className="action-btn" to={`/orcamentos/${orc.id}`}>
                        Ver
                      </Link>
                      <Link className="action-btn" to={`/orcamentos/${orc.id}/editar`}>
                        Editar
                      </Link>
                      <button
                        className="action-btn danger"
                        onClick={() => setDeleteTarget({ id: orc.id, titulo: orc.titulo })}
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Excluir orçamento?"
        message={`"${deleteTarget?.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/pages/OrcamentosListPage.tsx
git commit -m "feat: OrcamentosListPage com tabela, ações e ConfirmDialog"
```

---

## Task 10: OrcamentoCreatePage

**Files:**
- Create: `src/pages/OrcamentoCreatePage.tsx`

- [ ] **Step 1: Criar página**

```tsx
// src/pages/OrcamentoCreatePage.tsx
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card } from '../components/ui/Card';
import { OrcamentoForm, OrcamentoFormData } from '../components/ui/OrcamentoForm';
import { useCreateOrcamento } from '../hooks/useApi';

export function OrcamentoCreatePage() {
  const navigate = useNavigate();
  const createMutation = useCreateOrcamento();

  async function handleSubmit(data: OrcamentoFormData) {
    const created = await createMutation.mutateAsync(data);
    toast.success('Orçamento criado!');
    navigate(`/orcamentos/${created.id}`);
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Novo Orçamento</h1>
      </div>
      <Card style={{ maxWidth: 640 }}>
        <OrcamentoForm
          onSubmit={handleSubmit}
          onCancel={() => navigate('/orcamentos')}
          isLoading={createMutation.isPending}
          submitLabel="Criar Orçamento"
        />
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Verificar se `Card` aceita `style` prop**

Abrir `src/components/ui/Card.tsx`. Se a interface `CardProps` não tiver `style`, adicionar:

```tsx
// Adicionar ao interface CardProps:
style?: React.CSSProperties;

// Adicionar ao elemento <div className={...}>:
<div className={`card ${className || ''}`} style={style}>
```

- [ ] **Step 3: Commit**

```bash
git add src/pages/OrcamentoCreatePage.tsx src/components/ui/Card.tsx
git commit -m "feat: OrcamentoCreatePage com form e redirect para detalhe"
```

---

## Task 11: OrcamentoDetailPage

**Files:**
- Create: `src/pages/OrcamentoDetailPage.tsx`

- [ ] **Step 1: Criar página**

```tsx
// src/pages/OrcamentoDetailPage.tsx
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useDeleteOrcamento, useOrcamento } from '../hooks/useApi';

function formatCurrency(value: string) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(
    Number(value),
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('pt-BR');
}

export function OrcamentoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useOrcamento(id!);
  const deleteMutation = useDeleteOrcamento();
  const [showDelete, setShowDelete] = useState(false);

  async function handleDelete() {
    await deleteMutation.mutateAsync(id!, {
      onSuccess: () => {
        toast.success('Orçamento excluído.');
        navigate('/orcamentos');
      },
    });
  }

  if (isLoading) {
    return (
      <div className="loading-center">
        <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="empty-state">
        <p>Orçamento não encontrado.</p>
        <Link to="/orcamentos" style={{ marginTop: '1rem' }}>
          ← Voltar para lista
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/orcamentos" className="muted" style={{ fontSize: '0.875rem' }}>
            ← Orçamentos
          </Link>
          <h1 className="page-title" style={{ marginTop: '0.25rem' }}>
            {data.titulo}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button variant="outline" onClick={() => navigate(`/orcamentos/${id}/editar`)}>
            Editar
          </Button>
          <Button variant="outline" onClick={() => setShowDelete(true)}>
            Excluir
          </Button>
        </div>
      </div>

      <Card style={{ marginBottom: '1.5rem' }}>
        <div className="detail-grid">
          <div className="detail-field">
            <label>Status</label>
            <StatusBadge status={data.status} />
          </div>
          <div className="detail-field">
            <label>Custo Fixo Total</label>
            <p>{formatCurrency(data.custo_fixo_total)}</p>
          </div>
          <div className="detail-field">
            <label>Criado em</label>
            <p className="muted">{formatDate(data.created_at)}</p>
          </div>
          <div className="detail-field">
            <label>Atualizado em</label>
            <p className="muted">{formatDate(data.updated_at)}</p>
          </div>
          {data.descricao && (
            <div className="detail-field" style={{ gridColumn: '1 / -1' }}>
              <label>Descrição</label>
              <p>{data.descricao}</p>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <p className="detail-section-title">Fichas</p>
        <p className="muted" style={{ fontSize: '0.875rem' }}>
          Gerenciamento de fichas disponível na Fase 6.
        </p>
      </Card>

      <ConfirmDialog
        open={showDelete}
        title="Excluir orçamento?"
        message={`"${data.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/pages/OrcamentoDetailPage.tsx
git commit -m "feat: OrcamentoDetailPage com dados completos, badge e delete"
```

---

## Task 12: OrcamentoEditPage

**Files:**
- Create: `src/pages/OrcamentoEditPage.tsx`

- [ ] **Step 1: Criar página**

```tsx
// src/pages/OrcamentoEditPage.tsx
import { useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card } from '../components/ui/Card';
import { OrcamentoForm, OrcamentoFormData } from '../components/ui/OrcamentoForm';
import { useOrcamento, useUpdateOrcamento } from '../hooks/useApi';

export function OrcamentoEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useOrcamento(id!);
  const updateMutation = useUpdateOrcamento();

  async function handleSubmit(formData: OrcamentoFormData) {
    await updateMutation.mutateAsync({ id: id!, payload: formData });
    toast.success('Alterações salvas!');
    navigate(`/orcamentos/${id}`);
  }

  if (isLoading) {
    return (
      <div className="loading-center">
        <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
      </div>
    );
  }

  if (!data) {
    return <p className="muted">Orçamento não encontrado.</p>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Editar Orçamento</h1>
      </div>
      <Card style={{ maxWidth: 640 }}>
        <OrcamentoForm
          defaultValues={{
            titulo: data.titulo,
            descricao: data.descricao ?? undefined,
            custo_fixo_total: data.custo_fixo_total,
          }}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/orcamentos/${id}`)}
          isLoading={updateMutation.isPending}
          submitLabel="Salvar Alterações"
        />
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/pages/OrcamentoEditPage.tsx
git commit -m "feat: OrcamentoEditPage com form pré-preenchido e PATCH"
```

---

## Task 13: Melhorar LoginPage

**Files:**
- Modify: `src/pages/LoginPage.tsx`
- Modify: `src/hooks/useAuth.ts`

- [ ] **Step 1: Atualizar LoginPage com MFA condicional**

```tsx
// src/pages/LoginPage.tsx
import { useState } from 'react';
import { Card } from '../components/ui/Card';
import { LoginForm } from '../components/auth/LoginForm';
import { MFAForm } from '../components/auth/MFAForm';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [mfaRequired, setMfaRequired] = useState(false);
  const [partialToken, setPartialToken] = useState('');
  const { verifyMfa } = useAuth();

  function handleMfaRequired(token: string) {
    setPartialToken(token);
    setMfaRequired(true);
  }

  async function handleMfaVerify(code: string) {
    await verifyMfa({ partial_token: partialToken, totp_code: code });
  }

  return (
    <div className="login-page">
      <div className="auth-card">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--foreground)' }}>orcOS</h1>
          <p className="muted" style={{ marginTop: '0.5rem' }}>
            {mfaRequired ? 'Verificação em duas etapas' : 'Sistema de Orçamentos'}
          </p>
        </div>
        <Card>
          {mfaRequired ? (
            <MFAForm onVerify={handleMfaVerify} />
          ) : (
            <LoginForm onMfaRequired={handleMfaRequired} />
          )}
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Atualizar useAuth.ts — adicionar verifyMfa + callback onMfaRequired**

```typescript
// src/hooks/useAuth.ts
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const login = useCallback(
    async (
      data: { email: string; senha: string; tenant_id?: string },
      onMfaRequired?: (partialToken: string) => void,
    ) => {
      setIsLoading(true);
      try {
        const tenant_id = data.tenant_id || '00000000-0000-0000-0000-000000000000';
        const response = await api.post('/auth/login', {
          email: data.email,
          password: data.senha,
          tenant_id,
        });

        if (response.data.mfa_required) {
          onMfaRequired?.(response.data.partial_token ?? '');
          return response.data;
        }

        if (response.data.access_token) {
          localStorage.setItem('token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token ?? '');
          localStorage.setItem('tenant_id', tenant_id);
          navigate('/orcamentos');
        }
        return response.data;
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );

  const verifyMfa = useCallback(
    async (data: { partial_token: string; totp_code: string }) => {
      setIsLoading(true);
      try {
        const response = await api.post('/auth/mfa/verify', data);
        if (response.data.access_token) {
          localStorage.setItem('token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token ?? '');
          navigate('/orcamentos');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('tenant_id');
    navigate('/login');
  }, [navigate]);

  return {
    login,
    verifyMfa,
    logout,
    isLoading,
    isAuthenticated: !!localStorage.getItem('token'),
  };
}
```

- [ ] **Step 3: Atualizar LoginForm para aceitar callback onMfaRequired**

```tsx
// src/components/auth/LoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  senha: z.string().min(6, 'Mínimo 6 caracteres'),
});

type LoginData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onMfaRequired?: (partialToken: string) => void;
}

export function LoginForm({ onMfaRequired }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginData) => {
    try {
      await login(data, onMfaRequired);
    } catch {
      setError('root', { message: 'Email ou senha incorretos.' });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input
        label="Email"
        type="email"
        placeholder="seu@email.com"
        error={errors.email?.message}
        disabled={isLoading}
        {...register('email')}
      />
      <Input
        label="Senha"
        type="password"
        placeholder="••••••••"
        error={errors.senha?.message}
        disabled={isLoading}
        {...register('senha')}
      />
      {errors.root && (
        <p className="error-message" style={{ marginBottom: '0.75rem' }}>
          {errors.root.message}
        </p>
      )}
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? <span className="spinner" /> : 'Entrar'}
      </Button>
    </form>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add src/pages/LoginPage.tsx src/hooks/useAuth.ts src/components/auth/LoginForm.tsx
git commit -m "feat: LoginPage com MFA condicional e estilo consistente"
```

---

## Task 14: Build final + Teste Manual + Push

**Files:** nenhum novo

- [ ] **Step 1: Build sem erros**

```bash
cd "G:\Meu Drive\orcOS\frontend"
npm run build
```

Esperado: `✓ built in X.XXs` sem erros. Se houver erros TypeScript, corrigir antes de prosseguir.

- [ ] **Step 2: Iniciar backend**

```bash
cd "G:\Meu Drive\orcOS\backend"
uvicorn app.main:app --reload
```

- [ ] **Step 3: Iniciar frontend**

```bash
cd "G:\Meu Drive\orcOS\frontend"
npm run dev
```

Abrir http://localhost:5173.

- [ ] **Step 4: Testar fluxo completo**

Executar em ordem:

1. Acessar `/` → deve redirecionar para `/login` (sem token)
2. Fazer login com credenciais válidas → deve navegar para `/orcamentos`
3. Sidebar deve estar visível com link "Orçamentos" ativo
4. Clicar "Novo Orçamento" → formulário abre
5. Preencher título "Teste CRUD", custo "500.00" → clicar "Criar Orçamento"
6. Toast verde "Orçamento criado!" → redireciona para detalhe
7. Página de detalhe exibe título, status badge, custo formatado
8. Clicar "Editar" → form pré-preenchido com dados existentes
9. Alterar título → "Salvar Alterações" → toast "Alterações salvas!" → volta ao detalhe
10. Clicar "Excluir" → ConfirmDialog aparece → confirmar → toast "Excluído" → lista
11. Orçamento não aparece mais na lista

- [ ] **Step 5: Verificar erros da API**

Desligar o backend e tentar criar um orçamento. Toast de erro deve aparecer com mensagem legível.

- [ ] **Step 6: Push**

```bash
cd "G:\Meu Drive\orcOS"
git push origin claude/project-analysis-improvements-rqi2e
```

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
- [ ] `npm run build` sem erros TypeScript
