# Design: Fase 7 — Token Refresh + MFA Setup + Status + Auditoria

**Data:** 2026-05-14
**Status:** Aprovado
**Scope:** Quatro features frontend-only que completam o ciclo de vida do sistema: renovação automática de tokens, ativação de MFA pelo usuário, alteração inline de status de orçamento e painel de auditoria de integridade.

---

## Contexto

Backend FastAPI completamente implementado com endpoints para refresh de token, setup de MFA (TOTP), alteração de status de orçamento (via PATCH) e auditoria de cadeia de integridade (CA-006). Frontend React com Fases 5 e 6 entregues (CRUD completo de orçamentos e fichas + spreading). Esta fase preenche os quatro gaps funcionais restantes sem modificar o backend.

Stack existente: React 18, React Router 6, React Query 5, Zod, react-hook-form, Axios, react-hot-toast, CSS customizado.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Token refresh | Interceptor Axios em api.ts | Transparente para todos os hooks; sem duplicação |
| Retry de request | Axios original config | Evita loop infinito excluindo /auth/refresh e /auth/login |
| MFA QR code | qrcode.react + chave secreta (ambos) | Scan para celular + fallback manual para desktop |
| MFA step tracking | Estado local na página | Wizard simples, sem necessidade de React Query |
| Status change | Select inline no grid de detalhes | Menos cliques; auto-PATCH imediato |
| Status hook | Reutiliza useUpdateOrcamento | Sem hook adicional desnecessário |
| Auditoria access | Sem role check no frontend | Backend retorna 403; frontend exibe toast explicativo |
| Auditoria verify | GET /admin/audit/verify | Backend já implementado; retorna status atualizado |

---

## 1. Arquivos Criados e Modificados

| Ação | Arquivo | Responsabilidade |
|---|---|---|
| Modify | `src/services/api.ts` | Response interceptor 401: refresh → retry → logout |
| Modify | `src/types/index.ts` | Tipos MfaSetupResponse, AuditStatusResponse |
| Modify | `src/hooks/useApi.ts` | 4 novos hooks: useMfaSetup, useMfaVerify, useAuditStatus, useAuditVerify |
| Create | `src/pages/ConfiguracoesPage.tsx` | Wizard MFA 3 etapas + badge de status |
| Modify | `src/pages/OrcamentoDetailPage.tsx` | Campo status vira select inline com auto-PATCH |
| Create | `src/pages/AuditoriaPage.tsx` | Painel de status + botão verificar |
| Modify | `src/App.tsx` | Rotas /configuracoes e /admin/auditoria |
| Modify | `src/components/ui/Sidebar.tsx` | Links Configurações e Auditoria na sidebar |

---

## 2. Token Refresh — Interceptor 401

### Lógica do interceptor em `src/services/api.ts`

```typescript
// Após criar a instância axios `api`:
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Não interceptar refresh e login para evitar loop infinito
    const isAuthEndpoint =
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/mfa');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        localStorage.setItem('access_token', data.access_token);
        originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);
```

**Garantias:**
- `_retry: true` impede tentativas infinitas na mesma request
- Requests para `/auth/*` excluídas do interceptor
- Falha no refresh: `localStorage.clear()` + redirect para `/login`

---

## 3. Novos Tipos em `src/types/index.ts`

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

---

## 4. Novos Hooks em `src/hooks/useApi.ts`

```typescript
// MFA Setup — POST /auth/mfa/setup
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

// MFA Verify — POST /auth/mfa/verify
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

// Audit Status — GET /admin/audit/status
export function useAuditStatus() {
  return useQuery({
    queryKey: ['audit-status'],
    queryFn: async () => {
      const response = await api.get<AuditStatusResponse>('/admin/audit/status');
      return response.data;
    },
  });
}

// Audit Verify — GET /admin/audit/verify
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

---

## 5. ConfiguracoesPage — Wizard MFA

### Estrutura da página

```
ConfiguracoesPage (/configuracoes)
└── Seção "Autenticação de Dois Fatores"
    ├── [step === 'idle'] Badge "MFA não configurado" + botão "Ativar MFA"
    ├── [step === 'setup'] Spinner → resultado de useMfaSetup
    ├── [step === 'scan']
    │   ├── QR Code (qrcode.react com provisioning_uri)
    │   ├── Chave secreta + botão Copiar (navigator.clipboard)
    │   └── Botão "Já escaniei, continuar"
    └── [step === 'verify']
        ├── Input 6 dígitos (autoFocus, maxLength=6, inputMode=numeric)
        ├── Botão "Verificar" → useMfaVerify
        └── [success] Badge "✓ MFA ativo" + step volta a 'idle'
