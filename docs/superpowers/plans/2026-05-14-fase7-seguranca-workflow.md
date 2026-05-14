# Fase 7 — Token Refresh, MFA Setup, Status Inline, Auditoria

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar quatro features frontend-only que completam o ciclo de vida do sistema: renovação automática de tokens, ativação de MFA pelo usuário, alteração inline de status de orçamento e painel de auditoria de integridade.

**Architecture:** Interceptor Axios 401 transparente em `api.ts` cobre toda a app sem duplicação; MFA setup usa wizard de 3 etapas com estado local em `ConfiguracoesPage`; status de orçamento vira `<select>` com auto-PATCH reutilizando `useUpdateOrcamento`; `AuditoriaPage` consome dois endpoints existentes do backend.

**Tech Stack:** React 18, TypeScript, React Query v5, Axios, react-hook-form, qrcode.react, react-hot-toast, CSS customizado (variáveis CSS).

**Spec:** `docs/superpowers/specs/2026-05-14-fase7-seguranca-workflow-design.md`

---

## Mapa de arquivos

| Ação | Arquivo | O que muda |
|------|---------|-----------|
| Modify | `frontend/src/services/api.ts` | Response interceptor 401: refresh → retry → logout |
| Modify | `frontend/src/types/index.ts` | +4 tipos: MfaSetupResponse, MfaVerifyRequest, AuditStatusValue, AuditStatusResponse |
| Modify | `frontend/src/hooks/useApi.ts` | +4 hooks: useMfaSetup, useMfaVerify, useAuditStatus, useAuditVerify |
| Create | `frontend/src/pages/ConfiguracoesPage.tsx` | Wizard MFA (idle → scan → verify → active) |
| Modify | `frontend/src/pages/OrcamentoDetailPage.tsx` | Campo status: StatusBadge → select inline com auto-PATCH |
| Create | `frontend/src/pages/AuditoriaPage.tsx` | Painel badge + botão "Verificar agora" |
| Modify | `frontend/src/App.tsx` | Rotas /configuracoes e /admin/auditoria |
| Modify | `frontend/src/components/ui/Sidebar.tsx` | Links Configurações e Auditoria |
| Modify | `frontend/src/index.css` | .status-select + classes audit-badge |

---

## Task 1: Instalar qrcode.react

**Files:**
- Modify: `frontend/package.json` (via npm install)

> qrcode.react v4+ inclui tipos TypeScript nativos — não precisa de @types separado.

- [ ] **Step 1: Instalar dependência**

```bash
cd frontend
npm install qrcode.react
```

Expected output: `added N packages` sem erros.

- [ ] **Step 2: Verificar que o build passa**

```bash
npm run build
```

Expected: `✓ built in Xs` sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
cd frontend
git add package.json package-lock.json
git commit -m "chore: add qrcode.react dependency"
```

---

## Task 2: Token Refresh Interceptor

**Files:**
- Modify: `frontend/src/services/api.ts`

> CRÍTICO: O app usa a chave `'token'` no localStorage (não `'access_token'`).
> Ver `api.ts` request interceptor: `localStorage.getItem('token')`.
> Ver `useAuth.ts`: `localStorage.setItem('token', response.data.access_token)`.
> O interceptor 401 deve usar a mesma chave `'token'` para consistência.

- [ ] **Step 1: Substituir o conteúdo de `frontend/src/services/api.ts`**

```typescript
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Adiciona token e tenant_id em toda request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  const tenantId = localStorage.getItem('tenant_id');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  } else {
    config.headers['X-Tenant-ID'] = '00000000-0000-0000-0000-000000000000';
  }

  return config;
});

// Refresh automático em 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthEndpoint =
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/mfa');

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          { refresh_token: refreshToken },
        );
        localStorage.setItem('token', data.access_token);
        originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);
```

- [ ] **Step 2: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add 401 response interceptor with token refresh"
```

---

## Task 3: Novos tipos

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Adicionar os 4 novos tipos ao final de `frontend/src/types/index.ts`**

Adicionar APÓS a interface `MfaLoginRequest` (linha 87):

