# Fase 6 — CRUD de Fichas + Spreading UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar CRUD completo de fichas (itens de serviço/insumo) inline na OrcamentoDetailPage, cálculo de preço unitário por ficha via pricing engine, e spreading de custos fixos com resultado tabular.

**Architecture:** Fichas aparecem inline em `OrcamentoDetailPage` abaixo dos dados do orçamento. Form de criação/edição expande inline (não modal, não navegação). Todos os 3 tipos de precificação suportados (Markup, BDI Clássico, BDI Manual). Spreading substitui a tabela de fichas por resultado detalhado com badge CA-001.

**Tech Stack:** React 18, React Router 6, React Query 5, Zod, react-hook-form + useFieldArray, Axios, react-hot-toast, CSS customizado. Working directory: `G:\Meu Drive\orcOS\frontend`.

---

## File Map

| Ação | Arquivo | Responsabilidade |
|---|---|---|
| Modify | `src/types/index.ts` | Adicionar FichaCalcResult, SpreadingResultLine, SpreadingResponse |
| Modify | `src/hooks/useApi.ts` | 6 novos hooks + fix extractErrorMessage para 403 |
| Modify | `src/index.css` | Classes CSS para seção fichas, form inline, BDI Manual, spreading |
| Create | `src/components/ui/FichaForm.tsx` | Form Zod+RHF com campos dinâmicos por tipo de precificação |
| Create | `src/components/ui/SpreadingResultTable.tsx` | Tabela resultado spreading + badge CA-001 |
| Modify | `src/pages/OrcamentoDetailPage.tsx` | Substituir placeholder por seção fichas completa |

---

## Task 1: Tipos novos + fix extractErrorMessage

**Files:**
- Modify: `src/types/index.ts`
- Modify: `src/hooks/useApi.ts`

- [ ] **Step 1: Sobrescrever `src/types/index.ts` com os novos tipos**

```typescript
// src/types/index.ts
export enum TipoPrecificacao {
  MARKUP = 'markup',
  BDI_MANUAL = 'bdi_manual',
  BDI_CLASSICO = 'bdi_classico',
}

export interface Orcamento {
  id: string;
  titulo: string;
  descricao: string | null;
  tenant_id: string;
  status: string;
  custo_fixo_total: string;
  created_at: string;
  updated_at: string;
}

export interface Ficha {
  id: string;
  orcamento_id: string;
  tenant_id: string;
  descricao: string;
  unidade: string;
  quantidade: string;
  custo_unitario: string;
  tipo_precificacao: TipoPrecificacao | string;
  preco_unitario_calculado: string | null;
  ordem: number;
  created_at: string;
  updated_at: string;
}

export interface FichaCalcResult {
  ficha_id: string;
  preco_unitario: string;
  divisor: string | null;
  is_alert: boolean;
  detalhes: Record<string, string>;
}

export interface SpreadingResultLine {
  ficha_id: string;
  descricao: string;
  variable_unit_price: string;
  quantity: string;
  allocated_fixed: string;
  final_unit_price: string;
  final_line_total: string;
  carries_residue: boolean;
}

export interface SpreadingResponse {
  orcamento_id: string;
  custo_fixo_total: string;
  total_variavel: string;
  total_final: string;
  residuo_aplicado: boolean;
  linhas: SpreadingResultLine[];
  ca001_validado: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  tenant_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string | null;
  mfa_required: boolean;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  nome: string;
  tenant_id: string;
}

export interface MfaLoginRequest {
  partial_token: string;
  totp_code: string;
}
```

- [ ] **Step 2: Atualizar `extractErrorMessage` em `src/hooks/useApi.ts` para tratar 403**

Substituir apenas a função `extractErrorMessage` (linhas 9-16 do arquivo atual):

```typescript
function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 403) {
      return 'Autenticação de dois fatores necessária para esta ação.';
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  }
  return 'Erro inesperado. Tente novamente.';
}
```

- [ ] **Step 3: Verificar compilação**

```bash
npm run build 2>&1 | head -20
```

Esperado: sem erros TypeScript.

- [ ] **Step 4: Commit**

```bash
git add src/types/index.ts src/hooks/useApi.ts
git commit -m "feat: adiciona tipos FichaCalcResult e SpreadingResponse, trata 403 no extractErrorMessage"
```

---

## Task 2: Novos hooks de fichas em `useApi.ts`

**Files:**
- Modify: `src/hooks/useApi.ts`

- [ ] **Step 1: Sobrescrever `src/hooks/useApi.ts` com todos os hooks (existentes + novos)**

