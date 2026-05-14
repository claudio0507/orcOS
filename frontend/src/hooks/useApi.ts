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
