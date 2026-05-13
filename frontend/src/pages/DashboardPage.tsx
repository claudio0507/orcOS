import { useOrcamentos } from '../hooks/useApi';
import { useAuth } from '../hooks/useAuth';

export function DashboardPage() {
  const { data, isLoading, error } = useOrcamentos();
  const { logout } = useAuth();

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Dashboard orcOS</h1>
        <button onClick={logout}>Sair</button>
      </header>
      
      <p>Bem-vindo ao sistema de orçamentos.</p>

      <section>
        <h2>Meus Orçamentos</h2>
        {isLoading && <p>Carregando...</p>}
        {error && <p>Erro ao carregar orçamentos.</p>}
        
        {data && (
          <ul>
            {data.items.map((orc) => (
              <li key={orc.id}>
                <strong>{orc.titulo}</strong> - R$ {orc.custo_fixo_total} ({orc.status})
              </li>
            ))}
            {data.items.length === 0 && <li>Nenhum orçamento encontrado.</li>}
          </ul>
        )}
      </section>
    </div>
  );
}