```typescript
export interface MfaSetupResponse {
  secret: string;
  provisioning_uri: string;
}

export interface MfaVerifyRequest {
  secret: string;
  totp_code: string;
}

export type AuditStatusValue = 'OK' | 'CORRUPTED' | 'PENDING' | 'EMPTY';

export interface AuditStatusResponse {
  status: AuditStatusValue;
  checked_at?: string;
  total_entries?: number;
  corrupted_entry?: string | null;
}
```

- [ ] **Step 2: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add MFA setup and audit types"
```

---

## Task 4: Novos hooks

**Files:**
- Modify: `frontend/src/hooks/useApi.ts`

- [ ] **Step 1: Atualizar import de tipos no topo de `frontend/src/hooks/useApi.ts`**

Linha atual:
```typescript
import type { Ficha, FichaCalcResult, Orcamento, SpreadingResponse } from '../types';
```

Substituir por:
```typescript
import type {
  AuditStatusResponse,
  Ficha,
  FichaCalcResult,
  MfaSetupResponse,
  MfaVerifyRequest,
  Orcamento,
  SpreadingResponse,
} from '../types';
```

- [ ] **Step 2: Adicionar os 4 novos hooks ao final de `frontend/src/hooks/useApi.ts`**

Adicionar após `export function useSpreading() { ... }`:

```typescript
// ── MFA Setup ─────────────────────────────────────────────────────
export function useMfaSetup() {
  return useMutation({
    mutationFn: async () => {
      const response = await api.post<MfaSetupResponse>('/auth/mfa/setup');
      return response.data;
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

// ── MFA Verify (setup flow) ────────────────────────────────────────
export function useMfaVerify() {
  return useMutation({
    mutationFn: async (payload: MfaVerifyRequest) => {
      const response = await api.post('/auth/mfa/verify', payload);
      return response.data;
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

// ── Audit Status ───────────────────────────────────────────────────
export function useAuditStatus() {
  return useQuery({
    queryKey: ['audit-status'],
    queryFn: async () => {
      const response = await api.get<AuditStatusResponse>('/admin/audit/status');
      return response.data;
    },
  });
}

// ── Audit Verify ───────────────────────────────────────────────────
export function useAuditVerify() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const response = await api.get<AuditStatusResponse>('/admin/audit/verify');
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['audit-status'], data);
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}
```

- [ ] **Step 3: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useApi.ts
git commit -m "feat: add MFA setup/verify and audit hooks"
```

---

## Task 5: ConfiguracoesPage — Wizard MFA

**Files:**
- Create: `frontend/src/pages/ConfiguracoesPage.tsx`

> `qrcode.react` exporta `QRCodeSVG` como named export.
> `useMfaSetup` retorna `MfaSetupResponse | undefined` — proteger com `if (!mfaData)`.
> Wizard steps: 'idle' → 'scan' → 'verify' → 'active'.

- [ ] **Step 1: Criar `frontend/src/pages/ConfiguracoesPage.tsx`**

```tsx
import { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import toast from 'react-hot-toast';
import { useMfaSetup, useMfaVerify } from '../hooks/useApi';
import type { MfaSetupResponse } from '../types';

type MfaStep = 'idle' | 'scan' | 'verify' | 'active';

export function ConfiguracoesPage() {
  const [mfaStep, setMfaStep] = useState<MfaStep>('idle');
  const [mfaData, setMfaData] = useState<MfaSetupResponse | null>(null);
  const [verifyCode, setVerifyCode] = useState('');

  const mfaSetup = useMfaSetup();
  const mfaVerify = useMfaVerify();

  async function handleStartSetup() {
    try {
      const data = await mfaSetup.mutateAsync();
      setMfaData(data);
      setMfaStep('scan');
    } catch {
      // error toast shown by mutation
    }
  }

  async function handleVerify() {
    if (!mfaData) return;
    try {
      await mfaVerify.mutateAsync({ secret: mfaData.secret, totp_code: verifyCode });
      toast.success('MFA ativado com sucesso!');
      setMfaStep('active');
      setVerifyCode('');
    } catch {
      setVerifyCode('');
    }
  }

  function handleCopySecret() {
    if (!mfaData) return;
    navigator.clipboard.writeText(mfaData.secret).then(() => {
      toast.success('Chave copiada!');
    });
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Configurações</h1>
      </div>

      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
          maxWidth: '560px',
        }}
      >
        <h2 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: 600 }}>
          Autenticação de Dois Fatores (MFA)
        </h2>

        {/* idle */}
        {mfaStep === 'idle' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span
              style={{
                background: '#f1f5f9',
                color: '#64748b',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                fontSize: '0.8125rem',
                fontWeight: 600,
              }}
            >
              MFA não configurado
            </span>
            <button
              onClick={handleStartSetup}
              disabled={mfaSetup.isPending}
              style={{
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {mfaSetup.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Ativar MFA'
              )}
            </button>
          </div>
        )}

        {/* scan */}
        {mfaStep === 'scan' && mfaData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
              Escaneie o QR Code com Google Authenticator, Authy ou similar:
            </p>
            <QRCodeSVG value={mfaData.provisioning_uri} size={200} />
            <div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', marginBottom: '0.375rem' }}>
                Ou adicione manualmente a chave secreta:
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <code
                  style={{
                    background: '#f1f5f9',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8125rem',
                    letterSpacing: '0.05em',
                  }}
                >
                  {mfaData.secret}
                </code>
                <button
                  onClick={handleCopySecret}
                  style={{
                    background: 'none',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                  }}
                >
                  Copiar
                </button>
              </div>
            </div>
            <button
              onClick={() => setMfaStep('verify')}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Já escaniei, continuar →
            </button>
          </div>
        )}

        {/* verify */}
        {mfaStep === 'verify' && mfaData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
              Digite o código de 6 dígitos exibido no seu aplicativo autenticador:
            </p>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              autoFocus
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              style={{
                width: '8rem',
                padding: '0.5rem',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                fontSize: '1.25rem',
                textAlign: 'center',
                letterSpacing: '0.2em',
              }}
            />
            <button
              onClick={handleVerify}
              disabled={mfaVerify.isPending || verifyCode.length !== 6}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {mfaVerify.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Verificar'
              )}
            </button>
          </div>
        )}

        {/* active */}
        {mfaStep === 'active' && (
          <span
            style={{
              background: '#dcfce7',
              color: '#16a34a',
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.8125rem',
              fontWeight: 600,
            }}
          >
            ✓ MFA ativo
          </span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript. Se `QRCodeSVG` não for encontrado, confirmar que `npm install qrcode.react` foi executado na Task 1.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ConfiguracoesPage.tsx
git commit -m "feat: add ConfiguracoesPage with MFA setup wizard"
```

---

## Task 6: OrcamentoDetailPage — Status select inline

**Files:**
- Modify: `frontend/src/pages/OrcamentoDetailPage.tsx`

> `useUpdateOrcamento` já existe e faz PATCH `/orcamentos/:id`.
> O campo `status` no `detail-grid` substitui `<StatusBadge status={data.status} />`.
> Adicionar `useUpdateOrcamento` aos imports de hooks.

- [ ] **Step 1: Adicionar `useUpdateOrcamento` ao import de hooks em `OrcamentoDetailPage.tsx`**

Linha atual (linha 11-17):
```typescript
import {
  useCalcularFicha,
  useDeleteFicha,
  useDeleteOrcamento,
  useFichas,
  useOrcamento,
  useSpreading,
} from '../hooks/useApi';
```

Substituir por:
```typescript
import {
  useCalcularFicha,
  useDeleteFicha,
  useDeleteOrcamento,
  useFichas,
  useOrcamento,
  useSpreading,
  useUpdateOrcamento,
} from '../hooks/useApi';
```

- [ ] **Step 2: Adicionar a constante `STATUS_OPTIONS` e o hook `useUpdateOrcamento` após as declarações de estado existentes**

Após a linha `const spreading = useSpreading();` (linha 34), adicionar:

```typescript
const updateStatusMutation = useUpdateOrcamento();

const STATUS_OPTIONS = [
  { value: 'rascunho',   label: 'Rascunho' },
  { value: 'em_revisao', label: 'Em Revisão' },
  { value: 'aprovado',   label: 'Aprovado' },
  { value: 'cancelado',  label: 'Cancelado' },
] as const;
```

- [ ] **Step 3: Adicionar o handler `handleStatusChange` após o handler `handleSpreading`**

Após o fechamento de `handleSpreading` (após linha 94), adicionar:

```typescript
async function handleStatusChange(newStatus: string) {
  try {
    await updateStatusMutation.mutateAsync({ id: id!, payload: { status: newStatus } });
    toast.success('Status atualizado.');
  } catch {
    // error toast shown by mutation
  }
}
```

- [ ] **Step 4: Substituir `<StatusBadge status={data.status} />` pelo select inline**

Localizar no JSX (linhas ~162-165):
```tsx
<div className="detail-field">
  <label>Status</label>
  <StatusBadge status={data.status} />
</div>
```

Substituir por:
```tsx
<div className="detail-field">
  <label>Status</label>
  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
    <select
      value={data.status}
      onChange={(e) => handleStatusChange(e.target.value)}
      disabled={updateStatusMutation.isPending}
      className="status-select"
    >
      {STATUS_OPTIONS.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
    {updateStatusMutation.isPending && (
      <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
    )}
  </div>
</div>
```

- [ ] **Step 5: Remover import de `StatusBadge` se não usado em nenhum outro lugar da página**

Verificar se `StatusBadge` aparece em outra parte de `OrcamentoDetailPage.tsx`. Se não aparecer, remover da linha de import:

```typescript
import { StatusBadge } from '../components/ui/StatusBadge';
```

(Remover essa linha inteiramente — o componente ainda existe para outras pages, apenas não é importado aqui.)

- [ ] **Step 6: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript. O componente `StatusBadge` não é deletado — apenas deixa de ser importado nesta página.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/OrcamentoDetailPage.tsx
git commit -m "feat: replace StatusBadge with inline status select on OrcamentoDetailPage"
```

---

## Task 7: AuditoriaPage

**Files:**
- Create: `frontend/src/pages/AuditoriaPage.tsx`

> `useAuditStatus` é um query (GET automático ao montar).
> `useAuditVerify` é uma mutation (GET explícito via botão).
> Erro 403 vem como `axios.isAxiosError(error) && error.response?.status === 403`.
> `extractErrorMessage` em `useApi.ts` já retorna mensagem para 403 — o toast do `onError` é suficiente.
> Para exibir mensagem específica de 403 em lugar do spinner, verificar `error` do useAuditStatus.

- [ ] **Step 1: Criar `frontend/src/pages/AuditoriaPage.tsx`**

```tsx
import axios from 'axios';
import { useAuditStatus, useAuditVerify } from '../hooks/useApi';
import type { AuditStatusValue } from '../types';

const AUDIT_BADGE: Record<AuditStatusValue, { label: string; className: string }> = {
  OK:        { label: '✓ Cadeia íntegra',      className: 'audit-badge ok' },
  CORRUPTED: { label: '✗ Corrupção detectada', className: 'audit-badge corrupted' },
  PENDING:   { label: 'Verificação pendente',  className: 'audit-badge pending' },
  EMPTY:     { label: 'Sem registros',          className: 'audit-badge empty' },
};

export function AuditoriaPage() {
  const { data, isLoading, error } = useAuditStatus();
  const auditVerify = useAuditVerify();

  const is403 =
    axios.isAxiosError(error) && error.response?.status === 403;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Auditoria de Integridade</h1>
      </div>

      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
          maxWidth: '560px',
        }}
      >
        {isLoading && (
          <div className="loading-center" style={{ minHeight: '6rem' }}>
            <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
          </div>
        )}

        {is403 && (
          <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>
            Acesso restrito a administradores.
          </p>
        )}

        {!isLoading && !is403 && data && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <span className={AUDIT_BADGE[data.status].className}>
              {AUDIT_BADGE[data.status].label}
            </span>

            <div style={{ fontSize: '0.875rem', color: 'var(--muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {data.checked_at && (
                <span>Última verificação: {new Date(data.checked_at).toLocaleString('pt-BR')}</span>
              )}
              {data.total_entries !== undefined && (
                <span>Total de entradas: {data.total_entries}</span>
              )}
              {data.corrupted_entry && (
                <span style={{ color: '#dc2626' }}>
                  Entrada corrompida: <code>{data.corrupted_entry}</code>
                </span>
              )}
            </div>

            <button
              onClick={() => auditVerify.mutate()}
              disabled={auditVerify.isPending}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                padding: '0.4rem 0.875rem',
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {auditVerify.isPending ? (
                <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />
              ) : (
                'Verificar agora'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar build**

```bash
cd frontend && npm run build
```

Expected: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/AuditoriaPage.tsx
git commit -m "feat: add AuditoriaPage with integrity status and verify button"
```

---

## Task 8: App.tsx + Sidebar.tsx + CSS

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ui/Sidebar.tsx`
- Modify: `frontend/src/index.css`

### App.tsx

- [ ] **Step 1: Adicionar imports das duas novas páginas em `frontend/src/App.tsx`**

Após os imports existentes de páginas (após linha 11 `import { OrcamentoEditPage }`):

```typescript
import { ConfiguracoesPage } from './pages/ConfiguracoesPage';
import { AuditoriaPage } from './pages/AuditoriaPage';
```

- [ ] **Step 2: Adicionar as duas novas rotas dentro do bloco `<Route element={<ProtectedRoute>...`**

Após `<Route path="/orcamentos/:id/editar" element={<OrcamentoEditPage />} />` (antes do fechamento `</Route>`):

```tsx
<Route path="/configuracoes" element={<ConfiguracoesPage />} />
<Route path="/admin/auditoria" element={<AuditoriaPage />} />
```

O bloco de rotas deve ficar assim:
```tsx
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
  <Route path="/configuracoes" element={<ConfiguracoesPage />} />
  <Route path="/admin/auditoria" element={<AuditoriaPage />} />
</Route>
```

### Sidebar.tsx

- [ ] **Step 3: Substituir o conteúdo de `frontend/src/components/ui/Sidebar.tsx`**

```tsx
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
        <NavLink
          to="/configuracoes"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          ⚙️ Configurações
        </NavLink>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '0.5rem 0' }} />
        <NavLink
          to="/admin/auditoria"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          🔍 Auditoria
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <button onClick={logout}>Sair</button>
      </div>
    </aside>
  );
}
```

### CSS

- [ ] **Step 4: Adicionar as classes `.status-select` e `.audit-badge` ao final de `frontend/src/index.css`**

```css
/* ── Status select inline ── */
.status-select {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  background: var(--background);
  color: var(--foreground);
  cursor: pointer;
}

.status-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Audit badges ── */
.audit-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.875rem;
}

.audit-badge.ok        { background: #dcfce7; color: #16a34a; }
.audit-badge.corrupted { background: #fee2e2; color: #dc2626; }
.audit-badge.pending   { background: #f1f5f9; color: #64748b; }
.audit-badge.empty     { background: #fef9c3; color: #a16207; }
```

- [ ] **Step 5: Verificar build final**

```bash
cd frontend && npm run build
```

Expected: `✓ built in Xs` sem nenhum erro TypeScript ou de import.

- [ ] **Step 6: Commit final**

```bash
git add frontend/src/App.tsx frontend/src/components/ui/Sidebar.tsx frontend/src/index.css
git commit -m "feat: wire up Fase 7 routes, sidebar links, and CSS"
```

---

## Critérios de Aceitação (verificação manual)

Após o build passar, verificar no browser:

- [ ] Login → acesso a `/orcamentos` funciona normalmente
- [ ] Sidebar exibe links "Configurações" e "Auditoria"
- [ ] `/configuracoes` → botão "Ativar MFA" chama `POST /auth/mfa/setup` → mostra QR + chave
- [ ] Copiar chave funciona (toast "Chave copiada!")
- [ ] Step "Verificar" aceita só 6 dígitos; botão disabled antes de 6 dígitos
- [ ] `/admin/auditoria` exibe badge colorido com status atual
- [ ] Botão "Verificar agora" dispara `GET /admin/audit/verify` e atualiza badge sem reload
- [ ] 403 em auditoria exibe "Acesso restrito a administradores"
- [ ] Campo Status em `/orcamentos/:id` é um select; trocar envia PATCH e mostra toast
- [ ] Token expirado → interceptor faz refresh → request retentada transparentemente
- [ ] `npm run build` sem erros
