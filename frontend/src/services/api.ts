import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token e tenant_id
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  const tenantId = localStorage.getItem('tenant_id');
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  } else {
    // Fallback temporário para desenvolvimento/demo
    config.headers['X-Tenant-ID'] = '00000000-0000-0000-0000-000000000000';
  }
  
  return config;
});
