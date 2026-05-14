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
        const tenant_id = data.tenant_id || '395b1485-e979-411b-941d-9c152b4de585';
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