```typescript
// src/hooks/useApi.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { api } from '../services/api';
import type { Ficha, FichaCalcResult, Orcamento, SpreadingResponse } from '../types';

// ── Helpers ──────────────────────────────────────────────────────
function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 403) {
      return 'Autenticação de dois fatores necessária para esta ação.';
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  }
  return 'Erro inesperado. Tente novamente.';
}

// ── Orcamento Queries ──────────────────────────────────────────────
export function useOrcamentos() {
  return useQuery({
    queryKey: ['orcamentos'],
    queryFn: async () => {
      const response = await api.get<{ items: Orcamento[]; total: number }>('/orcamentos');
      return response.data;
    },
  });
}

export function useOrcamento(id: string | undefined) {
  return useQuery({
    queryKey: ['orcamento', id],
    queryFn: async () => {
      const response = await api.get<Orcamento>(`/orcamentos/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// ── Orcamento Mutations ────────────────────────────────────────────
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

// ── Ficha Query ────────────────────────────────────────────────────
export function useFichas(orcamentoId: string | undefined) {
  return useQuery({
    queryKey: ['fichas', orcamentoId],
    queryFn: async () => {
      const response = await api.get<Ficha[]>(`/orcamentos/${orcamentoId}/fichas`);
      return response.data;
    },
    enabled: !!orcamentoId,
  });
}

// ── Ficha Mutations ────────────────────────────────────────────────
export interface FichaPayload {
  descricao: string;
  unidade: string;
  quantidade: string;
  custo_unitario: string;
  tipo_precificacao: string;
  ordem: number;
  parametros_precificacao: Record<string, unknown> | null;
}

export function useCreateFicha() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      orcamentoId,
      payload,
    }: {
      orcamentoId: string;
      payload: FichaPayload;
    }) => {
      const response = await api.post<Ficha>(`/orcamentos/${orcamentoId}/fichas`, payload);
      return response.data;
    },
    onSuccess: (_data, { orcamentoId }) => {
      queryClient.invalidateQueries({ queryKey: ['fichas', orcamentoId] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useUpdateFicha() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      orcamentoId,
      fichaId,
      payload,
    }: {
      orcamentoId: string;
      fichaId: string;
      payload: Partial<FichaPayload>;
    }) => {
      const response = await api.patch<Ficha>(
        `/orcamentos/${orcamentoId}/fichas/${fichaId}`,
        payload,
      );
      return response.data;
    },
    onSuccess: (_data, { orcamentoId }) => {
      queryClient.invalidateQueries({ queryKey: ['fichas', orcamentoId] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useDeleteFicha() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      orcamentoId,
      fichaId,
    }: {
      orcamentoId: string;
      fichaId: string;
    }) => {
      await api.delete(`/orcamentos/${orcamentoId}/fichas/${fichaId}`);
    },
    onSuccess: (_data, { orcamentoId }) => {
      queryClient.invalidateQueries({ queryKey: ['fichas', orcamentoId] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useCalcularFicha() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      orcamentoId,
      fichaId,
    }: {
      orcamentoId: string;
      fichaId: string;
    }) => {
      const response = await api.post<FichaCalcResult>(
        `/orcamentos/${orcamentoId}/fichas/${fichaId}/calcular`,
      );
      return response.data;
    },
    onSuccess: (_data, { orcamentoId }) => {
      queryClient.invalidateQueries({ queryKey: ['fichas', orcamentoId] });
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}

export function useSpreading() {
  return useMutation({
    mutationFn: async (orcamentoId: string) => {
      const response = await api.post<SpreadingResponse>(
        `/orcamentos/${orcamentoId}/spreading`,
      );
      return response.data;
    },
    onError: (error: unknown) => {
      toast.error(extractErrorMessage(error));
    },
  });
}
```

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -20
```

Esperado: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add src/hooks/useApi.ts
git commit -m "feat: hooks CRUD fichas — useFichas, useCreate/Update/DeleteFicha, useCalcularFicha, useSpreading"
```

---

## Task 3: CSS — classes para seção fichas e spreading

**Files:**
- Modify: `src/index.css`

- [ ] **Step 1: Adicionar ao final de `src/index.css`**

```css
/* ── Fichas Section ──────────────────────────────────────────────── */
.fichas-section {
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
  margin-top: 1.5rem;
}

.fichas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.fichas-header h2 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--foreground);
}

/* ── Ficha Form Inline ───────────────────────────────────────────── */
.ficha-form-inline {
  background: var(--background);
  border: 2px solid var(--primary);
  border-radius: var(--radius);
  padding: 1.25rem;
  margin-bottom: 0.75rem;
}

.param-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.param-grid-5 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.bdi-manual-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 2fr auto;
  gap: 0.5rem;
  align-items: flex-start;
  padding: 0.5rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
}

