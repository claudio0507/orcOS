// src/App.tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from './components/ui/AppLayout';
import { ProtectedRoute } from './components/ui/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { OrcamentosListPage } from './pages/OrcamentosListPage';
import { OrcamentoCreatePage } from './pages/OrcamentoCreatePage';
import { OrcamentoDetailPage } from './pages/OrcamentoDetailPage';
import { OrcamentoEditPage } from './pages/OrcamentoEditPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
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
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
