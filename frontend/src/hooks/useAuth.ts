import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const login = useCallback(async (data: { email: string; senha: string; tenant_id?: string }) => {
    setIsLoading(true);
    try {
      // Mock tenant_id se não fornecido (para bater com o snippet do user que não tinha tenant_id)
      const tenant_id = data.tenant_id || '00000000-0000-0000-0000-000000000000';
      
      const response = await api.post('/auth/login', {
        email: data.email,
        password: data.senha, // Mapeando senha para password do backend
        tenant_id
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('tenant_id', tenant_id);
        navigate('/dashboard');
      }
      return response.data;
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('tenant_id');
    navigate('/login');
  }, [navigate]);

  return { 
    login, 
    logout, 
    isLoading,
    isAuthenticated: !!localStorage.getItem('token') 
  };
}
