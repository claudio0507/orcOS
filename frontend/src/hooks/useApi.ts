import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Orcamento } from '../types';

export function useOrcamentos() {
  return useQuery({
    queryKey: ['orcamentos'],
    queryFn: async () => {
      const response = await api.get<{ items: Orcamento[], total: number }>('/orcamentos');
      return response.data;
    },
  });
}
