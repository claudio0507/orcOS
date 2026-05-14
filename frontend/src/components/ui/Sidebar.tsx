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
        <NavLink
          to="/configuracoes"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          ⚙️ Configurações
        </NavLink>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '0.5rem 0' }} />
        <NavLink
          to="/admin/auditoria"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          🔍 Auditoria
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <button onClick={logout}>Sair</button>
      </div>
    </aside>
  );
}