```

### Estado local

```typescript
type MfaStep = 'idle' | 'scan' | 'verify' | 'active';
const [mfaStep, setMfaStep] = useState<MfaStep>('idle');
const [mfaData, setMfaData] = useState<MfaSetupResponse | null>(null);
const [verifyCode, setVerifyCode] = useState('');
```

### Fluxo

1. Clicar "Ativar MFA" → `mfaSetup.mutateAsync()` → armazena `{ secret, provisioning_uri }` em `mfaData` → `setMfaStep('scan')`
2. Usuário escaneia QR ou copia chave → clica "Já escaniei, continuar" → `setMfaStep('verify')`
3. Usuário digita 6 dígitos → `mfaVerify.mutateAsync({ secret: mfaData.secret, totp_code: verifyCode })` → toast "MFA ativado com sucesso!" → `setMfaStep('active')`
4. Erro em verify: toast com mensagem de erro, código limpo, step permanece 'verify'

### Dependência

```bash
npm install qrcode.react
```

`QRCodeSVG` do `qrcode.react` recebe `value={mfaData.provisioning_uri}` e `size={200}`.

---

## 6. Status de Orçamento — Select Inline

### Modificação em `OrcamentoDetailPage.tsx`

O campo "Status" no `detail-grid` deixa de usar `<StatusBadge status={data.status} />` e passa a usar um `<select>`:

```tsx
const STATUS_OPTIONS = [
  { value: 'rascunho',   label: 'Rascunho' },
  { value: 'em_revisao', label: 'Em Revisão' },
  { value: 'aprovado',   label: 'Aprovado' },
  { value: 'cancelado',  label: 'Cancelado' },
] as const;

// No detail-grid:
<div className="detail-field">
  <label>Status</label>
  <select
    value={data.status}
    onChange={(e) => handleStatusChange(e.target.value)}
    disabled={updateStatusMutation.isPending}
    className="status-select"
  >
    {STATUS_OPTIONS.map((opt) => (
      <option key={opt.value} value={opt.value}>{opt.label}</option>
    ))}
  </select>
  {updateStatusMutation.isPending && <span className="spinner" style={{ width: '0.875rem', height: '0.875rem' }} />}
</div>
```

### Handler

```typescript
async function handleStatusChange(newStatus: string) {
  try {
    await updateMutation.mutateAsync({ id: id!, payload: { status: newStatus } });
    toast.success('Status atualizado.');
  } catch {
    // error toast shown by mutation
  }
}
```

**Usa `useUpdateOrcamento` existente** — sem novo hook.

### CSS novo (`.status-select`)

```css
.status-select {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  background: var(--background);
  color: var(--foreground);
  cursor: pointer;
}
```

---

## 7. AuditoriaPage — Painel de Integridade

### Estrutura

```
AuditoriaPage (/admin/auditoria)
├── Cabeçalho "Auditoria de Integridade"
└── Card
    ├── Badge de status
    │   ├── OK        → verde  "✓ Cadeia íntegra"
    │   ├── CORRUPTED → vermelho "✗ Corrupção detectada"
    │   ├── PENDING   → cinza  "Verificação pendente"
    │   └── EMPTY     → amarelo "Sem registros"
    ├── Informações (checked_at, total_entries, corrupted_entry se houver)
    ├── Loading: spinner quando useAuditStatus está carregando
    ├── Erro 403: mensagem "Acesso restrito a administradores"
    └── Botão "Verificar agora" → useAuditVerify → atualiza badge
```

### Componente de badge

```tsx
const AUDIT_BADGE: Record<AuditStatusValue, { label: string; className: string }> = {
  OK:        { label: '✓ Cadeia íntegra',       className: 'audit-badge ok' },
  CORRUPTED: { label: '✗ Corrupção detectada',  className: 'audit-badge corrupted' },
  PENDING:   { label: 'Verificação pendente',   className: 'audit-badge pending' },
  EMPTY:     { label: 'Sem registros',           className: 'audit-badge empty' },
};
```

### CSS de auditoria

```css
.audit-badge { display: inline-flex; align-items: center; gap: 0.5rem;
               padding: 0.5rem 1rem; border-radius: 9999px; font-weight: 600; }
.audit-badge.ok        { background: #dcfce7; color: #16a34a; }
.audit-badge.corrupted { background: #fee2e2; color: #dc2626; }
.audit-badge.pending   { background: #f1f5f9; color: #64748b; }
.audit-badge.empty     { background: #fef9c3; color: #a16207; }
```

---

## 8. Navegação — App.tsx + Sidebar.tsx

### Novas rotas em App.tsx

```tsx
<Route path="/configuracoes" element={<ProtectedRoute><ConfiguracoesPage /></ProtectedRoute>} />
<Route path="/admin/auditoria" element={<ProtectedRoute><AuditoriaPage /></ProtectedRoute>} />
```

### Sidebar — novos links

```tsx
// Seção principal (já existente):
<SidebarLink to="/orcamentos" label="Orçamentos" />

// Adicionar abaixo:
<SidebarLink to="/configuracoes" label="Configurações" />

// Seção admin (nova, após separador):
<hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '0.5rem 0' }} />
<SidebarLink to="/admin/auditoria" label="Auditoria" />
```

---

## Critérios de Aceitação

- [ ] Token expirado → request automática de refresh → usuário não percebe interrupção
- [ ] Refresh expirado → redirect para /login (sem loop)
- [ ] MFA setup: QR code visível + chave secreta copiável + verificação de código ativa MFA
- [ ] Status de orçamento alterável inline (select) sem navegação
- [ ] Toast de erro se PATCH de status falhar
- [ ] Painel de auditoria exibe status atual com badge colorido
- [ ] Botão "Verificar agora" dispara verificação e atualiza badge
- [ ] 403 em auditoria mostra toast "Acesso restrito a administradores"
- [ ] `npm run build` sem erros TypeScript

---

## Fora de Escopo

- Desativação de MFA (não há endpoint backend)
- Histórico de verificações de auditoria
- Role-based sidebar (link de auditoria visível para todos; backend protege)
- Notificação automática de CORRUPTED (sem WebSocket/polling)
- Paginação de entradas de auditoria
