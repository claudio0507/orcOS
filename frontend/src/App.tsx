import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

/**
 * App principal do orcOS.
 * Gerencia as rotas da aplicação usando React Router 6.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        
        {/* Redirecionamento padrão para dashboard ou login */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Fallback para rotas não encontradas */}
        <Route path="*" element={<div className="p-8 text-center">Página não encontrada (404)</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
