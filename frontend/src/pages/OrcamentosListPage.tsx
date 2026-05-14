// src/pages/OrcamentosListPage.tsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useDeleteOrcamento, useOrcamentos } from '../hooks/useApi';
import { formatCurrency, formatDateShort } from '../utils/format';

export function OrcamentosListPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useOrcamentos();
  const deleteMutation = useDeleteOrcamento();

  const [deleteTarget, setDeleteTarget] = useState<{ id: string; titulo: string } | null>(null);

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast.success('Orçamento excluído.');
      setDeleteTarget(null);
    } catch {
      // error toast already shown by useDeleteOrcamento onError
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Orçamentos</h1>
        <Button onClick={() => navigate('/orcamentos/novo')}>+ Novo Orçamento</Button>
      </div>

      {isLoading && (
        <div className="loading-center">
          <span className="spinner" style={{ width: '2rem', height: '2rem' }} />
        </div>
      )}

      {error && (
        <p className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
          Erro ao carregar orçamentos. Tente novamente.
        </p>
      )}

      {data && data.items.length === 0 && (
        <div className="empty-state">
          <p style={{ marginBottom: '1rem' }}>Nenhum orçamento encontrado.</p>
          <Button onClick={() => navigate('/orcamentos/novo')}>Criar primeiro orçamento</Button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Título</th>
                <th>Status</th>
                <th>Custo Fixo</th>
                <th>Criado em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((orc) => (
                <tr key={orc.id}>
                  <td style={{ fontWeight: 500 }}>{orc.titulo}</td>
                  <td><StatusBadge status={orc.status} /></td>
                  <td>{formatCurrency(orc.custo_fixo_total)}</td>
                  <td className="muted">{formatDateShort(orc.created_at)}</td>
                  <td>
                    <div className="table-actions">
                      <Link className="action-btn" to={`/orcamentos/${orc.id}`}>
                        Ver
                      </Link>
                      <Link className="action-btn" to={`/orcamentos/${orc.id}/editar`}>
                        Editar
                      </Link>
                      <button
                        className="action-btn danger"
                        onClick={() => setDeleteTarget({ id: orc.id, titulo: orc.titulo })}
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Excluir orçamento?"
        message={`"${deleteTarget?.titulo}" será removido permanentemente.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