/* ── Spreading ───────────────────────────────────────────────────── */
.spreading-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 500;
}

.spreading-badge.ok {
  background: #dcfce7;
  color: #16a34a;
}

.spreading-badge.warn {
  background: #fef9c3;
  color: #a16207;
}

.spreading-table th:last-child,
.spreading-table td:last-child {
  font-weight: 600;
  color: #16a34a;
}

/* ── Ficha table inline form row ─────────────────────────────────── */
.ficha-inline-form-row td {
  padding: 0.75rem 0 0.75rem 0;
  background: var(--background);
}

@media (max-width: 768px) {
  .param-grid-3,
  .param-grid-5 {
    grid-template-columns: 1fr;
  }

  .bdi-manual-row {
    grid-template-columns: 1fr 1fr;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/index.css
git commit -m "feat: CSS para seção fichas, form inline, BDI Manual rows e spreading badge"
```

---

## Task 4: FichaForm — form inline com campos dinâmicos por tipo

**Files:**
- Create: `src/components/ui/FichaForm.tsx`

- [ ] **Step 1: Criar `src/components/ui/FichaForm.tsx`**

```tsx
// src/components/ui/FichaForm.tsx
import { useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './Button';
import { Input } from './Input';
import { useCreateFicha, useUpdateFicha } from '../../hooks/useApi';
import type { FichaPayload } from '../../hooks/useApi';

const pct = z.coerce
  .number({ invalid_type_error: 'Número obrigatório' })
  .min(0, 'Mínimo 0')
  .lt(1, 'Máximo 0.9999 (ex: 0.12 = 12%)');

const fichaSchema = z
  .object({
    descricao:          z.string().min(1, 'Obrigatório').max(500, 'Máximo 500 caracteres'),
    unidade:            z.string().max(50).default('un'),
    quantidade:         z.string().regex(/^\d+(\.\d+)?$/, 'Número positivo (ex: 25.00)'),
    custo_unitario:     z.string().regex(/^\d+(\.\d{1,2})?$/, 'Formato: 100.00'),
    tipo_precificacao:  z.enum(['markup', 'bdi_manual', 'bdi_classico']),
    ordem:              z.coerce.number().int().min(0).default(0),
    markup_tributes:    pct.optional(),
    markup_profit:      pct.optional(),
    markup_indirect:    pct.optional(),
    bdi_administration: pct.optional(),
    bdi_financial:      pct.optional(),
    bdi_risk:           pct.optional(),
    bdi_profit:         pct.optional(),
    bdi_tributes:       pct.optional(),
    bdi_components: z
      .array(
        z.object({
          name:            z.string().min(1, 'Nome obrigatório'),
          percent:         pct,
          base:            z.enum(['revenue', 'cost']),
          legal_reference: z.string().default(''),
        }),
      )
      .optional(),
  })
  .superRefine((data, ctx) => {
    if (data.tipo_precificacao === 'markup') {
      if (data.markup_tributes === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_tributes'] });
      if (data.markup_profit === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_profit'] });
      if (data.markup_indirect === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_indirect'] });
    }
    if (data.tipo_precificacao === 'bdi_classico') {
      const fields = [
        'bdi_administration', 'bdi_financial', 'bdi_risk', 'bdi_profit', 'bdi_tributes',
      ] as const;
      for (const field of fields) {
        if (data[field] === undefined)
          ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: [field] });
      }
    }
    if (data.tipo_precificacao === 'bdi_manual') {
      if (!data.bdi_components?.length)
        ctx.addIssue({
          code: 'custom',
          message: 'Adicione ao menos um componente',
          path: ['bdi_components'],
        });
    }
  });

type FichaFormData = z.infer<typeof fichaSchema>;

function buildPayload(data: FichaFormData): FichaPayload {
  let parametros_precificacao: Record<string, unknown> | null = null;

  if (data.tipo_precificacao === 'markup') {
    parametros_precificacao = {
      tributes: String(data.markup_tributes),
      profit:   String(data.markup_profit),
      indirect: String(data.markup_indirect),
    };
  } else if (data.tipo_precificacao === 'bdi_classico') {
    parametros_precificacao = {
      administration: String(data.bdi_administration),
      financial:      String(data.bdi_financial),
      risk:           String(data.bdi_risk),
      profit:         String(data.bdi_profit),
      tributes:       String(data.bdi_tributes),
    };
  } else {
    parametros_precificacao = {
      components: (data.bdi_components ?? []).map((c) => ({
        name:            c.name,
        percent:         String(c.percent),
        base:            c.base,
        legal_reference: c.legal_reference,
      })),
    };
  }

  return {
    descricao:               data.descricao,
    unidade:                 data.unidade,
    quantidade:              data.quantidade,
    custo_unitario:          data.custo_unitario,
    tipo_precificacao:       data.tipo_precificacao,
    ordem:                   data.ordem,
    parametros_precificacao,
  };
}

interface FichaFormProps {
  orcamentoId: string;
  fichaId?: string;
  defaultValues?: Partial<
    Pick<FichaFormData, 'descricao' | 'unidade' | 'quantidade' | 'custo_unitario' | 'tipo_precificacao' | 'ordem'>
  >;
  onSuccess: () => void;
  onCancel: () => void;
}

export function FichaForm({
  orcamentoId,
  fichaId,
  defaultValues,
  onSuccess,
  onCancel,
}: FichaFormProps) {
  const createFicha = useCreateFicha();
  const updateFicha = useUpdateFicha();
  const isEditing = !!fichaId;
  const isLoading = createFicha.isPending || updateFicha.isPending;

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<FichaFormData>({
    resolver: zodResolver(fichaSchema),
    defaultValues: {
      tipo_precificacao: 'markup',
      unidade: 'un',
      ordem: 0,
      ...defaultValues,
    },
  });

  const tipo = watch('tipo_precificacao');
  const { fields, append, remove } = useFieldArray({ control, name: 'bdi_components' });

  const onSubmit = async (data: FichaFormData) => {
    const payload = buildPayload(data);
    try {
      if (isEditing) {
        await updateFicha.mutateAsync({ orcamentoId, fichaId: fichaId!, payload });
      } else {
        await createFicha.mutateAsync({ orcamentoId, payload });
      }
      onSuccess();
    } catch {
      // error toast shown by mutation onError
    }
  };

  return (
    <div className="ficha-form-inline">
      <p style={{ fontWeight: 600, marginBottom: '1rem', color: 'var(--foreground)' }}>
        {isEditing ? 'Editar ficha' : 'Nova ficha'}
      </p>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Input
          label="Descrição *"
          placeholder="Ex: Placa de sinalização R-1 (PARE) — 0,50×0,50m"
          error={errors.descricao?.message}
          {...register('descricao')}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
          <Input
            label="Unidade"
            placeholder="un"
            error={errors.unidade?.message}
            {...register('unidade')}
          />
          <Input
            label="Quantidade *"
            placeholder="ex: 25.00"
            error={errors.quantidade?.message}
            {...register('quantidade')}
          />
          <Input
            label="Custo unitário (R$) *"
            placeholder="ex: 450.00"
            error={errors.custo_unitario?.message}
            {...register('custo_unitario')}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
          <div className="input-group">
            <label className="input-label">Tipo de precificação *</label>
            <select
              className="textarea-field"
              style={{ height: '2.5rem', padding: '0 0.75rem' }}
              {...register('tipo_precificacao')}
            >
              <option value="markup">Markup</option>
              <option value="bdi_classico">BDI Clássico (DNIT)</option>
              <option value="bdi_manual">BDI Manual</option>
            </select>
          </div>
          <Input
            label="Ordem"
            type="number"
            placeholder="0"
            error={errors.ordem?.message}
            {...register('ordem')}
          />
        </div>

        {tipo === 'markup' && (
          <div className="param-grid-3">
            <Input
              label="Tributos (ex: 0.12)"
              placeholder="0.12"
              error={errors.markup_tributes?.message}
              {...register('markup_tributes')}
            />
            <Input
              label="Lucro (ex: 0.10)"
              placeholder="0.10"
              error={errors.markup_profit?.message}
              {...register('markup_profit')}
            />
            <Input
              label="Indiretas (ex: 0.05)"
              placeholder="0.05"
              error={errors.markup_indirect?.message}
              {...register('markup_indirect')}
            />
          </div>
        )}

        {tipo === 'bdi_classico' && (
          <div className="param-grid-5">
            <Input
              label="Administração"
              placeholder="0.04"
              error={errors.bdi_administration?.message}
              {...register('bdi_administration')}
            />
            <Input
              label="Financeiro"
              placeholder="0.012"
              error={errors.bdi_financial?.message}
              {...register('bdi_financial')}
            />
            <Input
              label="Risco"
              placeholder="0.01"
              error={errors.bdi_risk?.message}
              {...register('bdi_risk')}
            />
            <Input
              label="Lucro"
              placeholder="0.08"
              error={errors.bdi_profit?.message}
              {...register('bdi_profit')}
            />
            <Input
              label="Tributos"
              placeholder="0.1365"
              error={errors.bdi_tributes?.message}
              {...register('bdi_tributes')}
            />
          </div>
        )}

        {tipo === 'bdi_manual' && (
          <div style={{ marginTop: '0.5rem' }}>
            <p className="input-label" style={{ marginBottom: '0.5rem' }}>
              Componentes BDI
            </p>
            {fields.map((field, index) => (
              <div key={field.id} className="bdi-manual-row">
                <Input
                  label="Nome"
                  placeholder="ISS"
                  error={errors.bdi_components?.[index]?.name?.message}
                  {...register(`bdi_components.${index}.name`)}
                />
                <Input
                  label="%"
                  placeholder="0.05"
                  error={errors.bdi_components?.[index]?.percent?.message}
                  {...register(`bdi_components.${index}.percent`)}
                />
                <div className="input-group">
                  <label className="input-label">Base</label>
                  <select
                    className="textarea-field"
                    style={{ height: '2.5rem', padding: '0 0.75rem' }}
                    {...register(`bdi_components.${index}.base`)}
                  >
                    <option value="revenue">Receita</option>
                    <option value="cost">Custo</option>
                  </select>
                </div>
                <Input
                  label="Ref. legal (opcional)"
                  placeholder="Art. 65"
                  {...register(`bdi_components.${index}.legal_reference`)}
                />
                <button
                  type="button"
                  onClick={() => remove(index)}
                  style={{
                    alignSelf: 'flex-end',
                    marginBottom: '0.25rem',
                    background: 'none',
                    border: 'none',
                    color: 'var(--muted)',
                    cursor: 'pointer',
                    fontSize: '1.25rem',
                    lineHeight: 1,
                  }}
                  aria-label="Remover componente"
                >
                  ✕
                </button>
              </div>
            ))}
            {typeof errors.bdi_components?.message === 'string' && (
              <p className="error-message">{errors.bdi_components.message}</p>
            )}
            <button
              type="button"
              onClick={() => append({ name: '', percent: 0, base: 'revenue', legal_reference: '' })}
              style={{
                fontSize: '0.875rem',
                color: 'var(--primary)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '0.25rem 0',
                marginBottom: '0.75rem',
              }}
            >
              + Adicionar componente
            </button>
          </div>
        )}

        <div className="form-actions">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <span className="spinner" />
            ) : isEditing ? (
              'Salvar alterações'
            ) : (
              'Criar ficha'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
```

**Nota importante:** Ao editar uma ficha, os parâmetros de precificação (markup_tributes, bdi_*, etc.) **não são pré-preenchidos** porque a API não os retorna no `FichaRead`. O usuário deve reinserir os parâmetros ao editar. Os campos base (descrição, unidade, quantidade, custo, tipo, ordem) são pré-preenchidos normalmente.

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -30
```

Esperado: sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/FichaForm.tsx
git commit -m "feat: FichaForm inline com Zod+RHF e campos dinâmicos para Markup, BDI Clássico e BDI Manual"
```

---

## Task 5: SpreadingResultTable

**Files:**
- Create: `src/components/ui/SpreadingResultTable.tsx`

- [ ] **Step 1: Criar `src/components/ui/SpreadingResultTable.tsx`**

```tsx
// src/components/ui/SpreadingResultTable.tsx
import type { SpreadingResponse } from '../../types';
import { formatCurrency } from '../../utils/format';

interface SpreadingResultTableProps {
  result: SpreadingResponse;
  onClear: () => void;
}

export function SpreadingResultTable({ result, onClear }: SpreadingResultTableProps) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.75rem',
          flexWrap: 'wrap',
          gap: '0.5rem',
        }}
      >
        <span className={`spreading-badge ${result.ca001_validado ? 'ok' : 'warn'}`}>
          {result.ca001_validado ? '✓ CA-001 validado' : '⚠ CA-001 falhou'}
        </span>
        <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.875rem', color: 'var(--muted)' }}>
          <span>Variável: {formatCurrency(result.total_variavel)}</span>
          <span>Fixo: {formatCurrency(result.custo_fixo_total)}</span>
          <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>
            Total: {formatCurrency(result.total_final)}
          </span>
        </div>
      </div>

      <div className="table-container">
        <table className="spreading-table">
          <thead>
            <tr>
              <th>Descrição</th>
              <th>Qtd</th>
              <th>Preço var. (R$)</th>
              <th>Fixo rat. (R$)</th>
              <th>Preço final (R$)</th>
            </tr>
          </thead>
          <tbody>
            {result.linhas.map((linha) => (
              <tr key={linha.ficha_id}>
                <td>
                  {linha.descricao}
                  {linha.carries_residue && (
                    <span
                      title="Absorveu resíduo de arredondamento (±R$0,01)"
                      style={{ marginLeft: '0.25rem', fontSize: '0.75rem', color: 'var(--muted)' }}
                    >
                      *
                    </span>
                  )}
                </td>
                <td>{linha.quantity}</td>
                <td>{formatCurrency(linha.variable_unit_price)}</td>
                <td>+{formatCurrency(linha.allocated_fixed)}</td>
                <td>{formatCurrency(linha.final_unit_price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        style={{
          marginTop: '0.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <p style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
          * Absorveu resíduo de arredondamento monetário (tolerância ±R$0,01)
        </p>
        <button
          type="button"
          onClick={onClear}
          style={{
            fontSize: '0.875rem',
            color: 'var(--muted)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            textDecoration: 'underline',
          }}
        >
          Limpar resultado
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -20
```

Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/SpreadingResultTable.tsx
git commit -m "feat: SpreadingResultTable com badge CA-001 e detalhe por ficha"
```

---

## Task 6: OrcamentoDetailPage — seção fichas completa

**Files:**
- Modify: `src/pages/OrcamentoDetailPage.tsx`

- [ ] **Step 1: Sobrescrever `src/pages/OrcamentoDetailPage.tsx`**

```tsx
// src/pages/OrcamentoDetailPage.tsx
import { Fragment, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { FichaForm } from '../components/ui/FichaForm';
import { SpreadingResultTable } from '../components/ui/SpreadingResultTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import {
  useCalcularFicha,
  useDeleteFicha,
  useDeleteOrcamento,
  useFichas,
  useOrcamento,
  useSpreading,
} from '../hooks/useApi';
import type { Ficha, SpreadingResponse } from '../types';
import { formatCurrency, formatDateLong } from '../utils/format';

export function OrcamentoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // orcamento
  const { data, isLoading, error } = useOrcamento(id);
  const deleteMutation = useDeleteOrcamento();
  const [showDeleteOrcamento, setShowDeleteOrcamento] = useState(false);

  // fichas
  const { data: fichas = [], isLoading: fichasLoading } = useFichas(id);
  const calcularFicha = useCalcularFicha();
  const deleteFicha = useDeleteFicha();
  const spreading = useSpreading();

  // ui state
  const [openFormId, setOpenFormId] = useState<string | null>(null);
  const [deleteFichaId, setDeleteFichaId] = useState<string | null>(null);
  const [spreadingResult, setSpreadingResult] = useState<SpreadingResponse | null>(null);

  // ── Handlers orcamento ──────────────────────────────────────────
  async function handleDeleteOrcamento() {
    try {
      await deleteMutation.mutateAsync(id!);
      toast.success('Orçamento excluído.');
      navigate('/orcamentos');
    } catch {
      // error toast shown by mutation
    }
  }

  // ── Handlers fichas ─────────────────────────────────────────────
  function openEditForm(fichaId: string) {
    setOpenFormId(openFormId === fichaId ? null : fichaId);
  }

  function openNewForm() {
    setOpenFormId(openFormId === 'new' ? null : 'new');
  }

  async function handleCalcular(fichaId: string) {
    try {
      const result = await calcularFicha.mutateAsync({ orcamentoId: id!, fichaId });
      toast.success(`Preço calculado: ${formatCurrency(result.preco_unitario)}`);
    } catch {
      // error toast shown by mutation
    }
  }

  async function handleDeleteFicha() {
    if (!deleteFichaId) return;
    try {
      await deleteFicha.mutateAsync({ orcamentoId: id!, fichaId: deleteFichaId });
      toast.success('Ficha excluída.');
    } catch {
      // error toast shown by mutation
    } finally {
      setDeleteFichaId(null);
    }
  }

  async function handleSpreading() {
    try {
      const result = await spreading.mutateAsync(id!);
      setSpreadingResult(result);
      toast.success(`Spreading aplicado! Total: ${formatCurrency(result.total_final)}`);
    } catch {
      // error toast shown by mutation
    }
  }

  function fichaToDefaultValues(ficha: Ficha) {
    return {
      descricao:         ficha.descricao,
      unidade:           ficha.unidade,
      quantidade:        ficha.quantidade,
      custo_unitario:    ficha.custo_unitario,
      tipo_precificacao: ficha.tipo_precificacao as 'markup' | 'bdi_manual' | 'bdi_classico',
      ordem:             ficha.ordem,
    };
  }

  // ── Loading / Error states ──────────────────────────────────────
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
        <Link to="/orcamentos" style={{ marginTop: '1rem', display: 'block' }}>
          ← Voltar para lista
        </Link>
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────────────
  return (
    <div>
      {/* ── Cabeçalho ── */}
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
          <Button variant="outline" onClick={() => setShowDeleteOrcamento(true)}>
            Excluir
          </Button>
        </div>
      </div>

      {/* ── Detalhes do orçamento ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}
      >
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
            <p className="muted">{formatDateLong(data.created_at)}</p>
          </div>
          <div className="detail-field">
            <label>Atualizado em</label>
            <p className="muted">{formatDateLong(data.updated_at)}</p>
          </div>
          {data.descricao && (
            <div className="detail-field" style={{ gridColumn: '1 / -1' }}>
              <label>Descrição</label>
              <p>{data.descricao}</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Seção Fichas ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1.5rem',
        }}
      >
        <div className="fichas-header">
          <h2>Fichas</h2>
          <Button size="sm" onClick={openNewForm}>
            {openFormId === 'new' ? '✕ Fechar' : '+ Nova ficha'}
          </Button>
        </div>

        {/* Form de criação */}
        {openFormId === 'new' && (
          <FichaForm
            orcamentoId={id!}
            onSuccess={() => {
              setOpenFormId(null);
              toast.success('Ficha criada!');
            }}
            onCancel={() => setOpenFormId(null)}
          />
        )}

        {/* Loading fichas */}
        {fichasLoading && (
          <div className="loading-center" style={{ minHeight: '6rem' }}>
            <span className="spinner" />
          </div>
        )}

        {/* Estado vazio */}
        {!fichasLoading && fichas.length === 0 && (
          <div className="empty-state" style={{ minHeight: '6rem' }}>
            <p>Nenhuma ficha cadastrada.</p>
            {openFormId !== 'new' && (
              <button
                type="button"
                onClick={openNewForm}
                style={{
                  marginTop: '0.5rem',
                  color: 'var(--primary)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                + Adicionar primeira ficha
              </button>
            )}
          </div>
        )}

        {/* Tabela normal ou resultado de spreading */}
        {!fichasLoading && fichas.length > 0 && (
          <>
            {spreadingResult ? (
              <SpreadingResultTable
                result={spreadingResult}
                onClear={() => setSpreadingResult(null)}
              />
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Descrição</th>
                      <th>Unidade</th>
                      <th>Qtd</th>
                      <th>Custo unit. (R$)</th>
                      <th>Preço calc. (R$)</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fichas.map((ficha) => (
                      <Fragment key={ficha.id}>
                        <tr>
                          <td>{ficha.descricao}</td>
                          <td>{ficha.unidade}</td>
                          <td>{ficha.quantidade}</td>
                          <td>{formatCurrency(ficha.custo_unitario)}</td>
                          <td>
                            {ficha.preco_unitario_calculado
                              ? formatCurrency(ficha.preco_unitario_calculado)
                              : <span className="muted">—</span>}
                          </td>
                          <td>
                            <div className="table-actions">
                              <button
                                className="action-btn"
                                onClick={() => handleCalcular(ficha.id)}
                                disabled={calcularFicha.isPending}
                                title="Calcular preço unitário"
                              >
                                Calcular
                              </button>
                              <button
                                className="action-btn"
                                onClick={() => openEditForm(ficha.id)}
                                title="Editar ficha"
                              >
                                {openFormId === ficha.id ? 'Fechar' : 'Editar'}
                              </button>
                              <button
                                className="action-btn"
                                onClick={() => setDeleteFichaId(ficha.id)}
                                title="Excluir ficha"
                              >
                                Excluir
                              </button>
                            </div>
                          </td>
                        </tr>
                        {openFormId === ficha.id && (
                          <tr className="ficha-inline-form-row">
                            <td colSpan={6}>
                              <FichaForm
                                orcamentoId={id!}
                                fichaId={ficha.id}
                                defaultValues={fichaToDefaultValues(ficha)}
                                onSuccess={() => {
                                  setOpenFormId(null);
                                  toast.success('Ficha atualizada!');
                                }}
                                onCancel={() => setOpenFormId(null)}
                              />
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Rodapé: custo fixo + spreading */}
            <div
              style={{
                marginTop: '1.25rem',
                paddingTop: '1rem',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '1rem',
                flexWrap: 'wrap',
              }}
            >
              <p style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>
                Custo fixo total do orçamento:{' '}
                <strong style={{ color: 'var(--foreground)' }}>
                  {formatCurrency(data.custo_fixo_total)}
                </strong>
              </p>
              <Button
                onClick={handleSpreading}
                disabled={spreading.isPending || fichas.length === 0}
              >
                {spreading.isPending ? <span className="spinner" /> : 'Executar Spreading'}
              </Button>
            </div>
          </>
        )}
      </div>

      {/* ── Dialogs ── */}
      <ConfirmDialog
        open={showDeleteOrcamento}
        title="Excluir orçamento?"
        message={`"${data.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDeleteOrcamento}
        onCancel={() => setShowDeleteOrcamento(false)}
        isLoading={deleteMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteFichaId}
        title="Excluir ficha?"
        message="Esta ficha será removida permanentemente do orçamento."
        confirmLabel="Excluir"
        onConfirm={handleDeleteFicha}
        onCancel={() => setDeleteFichaId(null)}
        isLoading={deleteFicha.isPending}
      />
    </div>
  );
}
```

- [ ] **Step 2: Verificar compilação**

```bash
npm run build 2>&1 | head -30
```

Esperado: `✓ built in X.XXs` sem erros TypeScript.

- [ ] **Step 3: Commit**

```bash
git add src/pages/OrcamentoDetailPage.tsx
git commit -m "feat: seção fichas completa em OrcamentoDetailPage — CRUD inline, Calcular e Spreading"
```

---

## Task 7: Build final + Push

**Files:** nenhum novo

- [ ] **Step 1: Build limpo**

```bash
npm run build 2>&1
```

Esperado: `✓ built in X.XXs` sem erros ou warnings de TypeScript.

- [ ] **Step 2: Teste manual — fluxo completo**

Iniciar backend e frontend:
```bash
# terminal 1
cd "G:\Meu Drive\orcOS\backend"
uvicorn app.main:app --reload

# terminal 2
cd "G:\Meu Drive\orcOS\frontend"
npm run dev
```

Abrir http://localhost:5173 e executar em ordem:
1. Login → `/orcamentos`
2. Abrir detalhe de um orçamento
3. Clicar "+ Nova ficha" → form expande
4. Preencher: descrição "Placa R-1", unidade "un", quantidade "25.00", custo "450.00", tipo "Markup", tributos "0.12", lucro "0.10", indiretas "0.05" → Criar ficha
5. Toast "Ficha criada!" → linha aparece na tabela
6. Clicar "Calcular" na linha → toast "Preço calculado: R$ 616,44"
7. Preço aparece na coluna "Preço calc."
8. Clicar "Editar" → form expande abaixo da linha pré-preenchido (base) → alterar descrição → Salvar alterações
9. Toast "Ficha atualizada!" → linha atualiza
10. Clicar "Executar Spreading" → tabela substitui por SpreadingResultTable com badge CA-001
11. Clicar "Limpar resultado" → volta à tabela normal
12. Clicar "Excluir" em uma ficha → ConfirmDialog → confirmar → toast "Ficha excluída"

- [ ] **Step 3: Testar BDI Manual**

1. Criar nova ficha, selecionar "BDI Manual"
2. Clicar "+ Adicionar componente" → linha aparece
3. Preencher: nome "ISS", % "0.05", base "Receita"
4. Adicionar segundo componente: "PIS/COFINS", "0.0365", "Receita"
5. Salvar → ficha aparece na tabela

- [ ] **Step 4: Push**

```bash
cd "G:\Meu Drive\orcOS"
git push origin claude/project-analysis-improvements-rqi2e
```

---

## Critérios de Aceitação

- [ ] Criar ficha funciona (Markup, BDI Clássico, BDI Manual)
- [ ] Editar ficha funciona (form pré-preenchido com campos base)
- [ ] Calcular preço funciona por linha (toast com valor)
- [ ] Excluir ficha funciona (ConfirmDialog + toast; erro 403 com mensagem clara)
- [ ] Spreading funciona (tabela inline substitui lista + badge CA-001)
- [ ] Erro 403 em spreading mostra "Autenticação de dois fatores necessária para esta ação."
- [ ] Só um form aberto por vez
- [ ] `npm run build` sem erros TypeScript
