// src/hooks/useApi.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { api } from '../services/api';
import type {
  AuditStatusResponse,
  Ficha,
  FichaCalcResult,
  MfaSetupResponse,
  MfaVerifyRequest,
  Orcamento,
  SpreadingResponse,
} from '../types';

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
  status?: string;
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
    retry: false,
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
