import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export function useApi() {
  const queryClient = useQueryClient();

  const useFetch = (key: string[], url: string) => {
    return useQuery({
      queryKey: key,
      queryFn: async () => {
        const response = await api.get(url);
        return response.data;
      },
    });
  };

  const usePost = (url: string, successKey?: string[]) => {
    return useMutation({
      mutationFn: async (data: any) => {
        const response = await api.post(url, data);
        return response.data;
      },
      onSuccess: () => {
        if (successKey) {
          queryClient.invalidateQueries({ queryKey: successKey });
        }
      },
    });
  };

  return { useFetch, usePost };
}
