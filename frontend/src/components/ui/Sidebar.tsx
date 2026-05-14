// src/components/ui/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function Sidebar() {
  const { logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">orcOS</div>
      <nav className="sidebar-nav">
        <NavLink
          to="/orcamentos"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          📋 Orçamentos
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <button onClick={logout}>Sair</button>
      </div>
    </aside>
  );
}
